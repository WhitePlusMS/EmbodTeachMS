"""C25 乐观并发锁冲突路径测试。

preparation_state 的 save_highlights/save_questions 使用 state_revision 条件 UPDATE，
读-改-写窗口内版本被并发推进时必须 409 PREPARATION_SESSION_CONFLICT，而不是静默丢更新。
通过 now_provider 注入确定性闸门：目标函数在条件 UPDATE 前最后调用 self._now()，
闸门在该时刻阻塞工作线程，主线程趁机用另一个 HTTP 请求推进状态版本。
"""

import inspect
import threading
import time
from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient

from app.document_parsing import CourseContentParsing
from app.document_parsing.models import ParsedParagraph, ParsingResult, ParsingStatus
from app.main import create_app
from app.teaching_classes.models import FileFormat


class StubCourseContentParsing(CourseContentParsing):
    """返回固定解析结果的备课解析替身，配合同步执行器让 parse 同步完成。"""

    def __init__(self) -> None:
        pass

    def parse(self, file_path: Path, file_format: FileFormat) -> ParsingResult:
        return ParsingResult(
            status=ParsingStatus.COMPLETED,
            paragraphs=[ParsedParagraph(order=1, block_type="paragraph", content="传感器融合是本节教学重点。")],
        )


class ConflictGate:
    """挂在 now_provider 上的确定性并发闸门。

    目标 module 函数（如 remove_highlight）在条件 UPDATE 前最后取时钟；
    首个进入该函数的线程被记下并阻塞在 blocked/release 之间，
    主线程等 blocked 后制造并发写入，再 set(release) 放行。
    其他线程与其他函数的取时钟调用直接放行（同步端点跑在线程池，阻塞单线程不卡事件循环）。
    """

    def __init__(self, target_frame: str) -> None:
        self._target_frame = target_frame
        self._armed = threading.Event()
        self._blocked = threading.Event()
        self._release = threading.Event()
        self._worker_ident: int | None = None

    def now(self) -> int:
        if self._armed.is_set() and self._in_target_frame():
            ident = threading.get_ident()
            if self._worker_ident is None:
                self._worker_ident = ident
            if ident == self._worker_ident:
                self._blocked.set()
                self._release.wait(timeout=10)
        return int(time.time())

    def _in_target_frame(self) -> bool:
        return any(frame.function == self._target_frame for frame in inspect.stack())

    def arm(self) -> None:
        self._armed.set()

    def wait_blocked(self) -> None:
        assert self._blocked.wait(timeout=10), "工作线程未进入目标函数，闸门失效"

    def release(self) -> None:
        self._release.set()


def _teacher(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "StrongPass123!",
            "displayName": username,
            "role": "teacher",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['accessToken']}"}


def _parsed_session(client: TestClient, headers: dict[str, str]) -> str:
    """建班、建备课会话、上传并同步解析完成，返回 class_id。"""
    created = client.post(
        "/api/teaching-classes",
        headers=headers,
        json={"name": "并发冲突班", "joinPolicy": "free"},
    )
    assert created.status_code == 201
    class_id = created.json()["data"]["id"]
    session = client.post(
        f"/api/teaching-classes/{class_id}/preparation-session",
        headers=headers,
    )
    assert session.status_code == 201
    uploaded = client.put(
        f"/api/teaching-classes/{class_id}/preparation-session/upload",
        headers=headers,
        files={"file": ("lesson.md", b"# lesson")},
    )
    assert uploaded.status_code == 200
    parsed = client.post(
        f"/api/teaching-classes/{class_id}/preparation-session/parse",
        headers=headers,
    )
    assert parsed.status_code == 200
    return class_id


def _run_in_thread(call: Callable[[], object]) -> tuple[threading.Thread, dict[str, object]]:
    outcome: dict[str, object] = {}

    def runner() -> None:
        try:
            outcome["response"] = call()
        except Exception as exc:  # noqa: BLE001 - 测试需把线程内异常带回主线程断言
            outcome["error"] = exc

    thread = threading.Thread(target=runner)
    thread.start()
    return thread, outcome


def _join_and_collect(thread: threading.Thread, outcome: dict[str, object]) -> object:
    thread.join(timeout=10)
    assert not thread.is_alive(), "工作线程未结束，可能发生死锁"
    assert "error" not in outcome, f"工作线程内异常: {outcome.get('error')}"
    return outcome["response"]


