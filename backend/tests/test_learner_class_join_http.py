"""学习者教学班加入功能HTTP集成测试"""

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


def test_learner_can_discover_joinable_classes(tmp_path: Path) -> None:
    """学习者可以发现可加入的教学班（排除closed状态）"""
    app = create_app(
        database_path=tmp_path / "discover_classes.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_discover")
        learner_headers = register_user(client, "learner_discover", "learner")

        # 教师创建三种策略的教学班
        policies = ["free", "approval", "closed"]
        class_ids = {}
        for i, policy in enumerate(policies):
            response = client.post(
                "/api/teaching-classes",
                headers=teacher_headers,
                json={
                    "name": f"{policy}策略班级{i+1}",
                    "joinPolicy": policy,
                },
            )
            assert response.status_code == 201
            class_ids[policy] = response.json()["data"]["id"]

        # 学习者发现班级（应该只看到free和approval，排除closed）
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "CLASSES_DISCOVERED"
        assert len(body["data"]["items"]) == 2  # free和approval

        # 验证返回的班级信息正确
        discovered_classes = body["data"]["items"]
        discovered_policies = {cls["joinPolicy"] for cls in discovered_classes}
        assert discovered_policies == {"free", "approval"}

        # 验证每个班级都有正确的字段
        for cls in discovered_classes:
            assert cls["id"]
            assert cls["name"]
            assert cls["joinPolicy"] in ["free", "approval"]
            assert cls["memberCount"] == 0  # 初始成员数为0
            assert cls["isMember"] is False  # 初始不是成员
            assert cls["createdAt"]
            assert cls["updatedAt"]


def test_learner_can_join_free_class(tmp_path: Path) -> None:
    """学习者可以加入free策略的教学班"""
    app = create_app(
        database_path=tmp_path / "join_free_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_join")
        learner_headers = register_user(client, "learner_join", "learner")

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
        body = response.json()
        assert body["code"] == "CLASS_JOINED"
        assert body["data"]["classId"] == class_id
        assert body["data"]["learnerId"]
        assert body["data"]["joinedAt"]
        assert body["data"]["isNewMember"] is True

        # 验证成员关系已建立
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        joined_class = next(cls for cls in discovered_classes if cls["id"] == class_id)
        assert joined_class["isMember"] is True
        assert joined_class["memberCount"] == 1


def test_learner_cannot_join_approval_class_directly(tmp_path: Path) -> None:
    """学习者不能直接加入approval策略的教学班"""
    app = create_app(
        database_path=tmp_path / "join_approval_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_approval")
        learner_headers = register_user(client, "learner_approval", "learner")

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

        # 学习者尝试直接加入（应该失败）
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "CLASS_JOIN_APPROVAL_REQUIRED"
        assert "需要申请加入" in body["message"]

        # 验证班级仍然可见但未加入
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        approval_class = next(cls for cls in discovered_classes if cls["id"] == class_id)
        assert approval_class["isMember"] is False
        assert approval_class["memberCount"] == 0


def test_learner_cannot_join_closed_class(tmp_path: Path) -> None:
    """学习者不能加入closed策略的教学班"""
    app = create_app(
        database_path=tmp_path / "join_closed_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_closed")
        learner_headers = register_user(client, "learner_closed", "learner")

        # 教师创建closed策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "关闭加入班级",
                "joinPolicy": "closed",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 学习者尝试加入（应该失败）
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "CLASS_JOIN_FORBIDDEN"
        assert "已关闭加入" in body["message"]

        # 验证closed班级在发现列表中不可见
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        closed_class_ids = [cls["id"] for cls in discovered_classes]
        assert class_id not in closed_class_ids


