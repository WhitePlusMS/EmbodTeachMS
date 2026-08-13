from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def register(client: TestClient, username: str, role: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "StrongPass123!", "displayName": username, "role": role},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def test_teacher_simulation_summary_is_structured_and_scoped(tmp_path: Path) -> None:
    app = create_app(database_path=tmp_path / "teacher-summary.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher = register(client, "summary_teacher", "teacher")
        learner = register(client, "summary_learner", "learner")
        other_teacher = register(client, "summary_other_teacher", "teacher")
        class_id = client.post("/api/teaching-classes", headers=teacher, json={"name": "摘要班", "joinPolicy": "free"}).json()["data"]["id"]
        learner_id = client.get("/api/auth/me", headers=learner).json()["data"]["id"]
        assert client.post(f"/api/teaching-classes/{class_id}/join", headers=learner).status_code == 201
        pairing = client.post(f"/api/teaching-classes/{class_id}/webots/pairing", headers=learner).json()["data"]
        assert client.post(f"/api/teaching-classes/{class_id}/webots/pairing/bind", json={"pairingToken": pairing["pairingToken"], "connectorId": "summary-demo"}).status_code == 200
        run = client.post(f"/api/teaching-classes/{class_id}/webots/runs", headers=learner, json={"connectorId": "summary-demo"}).json()["data"]
        assert client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run['id']}/result", headers=learner, json={"epoch": 0, "status": "completed", "result": {"score": 0.8}}).status_code == 200

        summary = client.get(f"/api/teaching-classes/{class_id}/webots/simulation-summary", headers=teacher)
        assert summary.status_code == 200
        data = summary.json()["data"]
        assert data["runCount"] == 1 and data["completedCount"] == 1
        assert data["latestResult"] == {"score": 0.8}
        assert "payload" not in data and "path" not in data

        learner_summary = client.get(f"/api/teaching-classes/{class_id}/learners/{learner_id}/webots/simulation-summary", headers=teacher)
        assert learner_summary.status_code == 200
        assert learner_summary.json()["data"]["latestTerminalStatus"] == "completed"
        assert client.get(f"/api/teaching-classes/{class_id}/webots/simulation-summary", headers=other_teacher).status_code == 404
