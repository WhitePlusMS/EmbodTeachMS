"""学习概览 HTTP 契约测试 - 验证两个学习者同班时的数据隔离"""

import json
import time
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


def create_class_with_content_and_homework(client: TestClient, database, tmp_path: Path) -> tuple[dict[str, str], dict[str, str], dict[str, str], str, str, str]:
    """创建教学班、两个学习者、课程内容和作业"""
    teacher = register_user(client, f"teacher_{uuid.uuid4().hex[:8]}", "teacher")
    learner1 = register_user(client, f"learner1_{uuid.uuid4().hex[:8]}", "learner")
    learner2 = register_user(client, f"learner2_{uuid.uuid4().hex[:8]}", "learner")

    # 创建教学班
    class_response = client.post(
        "/api/teaching-classes",
        headers=teacher,
        json={"name": "学习概览测试班", "joinPolicy": "free"},
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["data"]["id"]

    # 学习者加入教学班
    join_response1 = client.post(
        f"/api/teaching-classes/{class_id}/join",
        headers=learner1,
    )
    assert join_response1.status_code == 201

    join_response2 = client.post(
        f"/api/teaching-classes/{class_id}/join",
        headers=learner2,
    )
    assert join_response2.status_code == 201

    # 创建课程内容
    content_id = str(uuid.uuid4())
    now = int(time.time())
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO course_contents
              (id, class_id, content_type, publication_status, title, content, created_at, updated_at)
            VALUES (?, ?, 'knowledge_module', 'published', ?, ?, ?, ?)
            """,
            (content_id, class_id, "学习概览测试内容", "测试内容正文", now, now),
        )

    # 创建基准练习内容（用于掌握度测试）
    with database.connect() as connection:
        insert_published_question(
            connection,
            class_id,
            stem="题目内容",
            options=["A", "B"],
            correct_answers=[0],
            knowledge_points=["运动控制"],
            title="基准练习",
            now=now,
        )

    # 创建作业
    homework_id = str(uuid.uuid4())
    with database.connect() as connection:
        connection.execute(
            """
            INSERT INTO course_contents
              (id, class_id, content_type, publication_status, title, content, due_at, description, created_at, updated_at)
            VALUES (?, ?, 'homework', 'published', ?, ?, ?, ?, ?, ?)
            """,
            (homework_id, class_id, "学习概览测试作业", "作业内容", now + 86400, "作业描述", now, now),
        )

        # 创建作业题目
        question_id = insert_published_question(
            connection,
            class_id,
            stem="测试题目",
            options=["A", "B"],
            correct_answers=[0],
            title="作业题目",
            now=now,
        )

        # 建立作业与题目的关联
        connection.execute(
            """
            INSERT INTO homework_questions (homework_id, question_id, ordinal)
            VALUES (?, ?, 0)
            """,
            (homework_id, question_id),
        )

    return teacher, learner1, learner2, class_id, content_id, homework_id


def test_two_learners_see_only_their_own_data_in_home_summary(tmp_path: Path) -> None:
    """测试两个学习者同班时，首页汇总只返回当前 token 对应的事实"""
    app, database = build_app(database_path=tmp_path / "home-summary-isolation.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher, learner1, learner2, class_id, content_id, homework_id = create_class_with_content_and_homework(client, database, tmp_path)

        # 学习者1标记内容完成
        complete_response = client.post(
            f"/api/teaching-classes/{class_id}/contents/{content_id}/complete",
            headers=learner1,
        )
        assert complete_response.status_code == 201

        # 学习者1获取首页汇总
        summary1_response = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner1,
        )
        assert summary1_response.status_code == 200
        summary1_data = summary1_response.json()["data"]

        # 学习者2获取首页汇总
        summary2_response = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner2,
        )
        assert summary2_response.status_code == 200
        summary2_data = summary2_response.json()["data"]

        # 验证完成统计隔离：学习者1已完成1个内容，学习者2未完成
        assert summary1_data["completionStats"]["completedContents"] == 1
        # 作业内嵌题目不属于课程首页的顶层学习内容，完成率分母只统计课件、课堂练习和作业。
        assert summary1_data["completionStats"]["completionRate"] == 0.33
        assert len(summary1_data["contentList"]) == 3
        assert all(item["title"] != "作业题目" for item in summary1_data["contentList"])
        completed_item = next(item for item in summary1_data["contentList"] if item["id"] == content_id)
        assert completed_item["completed"] is True
        assert summary2_data["completionStats"]["completedContents"] == 0
        assert summary2_data["completionStats"]["completionRate"] == 0.0

        # 学习者1跳过已完成内容，学习者2仍从该内容开始。
        assert summary1_data["nextContent"] is not None
        assert summary1_data["nextContent"]["id"] != content_id
        assert summary2_data["nextContent"] is not None
        assert summary2_data["nextContent"]["id"] == content_id


def test_two_learners_see_only_their_own_data_in_mastery_summary(tmp_path: Path) -> None:
    """测试两个学习者同班时，掌握度摘要只返回当前 token 对应的事实"""
    app, database = build_app(database_path=tmp_path / "mastery-summary-isolation.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher, learner1, learner2, class_id, content_id, homework_id = create_class_with_content_and_homework(client, database, tmp_path)

        # 为学习者1插入一条真实基准练习证据。
        practice_id = None
        with database.connect() as connection:
            practice_row = connection.execute(
                "SELECT id FROM course_contents WHERE class_id = ? AND content_type = 'question'",
                (class_id,)
            ).fetchone()
            practice_id = practice_row["id"]

            # 单条真实题目证据足以验证两名学习者之间的数据隔离。
            for i in range(1):
                run_id = str(uuid.uuid4())
                now = int(time.time())
                connection.execute(
                    """
                    INSERT INTO baseline_practice_runs
                      (id, learner_id, class_id, content_id, status, is_correct, first_attempt_answers,
                       correct_answers, knowledge_points, result_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id, learner1["user_id"], class_id, practice_id, "completed", 1,
                        json.dumps(["A"]), json.dumps(["A"]), json.dumps(["运动控制"]),
                        "first_correct", now, now
                    ),
                )

        # 学习者1获取掌握度摘要
        mastery1_response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner1,
        )
        assert mastery1_response.status_code == 200
        mastery1_data = mastery1_response.json()["data"]

        # 学习者2获取掌握度摘要
        mastery2_response = client.get(
            f"/api/teaching-classes/{class_id}/mastery-summary",
            headers=learner2,
        )
        assert mastery2_response.status_code == 200
        mastery2_data = mastery2_response.json()["data"]

        # 验证掌握度隔离：学习者1有掌握度数据，学习者2为空
        assert mastery1_data["status"] == "success"
        assert mastery1_data["totalKnowledgePoints"] == 1
        assert sum(mastery1_data["levelDistribution"].values()) == 1
        assert len(mastery1_data["knowledgePoints"]) == 1
        assert mastery1_data["knowledgePoints"][0]["knowledgePoint"] == "运动控制"

        assert mastery2_data["status"] == "success"
        assert mastery2_data["totalKnowledgePoints"] == 0
        assert mastery2_data["levelDistribution"]["unlearned"] == 0
        assert len(mastery2_data["knowledgePoints"]) == 0


