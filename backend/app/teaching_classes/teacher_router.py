"""教师分析路由：教师仪表盘、学习者管理、聚合统计、仿真摘要、AI 作业分析。

prefix=/api/teaching-classes
"""
from fastapi import APIRouter

from app.common.api_response import ApiResponse
from app.common.responses import documented_error, success_response
from app.teaching_classes._deps import (
    HomeworkAIGradingDep,
    LearnerDep,
    PracticeModuleDep,
    Request,
    TeacherDep,
    TeacherInsightDep,
    TeacherAgentAIDep,
)
from app.teaching_classes.teacher_agent_ai import TeacherAIAnalysisView
from app.teaching_classes.models import (
    ClassAggregateStatsView,
    HomeworkAIAnalysisView,
    LearnerDetailView,
    LearnerListView,
    SimulationSummaryView,
    TeacherDashboardView,
)

router = APIRouter(prefix="/api/teaching-classes", tags=["teaching-classes"])


@router.get(
    "/{class_id}/aggregate-stats",
    response_model=ApiResponse[ClassAggregateStatsView],
    responses={403: documented_error("只有教学班正式成员可以查看聚合统计"), 404: documented_error("教学班不存在")},
)
def get_class_aggregate_stats(
    request: Request,
    class_id: str,
    learner: LearnerDep,
    practice: PracticeModuleDep,
) -> ApiResponse[ClassAggregateStatsView]:
    aggregate_stats = practice.get_class_aggregate_stats(class_id, learner)
    if aggregate_stats.insufficient_sample:
        return success_response(request, code="INSUFFICIENT_SAMPLE", message="样本不足，无法显示聚合统计", data=aggregate_stats)
    if aggregate_stats.no_data:
        return success_response(request, code="NO_DATA", message="无学习数据", data=aggregate_stats)
    return success_response(request, code="CLASS_AGGREGATE_STATS_FETCHED", message="班级聚合统计获取成功", data=aggregate_stats)


@router.get(
    "/{class_id}/teacher-dashboard",
    response_model=ApiResponse[TeacherDashboardView],
    responses={403: documented_error("只有班级教师可以查看dashboard"), 404: documented_error("教学班不存在")},
)
def get_teacher_dashboard(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    teacher_insight: TeacherInsightDep,
) -> ApiResponse[TeacherDashboardView]:
    dashboard_data = teacher_insight.get_teacher_dashboard(class_id, teacher)
    if dashboard_data.insufficient_sample:
        return success_response(request, code="INSUFFICIENT_SAMPLE", message="样本不足，无法显示dashboard数据", data=dashboard_data)
    if dashboard_data.no_data:
        return success_response(request, code="NO_DATA", message="无学习数据", data=dashboard_data)
    return success_response(request, code="TEACHER_DASHBOARD_FETCHED", message="教师dashboard数据获取成功", data=dashboard_data)


@router.post(
    "/{class_id}/teacher-dashboard/ai-analysis",
    response_model=ApiResponse[TeacherAIAnalysisView],
    responses={403: documented_error("只有班级教师可以生成学情分析"), 404: documented_error("教学班不存在")},
)
def generate_teacher_ai_analysis(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    teacher_insight: TeacherInsightDep,
    teacher_agent_ai: TeacherAgentAIDep,
) -> ApiResponse[TeacherAIAnalysisView]:
    """小 B：只把当前教师自有班级的聚合事实发送给模型。"""
    dashboard = teacher_insight.get_teacher_dashboard(class_id, teacher)
    analysis = teacher_agent_ai.analyze_dashboard(dashboard)
    return success_response(
        request,
        code="TEACHER_AI_ANALYSIS_COMPLETED",
        message="班级学情分析已生成",
        data=analysis,
    )


@router.get(
    "/{class_id}/webots/simulation-summary",
    response_model=ApiResponse[SimulationSummaryView],
    responses={403: documented_error("只有班级教师可以查看仿真摘要"), 404: documented_error("教学班不存在")},
)
def get_teacher_simulation_summary(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    teacher_insight: TeacherInsightDep,
) -> ApiResponse[SimulationSummaryView]:
    summary = teacher_insight.get_teacher_simulation_summary(class_id, teacher)
    return success_response(request, code="TEACHER_SIMULATION_SUMMARY_FETCHED", message="班级仿真摘要获取成功", data=summary)


@router.get(
    "/{class_id}/learners",
    response_model=ApiResponse[LearnerListView],
    responses={403: documented_error("只有班级教师可以查看学习者列表"), 404: documented_error("教学班不存在")},
)
def get_class_learners(
    request: Request,
    class_id: str,
    teacher: TeacherDep,
    teacher_insight: TeacherInsightDep,
) -> ApiResponse[LearnerListView]:
    learners = teacher_insight.get_class_learners(class_id, teacher)
    return success_response(request, code="LEARNERS_LISTED", message="学习者列表获取成功", data=learners)


@router.get(
    "/{class_id}/learners/{learner_id}",
    response_model=ApiResponse[LearnerDetailView],
    responses={403: documented_error("只有班级教师可以查看学习者详情"), 404: documented_error("学习者不存在或不是班级正式成员")},
)
def get_learner_detail(
    request: Request,
    class_id: str,
    learner_id: str,
    teacher: TeacherDep,
    teacher_insight: TeacherInsightDep,
) -> ApiResponse[LearnerDetailView]:
    learner_detail = teacher_insight.get_learner_detail(class_id, learner_id, teacher)
    return success_response(request, code="LEARNER_DETAIL_FETCHED", message="学习者详情获取成功", data=learner_detail)


@router.get(
    "/{class_id}/learners/{learner_id}/webots/simulation-summary",
    response_model=ApiResponse[SimulationSummaryView],
    responses={403: documented_error("只有班级教师可以查看仿真摘要"), 404: documented_error("学习者不存在或不是班级正式成员")},
)
def get_teacher_learner_simulation_summary(
    request: Request,
    class_id: str,
    learner_id: str,
    teacher: TeacherDep,
    teacher_insight: TeacherInsightDep,
) -> ApiResponse[SimulationSummaryView]:
    summary = teacher_insight.get_teacher_learner_simulation_summary(class_id, learner_id, teacher)
    return success_response(request, code="TEACHER_LEARNER_SIMULATION_SUMMARY_FETCHED", message="学习者仿真摘要获取成功", data=summary)


@router.get(
    "/{class_id}/homework/{homework_id}/ai-analysis/{learner_id}",
    response_model=ApiResponse[HomeworkAIAnalysisView],
    responses={403: documented_error("只有班级教师可以查看 AI 作业分析"), 404: documented_error("作业或学习者不存在")},
)
def get_homework_ai_analysis(
    request: Request,
    class_id: str,
    homework_id: str,
    learner_id: str,
    teacher: TeacherDep,
    homework_ai_grading: HomeworkAIGradingDep,
) -> ApiResponse[HomeworkAIAnalysisView]:
    """小C：AI 作业批改分析 - 对指定学习者的已提交作业生成错因分析与学习建议。"""
    view = homework_ai_grading.analyze_submission(
        class_id, homework_id, learner_id, teacher
    )
    return success_response(
        request,
        code="HOMEWORK_AI_ANALYSIS_COMPLETED",
        message="AI 作业分析已生成",
        data=HomeworkAIAnalysisView(
            homework_id=homework_id,
            learner_id=learner_id,
            analysis=view.analysis,
            suggestions=view.suggestions,
            source=view.source,
        ),
    )
