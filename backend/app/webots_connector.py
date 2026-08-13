"""Webots 替身连接器协议：只提供持久化契约，不启动真实 Webots。"""

import hashlib
import json
import secrets
import sqlite3
import uuid

from app.auth.models import UserView
from app.common.errors import BusinessError
from app.database import Database
from app.teaching_classes.access import TeachingClassAccess
from app.webots_models import (
    PairingView,
    PairingBindRequest,
    ConnectorView,
    EnvironmentReportRequest,
    EnvironmentView,
    TaskCatalogView,
    RunCreateRequest,
    RunView,
    RunCommandRequest,
    RunEventRequest,
    RunResultRequest,
    ProtocolEnvelope,
)


class WebotsConnectorService:
    def __init__(self, database: Database, now_provider, access: TeachingClassAccess | None = None) -> None:
        self._database = database
        self._now = now_provider
        self._access = access or TeachingClassAccess()

    def _require_member(self, connection: sqlite3.Connection, class_id: str, learner: UserView) -> None:
        self._access.require_membership_or_not_found(
            connection,
            class_id,
            learner.id,
            code="WEBOTS_MEMBERSHIP_REQUIRED",
            message="教学班不存在或学习者未加入",
        )

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_pairing(self, class_id: str, learner: UserView) -> PairingView:
        now = self._now()
        token = secrets.token_urlsafe(24)
        expires_at = now + 300
        with self._database.connect() as connection:
            self._require_member(connection, class_id, learner)
            connection.execute(
                "UPDATE webots_pairings SET used_at=? WHERE class_id=? AND learner_id=? AND used_at IS NULL",
                (now, class_id, learner.id),
            )
            connection.execute(
                "INSERT INTO webots_pairings(id,class_id,learner_id,token_hash,expires_at,used_at,created_at) VALUES(?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), class_id, learner.id, self._token_hash(token), expires_at, None, now),
            )
        return PairingView(pairing_token=token, expires_at=expires_at)

    def bind_pairing(self, class_id: str, request: PairingBindRequest) -> ConnectorView:
        now = self._now()
        connector_token = secrets.token_urlsafe(32)
        with self._database.connect() as connection:
            # 立即写事务让“校验未使用”和“消费凭证”成为一个不可分割操作。
            connection.execute("BEGIN IMMEDIATE")
            pairing = connection.execute(
                "SELECT * FROM webots_pairings WHERE class_id=? AND token_hash=?",
                (class_id, self._token_hash(request.pairing_token)),
            ).fetchone()
            if pairing is None or pairing["used_at"] is not None or pairing["expires_at"] <= now:
                raise BusinessError(status_code=400, code="WEBOTS_PAIRING_INVALID", message="配对凭证无效、已使用或已过期")
            consumed = connection.execute(
                "UPDATE webots_pairings SET used_at=? WHERE id=? AND used_at IS NULL AND expires_at>?",
                (now, pairing["id"], now),
            )
            if consumed.rowcount != 1:
                raise BusinessError(status_code=400, code="WEBOTS_PAIRING_INVALID", message="配对凭证无效、已使用或已过期")
            try:
                connection.execute(
                    "INSERT INTO webots_connectors(connector_id,class_id,learner_id,token_hash,bound_at,environment_json) VALUES(?,?,?,?,?,?)",
                    (
                        request.connector_id,
                        class_id,
                        pairing["learner_id"],
                        self._token_hash(connector_token),
                        now,
                        "{}",
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise BusinessError(
                    status_code=409,
                    code="WEBOTS_CONNECTOR_EXISTS",
                    message="连接器标识已绑定",
                ) from error
        return ConnectorView(
            connector_id=request.connector_id,
            connector_token=connector_token,
            class_id=class_id,
            learner_id=pairing["learner_id"],
            bound_at=now,
        )

    def report_environment(
        self,
        class_id: str,
        request: EnvironmentReportRequest,
        connector_token: str | None,
        now: int | None = None,
    ) -> EnvironmentView:
        reported_at = self._now() if now is None else now
        safe_environment = {key: value for key, value in request.environment.items() if key in {"runtime", "version", "status", "capabilities"} and len(value) <= 200}
        with self._database.connect() as connection:
            connector = connection.execute(
                "SELECT token_hash FROM webots_connectors WHERE class_id=? AND connector_id=?",
                (class_id, request.connector_id),
            ).fetchone()
            supplied_hash = self._token_hash(connector_token) if connector_token else ""
            if connector is None or not secrets.compare_digest(connector["token_hash"], supplied_hash):
                raise BusinessError(status_code=401, code="WEBOTS_CONNECTOR_UNAUTHORIZED", message="连接器凭证无效")
            connection.execute(
                "UPDATE webots_connectors SET environment_json=? WHERE class_id=? AND connector_id=?",
                (json.dumps(safe_environment, ensure_ascii=False), class_id, request.connector_id),
            )
        return EnvironmentView(connector_id=request.connector_id, environment=safe_environment, reported_at=reported_at)

    def get_environment(self, class_id: str, learner: UserView, connector_id: str) -> EnvironmentView:
        with self._database.connect() as connection:
            self._require_member(connection, class_id, learner)
            row = connection.execute(
                "SELECT connector_id, environment_json, bound_at FROM webots_connectors WHERE class_id=? AND connector_id=? AND learner_id=?",
                (class_id, connector_id, learner.id),
            ).fetchone()
            if row is None:
                raise BusinessError(status_code=404, code="WEBOTS_CONNECTOR_NOT_FOUND", message="连接器不存在")
            return EnvironmentView(connector_id=row["connector_id"], environment=json.loads(row["environment_json"]), reported_at=row["bound_at"])

    def list_tasks(self, class_id: str, learner: UserView) -> TaskCatalogView:
        with self._database.connect() as connection:
            self._require_member(connection, class_id, learner)
        return TaskCatalogView(items=[])

    def create_run(self, class_id: str, request: RunCreateRequest, learner: UserView) -> RunView:
        now = self._now()
        with self._database.connect() as connection:
            self._require_member(connection, class_id, learner)
            connector = connection.execute(
                "SELECT 1 FROM webots_connectors WHERE class_id=? AND connector_id=? AND learner_id=?",
                (class_id, request.connector_id, learner.id),
            ).fetchone()
            if connector is None:
                raise BusinessError(status_code=404, code="WEBOTS_CONNECTOR_NOT_FOUND", message="连接器不存在")
            run_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO webots_runs(id,class_id,learner_id,connector_id,task_id,status,epoch,result_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (run_id, class_id, learner.id, request.connector_id, request.task_id, "created", 0, "{}", now, now),
            )
            row = connection.execute("SELECT * FROM webots_runs WHERE id=?", (run_id,)).fetchone()
            return self._to_run(connection, row)

    def list_runs(self, class_id: str, learner: UserView) -> list[RunView]:
        """只返回当前学习者在当前教学班的运行历史，避免跨班或跨用户泄露。"""
        with self._database.connect() as connection:
            self._require_member(connection, class_id, learner)
            rows = connection.execute(
                "SELECT * FROM webots_runs WHERE class_id=? AND learner_id=? ORDER BY created_at DESC",
                (class_id, learner.id),
            ).fetchall()
            return [self._to_run(connection, row) for row in rows]

    def _run(self, connection: sqlite3.Connection, class_id: str, run_id: str, learner: UserView) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM webots_runs WHERE id=? AND class_id=? AND learner_id=?", (run_id, class_id, learner.id)).fetchone()
        if row is None:
            raise BusinessError(status_code=404, code="WEBOTS_RUN_NOT_FOUND", message="仿真运行不存在")
        return row

    def command(self, class_id: str, run_id: str, request: RunCommandRequest, learner: UserView) -> RunView:
        now = self._now()
        with self._database.connect() as connection:
            row = self._run(connection, class_id, run_id, learner)
            if request.command == "hard_reset":
                new_run_id = str(uuid.uuid4())
                connection.execute(
                    "INSERT INTO webots_runs(id,class_id,learner_id,connector_id,task_id,status,epoch,result_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        new_run_id,
                        class_id,
                        learner.id,
                        row["connector_id"],
                        row["task_id"],
                        "created",
                        0,
                        "{}",
                        now,
                        now,
                    ),
                )
                created = connection.execute("SELECT * FROM webots_runs WHERE id=?", (new_run_id,)).fetchone()
                return self._to_run(connection, created)
            if request.command == "reset":
                if row["status"] in {"completed", "failed"}:
                    raise BusinessError(status_code=409, code="WEBOTS_RUN_TERMINAL", message="终态运行不可重置")
                updated_cursor = connection.execute("UPDATE webots_runs SET status='created', epoch=epoch+1, updated_at=? WHERE id=? AND status=? AND epoch=?", (now, run_id, row["status"], row["epoch"]))
            elif request.command == "start":
                if row["status"] in {"completed", "failed"}:
                    raise BusinessError(status_code=409, code="WEBOTS_RUN_TERMINAL", message="终态运行不可启动")
                updated_cursor = connection.execute("UPDATE webots_runs SET status='running', updated_at=? WHERE id=? AND status=? AND epoch=?", (now, run_id, row["status"], row["epoch"]))
            else:
                if row["status"] in {"completed", "failed"}:
                    raise BusinessError(status_code=409, code="WEBOTS_RUN_TERMINAL", message="终态运行不可失败")
                updated_cursor = connection.execute("UPDATE webots_runs SET status='failed', updated_at=? WHERE id=? AND status=? AND epoch=?", (now, run_id, row["status"], row["epoch"]))
            if updated_cursor.rowcount != 1:
                raise BusinessError(status_code=409, code="WEBOTS_RUN_STATE_CONFLICT", message="运行状态已变化，请刷新后重试")
            updated = connection.execute("SELECT * FROM webots_runs WHERE id=?", (run_id,)).fetchone()
            return self._to_run(connection, updated)

    def add_event(self, class_id: str, run_id: str, request: RunEventRequest, learner: UserView) -> RunView:
        now = self._now()
        payload = json.dumps({"event_type": request.event_type, "payload": request.payload}, sort_keys=True, ensure_ascii=False)
        with self._database.connect() as connection:
            # 序号检查与插入必须串行，否则两个相邻事件可能同时通过 MAX 校验。
            connection.execute("BEGIN IMMEDIATE")
            row = self._run(connection, class_id, run_id, learner)
            if request.epoch != row["epoch"] or row["status"] in {"completed", "failed"}:
                raise BusinessError(status_code=409, code="WEBOTS_EVENT_REJECTED", message="事件 epoch 或运行状态无效")
            existing = connection.execute("SELECT payload_json FROM webots_run_events WHERE run_id=? AND epoch=? AND sequence=?", (run_id, request.epoch, request.sequence)).fetchone()
            if existing:
                if existing["payload_json"] != payload:
                    raise BusinessError(status_code=409, code="WEBOTS_EVENT_CONFLICT", message="事件序号内容冲突")
                return self._to_run(connection, row)
            previous = connection.execute("SELECT MAX(sequence) AS value FROM webots_run_events WHERE run_id=? AND epoch=?", (run_id, request.epoch)).fetchone()["value"] or 0
            if request.sequence != previous + 1:
                raise BusinessError(status_code=409, code="WEBOTS_EVENT_OUT_OF_ORDER", message="事件序号存在缺口或乱序")
            connection.execute("INSERT INTO webots_run_events(run_id,epoch,sequence,payload_json,created_at) VALUES(?,?,?,?,?)", (run_id, request.epoch, request.sequence, payload, now))
            if row["status"] == "created":
                connection.execute("UPDATE webots_runs SET status='running', updated_at=? WHERE id=?", (now, run_id))
            updated = connection.execute("SELECT * FROM webots_runs WHERE id=?", (run_id,)).fetchone()
            return self._to_run(connection, updated)

    def submit_result(self, class_id: str, run_id: str, request: RunResultRequest, learner: UserView) -> RunView:
        now = self._now()
        result_json = json.dumps(request.result, sort_keys=True, ensure_ascii=False)
        with self._database.connect() as connection:
            row = self._run(connection, class_id, run_id, learner)
            if request.epoch != row["epoch"]:
                raise BusinessError(status_code=409, code="WEBOTS_RESULT_EPOCH_CONFLICT", message="结果 epoch 不匹配")
            if row["status"] in {"completed", "failed"}:
                if row["status"] == request.status and row["result_json"] == result_json:
                    return self._to_run(connection, row)
                raise BusinessError(status_code=409, code="WEBOTS_RESULT_CONFLICT", message="终态结果内容冲突")
            updated_cursor = connection.execute("UPDATE webots_runs SET status=?, result_json=?, updated_at=? WHERE id=? AND status=? AND epoch=?", (request.status, result_json, now, run_id, row["status"], row["epoch"]))
            if updated_cursor.rowcount != 1:
                raise BusinessError(status_code=409, code="WEBOTS_RESULT_CONFLICT", message="运行状态已变化，请刷新后重试")
            updated = connection.execute("SELECT * FROM webots_runs WHERE id=?", (run_id,)).fetchone()
            return self._to_run(connection, updated)

    @staticmethod
    def _to_run(connection: sqlite3.Connection, row: sqlite3.Row) -> RunView:
        last_sequence = connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) AS value FROM webots_run_events WHERE run_id=? AND epoch=?",
            (row["id"], row["epoch"]),
        ).fetchone()["value"]
        return RunView(
            id=row["id"],
            class_id=row["class_id"],
            learner_id=row["learner_id"],
            connector_id=row["connector_id"],
            task_id=row["task_id"],
            status=row["status"],
            epoch=row["epoch"],
            next_event_sequence=last_sequence + 1,
            result=json.loads(row["result_json"]) if row["result_json"] != "{}" else None,
        )