def test_two_learners_see_only_their_own_homework_submissions(tmp_path: Path) -> None:
    """测试两个学习者同班时，作业提交只返回当前 token 对应的事实"""
    app, database = build_app(database_path=tmp_path / "homework-submission-isolation.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher, learner1, learner2, class_id, content_id, homework_id = create_class_with_content_and_homework(client, database, tmp_path)

        # 学习者1提交作业
        submit_request = {
            "classId": class_id,
            "homeworkId": homework_id,
            "answers": {}
        }

        # 获取作业题目ID
        with database.connect() as connection:
            question_row = connection.execute(
                "SELECT question_id FROM homework_questions WHERE homework_id = ?",
                (homework_id,)
            ).fetchone()
            if question_row:
                submit_request["answers"][question_row["question_id"]] = [0]

        submit_response1 = client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner1,
            json=submit_request
        )
        assert submit_response1.status_code == 201

        # 学习者1获取作业列表
        homework_list1_response = client.get(
            f"/api/teaching-classes/{class_id}/homework",
            headers=learner1,
        )
        assert homework_list1_response.status_code == 200
        homework_list1_data = homework_list1_response.json()["data"]

        # 学习者2获取作业列表
        homework_list2_response = client.get(
            f"/api/teaching-classes/{class_id}/homework",
            headers=learner2,
        )
        assert homework_list2_response.status_code == 200
        homework_list2_data = homework_list2_response.json()["data"]

        # 验证作业提交隔离：学习者1有提交记录，学习者2没有
        assert homework_id in homework_list1_data["submissions"]
        assert homework_list1_data["submissions"][homework_id]["status"] == "submitted"

        assert homework_id not in homework_list2_data["submissions"]


