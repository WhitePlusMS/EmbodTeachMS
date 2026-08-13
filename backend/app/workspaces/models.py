from pydantic import BaseModel

from app.auth.models import UserRole


class WorkspaceView(BaseModel):
    role: UserRole
    title: str
    navigation: list[str]

