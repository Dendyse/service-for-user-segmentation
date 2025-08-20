import requests
import random
import pytest

BASE_URL = "http://localhost:8000"
TEST_USER_ID = random.randint(10000, 99999)
TEST_SEGMENT_1 = "TEST_SEGMENT_1"
TEST_SEGMENT_2 = "TEST_SEGMENT_2"

@pytest.fixture(autouse=True)
def clean_up():
    yield
    requests.delete(f"{BASE_URL}/segments/{TEST_SEGMENT_1}", timeout=5)
    requests.delete(f"{BASE_URL}/segments/{TEST_SEGMENT_2}", timeout=5)

def test_segment_creation_and_deletion():
    response = requests.post(
        f"{BASE_URL}/segments/",
        json={"slug": TEST_SEGMENT_1},
        timeout=5
    )
    assert response.status_code == 200
    
    response = requests.post(
        f"{BASE_URL}/segments/",
        json={"slug": TEST_SEGMENT_1},
        timeout=5
    )
    assert response.status_code == 400
    
    response = requests.delete(f"{BASE_URL}/segments/{TEST_SEGMENT_1}", timeout=5)
    assert response.status_code == 200
    
    response = requests.delete(f"{BASE_URL}/segments/{TEST_SEGMENT_1}", timeout=5)
    assert response.status_code == 404

def test_user_segments_operations():
    requests.post(f"{BASE_URL}/segments/", json={"slug": TEST_SEGMENT_1}, timeout=5)
    requests.post(f"{BASE_URL}/segments/", json={"slug": TEST_SEGMENT_2}, timeout=5)
    
    response = requests.post(
        f"{BASE_URL}/users/{TEST_USER_ID}/segments",
        json={"add": [TEST_SEGMENT_1, TEST_SEGMENT_2]},
        timeout=5
    )
    assert response.status_code == 200
    
    response = requests.get(f"{BASE_URL}/users/{TEST_USER_ID}/segments", timeout=5)
    assert response.status_code == 200
    assert TEST_SEGMENT_1 in response.json()["segments"]
    assert TEST_SEGMENT_2 in response.json()["segments"]
    
    response = requests.post(
        f"{BASE_URL}/users/{TEST_USER_ID}/segments",
        json={"remove": [TEST_SEGMENT_1]},
        timeout=5
    )
    assert response.status_code == 200
    
    response = requests.get(f"{BASE_URL}/users/{TEST_USER_ID}/segments", timeout=5)
    assert response.status_code == 200
    assert TEST_SEGMENT_1 not in response.json()["segments"]
    assert TEST_SEGMENT_2 in response.json()["segments"]
    
    response = requests.post(
        f"{BASE_URL}/users/{TEST_USER_ID}/segments",
        json={"add": ["NON_EXISTENT_SEGMENT"]},
        timeout=5
    )
    assert response.status_code == 404
    
    non_existent_user = 999999
    response = requests.get(f"{BASE_URL}/users/{non_existent_user}/segments", timeout=5)
    assert response.status_code == 404

def test_distribution():
    requests.post(f"{BASE_URL}/segments/", json={"slug": TEST_SEGMENT_1}, timeout=5)
    for i in range(10):
        user_id = 1000 + i
        requests.post(
            f"{BASE_URL}/users/{user_id}/segments",
            json={"add": []},
            timeout=5
        )
    response = requests.post(
        f"{BASE_URL}/segments/{TEST_SEGMENT_1}/distribute",
        json={"percent": 30},
        timeout=5
    )
    assert response.status_code == 200
    result = response.json()
    assert result["users_added"] == 3
    
    response = requests.post(
        f"{BASE_URL}/segments/NON_EXISTENT_SEGMENT/distribute",
        json={"percent": 30},
        timeout=5
    )
    assert response.status_code == 404
    
    response = requests.post(
        f"{BASE_URL}/segments/{TEST_SEGMENT_1}/distribute",
        json={"percent": 150},
        timeout=5
    )
    assert response.status_code == 400

if __name__ == "__main__":
    pytest.main([__file__])