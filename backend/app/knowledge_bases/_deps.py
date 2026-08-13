"""共享依赖注入函数和权限快捷方式。

knowledge_bases 路由复用这些依赖，避免在每个路由重复定义。
"""
from typing import Annotated

from fastapi import Depends, Request

from app.auth.models import UserRole, UserView
from app.auth.router import get_current_user, require_role
from app.knowledge_bases.service import KnowledgeBaseService


def get_knowledge_base_service(request: Request) -> KnowledgeBaseService:
    return request.app.state.knowledge_base_service


require_teacher_simple = require_role(UserRole.TEACHER, message="只有教师可以管理课件知识库")

TeacherDep = Annotated[UserView, Depends(require_teacher_simple)]
KnowledgeBaseServiceDep = Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)]
