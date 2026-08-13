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


def test_webots_demo_pairing_environment_run_and_conflicts(tmp_path: Path) -> None:
    app = create_app(database_path=tmp_path / "webots.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher = register(client, "webots_teacher", "teacher")
        learner = register(client, "webots_learner", "learner")
        created = client.post("/api/teaching-classes", headers=teacher, json={"name": "Webots班", "joinPolicy": "free"})
        class_id = created.json()["data"]["id"]
        joined = client.post(f"/api/teaching-classes/{class_id}/join", headers=learner)
        assert joined.status_code == 201

        pairing = client.post(f"/api/teaching-classes/{class_id}/webots/pairing", headers=learner)
        assert pairing.status_code == 200
        token = pairing.json()["data"]["pairingToken"]
        bound = client.post(f"/api/teaching-classes/{class_id}/webots/pairing/bind", json={"pairingToken": token, "connectorId": "demo-1"})
        assert bound.status_code == 200
        connector_token = bound.json()["data"]["connectorToken"]
        assert client.post(f"/api/teaching-classes/{class_id}/webots/pairing/bind", json={"pairingToken": token, "connectorId": "demo-2"}).status_code == 400
        environment_body = {"connectorId": "demo-1", "environment": {"runtime": "demo", "path": "C:\\secret"}}
        assert client.post(f"/api/teaching-classes/{class_id}/webots/environment", json=environment_body).status_code == 401
        assert client.post(
            f"/api/teaching-classes/{class_id}/webots/environment",
            headers={"X-Connector-Token": "wrong-token"},
            json=environment_body,
        ).status_code == 401
        environment = client.post(
            f"/api/teaching-classes/{class_id}/webots/environment",
            headers={"X-Connector-Token": connector_token},
            json=environment_body,
        )
        assert environment.status_code == 200
        assert "path" not in environment.json()["data"]["environment"]
        assert client.get(f"/api/teaching-classes/{class_id}/webots/tasks", headers=learner).json()["data"]["items"] == []
        envelope = client.post(
            f"/api/teaching-classes/{class_id}/webots/messages",
            headers=learner,
            json={"protocolVersion": "webots-demo-v1", "messageId": "m1", "messageType": "event", "epoch": 0, "eventSequence": 1, "payload": {}},
        )
        assert envelope.status_code == 200
        assert client.post(
            f"/api/teaching-classes/{class_id}/webots/messages",
            headers=learner,
            json={"protocolVersion": "webots-v0", "messageId": "m2", "messageType": "event", "epoch": 0, "payload": {}},
        ).status_code == 422

        run = client.post(f"/api/teaching-classes/{class_id}/webots/runs", headers=learner, json={"connectorId": "demo-1", "taskId": ""})
        assert run.status_code == 200
        assert run.json()["data"]["nextEventSequence"] == 1
        run_id = run.json()["data"]["id"]
        started = client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run_id}/command", headers=learner, json={"command": "start"})
        assert started.json()["data"]["status"] == "running"
        event = {"epoch": 0, "sequence": 1, "eventType": "tick", "payload": {"state": "running"}}
        first_event = client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run_id}/events", headers=learner, json=event)
        assert first_event.status_code == 200
        assert first_event.json()["data"]["nextEventSequence"] == 2
        duplicate_event = client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run_id}/events", headers=learner, json=event)
        assert duplicate_event.status_code == 200
        assert duplicate_event.json()["data"]["nextEventSequence"] == 2
        conflict = {**event, "payload": {"state": "different"}}
        assert client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run_id}/events", headers=learner, json=conflict).status_code == 409
        result = {"epoch": 0, "status": "completed", "result": {"score": 1}}
        assert client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run_id}/result", headers=learner, json=result).status_code == 200
        assert client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run_id}/result", headers=learner, json=result).status_code == 200
        assert client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run_id}/command", headers=learner, json={"command": "start"}).status_code == 409


def test_webots_cross_user_cannot_control_run(tmp_path: Path) -> None:
    app = create_app(database_path=tmp_path / "webots_scope.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher = register(client, "webots_scope_teacher", "teacher")
        learner = register(client, "webots_scope_learner", "learner")
        other = register(client, "webots_scope_other", "learner")
        class_id = client.post("/api/teaching-classes", headers=teacher, json={"name": "Scope班", "joinPolicy": "free"}).json()["data"]["id"]
        client.post(f"/api/teaching-classes/{class_id}/join", headers=learner)
        pairing = client.post(f"/api/teaching-classes/{class_id}/webots/pairing", headers=learner).json()["data"]
        client.post(f"/api/teaching-classes/{class_id}/webots/pairing/bind", json={"pairingToken": pairing["pairingToken"], "connectorId": "scope-demo"})
        run = client.post(f"/api/teaching-classes/{class_id}/webots/runs", headers=learner, json={"connectorId": "scope-demo"}).json()["data"]
        assert client.post(f"/api/teaching-classes/{class_id}/webots/runs/{run['id']}/command", headers=other, json={"command": "start"}).status_code == 404
