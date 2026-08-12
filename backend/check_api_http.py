from fastapi.testclient import TestClient
from main import app
import logging

logging.basicConfig(level=logging.DEBUG)

client = TestClient(app)

def test_get_resources():
    response = client.get("/api/v1/resources/?page_size=100")
    print("Status:", response.status_code)
    if response.status_code != 200:
        print("Error detail:", response.json())
    else:
        data = response.json()
        print("Success! total:", data.get("total"))
        print("Items length:", len(data.get("items", [])))

if __name__ == "__main__":
    test_get_resources()
