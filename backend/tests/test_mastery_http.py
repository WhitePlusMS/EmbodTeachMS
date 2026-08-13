"""掌握度系统 HTTP 测试

基准练习证据一律通过公开 API 驱动真实状态机产出，
不再直接 INSERT 行（避免 fixture 与生产写入格式漂移的"平行宇宙"）。
"""

import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import build_app
from tests.question_factory import insert_published_question


def register_user(client: TestClient, username: str, role: str) -> dict[str, str]:
    """注册用户并返回认证头信息"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": username,
            "role": role,
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    return {
        "Authorization": f"Bearer {data['accessToken']}",
        "user_id": data["user"]["id"],
    }


def create_class_with_teacher_and_learner(client: TestClient) -> tuple[dict[str, str], dict[str, str], str]:
    """创建教学班并添加学习者"""
    teacher = register_user(client, f"teacher_{uuid.uuid4().hex[:8]}", "teacher")
    learner = register_user(client, f"learner_{uuid.uuid4().hex[:8]}", "learner")

    # 创建教学班
    class_response = client.post(
        "/api/teaching-classes",
        headers=teacher,
        json={"name": "掌握度测试班", "joinPolicy": "free"},
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["data"]["id"]

    # 学习者加入教学班
    join_response = client.post(
        f"/api/teaching-classes/{class_id}/join",
        headers=learner,
    )
    assert join_response.status_code == 201

    return teacher, learner, class_id


def create_baseline_practice_content(
    database,
    class_id: str,
    knowledge_points: list[str],
    title: str = "基准练习",
) -> str:
    """创建基准练习内容（公开题面走 Database seam，判分事实由状态机消费）"""
    content_id = str(uuid.uuid4())
    with database.connect() as connection:
        insert_published_question(
            connection,
            class_id,
            content_id=content_id,
            stem=title,
            options=["A", "B"],
            correct_answers=[0],
            knowledge_points=knowledge_points,
            title=title,
        )
    return content_id


def baseline_endpoint(class_id: str, content_id: str, action: str = "") -> str:
    suffix = f"/{action}" if action else ""
    return f"/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice{suffix}"


def start_baseline_practice(client: TestClient, learner: dict[str, str], class_id: str, content_id: str) -> None:
    """首次访问详情，状态机建立 initial 运行"""
    response = client.get(baseline_endpoint(class_id, content_id), headers=learner)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "initial"


def submit_baseline_answer(
    client: TestClient,
    learner: dict[str, str],
    class_id: str,
    content_id: str,
    answers: list[int],
) -> dict:
    """提交一次作答并返回状态机结果"""
    response = client.post(
        baseline_endpoint(class_id, content_id, "submit"),
        headers=learner,
        json={"selectedAnswers": answers},
    )
    assert response.status_code == 201
    return response.json()["data"]


def complete_baseline_first_correct(client: TestClient, learner: dict[str, str], class_id: str, content_id: str) -> None:
    """驱动状态机产出 first_correct 证据（首次作答即正确）"""
    start_baseline_practice(client, learner, class_id, content_id)
    result = submit_baseline_answer(client, learner, class_id, content_id, [0])
    assert result["status"] == "completed"
    assert result["isCorrect"] is True


def complete_baseline_hint_correct(client: TestClient, learner: dict[str, str], class_id: str, content_id: str) -> None:
    """驱动状态机产出 hint_correct 证据（首答错误、看提示后答对）"""
    start_baseline_practice(client, learner, class_id, content_id)
    first = submit_baseline_answer(client, learner, class_id, content_id, [1])
    assert first["status"] == "prompt_shown"
    second = submit_baseline_answer(client, learner, class_id, content_id, [0])
    assert second["status"] == "completed"
    assert second["isCorrect"] is True


def test_mastery_summary_empty_for_new_learner(tmp_path: Path) -> None:
    """测试新学习者的掌握度摘要为空状态"""
    app, _ = build_app(tmp_path / "mastery.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 获取掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证空状态
        assert data["status"] == "success"
        assert data["totalKnowledgePoints"] == 0
        assert data["levelDistribution"] == {
            "unlearned": 0,
            "consolidating": 0,
            "basic_mastery": 0,
            "proficient_mastery": 0
        }
        assert data["knowledgePoints"] == []
        assert data["nextSuggestion"] == ""


def test_non_member_cannot_access_mastery_summary(tmp_path: Path) -> None:
    """测试非班级成员无法访问掌握度摘要"""
    app, _ = build_app(tmp_path / "mastery-permission.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, _, class_id = create_class_with_teacher_and_learner(client)
        outsider = register_user(client, f"outsider_{uuid.uuid4().hex[:8]}", "learner")

        # 非成员访问掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=outsider,
        )
        assert response.status_code == 403


def test_basic_mastery_level_with_three_questions(tmp_path: Path) -> None:
    """测试3道题达到基本掌握级别"""
    app, database = build_app(tmp_path / "mastery-basic.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 创建3个不同的基准练习内容，都包含"运动控制"知识点
        content_ids = []
        for i in range(3):
            content_id = create_baseline_practice_content(
                database, class_id,
                ["运动控制"],
                f"基准练习{i+1}"
            )
            content_ids.append(content_id)

        # 通过真实状态机为每个题目产出 first_correct 证据
        for content_id in content_ids:
            complete_baseline_first_correct(client, learner, class_id, content_id)

        # 获取掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证基本掌握状态
        assert data["status"] == "success"
        assert data["totalKnowledgePoints"] == 1  # 只有一个知识点"运动控制"
        assert data["levelDistribution"]["basic_mastery"] == 1

        # 验证知识点详情
        assert len(data["knowledgePoints"]) == 1
        kp_detail = data["knowledgePoints"][0]
        assert kp_detail["knowledgePoint"] == "运动控制"
        assert kp_detail["masteryLevel"] == "basic_mastery"
        assert kp_detail["weightedScore"] >= 4.0  # 3道题 * 2分 * 2.0系数 = 12分
        assert kp_detail["recentEvidenceCount"] == 3
        assert kp_detail["firstCorrectCount"] == 3


def test_proficient_mastery_level_with_five_questions(tmp_path: Path) -> None:
    """测试5道题达到熟练掌握级别（至少3道首次正确）"""
    app, database = build_app(tmp_path / "mastery-proficient.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 创建5个不同的基准练习内容，都包含"运动控制"知识点
        content_ids = []
        for i in range(5):
            content_id = create_baseline_practice_content(
                database, class_id,
                ["运动控制"],
                f"基准练习{i+1}"
            )
            content_ids.append(content_id)

        # 前3道首次正确，后2道提示后正确（全部走真实状态机）
        for i, content_id in enumerate(content_ids):
            if i < 3:
                complete_baseline_first_correct(client, learner, class_id, content_id)
            else:
                complete_baseline_hint_correct(client, learner, class_id, content_id)

        # 获取掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证熟练掌握状态
        assert data["status"] == "success"
        assert data["totalKnowledgePoints"] == 1
        assert data["levelDistribution"]["proficient_mastery"] == 1

        # 验证知识点详情
        kp_detail = data["knowledgePoints"][0]
        assert kp_detail["knowledgePoint"] == "运动控制"
        assert kp_detail["masteryLevel"] == "proficient_mastery"
        assert kp_detail["weightedScore"] >= 10.0  # (3*2 + 2*1) * 2.0系数 = 16分
        assert kp_detail["recentEvidenceCount"] == 5
        assert kp_detail["firstCorrectCount"] == 3


def test_classroom_practice_attempts_do_not_affect_mastery(tmp_path: Path) -> None:
    """测试课堂练习作答不影响掌握度"""
    app, database = build_app(tmp_path / "mastery-classroom.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 创建课堂练习内容
        content_id = create_baseline_practice_content(
            database, class_id,
            ["运动控制"],
            "课堂练习"
        )

        # 通过公开 API 提交课堂练习作答
        submitted = client.post(
            f"/api/teaching-classes/{class_id}/published-contents/{content_id}/submit-answer",
            headers=learner,
            json={"classId": class_id, "contentId": content_id, "selectedAnswers": [0]},
        )
        assert submitted.status_code == 201

        # 获取掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证课堂练习记录不影响掌握度
        assert data["totalKnowledgePoints"] == 0
        assert data["knowledgePoints"] == []


def test_initial_prompt_shown_status_does_not_count(tmp_path: Path) -> None:
    """测试initial/prompt_shown状态的练习不计入证据"""
    app, database = build_app(tmp_path / "mastery-initial.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 创建基准练习内容并停留在 initial 状态
        content_id = create_baseline_practice_content(
            database, class_id,
            ["运动控制"],
            "基准练习"
        )
        start_baseline_practice(client, learner, class_id, content_id)

        # 另一题目驱动到 prompt_shown 状态（首答错误后未继续）
        prompt_content_id = create_baseline_practice_content(
            database,
            class_id,
            ["运动控制"],
            "基准练习2",
        )
        start_baseline_practice(client, learner, class_id, prompt_content_id)
        first = submit_baseline_answer(client, learner, class_id, prompt_content_id, [1])
        assert first["status"] == "prompt_shown"

        # 获取掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证非终态记录不影响掌握度
        assert data["totalKnowledgePoints"] == 0
        assert data["knowledgePoints"] == []


def test_content_without_knowledge_points_ignored(tmp_path: Path) -> None:
    """测试无知识点的内容被忽略"""
    app, database = build_app(tmp_path / "mastery-no-kp.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 创建没有知识点的基准练习内容
        content_id = create_baseline_practice_content(
            database, class_id,
            [],
            "普通练习"
        )

        # 通过真实状态机产出 first_correct 证据
        complete_baseline_first_correct(client, learner, class_id, content_id)

        # 获取掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证无知识点的内容被忽略
        assert data["totalKnowledgePoints"] == 0
        assert data["knowledgePoints"] == []


def test_home_summary_next_suggestions_length_one(tmp_path: Path) -> None:
    """测试首页汇总的nextSuggestions长度始终为1"""
    app, database = build_app(tmp_path / "mastery-home.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 创建一些基准练习内容并驱动到 prompt_shown 状态（用于测试重试建议）
        content_id = create_baseline_practice_content(
            database, class_id,
            ["运动控制"],
            "基准练习"
        )
        start_baseline_practice(client, learner, class_id, content_id)
        first = submit_baseline_answer(client, learner, class_id, content_id, [1])
        assert first["status"] == "prompt_shown"

        # 获取首页汇总
        response = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证nextSuggestions长度为1
        assert len(data["nextSuggestions"]) == 1
        suggestion = data["nextSuggestions"][0]

        # 验证建议内容合理（应该包含"重试练习"）
        assert "重试练习" in suggestion


def test_mastery_summary_fields_exist(tmp_path: Path) -> None:
    """测试掌握度摘要包含所有必需字段"""
    app, _ = build_app(tmp_path / "mastery-fields.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        _, learner, class_id = create_class_with_teacher_and_learner(client)

        # 获取掌握度摘要
        response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner,
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证必需字段存在
        assert "status" in data
        assert "message" in data
        assert "totalKnowledgePoints" in data
        assert "levelDistribution" in data
        assert "knowledgePoints" in data
        assert "nextSuggestion" in data

        # 验证levelDistribution包含所有级别
        level_dist = data["levelDistribution"]
        assert "unlearned" in level_dist
        assert "consolidating" in level_dist
        assert "basic_mastery" in level_dist
        assert "proficient_mastery" in level_dist

        # 验证knowledgePoints中每个知识点包含必需字段
        for kp in data["knowledgePoints"]:
            assert "knowledgePoint" in kp
            assert "masteryLevel" in kp
            assert "weightedScore" in kp
            assert "recentEvidenceCount" in kp
            assert "firstCorrectCount" in kp
            assert "levelChange" in kp
            assert "latestEvidence" in kp
