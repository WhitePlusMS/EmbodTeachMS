"""作业路由：作业草稿、提交、详情、列表。

prefix=/api/teaching-classes
"""
from fastapi import APIRouter, status

from app.common.api_response import ApiResponse
from app.common.responses import documented_error, success_response
from app.teaching_classes._deps import (
    HomeworkModuleDep,
    LearnerDep,
    Request,
    TeacherDep,
)
from app.teaching_classes.models import (
    HomeworkListView,
    HomeworkSubmissionDetailView,
    HomeworkSubmissionResultView,
    HomeworkSubmissionView,
    SaveHomeworkDraftBody,
    SaveHomeworkDraftRequest,
    SubmitHomeworkBody,
    SubmitHomeworkRequest,
    TeacherHomeworkListView,
)

router = APIRouter(prefix="/api/teaching-classes", tags=["teaching-classes"])


@router.post(
    "/{class_id}/homework/{homework_id}/save-draft",
    response_model=ApiResponse[HomeworkSubmissionView],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("作业已提交或答案格式无效"), 403: documented_error("只有班级正式成员可以保存作业草稿"), 404: documented_error("作业不存在")},
)
def save_homework_draft(
    request: Request,
    class_id: str,
    homework_id: str,
    body: SaveHomeworkDraftBody,
    learner: LearnerDep,
    homework: HomeworkModuleDep,
) -> ApiResponse[HomeworkSubmissionView]:
    submission = homework.save_homework_draft(SaveHomeworkDraftRequest(class_id=class_id, homework_id=homework_id, answers=body.answers), learner)
    return success_response(request, code="HOMEWORK_DRAFT_SAVED", message="作业草稿保存成功", data=submission)


@router.post(
    "/{class_id}/homework/{homework_id}/submit",
    response_model=ApiResponse[HomeworkSubmissionResultView],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("作业已提交或答案格式无效"), 403: documented_error("只有班级正式成员可以提交作业"), 404: documented_error("作业不存在")},
)
def submit_homework(
    request: Request,
    class_id: str,
    homework_id: str,
    body: SubmitHomeworkBody,
    learner: LearnerDep,
    homework: HomeworkModuleDep,
) -> ApiResponse[HomeworkSubmissionResultView]:
    result = homework.submit_homework(SubmitHomeworkRequest(class_id=class_id, homework_id=homework_id, answers=body.answers), learner)
    return success_response(request, code="HOMEWORK_SUBMITTED", message="作业提交成功", data=result)


@router.get(
    "/{class_id}/homework/{homework_id}/submission",
    response_model=ApiResponse[HomeworkSubmissionDetailView],
    responses={403: documented_error("只有班级正式成员可以查看作业提交详情"), 404: documented_error("作业不存在")},
)
def get_homework_submission_detail(
    request: Request,
    class_id: str,
    homework_id: str,
    learner: LearnerDep,
    homework: HomeworkModuleDep,
) -> ApiResponse[HomeworkSubmissionDetailView]:
    detail = homework.get_homework_submission_detail(class_id, homework_id, learner)
    return success_response(request, code="HOMEWORK_SUBMISSION_DETAIL_FETCHED", message="作业提交详情获取成功", data=detail)


@router.get(
    "/{class_id}/homework",
    response_model=ApiResponse[HomeworkListView],
    responses={403: documented_error("只有班级正式成员可以查看作业列表"), 404: documented_error("教学班不存在")},
)
def list_homework_for_learner(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    homework: HomeworkModuleDep,
) -> ApiResponse[HomeworkListView]:
    homework_list = homework.list_homework_for_learner(class_id, learner)
    return success_response(request, code="HOMEWORK_LIST_FETCHED", message="作业列表获取成功", data=homework_list)


@router.get(
    "/{class_id}/teacher-homework",
    response_model=ApiResponse[TeacherHomeworkListView],
    responses={403: documented_error("只有班级教师可以查看作业统计"), 404: documented_error("教学班不存在")},
)
def list_teacher_homework(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    homework: HomeworkModuleDep,
) -> ApiResponse[TeacherHomeworkListView]:
    homework_list = homework.list_teacher_homework(class_id, teacher)
    return success_response(
        request, code="TEACHER_HOMEWORK_LISTED",
        message="教师作业统计获取成功" if not homework_list.no_data else "暂无已发布作业", data=homework_list,
    )