def test_learner_cannot_join_nonexistent_class(tmp_path: Path) -> None:
    """学习者不能加入不存在的教学班"""
    app = create_app(
        database_path=tmp_path / "join_nonexistent_class.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner_headers = register_user(client, "learner_nonexistent", "learner")

        # 尝试加入不存在的班级
        response = client.post(
            "/api/teaching-classes/nonexistent-class-id/join",
            headers=learner_headers,
        )
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "RESOURCE_NOT_FOUND"
        assert "教学班不存在" in body["message"]


def test_learner_cannot_join_same_class_twice(tmp_path: Path) -> None:
    """学习者重复加入同一班级不会创建重复成员关系"""
    app = create_app(
        database_path=tmp_path / "join_twice.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_twice")
        learner_headers = register_user(client, "learner_twice", "learner")

        # 教师创建free策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "重复加入测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 第一次加入
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201
        first_join = response.json()["data"]
        assert first_join["isNewMember"] is True

        # 第二次加入
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201
        second_join = response.json()["data"]
        assert second_join["isNewMember"] is False  # 不是新成员
        assert second_join["classId"] == class_id
        assert second_join["learnerId"] == first_join["learnerId"]

        # 验证成员数仍然是1
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        joined_class = next(cls for cls in discovered_classes if cls["id"] == class_id)
        assert joined_class["memberCount"] == 1


def test_teacher_cannot_access_learner_discover_endpoint(tmp_path: Path) -> None:
    """教师不能访问学习者的发现接口"""
    app = create_app(
        database_path=tmp_path / "teacher_discover.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_no_discover")

        # 教师尝试访问发现接口
        response = client.get("/api/teaching-classes/discover", headers=teacher_headers)
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "AUTH_ROLE_FORBIDDEN"
        assert "只有学习者" in body["message"]


def test_teacher_cannot_access_learner_join_endpoint(tmp_path: Path) -> None:
    """教师不能访问学习者的加入接口"""
    app = create_app(
        database_path=tmp_path / "teacher_join.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_no_join")
        learner_headers = register_user(client, "learner_for_teacher", "learner")

        # 学习者创建班级
        response = client.post(
            "/api/teaching-classes",
            headers=learner_headers,
            json={
                "name": "教师尝试加入测试",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 403  # 学习者不能创建班级

        # 教师尝试访问加入接口
        response = client.post(
            "/api/teaching-classes/some-class/join",
            headers=teacher_headers,
        )
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "AUTH_ROLE_FORBIDDEN"
        assert "只有学习者" in body["message"]


def test_multiple_learners_can_join_same_class(tmp_path: Path) -> None:
    """多个学习者可以加入同一个free策略班级"""
    app = create_app(
        database_path=tmp_path / "multiple_learners.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_multi")
        learner1_headers = register_user(client, "learner1_multi", "learner")
        learner2_headers = register_user(client, "learner2_multi", "learner")

        # 教师创建free策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "多人加入测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 第一个学习者加入
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner1_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["isNewMember"] is True

        # 第二个学习者加入
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner2_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["isNewMember"] is True

        # 验证成员数增加到2
        response = client.get("/api/teaching-classes/discover", headers=learner1_headers)
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        joined_class = next(cls for cls in discovered_classes if cls["id"] == class_id)
        assert joined_class["memberCount"] == 2


def test_class_member_count_updates_correctly(tmp_path: Path) -> None:
    """教学班成员数在加入后正确更新"""
    app = create_app(
        database_path=tmp_path / "member_count.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_count")
        learner1_headers = register_user(client, "learner1_count", "learner")
        learner2_headers = register_user(client, "learner2_count", "learner")

        # 教师创建free策略的教学班
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "成员数测试班",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201
        class_id = response.json()["data"]["id"]

        # 教师查看初始成员数
        response = client.get(f"/api/teaching-classes/{class_id}", headers=teacher_headers)
        assert response.status_code == 200
        assert response.json()["data"]["memberCount"] == 0

        # 第一个学习者加入
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner1_headers,
        )
        assert response.status_code == 201

        # 教师查看成员数更新
        response = client.get(f"/api/teaching-classes/{class_id}", headers=teacher_headers)
        assert response.status_code == 200
        assert response.json()["data"]["memberCount"] == 1

        # 第二个学习者加入
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner2_headers,
        )
        assert response.status_code == 201

        # 教师查看成员数再次更新
        response = client.get(f"/api/teaching-classes/{class_id}", headers=teacher_headers)
        assert response.status_code == 200
        assert response.json()["data"]["memberCount"] == 2


def test_learner_mine_endpoint_initial_empty(tmp_path: Path) -> None:
    """学习者mine接口初始为空"""
    app = create_app(
        database_path=tmp_path / "mine_empty.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner_headers = register_user(client, "learner_mine", "learner")

        # mine接口初始为空
        response = client.get("/api/teaching-classes/mine", headers=learner_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "LEARNER_CLASSES_LISTED"
        assert len(body["data"]["items"]) == 0


def test_learner_mine_endpoint_shows_only_real_members(tmp_path: Path) -> None:
    """mine接口只显示真实成员，不包含发现但未加入的班级"""
    app = create_app(
        database_path=tmp_path / "mine_real_members.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_mine")
        learner_headers = register_user(client, "learner_mine_real", "learner")

        # 教师创建多个班级
        free_class_response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "自由加入班级",
                "joinPolicy": "free",
            },
        )
        assert free_class_response.status_code == 201
        free_class_id = free_class_response.json()["data"]["id"]

        approval_class_response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "申请加入班级",
                "joinPolicy": "approval",
            },
        )
        assert approval_class_response.status_code == 201
        approval_class_id = approval_class_response.json()["data"]["id"]

        # 学习者查看mine接口（应该为空）
        response = client.get("/api/teaching-classes/mine", headers=learner_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

        # 学习者查看discover接口（应该看到free和approval班级）
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        assert len(discovered_classes) == 2

        # 学习者加入free策略班级
        response = client.post(
            f"/api/teaching-classes/{free_class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201

        # mine接口应该只显示已加入的free班级
        response = client.get("/api/teaching-classes/mine", headers=learner_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "LEARNER_CLASSES_LISTED"
        assert len(body["data"]["items"]) == 1
        joined_class = body["data"]["items"][0]
        assert joined_class["id"] == free_class_id
        assert joined_class["name"] == "自由加入班级"
        assert joined_class["joinPolicy"] == "free"
        assert joined_class["memberCount"] == 1

        # discover接口应该仍然显示两个班级，但free班级的isMember为True
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        discovered_classes = response.json()["data"]["items"]
        assert len(discovered_classes) == 2

        free_class_discover = next(cls for cls in discovered_classes if cls["id"] == free_class_id)
        assert free_class_discover["isMember"] is True

        approval_class_discover = next(cls for cls in discovered_classes if cls["id"] == approval_class_id)
        assert approval_class_discover["isMember"] is False


def test_learner_mine_endpoint_response_has_request_id(tmp_path: Path) -> None:
    """mine接口响应包含requestId"""
    app = create_app(
        database_path=tmp_path / "mine_request_id.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        learner_headers = register_user(client, "learner_request_id", "learner")

        # mine接口响应应该包含requestId
        response = client.get("/api/teaching-classes/mine", headers=learner_headers)
        assert response.status_code == 200
        body = response.json()
        assert "requestId" in body
        assert body["requestId"] is not None


def test_discover_endpoint_response_has_request_id(tmp_path: Path) -> None:
    """discover接口响应包含requestId"""
    app = create_app(
        database_path=tmp_path / "discover_request_id.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_request_id")
        learner_headers = register_user(client, "learner_discover_request_id", "learner")

        # 教师创建一个班级
        response = client.post(
            "/api/teaching-classes",
            headers=teacher_headers,
            json={
                "name": "测试班级",
                "joinPolicy": "free",
            },
        )
        assert response.status_code == 201

        # discover接口响应应该包含requestId
        response = client.get("/api/teaching-classes/discover", headers=learner_headers)
        assert response.status_code == 200
        body = response.json()
        assert "requestId" in body
        assert body["requestId"] is not None


def test_join_endpoint_response_has_request_id(tmp_path: Path) -> None:
    """join接口响应包含requestId"""
    app = create_app(
        database_path=tmp_path / "join_request_id.db",
        jwt_secret="test-secret-with-enough-length",
    )

    with TestClient(app) as client:
        teacher_headers = register_user(client, "teacher_join_request_id")
        learner_headers = register_user(client, "learner_join_request_id", "learner")

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

        # join接口响应应该包含requestId
        response = client.post(
            f"/api/teaching-classes/{class_id}/join",
            headers=learner_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert "requestId" in body
        assert body["requestId"] is not None