def _conflict_app(database_path: Path, gate: ConflictGate):
    return create_app(
        database_path=database_path,
        jwt_secret="test-secret-with-enough-length",
        now_provider=gate.now,
        course_content_parsing=StubCourseContentParsing(),
        parsing_executor=lambda task: task(),
    )


def test_concurrent_highlight_overwrite_returns_conflict(tmp_path: Path) -> None:
    """取消重点与新增重点并发：基于过期 highlights blob 的整列覆写必须 409，不得静默丢更新。"""
    gate = ConflictGate(target_frame="remove_highlight")
    app = _conflict_app(tmp_path / "highlight_conflict.db", gate)
    with TestClient(app) as client:
        headers = _teacher(client, "highlight_conflict_teacher")
        class_id = _parsed_session(client, headers)

        added = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/highlights",
            headers=headers,
            json={"paragraphOrdinal": 1, "startOffset": 0, "endOffset": 4},
        )
        assert added.status_code == 201
        highlight_id = added.json()["data"]["id"]

        gate.arm()
        thread, outcome = _run_in_thread(
            lambda: client.request(
                "DELETE",
                f"/api/teaching-classes/{class_id}/preparation-session/highlights",
                headers=headers,
                json={"highlightId": highlight_id},
            )
        )
        try:
            # 工作线程已读入旧 state_revision 并停在条件 UPDATE 前；此时另一请求推进版本
            gate.wait_blocked()
            concurrent_add = client.post(
                f"/api/teaching-classes/{class_id}/preparation-session/highlights",
                headers=headers,
                json={"paragraphOrdinal": 1, "startOffset": 6, "endOffset": 10},
            )
            assert concurrent_add.status_code == 201
        finally:
            gate.release()

        response = _join_and_collect(thread, outcome)
        assert response.status_code == 409
        assert response.json()["code"] == "PREPARATION_SESSION_CONFLICT"

        # 冲突被拒绝后两条重点都在：并发写入未丢失，过期覆写未生效
        listed = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights",
            headers=headers,
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["totalHighlights"] == 2


def test_concurrent_question_overwrite_returns_conflict(tmp_path: Path) -> None:
    """删除题目与确认题目并发：基于过期 questions blob 的整列覆写必须 409，不得静默丢更新。"""
    gate = ConflictGate(target_frame="delete_question")
    app = _conflict_app(tmp_path / "question_conflict.db", gate)
    with TestClient(app) as client:
        headers = _teacher(client, "question_conflict_teacher")
        class_id = _parsed_session(client, headers)

        created = client.post(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=headers,
            json={
                "type": "single_choice",
                "stem": "传感器融合的核心作用是什么？",
                "options": ["整合多源观测", "删除全部观测"],
                "answers": [0],
                "knowledgePoints": ["传感器融合"],
                "highlightSourceIds": [],
                "hint": "",
                "explanation": "",
            },
        )
        assert created.status_code == 201
        question_id = created.json()["data"]["id"]

        gate.arm()
        thread, outcome = _run_in_thread(
            lambda: client.request(
                "DELETE",
                f"/api/teaching-classes/{class_id}/preparation-session/questions",
                headers=headers,
                json={"questionId": question_id},
            )
        )
        try:
            # 工作线程已读入旧 state_revision 并停在条件 UPDATE 前；此时另一请求推进版本
            gate.wait_blocked()
            concurrent_update = client.put(
                f"/api/teaching-classes/{class_id}/preparation-session/questions/{question_id}",
                headers=headers,
                json={
                    "type": "single_choice",
                    "stem": "更新后的传感器融合题目？",
                    "options": ["整合多源观测", "删除全部观测"],
                    "answers": [0],
                    "knowledgePoints": ["传感器融合"],
                    "highlightSourceIds": [],
                    "hint": "",
                    "explanation": "",
                },
            )
            assert concurrent_update.status_code == 200
        finally:
            gate.release()

        response = _join_and_collect(thread, outcome)
        assert response.status_code == 409
        assert response.json()["code"] == "PREPARATION_SESSION_CONFLICT"

        # 冲突被拒绝后题目仍保留并发更新：过期删除未静默覆盖并发写入
        listed = client.get(
            f"/api/teaching-classes/{class_id}/preparation-session/questions",
            headers=headers,
        )
        assert listed.status_code == 200
        items = listed.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["stem"] == "更新后的传感器融合题目？"
