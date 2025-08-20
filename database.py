from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    segments = relationship('UserSegment', back_populates='user')

class Segment(Base):
    __tablename__ = 'segments'
    slug = Column(String(50), primary_key=True)
    users = relationship('UserSegment', back_populates='segment')

class UserSegment(Base):
    __tablename__ = 'user_segments'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    segment_slug = Column(String(50), ForeignKey('segments.slug'), primary_key=True)
    
    user = relationship('User', back_populates='segments')
    segment = relationship('Segment', back_populates='users')

engine = create_engine('sqlite:///user_segments.db', echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("БД создана")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Index('idx_user_id', UserSegment.user_id)
Index('idx_segment_slug', UserSegment.segment_slug)

if __name__ == "__main__":
    init_db()