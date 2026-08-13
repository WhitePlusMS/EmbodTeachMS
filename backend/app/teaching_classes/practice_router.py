"""练习路由：课堂练习、基准练习、掌握度摘要。

prefix=/api/teaching-classes
"""
from fastapi import APIRouter, status

from app.common.api_response import ApiResponse
from app.common.responses import documented_error, success_response
from app.teaching_classes._deps import (
    LearnerDep,
    PracticeModuleDep,
    Request,
)
from app.teaching_classes.baseline_practice_models import (
    BaselinePracticeDetail,
    BaselinePracticeResult,
    BaselinePracticeSubmitRequest,
)
from app.teaching_classes.models import (
    ClassroomPracticeAnswerBody,
    ClassroomPracticeContentDetailView,
    ClassroomPracticeResultView,
    MasterySummaryView,
)

router = APIRouter(prefix="/api/teaching-classes", tags=["teaching-classes"])


@router.get(
    "/{class_id}/published-contents/{content_id}/practice-detail",
    response_model=ApiResponse[ClassroomPracticeContentDetailView],
    responses={400: documented_error("该内容不是课堂练习"), 403: documented_error("只有班级正式成员可以查看课堂练习"), 404: documented_error("课堂练习不存在")},
)
def get_classroom_practice_content_detail(
    request: Request,
    class_id: str,
    content_id: str,
    learner: LearnerDep,
    practice: PracticeModuleDep,
) -> ApiResponse[ClassroomPracticeContentDetailView]:
    detail = practice.get_classroom_practice_content_detail(class_id, content_id, learner)
    return success_response(request, code="CLASSROOM_PRACTICE_DETAIL_FETCHED", message="课堂练习详情获取成功", data=detail)


@router.post(
    "/{class_id}/published-contents/{content_id}/submit-answer",
    response_model=ApiResponse[ClassroomPracticeResultView],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("已作答或答案无效"), 403: documented_error("只有班级正式成员可以作答课堂练习"), 404: documented_error("课堂练习不存在")},
)
def submit_classroom_practice_answer(
    request: Request,
    class_id: str,
    content_id: str,
    body: ClassroomPracticeAnswerBody,
    learner: LearnerDep,
    practice: PracticeModuleDep,
) -> ApiResponse[ClassroomPracticeResultView]:
    from app.teaching_classes.models import ClassroomPracticeAnswerRequest
    result = practice.submit_classroom_practice_answer(
        ClassroomPracticeAnswerRequest(class_id=class_id, content_id=content_id, selected_answers=body.selected_answers), learner,
    )
    return success_response(request, code="CLASSROOM_PRACTICE_ANSWER_SUBMITTED", message="答案提交成功", data=result)


@router.get(
    "/{class_id}/published-contents/{content_id}/baseline-practice",
    response_model=ApiResponse[BaselinePracticeDetail],
    responses={400: documented_error("该内容不是基准练习"), 403: documented_error("只有班级正式成员可以查看基准练习"), 404: documented_error("基准练习不存在")},
)
def get_baseline_practice_detail(
    request: Request,
    class_id: str,
    content_id: str,
    learner: LearnerDep,
    practice: PracticeModuleDep,
) -> ApiResponse[BaselinePracticeDetail]:
    detail = practice.get_baseline_practice_detail(class_id, content_id, learner)
    return success_response(request, code="BASELINE_PRACTICE_DETAIL_FETCHED", message="基准练习详情获取成功", data=detail)


@router.post(
    "/{class_id}/published-contents/{content_id}/baseline-practice/submit",
    response_model=ApiResponse[BaselinePracticeResult],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("答案为空或练习已进入终态"), 403: documented_error("只有班级正式成员可以提交基准练习"), 404: documented_error("基准练习不存在")},
)
def submit_baseline_practice_answer(
    request: Request,
    class_id: str,
    content_id: str,
    body: BaselinePracticeSubmitRequest,
    learner: LearnerDep,
    practice: PracticeModuleDep,
) -> ApiResponse[BaselinePracticeResult]:
    result = practice.submit_baseline_practice_answer(class_id, content_id, body.selected_answers, learner)
    return success_response(request, code="BASELINE_PRACTICE_ANSWER_SUBMITTED", message="基准练习答案提交成功", data=result)


@router.post(
    "/{class_id}/published-contents/{content_id}/baseline-practice/abandon",
    response_model=ApiResponse[BaselinePracticeResult],
    status_code=status.HTTP_201_CREATED,
    responses={400: documented_error("练习已进入终态"), 403: documented_error("只有班级正式成员可以放弃基准练习"), 404: documented_error("基准练习不存在")},
)
def abandon_baseline_practice(
    request: Request,
    class_id: str,
    content_id: str,
    learner: LearnerDep,
    practice: PracticeModuleDep,
) -> ApiResponse[BaselinePracticeResult]:
    result = practice.abandon_baseline_practice(class_id, content_id, learner)
    return success_response(request, code="BASELINE_PRACTICE_ABANDONED", message="基准练习放弃成功", data=result)


@router.get(
    "/{class_id}/mastery-summary",
    response_model=ApiResponse[MasterySummaryView],
    responses={403: documented_error("只有班级正式成员可以查看掌握度摘要"), 404: documented_error("教学班不存在")},
)
def get_mastery_summary(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    practice: PracticeModuleDep,
) -> ApiResponse[MasterySummaryView]:
    mastery_summary = practice.get_mastery_summary(class_id, learner)
    return success_response(request, code="MASTERY_SUMMARY_FETCHED", message="掌握度摘要获取成功", data=mastery_summary)
