"""共享依赖注入函数和权限快捷方式。

teaching_classes 子路由复用这些依赖，避免在每个子路由文件重复定义。
"""
from typing import Annotated

from fastapi import Depends, Request

from app.auth.models import UserRole, UserView
from app.auth.router import get_current_user, require_role
from app.knowledge_bases.service import KnowledgeBaseService
from app.teaching_classes.course_overview import CourseOverviewModule
from app.teaching_classes.content_query import PublishedContentQuery
from app.teaching_classes.homework import HomeworkModule
from app.teaching_classes.homework_ai_grading import HomeworkAIGrading
from app.teaching_classes.preparation_sessions import PreparationSessionModule
from app.teaching_classes.practice import PracticeModule
from app.teaching_classes.publication import PublicationModule
from app.teaching_classes.service import TeachingClassService
from app.teaching_classes.teacher_insight import TeacherInsightModule
from app.teaching_classes.teacher_agent_ai import TeacherAgentAI
from app.webots_connector import WebotsConnectorService


def get_teaching_class_service(request: Request) -> TeachingClassService:
    return request.app.state.teaching_class_service


def get_course_overview_module(request: Request) -> CourseOverviewModule:
    return request.app.state.course_overview_module


def get_content_query_module(request: Request) -> PublishedContentQuery:
    return request.app.state.content_query_module


def get_preparation_session_module(request: Request) -> PreparationSessionModule:
    return request.app.state.preparation_session_module


def get_publication_module(request: Request) -> PublicationModule:
    return request.app.state.publication_module


def get_practice_module(request: Request) -> PracticeModule:
    return request.app.state.practice_module


def get_homework_module(request: Request) -> HomeworkModule:
    return request.app.state.homework_module


def get_teacher_insight_module(request: Request) -> TeacherInsightModule:
    return request.app.state.teacher_insight_module


def get_homework_ai_grading(request: Request) -> HomeworkAIGrading:
    return request.app.state.homework_ai_grading


def get_teacher_agent_ai(request: Request) -> TeacherAgentAI:
    return request.app.state.teacher_agent_ai


def get_webots_connector_service(request: Request) -> WebotsConnectorService:
    return request.app.state.webots_connector_service


def get_knowledge_base_service(request: Request) -> KnowledgeBaseService:
    return request.app.state.knowledge_base_service


require_teacher = require_role(UserRole.TEACHER, message="只有教师可以访问教学班功能")

require_learner = require_role(UserRole.LEARNER, message="只有学习者可以访问此功能")


TeacherDep = Annotated[UserView, Depends(require_teacher)]
LearnerDep = Annotated[UserView, Depends(require_learner)]
CurrentUserDep = Annotated[UserView, Depends(get_current_user)]

TeachingClassServiceDep = Annotated[TeachingClassService, Depends(get_teaching_class_service)]
CourseOverviewDep = Annotated[CourseOverviewModule, Depends(get_course_overview_module)]
ContentQueryDep = Annotated[PublishedContentQuery, Depends(get_content_query_module)]
PreparationSessionDep = Annotated[PreparationSessionModule, Depends(get_preparation_session_module)]
PublicationModuleDep = Annotated[PublicationModule, Depends(get_publication_module)]
PracticeModuleDep = Annotated[PracticeModule, Depends(get_practice_module)]
HomeworkModuleDep = Annotated[HomeworkModule, Depends(get_homework_module)]
TeacherInsightDep = Annotated[TeacherInsightModule, Depends(get_teacher_insight_module)]
HomeworkAIGradingDep = Annotated[HomeworkAIGrading, Depends(get_homework_ai_grading)]
TeacherAgentAIDep = Annotated[TeacherAgentAI, Depends(get_teacher_agent_ai)]
WebotsServiceDep = Annotated[WebotsConnectorService, Depends(get_webots_connector_service)]
KnowledgeBaseServiceDep = Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)]
