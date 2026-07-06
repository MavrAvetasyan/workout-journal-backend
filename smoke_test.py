from fastapi.testclient import TestClient
import uuid

from app.database import Base, engine
from app.main import app


def run():
    Base.metadata.create_all(bind=engine)
    email = f"demo-{uuid.uuid4()}@example.com"
    with TestClient(app) as client:
        register_response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "password123"},
        )
        assert register_response.status_code == 201, register_response.text
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        exercise_response = client.post(
            "/api/exercises",
            json={"name": "Жим лежа", "type": "strength", "description": "", "archived": False},
            headers=headers,
        )
        assert exercise_response.status_code == 201, exercise_response.text
        exercise_id = exercise_response.json()["id"]

        workout_response = client.post(
            "/api/workouts",
            json={
                "title": "Грудь",
                "type": "strength",
                "status": "planned",
                "start_time": None,
                "end_time": None,
                "exercises": [
                    {
                        "exercise_id": exercise_id,
                        "status": "pending",
                        "plan": {"sets": 4, "weight": 80, "reps": 8, "note": ""},
                        "fact": None,
                    }
                ],
            },
            headers=headers,
        )
        assert workout_response.status_code == 201, workout_response.text

        measurement_response = client.post(
            "/api/measurements",
            json={"title": "Утро", "date": "2026-06-25", "weight": 82.4, "body_fat": 14.2, "note": ""},
            headers=headers,
        )
        assert measurement_response.status_code == 201, measurement_response.text

        sync_response = client.get("/api/sync", headers=headers)
        assert sync_response.status_code == 200, sync_response.text
        payload = sync_response.json()
        assert len(payload["exercises"]) == 1
        assert len(payload["workouts"]) == 1
        assert len(payload["measurements"]) == 1

        health_response = client.get("/health")
        assert health_response.status_code == 200, health_response.text

    print("Smoke test passed")


if __name__ == "__main__":
    run()
