from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import random
from database import get_db, User, Segment, UserSegment
from sqlalchemy import func

app = FastAPI()

@app.on_event("startup")
def startup_event():
    from database import init_db
    init_db()

class SegmentCreate(BaseModel):
    slug: str

class UserSegmentsUpdate(BaseModel):
    add: list[str] = []
    remove: list[str] = []

class DistributionRequest(BaseModel):
    percent: int

@app.post("/segments/")
def create_segment(segment: SegmentCreate, db: Session = Depends(get_db)):
    if db.query(Segment).filter(Segment.slug == segment.slug).first():
        raise HTTPException(400, "Segment already exists")
    
    new_segment = Segment(slug=segment.slug)
    db.add(new_segment)
    db.commit()
    return {"message": f"Segment {segment.slug} created"}

@app.delete("/segments/{slug}")
def delete_segment(slug: str, db: Session = Depends(get_db)):
    segment = db.query(Segment).filter(Segment.slug == slug).first()
    if not segment:
        raise HTTPException(404, "Segment not found")
    
    db.query(UserSegment).filter(UserSegment.segment_slug == slug).delete()
    db.delete(segment)
    db.commit()
    return {"message": f"Segment {slug} deleted"}

@app.post("/users/{user_id}/segments")
def update_user_segments(
    user_id: int, 
    update: UserSegmentsUpdate, 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()

    for slug in update.add:
        if not db.query(Segment).filter(Segment.slug == slug).first():
            raise HTTPException(404, f"Segment {slug} not found")
        
        try:
            user_segment = UserSegment(user_id=user_id, segment_slug=slug)
            db.add(user_segment)
            db.commit()
        except IntegrityError:
            db.rollback()
    
    for slug in update.remove:
        db.query(UserSegment).filter(
            UserSegment.user_id == user_id,
            UserSegment.segment_slug == slug
        ).delete()
        db.commit()
    
    return {"message": "Segments updated"}

@app.get("/users/{user_id}/segments")
def get_user_segments(user_id: int, db: Session = Depends(get_db)):

    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(404, "User not found")
    
    segments = db.query(UserSegment.segment_slug).filter(
        UserSegment.user_id == user_id
    ).all()
    
    return {
        "user_id": user_id,
        "segments": [s[0] for s in segments]
    }

@app.post("/segments/{slug}/distribute")
def distribute_segment(
    slug: str, 
    request: DistributionRequest, 
    db: Session = Depends(get_db)
):
    if not 0 <= request.percent <= 100:
        raise HTTPException(400, "Percent must be between 0 and 100")
    
    if not db.query(Segment).filter(Segment.slug == slug).first():
        raise HTTPException(404, "Segment not found")
    
    total_users = db.query(func.count(User.id)).scalar()
    
    if total_users == 0:
        raise HTTPException(404, "No users found")
    
    users_with_segment = [
        row[0] for row in 
        db.query(UserSegment.user_id)
        .filter(UserSegment.segment_slug == slug)
        .distinct()
        .all()
    ]
    
    all_users = [row[0] for row in db.query(User.id).all()]
    available_users = [uid for uid in all_users if uid not in users_with_segment]
    
    if not available_users:
        return {
            "segment": slug,
            "percent": request.percent,
            "users_added": 0,
            "message": "No available users without this segment"
        }
    
    target_count = int(len(available_users) * request.percent / 100)
    
    selected_users = random.sample(available_users, min(target_count, len(available_users)))
    
    added_count = 0
    for user_id in selected_users:
        try:
            exists = db.query(UserSegment).filter(
                UserSegment.user_id == user_id,
                UserSegment.segment_slug == slug
            ).first()
            
            if not exists:
                user_segment = UserSegment(user_id=user_id, segment_slug=slug)
                db.add(user_segment)
                added_count += 1
        except:
            continue
    db.commit()
    
    return {
        "segment": slug,
        "percent": request.percent,
        "users_added": added_count,
        "total_users": total_users,
        "available_users": len(available_users)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)