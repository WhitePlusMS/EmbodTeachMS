import logging
import time
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHttpException

from app.auth.router import router as auth_router
from app.auth.service import AuthService
from app.common.api_response import ApiResponse
from app.common.errors import BusinessError
from app.database import Database
from app.document_parsing import CourseContentParsing
from app.llm_gateway import ChatGateway, UnconfiguredChatGateway
from app.llm_gateway.router import router as xiaod_router
from app.knowledge_bases.router import router as knowledge_base_router
from app.knowledge_bases.service import KnowledgeBaseService
from app.teaching_classes.class_router import router as class_router
from app.teaching_classes.content_router import router as content_router
from app.teaching_classes.preparation_router import router as preparation_router
from app.teaching_classes.practice_router import router as practice_router
from app.teaching_classes.homework_router import router as homework_router
from app.teaching_classes.webots_router import router as webots_router
from app.teaching_classes.teacher_router import router as teacher_router
from app.teaching_classes.preparation_sessions import (
    BackgroundExecutor,
    PreparationSessionModule,
    run_in_daemon_thread,
)
from app.teaching_classes.access import TeachingClassAccess
from app.teaching_classes.service import TeachingClassService
from app.teaching_classes.publication import PublicationModule
from app.teaching_classes.practice import PracticeModule
from app.teaching_classes.homework import HomeworkModule
from app.teaching_classes.homework_ai_grading import HomeworkAIGrading
from app.teaching_classes.teacher_agent_ai import TeacherAgentAI
from app.teaching_classes.teacher_insight import TeacherInsightModule
from app.teaching_classes.course_content_publisher import CourseContentPublisher
from app.workspaces.router import router as workspace_router
from app.webots_connector import WebotsConnectorService


logger = logging.getLogger("course_agent.api")


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    body = ApiResponse[None](
        code=code,
        message=message,
        data=None,
        request_id=request.state.request_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(by_alias=True),
    )


