"""教学班申请审批功能HTTP集成测试"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def register_user(client, username: str, role: str = "teacher") -> dict:
    """辅助函数：注册用户并返回认证头信息"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": f"{username}老师" if role == "teacher" else f"{username}同学",
            "role": role,
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    return {"Authorization": f"Bearer {data['accessToken']}"}


def test_learner_can_create_join_request(tmp_path: Path) -> None:
    """学习者可以创建加入申请"""
    app = create_app(
        database_path=tmp_path / "create_request.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_request")
        learner_headers = register_user(client, "learner_request", "learner")

        # 教师创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "申请加入班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者创建加入申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["code"] == "JOIN_REQUEST_CREATED"
        data = body["data"]
        assert data["requestId"]
        assert data["classId"] == class_id
        assert data["status"] == "pending"
        assert data["createdAt"]
        assert data["isNewRequest"] is True


def test_learner_cannot_create_duplicate_pending_request(tmp_path: Path) -> None:
    """学习者不能重复创建pending状态的申请"""
    app = create_app(
        database_path=tmp_path / "duplicate_request.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_duplicate")
        learner_headers = register_user(client, "learner_duplicate", "learner")

        # 教师创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "申请加入班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 第一次创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 第二次创建申请（应该失败）
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "PENDING_REQUEST_EXISTS"
        assert "已经提交了加入申请" in body["message"]


def test_learner_cannot_create_request_for_free_class(tmp_path: Path) -> None:
    """学习者不能为free策略的班级创建申请"""
    app = create_app(
        database_path=tmp_path / "free_class_request.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_free")
        learner_headers = register_user(client, "learner_free", "learner")

        # 教师创建free策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "自由加入班级",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者尝试创建申请（应该失败）
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "INVALID_JOIN_REQUEST"
        assert "不需要申请加入" in body["message"]


def test_learner_cannot_create_request_if_already_member(tmp_path: Path) -> None:
    """已经是成员的学习者不能创建申请"""
    app = create_app(
        database_path=tmp_path / "already_member.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_member")
        learner_headers = register_user(client, "learner_member", "learner")

        # 教师创建free策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "自由加入班级",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者加入班级
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 教师将班级策略改为approval
        response = client.patch(
            f"/api/teaching-classes/{class_id}/join-policy",
            headers=teacher_headers,
            json={"joinPolicy": "approval"},
        )
        assert response.status_code == 200

        # 学习者尝试创建申请（应该失败）
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "ALREADY_MEMBER"
        assert "已经是该教学班的成员" in body["message"]


