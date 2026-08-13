"""Webots 路由：配对、绑定、环境报告、运行管理。

prefix=/api/teaching-classes
"""
from fastapi import APIRouter, Header

from app.common.api_response import ApiResponse
from app.common.responses import success_response
from app.teaching_classes._deps import (
    LearnerDep,
    Request,
    WebotsServiceDep,
)
from app.webots_models import (
    ConnectorView,
    EnvironmentReportRequest,
    EnvironmentView,
    PairingBindRequest,
    PairingView,
    ProtocolEnvelope,
    RunCommandRequest,
    RunCreateRequest,
    RunEventRequest,
    RunResultRequest,
    RunView,
    TaskCatalogView,
)

router = APIRouter(prefix="/api/teaching-classes", tags=["teaching-classes"])


@router.post("/{class_id}/webots/pairing", response_model=ApiResponse[PairingView])
def create_webots_pairing(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[PairingView]:
    pairing = service.create_pairing(class_id, learner)
    return success_response(request, code="WEBOTS_PAIRING_CREATED", message="替身连接器配对凭证已生成", data=pairing)


@router.post("/{class_id}/webots/pairing/bind", response_model=ApiResponse[ConnectorView])
def bind_webots_pairing(
    request: Request,
    class_id: str,
    body: PairingBindRequest,
    service: WebotsServiceDep,
) -> ApiResponse[ConnectorView]:
    connector = service.bind_pairing(class_id, body)
    return success_response(request, code="WEBOTS_CONNECTOR_BOUND", message="替身连接器已绑定", data=connector)


@router.post("/{class_id}/webots/environment", response_model=ApiResponse[EnvironmentView])
def report_webots_environment(
    request: Request,
    class_id: str,
    body: EnvironmentReportRequest,
    service: WebotsServiceDep,
    connector_token: str | None = Header(alias="X-Connector-Token", default=None),
) -> ApiResponse[EnvironmentView]:
    environment = service.report_environment(class_id, body, connector_token)
    return success_response(request, code="WEBOTS_ENVIRONMENT_REPORTED", message="替身环境报告已登记", data=environment)


@router.get("/{class_id}/webots/environment/{connector_id}", response_model=ApiResponse[EnvironmentView])
def get_webots_environment(
    request: Request,
    class_id: str,
    connector_id: str,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[EnvironmentView]:
    environment = service.get_environment(class_id, learner, connector_id)
    return success_response(request, code="WEBOTS_ENVIRONMENT_FETCHED", message="替身环境报告获取成功", data=environment)


@router.get("/{class_id}/webots/tasks", response_model=ApiResponse[TaskCatalogView])
def list_webots_tasks(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[TaskCatalogView]:
    tasks = service.list_tasks(class_id, learner)
    return success_response(request, code="WEBOTS_TASKS_LISTED", message="替身任务目录获取成功", data=tasks)


@router.post("/{class_id}/webots/runs", response_model=ApiResponse[RunView])
def create_webots_run(
    request: Request,
    class_id: str,
    body: RunCreateRequest,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[RunView]:
    run = service.create_run(class_id, body, learner)
    return success_response(request, code="WEBOTS_RUN_CREATED", message="替身仿真运行已创建", data=run)


@router.get("/{class_id}/webots/runs", response_model=ApiResponse[list[RunView]])
def list_webots_runs(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[list[RunView]]:
    runs = service.list_runs(class_id, learner)
    return success_response(request, code="WEBOTS_RUNS_LISTED", message="替身仿真历史获取成功", data=runs)


@router.post("/{class_id}/webots/runs/{run_id}/command", response_model=ApiResponse[RunView])
def command_webots_run(
    request: Request,
    class_id: str,
    run_id: str,
    body: RunCommandRequest,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[RunView]:
    run = service.command(class_id, run_id, body, learner)
    return success_response(request, code="WEBOTS_RUN_COMMAND_ACCEPTED", message="替身仿真命令已处理", data=run)


@router.post("/{class_id}/webots/runs/{run_id}/events", response_model=ApiResponse[RunView])
def add_webots_event(
    request: Request,
    class_id: str,
    run_id: str,
    body: RunEventRequest,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[RunView]:
    run = service.add_event(class_id, run_id, body, learner)
    return success_response(request, code="WEBOTS_EVENT_ACCEPTED", message="替身事件已处理", data=run)


@router.post("/{class_id}/webots/runs/{run_id}/result", response_model=ApiResponse[RunView])
def submit_webots_result(
    request: Request,
    class_id: str,
    run_id: str,
    body: RunResultRequest,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[RunView]:
    run = service.submit_result(class_id, run_id, body, learner)
    return success_response(request, code="WEBOTS_RESULT_ACCEPTED", message="替身权威结果已处理", data=run)


@router.post("/{class_id}/webots/messages", response_model=ApiResponse[ProtocolEnvelope])
def validate_webots_envelope(
    request: Request,
    class_id: str,
    body: ProtocolEnvelope,
    learner: LearnerDep,
    service: WebotsServiceDep,
) -> ApiResponse[ProtocolEnvelope]:
    service.list_tasks(class_id, learner)
    return success_response(request, code="WEBOTS_ENVELOPE_ACCEPTED", message="替身协议信封已验证", data=body)