def create_app(
    *,
    database_path: Path,
    jwt_secret: str,
    allowed_origins: tuple[str, ...] = (),
    now_provider: Callable[[], int] | None = None,
    course_content_parsing: CourseContentParsing | None = None,
    parsing_executor: BackgroundExecutor | None = None,
    chat_gateway: ChatGateway | None = None,
) -> FastAPI:
    database = Database(database_path)
    current_time = now_provider or (lambda: int(time.time()))
    content_parser = course_content_parsing or CourseContentParsing()
    background_executor = parsing_executor or run_in_daemon_thread
    teaching_chat_gateway = chat_gateway or UnconfiguredChatGateway()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database.initialize()
        app.state.auth_service = AuthService(database, jwt_secret, current_time)
        app.state.course_content_parsing = content_parser
        app.state.knowledge_base_service = KnowledgeBaseService(database, current_time)
        app.state.practice_module = PracticeModule(database, current_time)
        app.state.homework_module = HomeworkModule(database, current_time)
        app.state.homework_ai_grading = HomeworkAIGrading(
            database, teaching_chat_gateway
        )
        app.state.teacher_agent_ai = TeacherAgentAI(teaching_chat_gateway)
        app.state.teacher_insight_module = TeacherInsightModule(
            database, app.state.practice_module
        )

        # 备课模块共享的依赖：让 PublicationModule 和 PreparationSessionModule
        # 共享同一份 PreparationSessionRecords / StateStore / QuestionReviewModel，
        # 避免两条初始化路径导致数据查询不一致。
        from app.teaching_classes.preparation_state import PreparationSessionStateStore
        from app.teaching_classes.preparation_sessions import PreparationSessionRecords
        from app.teaching_classes.question_review import QuestionReviewModule
        from app.teaching_classes.course_overview import CourseOverviewModule
        from app.teaching_classes.content_query import PublishedContentQuery
        shared_records = PreparationSessionRecords()
        shared_state_store = PreparationSessionStateStore()
        shared_question_review = QuestionReviewModule()

        # 直接实例化子模块，避免通过 TeachingClassService 私有属性访问
        app.state.course_overview_module = CourseOverviewModule(database, current_time, chat_gateway=teaching_chat_gateway)
        app.state.content_query_module = PublishedContentQuery(database, current_time, app.state.practice_module)

        app.state.teaching_class_service = TeachingClassService(
            database,
            current_time,
            app.state.practice_module,
            course_overview=app.state.course_overview_module,
            content_query=app.state.content_query_module,
            chat_gateway=teaching_chat_gateway,
        )
        app.state.preparation_session_module = PreparationSessionModule(
            database,
            current_time,
            content_parser,
            background_executor,
            app.state.knowledge_base_service,
            chat_gateway=teaching_chat_gateway,
            records=shared_records,
            state_store=shared_state_store,
            question_review=shared_question_review,
        )
        app.state.course_content_publisher = CourseContentPublisher(current_time)
        app.state.publication_module = PublicationModule(
            database, current_time, app.state.course_content_publisher,
            records=shared_records,
            state_store=shared_state_store,
            question_review=shared_question_review,
        )
        app.state.webots_connector_service = WebotsConnectorService(
            database, current_time, TeachingClassAccess()
        )
        app.state.xiaod_chat_gateway = teaching_chat_gateway
        yield

    app = FastAPI(
        title="EmbodTeachMS 具身课堂 API",
        version="0.1.0",
        lifespan=lifespan,
    )

    def custom_openapi() -> dict[str, object]:
        """让 OpenAPI 的校验错误与运行时统一响应 DTO 保持一致。"""
        if app.openapi_schema is None:
            schema = get_openapi(
                title=app.title,
                version=app.version,
                routes=app.routes,
            )
            error_schema = {
                "$ref": "#/components/schemas/ApiResponse_NoneType_"
            }
            for path_item in schema.get("paths", {}).values():
                for operation in path_item.values():
                    if not isinstance(operation, dict):
                        continue
                    responses = operation.get("responses")
                    if not isinstance(responses, dict) or "422" not in responses:
                        continue
                    responses["422"] = {
                        "description": "请求参数不正确",
                        "content": {"application/json": {"schema": error_schema}},
                    }
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
            expose_headers=["X-Request-Id"],
        )

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = request.headers.get(
            "X-Request-Id", str(uuid.uuid4())
        )
        started_at = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        logger.info(
            "request_complete method=%s path=%s status=%s duration_ms=%d request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started_at) * 1000,
            request.state.request_id,
        )
        return response

    @app.exception_handler(BusinessError)
    async def handle_business_error(
        request: Request, error: BusinessError
    ) -> JSONResponse:
        logger.info(
            "business_error path=%s code=%s request_id=%s",
            request.url.path,
            error.code,
            request.state.request_id,
        )
        return _error_response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=error.message,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, _error: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
            message="请求参数不正确",
        )

    @app.exception_handler(StarletteHttpException)
    async def handle_http_error(
        request: Request, error: StarletteHttpException
    ) -> JSONResponse:
        if error.status_code == 404:
            return _error_response(
                request,
                status_code=404,
                code="RESOURCE_NOT_FOUND",
                message="请求的资源不存在",
            )
        return _error_response(
            request,
            status_code=error.status_code,
            code="HTTP_ERROR",
            message="请求失败",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, error: Exception
    ) -> JSONResponse:
        # 只记录异常类型和请求定位信息，避免异常消息意外包含正文或凭证。
        logger.error(
            "unexpected_error path=%s error_type=%s request_id=%s",
            request.url.path,
            type(error).__name__,
            request.state.request_id,
        )
        return _error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="服务暂时不可用，请稍后重试",
        )

    app.include_router(auth_router)
    app.include_router(workspace_router)
    app.include_router(knowledge_base_router)
    app.include_router(class_router)
    app.include_router(content_router)
    app.include_router(preparation_router)
    app.include_router(practice_router)
    app.include_router(homework_router)
    app.include_router(webots_router)
    app.include_router(teacher_router)
    app.include_router(xiaod_router)
    return app