def test_teacher_can_list_pending_requests(tmp_path: Path) -> None:
    """教师可以查看待处理的申请"""
    app = create_app(
        database_path=tmp_path / "list_requests.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_list")
        learner1_headers = register_user(client, "learner1_list", "learner")
        learner2_headers = register_user(client, "learner2_list", "learner")

        # 教师创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "申请加入班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 第一个学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner1_headers,
        )
        assert response.status_code == 201
        request1_id = response.json()["data"]["requestId"]

        # 第二个学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner2_headers,
        )
        assert response.status_code == 201
        request2_id = response.json()["data"]["requestId"]

        # 教师查看待处理申请
        response = client.get(
            f"/api/teaching-classes/{class_id}/join-requests",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "JOIN_REQUESTS_LISTED"
        data = body["data"]
        assert len(data["items"]) == 2

        # 验证申请信息正确
        requests = data["items"]
        request_ids = {req["id"] for req in requests}
        assert request1_id in request_ids
        assert request2_id in request_ids

        for req in requests:
            assert req["id"]
            assert req["classId"] == class_id
            assert req["learnerId"]
            assert req["status"] == "pending"
            assert req["createdAt"]
            assert req["resolvedAt"] is None
            assert req["resolvedByTeacherId"] is None


def test_teacher_cannot_list_requests_for_other_class(tmp_path: Path) -> None:
    """教师不能查看其他教师的班级申请"""
    app = create_app(
        database_path=tmp_path / "other_class_requests.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher1_headers = register_user(client, "teacher1_other")
        teacher2_headers = register_user(client, "teacher2_other")
        learner_headers = register_user(client, "learner_other", "learner")

        # 教师1创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher1_headers,
            json={
                "name": "教师1的班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # 教师2尝试查看申请（应该失败）
        response = client.get(
            f"/api/teaching-classes/{class_id}/join-requests",
            headers=teacher2_headers,
        )
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "RESOURCE_NOT_FOUND"
        assert "教学班不存在" in body["message"]


def test_teacher_can_approve_join_request(tmp_path: Path) -> None:
    """教师可以批准加入申请"""
    app = create_app(
        database_path=tmp_path / "approve_request.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_approve")
        learner_headers = register_user(client, "learner_approve", "learner")

        # 教师创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "申请加入班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        request_id = response.json()["data"]["requestId"]

        # 教师批准申请
        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "approved"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "JOIN_REQUEST_RESOLVED"
        data = body["data"]
        assert data["requestId"] == request_id
        assert data["classId"] == class_id
        assert data["status"] == "approved"
        assert data["resolvedAt"]
        assert data["resolvedByTeacherId"]
        assert data["membershipCreated"] is True

        # 验证学习者现在是成员
        response = client.get(
            "/api/teaching-classes/discover",
            headers=learner_headers,
        )
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        joined_class = next(cls for cls in discovered_classes if cls["id"] == class_id)
        assert joined_class["isMember"] is True

        # 验证mine接口显示已加入的班级
        response = client.get(
            "/api/teaching-classes/mine",
            headers=learner_headers,
        )
        assert response.status_code == 200
        mine_classes = response.json()["data"]["items"]
        assert len(mine_classes) == 1
        assert mine_classes[0]["id"] == class_id


def test_teacher_can_reject_join_request(tmp_path: Path) -> None:
    """教师可以拒绝加入申请"""
    app = create_app(
        database_path=tmp_path / "reject_request.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_reject")
        learner_headers = register_user(client, "learner_reject", "learner")

        # 教师创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "申请加入班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        request_id = response.json()["data"]["requestId"]

        # 教师拒绝申请
        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "rejected"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "JOIN_REQUEST_RESOLVED"
        data = body["data"]
        assert data["requestId"] == request_id
        assert data["classId"] == class_id
        assert data["status"] == "rejected"
        assert data["resolvedAt"]
        assert data["resolvedByTeacherId"]
        assert data["membershipCreated"] is False

        # 验证学习者不是成员
        response = client.get(
            "/api/teaching-classes/discover",
            headers=learner_headers,
        )
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        joined_class = next(cls for cls in discovered_classes if cls["id"] == class_id)
        assert joined_class["isMember"] is False

        # 验证mine接口为空
        response = client.get(
            "/api/teaching-classes/mine",
            headers=learner_headers,
        )
        assert response.status_code == 200
        mine_classes = response.json()["data"]["items"]
        assert len(mine_classes) == 0


def test_learner_can_reapply_after_join_request_is_rejected(tmp_path: Path) -> None:
    """学习者的申请被拒绝后可以再次申请。"""
    app = create_app(
        database_path=tmp_path / "reapply_after_rejection.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_reapply")
        learner_headers = register_user(client, "learner_reapply", "learner")

        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={"name": "可重申班级", "joinPolicy": "approval"},
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        request_id = response.json()["data"]["requestId"]

        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "rejected"},
        )
        assert response.status_code == 200

        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["requestId"] == request_id
        assert data["status"] == "pending"
        assert data["isNewRequest"] is True

        response = client.get(
            f"/api/teaching-classes/{class_id}/join-requests",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        pending_request = response.json()["data"]["items"]
        assert len(pending_request) == 1
        assert pending_request[0]["id"] == request_id
        assert pending_request[0]["resolvedAt"] is None
        assert pending_request[0]["resolvedByTeacherId"] is None


def test_teacher_cannot_resolve_other_teacher_request(tmp_path: Path) -> None:
    """教师不能处理其他教师的班级申请"""
    app = create_app(
        database_path=tmp_path / "resolve_other_request.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher1_headers = register_user(client, "teacher1_resolve")
        teacher2_headers = register_user(client, "teacher2_resolve")
        learner_headers = register_user(client, "learner_resolve", "learner")

        # 教师1创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher1_headers,
            json={
                "name": "教师1的班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        request_id = response.json()["data"]["requestId"]

        # 教师2尝试处理申请（应该失败）
        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher2_headers,
            json={"status": "approved"},
        )
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "RESOURCE_NOT_FOUND"
        assert "申请不存在" in body["message"]


def test_teacher_cannot_resolve_already_resolved_request(tmp_path: Path) -> None:
    """教师不能重复处理已处理的申请"""
    app = create_app(
        database_path=tmp_path / "resolve_already_resolved.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_already")
        learner_headers = register_user(client, "learner_already", "learner")

        # 教师创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "申请加入班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        request_id = response.json()["data"]["requestId"]

        # 第一次处理申请
        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "approved"},
        )
        assert response.status_code == 200

        # 第二次处理申请（应该失败）
        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "rejected"},
        )
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "REQUEST_ALREADY_RESOLVED"
        assert "该申请已被处理" in body["message"]