def test_data_consistency_after_fact_changes(tmp_path: Path) -> None:
    """测试事实变化后重新 GET 得到一致结果"""
    app, database = build_app(database_path=tmp_path / "data-consistency.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher, learner1, learner2, class_id, content_id, homework_id = create_class_with_content_and_homework(client, database, tmp_path)

        # 初始状态：两个学习者都未完成内容
        summary1_before = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner1,
        ).json()["data"]
        summary2_before = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner2,
        ).json()["data"]

        assert summary1_before["completionStats"]["completedContents"] == 0
        assert summary2_before["completionStats"]["completedContents"] == 0

        # 学习者1标记内容完成
        client.post(
            f"/api/teaching-classes/{class_id}/contents/{content_id}/complete",
            headers=learner1,
        )

        # 重新获取：学习者1已完成，学习者2未完成
        summary1_after = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner1,
        ).json()["data"]
        summary2_after = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner2,
        ).json()["data"]

        assert summary1_after["completionStats"]["completedContents"] == 1
        assert summary2_after["completionStats"]["completedContents"] == 0

        # 验证数据一致性：事实变化后重新 GET 得到一致结果
        assert summary1_before["completionStats"]["completedContents"] != summary1_after["completionStats"]["completedContents"]
        assert summary2_before["completionStats"]["completedContents"] == summary2_after["completionStats"]["completedContents"]


def test_webots_simulation_status_not_configured(tmp_path: Path) -> None:
    """测试 Webots 模拟状态为未配置，不应伪造测试结果"""
    app, database = build_app(database_path=tmp_path / "webots-not-configured.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher, learner1, learner2, class_id, content_id, homework_id = create_class_with_content_and_homework(client, database, tmp_path)

        # 获取首页汇总 - Webots 相关字段应为空或默认值
        summary_response = client.get(
            f"/api/teaching-classes/{class_id}/home-summary",
            headers=learner1,
        )
        assert summary_response.status_code == 200
        summary_data = summary_response.json()["data"]

        # 验证 Webots 相关字段不存在或为空
        # 根据当前实现，首页汇总不包含 Webots 特定字段
        # 验证没有伪造的 Webots 数据
        assert "simulationStatus" not in summary_data
        assert "webotsTasks" not in summary_data
        assert "webotsScores" not in summary_data


def test_homework_submission_after_fact_changes(tmp_path: Path) -> None:
    """测试作业提交事实变化后重新 GET 得到一致结果"""
    app, database = build_app(database_path=tmp_path / "homework-fact-changes.db", jwt_secret="test-secret-with-enough-length")
    with TestClient(app) as client:
        teacher, learner1, learner2, class_id, content_id, homework_id = create_class_with_content_and_homework(client, database, tmp_path)

        # 初始状态：学习者1没有作业提交
        homework_list1_before = client.get(
            f"/api/teaching-classes/{class_id}/homework",
            headers=learner1,
        ).json()["data"]

        assert homework_id not in homework_list1_before["submissions"]

        # 学习者1提交作业
        submit_request = {
            "classId": class_id,
            "homeworkId": homework_id,
            "answers": {}
        }

        with database.connect() as connection:
            question_row = connection.execute(
                "SELECT question_id FROM homework_questions WHERE homework_id = ?",
                (homework_id,)
            ).fetchone()
            if question_row:
                submit_request["answers"][question_row["question_id"]] = [0]

        client.post(
            f"/api/teaching-classes/{class_id}/homework/{homework_id}/submit",
            headers=learner1,
            json=submit_request
        )

        # 重新获取：学习者1有提交记录
        homework_list1_after = client.get(
            f"/api/teaching-classes/{class_id}/homework",
            headers=learner1,
        ).json()["data"]

        assert homework_id in homework_list1_after["submissions"]
        assert homework_list1_after["submissions"][homework_id]["status"] == "submitted"

        # 验证数据一致性
        assert homework_list1_before["submissions"] != homework_list1_after["submissions"]
