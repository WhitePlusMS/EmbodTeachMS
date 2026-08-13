"""Webots 模型定义。与 webots_connector 服务分离，遵循模型→服务分层原则。"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PairingView(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)

    pairing_token: str = Field(min_length=1)
    expires_at: int
    source: Literal["demo"] = "demo"


class PairingBindRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    pairing_token: str = Field(min_length=1)
    connector_id: str = Field(min_length=1, max_length=120)


class ConnectorView(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    connector_id: str
    connector_token: str
    class_id: str
    learner_id: str
    source: Literal["demo"] = "demo"
    bound_at: int


class EnvironmentReportRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    connector_id: str = Field(min_length=1, max_length=120)
    environment: dict[str, str] = Field(default_factory=dict, max_length=20)


class EnvironmentView(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    connector_id: str
    environment: dict[str, str]
    source: Literal["demo"] = "demo"
    reported_at: int


class TaskCatalogView(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    items: list[dict[str, str]]
    source: Literal["demo"] = "demo"


class RunCreateRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    connector_id: str = Field(min_length=1, max_length=120)
    task_id: str = Field(default="", max_length=120)


class RunView(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    id: str
    class_id: str
    learner_id: str
    connector_id: str
    task_id: str
    status: Literal["created", "dispatched", "running", "completed", "failed"]
    epoch: int
    next_event_sequence: int = Field(ge=1)
    source: Literal["demo"] = "demo"
    result: dict[str, object] | None = None


class RunCommandRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    command: Literal["start", "reset", "hard_reset", "fail"]


class RunEventRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    epoch: int = Field(ge=0)
    sequence: int = Field(ge=1)
    event_type: str = Field(min_length=1, max_length=80)
    payload: dict[str, object] = Field(default_factory=dict)


class RunResultRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    epoch: int = Field(ge=0)
    status: Literal["completed", "failed"]
    result: dict[str, object] = Field(default_factory=dict)


class ProtocolEnvelope(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    protocol_version: Literal["webots-demo-v1"]
    message_id: str = Field(min_length=1)
    message_type: Literal["environment", "command", "event", "result"]
    run_id: str | None = None
    epoch: int = Field(ge=0)
    event_sequence: int | None = Field(default=None, ge=1)
    payload: dict[str, object] = Field(default_factory=dict)