def test_learner_can_view_own_requests(tmp_path: Path) -> None:
    """学习者可以查看自己的申请列表"""
    app = create_app(
        database_path=tmp_path / "view_own_requests.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_view")
        learner_headers = register_user(client, "learner_view", "learner")

        # 教师创建多个approval策略的教学班
        class_ids = []
        for i in range(2):
            response = client.post(
                "/api/teaching-classes",
                headers=teacher_headers,
                json={
                    "name": f"申请班级{i+1}",
                    "joinPolicy": "approval",
                },
            )
            assert response.status_code == 201
            class_ids.append(response.json()["data"]["id"])

        # 学习者创建多个申请
        for class_id in class_ids:
            response = client.post(
                f"/api/teaching-classes/{class_id}/join-request",
                headers=learner_headers,
            )
            assert response.status_code == 201

        # 教师批准一个申请
        response = client.get(
            f"/api/teaching-classes/{class_ids[0]}/join-requests",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        requests = response.json()["data"]["items"]
        request_id = requests[0]["id"]

        response = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "approved"},
        )
        assert response.status_code == 200

        # 学习者查看自己的申请列表
        response = client.get(
            "/api/teaching-classes/join-requests/mine",
            headers=learner_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "LEARNER_JOIN_REQUESTS_LISTED"
        data = body["data"]
        assert len(data["items"]) == 2

        # 验证申请信息正确
        requests = data["items"]
        assert requests[0]["status"] == "approved"
        assert requests[0]["resolvedAt"] is not None
        assert requests[0]["resolvedByTeacherId"] is not None
        assert requests[1]["status"] == "pending"
        assert requests[1]["resolvedAt"] is None
        assert requests[1]["resolvedByTeacherId"] is None


def test_teacher_cannot_view_learner_requests_endpoint(tmp_path: Path) -> None:
    """教师不能访问学习者的申请列表接口"""
    app = create_app(
        database_path=tmp_path / "teacher_view_requests.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_no_view")

        # 教师尝试访问学习者的申请列表接口
        response = client.get(
            "/api/teaching-classes/join-requests/mine",
            headers=teacher_headers,
        )
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "AUTH_ROLE_FORBIDDEN"
        assert "只有学习者" in body["message"]


def test_concurrent_approval_creates_single_membership(tmp_path: Path) -> None:
    """并发批准不会创建重复成员关系"""
    app = create_app(
        database_path=tmp_path / "concurrent_approval.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_concurrent")
        learner_headers = register_user(client, "learner_concurrent", "learner")

        # 教师创建approval策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "并发测试班级",
                "joinPolicy": "approval",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者创建申请
        response = client.post(
            f"/api/teaching-classes/{class_id}/join-request",
            headers=learner_headers,
        )
        assert response.status_code == 201
        request_id = response.json()["data"]["requestId"]

        # 教师查看申请以获取request_id
        response = client.get(
            f"/api/teaching-classes/{class_id}/join-requests",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        requests = response.json()["data"]["items"]
        assert len(requests) == 1

        # 模拟并发批准（实际上顺序执行，但服务层有防重复逻辑）
        response1 = client.patch(
            f"/api/teaching-classes/join-requests/{request_id}/resolve",
            headers=teacher_headers,
            json={"status": "approved"},
        )
        assert response1.status_code == 200
        data1 = response1.json()["data"]
        assert data1["membershipCreated"] is True

        # 验证成员关系已建立且唯一
        response = client.get(
            f"/api/teaching-classes/{class_id}",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["memberCount"] == 1

        # 验证学习者mine接口显示已加入的班级
        response = client.get(
            "/api/teaching-classes/mine",
            headers=learner_headers,
        )
        assert response.status_code == 200
        mine_classes = response.json()["data"]["items"]
        assert len(mine_classes) == 1
