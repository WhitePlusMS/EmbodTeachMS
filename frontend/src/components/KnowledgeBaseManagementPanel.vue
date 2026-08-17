<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
	ApiError,
	type KnowledgeBaseDocumentView,
	type KnowledgeBaseIndexStatusView,
	type KnowledgeBaseSearchView,
	type KnowledgeBaseSegmentPreviewView,
	type KnowledgeBaseSegmentView,
	type KnowledgeBaseSettingsView,
	type KnowledgeBaseView,
	type TeachingClassView,
} from "../api/client";
import type { SessionClient } from "../api/session";
import { useAsyncAction } from "../modules/async-action";
import { useAsyncResource } from "../modules/async-resource";
import { toggleSelection } from "../modules/collection-state";
import KnowledgeBaseDocumentManagementPanel from "./KnowledgeBaseDocumentManagementPanel.vue";
import KnowledgeBaseDocumentPicker from "./KnowledgeBaseDocumentPicker.vue";

const props = defineProps<{
	classes: TeachingClassView[];
	activeClassId?: string | undefined;
	session: SessionClient;
}>();

const emit = defineEmits<{
	backToCourses: [];
}>();

type WorkbenchTab = "documents" | "segments" | "retrieval";
type LoadState = "loading" | "ready" | "empty" | "error";
type KnowledgeBaseResources = {
	documents: KnowledgeBaseDocumentView[];
	settings: KnowledgeBaseSettingsView;
	indexStatus: KnowledgeBaseIndexStatusView;
};

const ADVANCED_SEPARATOR_OPTIONS = [
	{ value: "#", label: "# · 一级标题" },
	{ value: "##", label: "## · 二级标题" },
	{ value: "###", label: "### · 三级标题" },
	{ value: "。", label: "。 · 句号" },
	{ value: "，", label: "， · 逗号" },
	{ value: "；", label: "； · 分号" },
] as const;

const errorMessage = ref("");
const notice = ref("");
const knowledgeBasesResource = useAsyncResource<KnowledgeBaseView[]>((reason) => {
	console.error("Failed to load teacher knowledge bases:", reason);
	return messageFor(reason);
});
const knowledgeBaseResource = useAsyncResource<KnowledgeBaseResources>((reason) => {
	console.error("Failed to load knowledge base resources:", reason);
	return messageFor(reason);
});
const segmentsResource = useAsyncResource<KnowledgeBaseSegmentView[]>((reason) => {
	console.error("Failed to load knowledge base segments:", reason);
	return messageFor(reason);
});
const createKnowledgeBaseAction = useAsyncAction<KnowledgeBaseView>(messageFor);
const saveKnowledgeBaseAction = useAsyncAction<KnowledgeBaseView>(messageFor);
const archiveKnowledgeBaseAction = useAsyncAction<boolean>(messageFor);
const previewSegmentsAction = useAsyncAction<KnowledgeBaseSegmentPreviewView>(messageFor);
const rebuildSegmentsAction = useAsyncAction<{
	result: Awaited<ReturnType<SessionClient["rebuildKnowledgeBaseSegments"]>>;
	indexStatus: KnowledgeBaseIndexStatusView;
}>(messageFor);
const retrievalAction = useAsyncAction<KnowledgeBaseSearchView>(messageFor);
const importDocumentsAction = useAsyncAction<Awaited<ReturnType<SessionClient["importKnowledgeBaseDocuments"]>>>(messageFor);
const knowledgeBases = knowledgeBasesResource.data;
const selectedKnowledgeBaseId = ref("");
const documents = ref<KnowledgeBaseDocumentView[]>([]);
const indexStatus = ref<KnowledgeBaseIndexStatusView | null>(null);
const settings = ref<KnowledgeBaseSettingsView | null>(null);
const segments = computed(() => segmentsResource.data.value ?? []);
const activeTab = ref<WorkbenchTab>("documents");
const selectedSegmentDocumentId = ref("");
const preview = ref<KnowledgeBaseSegmentPreviewView | null>(null);
const retrievalResult = ref<KnowledgeBaseSearchView | null>(null);

const newKnowledgeBaseName = ref("");
const newKnowledgeBaseDescription = ref("");
const editingKnowledgeBase = ref(false);
const editingName = ref("");
const editingDescription = ref("");
const retrievalQuery = ref("");
const retrievalMode = ref<"keyword" | "vector" | "hybrid">("hybrid");
const retrievalTopK = ref(5);
const retrievalMinScore = ref(0);
const selectedImportDocumentIds = ref<string[]>([]);
const importClassId = ref("");
const importConflictStrategy = ref<"skip" | "replace" | "copy">("skip");

const loading = computed(() => knowledgeBasesResource.loading.value || knowledgeBaseResource.loading.value);
const creating = createKnowledgeBaseAction.loading;
const saving = computed(() => saveKnowledgeBaseAction.loading.value || archiveKnowledgeBaseAction.loading.value);
const previewing = previewSegmentsAction.loading;
const rebuilding = rebuildSegmentsAction.loading;
const testingRetrieval = retrievalAction.loading;
const importing = importDocumentsAction.loading;
const currentKnowledgeBase = computed(
	() => knowledgeBases.value?.find((item) => item.id === selectedKnowledgeBaseId.value) ?? null,
);
const activeKnowledgeBases = computed(() => (knowledgeBases.value ?? []).filter((item) => item.status !== "archived"));
const archivedKnowledgeBases = computed(() => (knowledgeBases.value ?? []).filter((item) => item.status === "archived"));
const state = computed<LoadState>(() => {
	if (knowledgeBasesResource.loading.value || knowledgeBasesResource.data.value === null && !knowledgeBasesResource.error.value) return "loading";
	if (knowledgeBasesResource.error.value) return "error";
	return selectedKnowledgeBaseId.value ? "ready" : "empty";
});
const selectedSegmentDocument = computed(
	() => documents.value.find((item) => item.id === selectedSegmentDocumentId.value) ?? null,
);
const visibleSegments = computed(() =>
	selectedSegmentDocumentId.value
		? segments.value.filter((item) => item.documentId === selectedSegmentDocumentId.value)
		: segments.value,
);
const canImport = computed(() =>
	Boolean(importClassId.value && selectedImportDocumentIds.value.length && currentKnowledgeBase.value),
);
const advancedSeparator = computed({
	get: () => settings.value?.separators[0] ?? "#",
	set: (value: string) => {
		if (settings.value) settings.value.separators = [value];
	},
});

function messageFor(error: unknown): string {
	if (error instanceof ApiError && error.status === 401) return "登录状态已失效，请重新登录后再试。";
	if (error instanceof ApiError && error.status === 403) return "你没有权限执行当前知识库操作。";
	if (error instanceof ApiError) return error.message;
	return "知识库操作失败，请检查服务连接后重试。";
}

function clearTransientMessages(): void {
	errorMessage.value = "";
	notice.value = "";
}

function handleDocumentNotice(message: string): void {
	errorMessage.value = "";
	notice.value = message;
}

function handleDocumentError(message: string): void {
	notice.value = "";
	errorMessage.value = message;
}

async function refreshCurrentKnowledgeBase(): Promise<void> {
	const current = currentKnowledgeBase.value;
	if (current) await loadKnowledgeBase(current.id);
}

async function loadKnowledgeBases(preferredId?: string): Promise<void> {
	clearTransientMessages();
	const items = await knowledgeBasesResource.execute(async () =>
		(await props.session.listTeacherKnowledgeBases()).items.filter((item) => item.kind === "reusable"),
	);
	if (!items) {
		errorMessage.value = knowledgeBasesResource.error.value ?? "知识库加载失败";
		return;
	}
	const nextId =
		preferredId && items.some((item) => item.id === preferredId)
			? preferredId
			: (items.find((item) => item.status !== "archived")?.id ?? items[0]?.id ?? "");
	selectedKnowledgeBaseId.value = nextId;
	if (nextId) await loadKnowledgeBase(nextId);
}

async function loadKnowledgeBase(knowledgeBaseId: string): Promise<void> {
	if (!knowledgeBaseId) return;
	documents.value = [];
	settings.value = null;
	segmentsResource.reset();
	preview.value = null;
	retrievalResult.value = null;
	selectedImportDocumentIds.value = [];
	const resources = await knowledgeBaseResource.execute(async () => {
		const [documentView, settingsView, indexView] = await Promise.all([
			props.session.listKnowledgeBaseDocuments(knowledgeBaseId),
			props.session.getKnowledgeBaseSettings(knowledgeBaseId),
			props.session.getKnowledgeBaseIndexStatus(knowledgeBaseId),
		]);
		return { documents: documentView.items, settings: settingsView, indexStatus: indexView };
	});
	if (!resources || selectedKnowledgeBaseId.value !== knowledgeBaseId) {
		if (knowledgeBaseResource.error.value) errorMessage.value = knowledgeBaseResource.error.value;
		return;
	}
	documents.value = resources.documents;
	settings.value = resources.settings;
	indexStatus.value = resources.indexStatus;
	selectedSegmentDocumentId.value = resources.documents[0]?.id ?? "";
	if (activeTab.value === "segments") await loadSegments(knowledgeBaseId);
	if (knowledgeBaseResource.error.value) errorMessage.value = knowledgeBaseResource.error.value;
}

async function selectKnowledgeBase(knowledgeBaseId: string): Promise<void> {
	selectedKnowledgeBaseId.value = knowledgeBaseId;
	await loadKnowledgeBase(knowledgeBaseId);
}

async function createKnowledgeBase(): Promise<void> {
	const name = newKnowledgeBaseName.value.trim();
	if (!name || creating.value) return;
	clearTransientMessages();
	const created = await createKnowledgeBaseAction.execute(() => props.session.createTeacherKnowledgeBase({
			name,
			description: newKnowledgeBaseDescription.value.trim(),
		}));
	if (!created) {
		errorMessage.value = createKnowledgeBaseAction.error.value ?? "知识库创建失败";
		return;
	}
	newKnowledgeBaseName.value = "";
	newKnowledgeBaseDescription.value = "";
	notice.value = "知识库已创建。";
	await loadKnowledgeBases(created.id);
}

function startKnowledgeBaseEdit(): void {
	if (!currentKnowledgeBase.value) return;
	editingKnowledgeBase.value = true;
	editingName.value = currentKnowledgeBase.value.name;
	editingDescription.value = currentKnowledgeBase.value.description;
}

async function saveKnowledgeBase(): Promise<void> {
	const current = currentKnowledgeBase.value;
	if (!current || !editingName.value.trim()) return;
	clearTransientMessages();
	const updated = await saveKnowledgeBaseAction.execute(() => props.session.updateTeacherKnowledgeBase(current.id, {
			name: editingName.value.trim(),
			description: editingDescription.value.trim(),
		}));
	if (!updated) {
		errorMessage.value = saveKnowledgeBaseAction.error.value ?? "知识库保存失败";
		return;
	}
	knowledgeBases.value = (knowledgeBases.value ?? []).map((item) => (item.id === updated.id ? updated : item));
	editingKnowledgeBase.value = false;
	notice.value = "知识库信息已保存。";
}

async function archiveKnowledgeBase(): Promise<void> {
	const current = currentKnowledgeBase.value;
	if (!current || !window.confirm(`确定归档“${current.name}”吗？归档后会从可用列表移到“已归档”区。`)) return;
	clearTransientMessages();
	const archived = await archiveKnowledgeBaseAction.execute(async () => {
		await props.session.archiveTeacherKnowledgeBase(current.id);
		return true;
	});
	if (!archived) {
		errorMessage.value = archiveKnowledgeBaseAction.error.value ?? "知识库归档失败";
		return;
	}
	// 归档后已无可编辑对象，避免刷新期间残留编辑表单。
	editingKnowledgeBase.value = false;
	notice.value = "知识库已归档。";
	await loadKnowledgeBases();
}

async function loadSegments(knowledgeBaseId = selectedKnowledgeBaseId.value): Promise<void> {
	if (!knowledgeBaseId) return;
	const items = await segmentsResource.execute(async () => (await props.session.listKnowledgeBaseSegments(knowledgeBaseId)).items);
	if (!items) errorMessage.value = segmentsResource.error.value ?? "分段加载失败";
}

async function openDocumentSegments(document: KnowledgeBaseDocumentView): Promise<void> {
	selectedSegmentDocumentId.value = document.id;
	preview.value = null;
	activeTab.value = "segments";
	await loadSegments();
	await previewSegments();
}

function segmentRequest(documentId: string) {
	const currentSettings = settings.value;
	if (!currentSettings) return null;
	return {
		documentId,
		mode: currentSettings.mode,
		maxCharacters: currentSettings.maxCharacters,
		overlapCharacters: currentSettings.overlapCharacters,
		separators:
			currentSettings.mode === "advanced" ? [advancedSeparator.value] : currentSettings.separators,
		cleaningRules: currentSettings.cleaningRules,
	};
}

async function previewSegments(): Promise<void> {
	const current = currentKnowledgeBase.value;
	const request = segmentRequest(selectedSegmentDocumentId.value);
	if (!current || !request || previewing.value) return;
	const result = await previewSegmentsAction.execute(async () => {
		const nextPreview = await props.session.previewKnowledgeBaseSegments(current.id, request);
		// 首次预览可能触发后端按需解析；同步文档状态，避免仍用“待解析”禁用导入复选框。
		documents.value = (await props.session.listKnowledgeBaseDocuments(current.id)).items;
		return nextPreview;
	});
	if (result) preview.value = result;
	else errorMessage.value = previewSegmentsAction.error.value ?? "分段预览失败";
}

async function rebuildSegments(): Promise<void> {
	const current = currentKnowledgeBase.value;
	const request = segmentRequest(selectedSegmentDocumentId.value);
	if (!current || !request) return;
	const resources = await rebuildSegmentsAction.execute(async () => ({
		result: await props.session.rebuildKnowledgeBaseSegments(current.id, request),
		indexStatus: await props.session.getKnowledgeBaseIndexStatus(current.id),
	}));
	if (!resources) {
		errorMessage.value = rebuildSegmentsAction.error.value ?? "分段重建失败";
		return;
	}
	settings.value = resources.result.settings;
	indexStatus.value = resources.indexStatus;
	preview.value = null;
	notice.value = `已重建 ${resources.result.chunkCount} 个分段，索引状态：${resources.result.indexStatus === "ready" ? "可检索" : "失败"}。`;
	await loadSegments(current.id);
}

async function testRetrieval(): Promise<void> {
	const current = currentKnowledgeBase.value;
	if (!current || !retrievalQuery.value.trim()) return;
	const result = await retrievalAction.execute(() => props.session.testKnowledgeBaseRetrieval(current.id, {
			query: retrievalQuery.value.trim(),
			mode: retrievalMode.value,
			topK: Math.min(20, Math.max(1, retrievalTopK.value)),
			minScore: Math.max(0, retrievalMinScore.value),
		}));
	if (result) retrievalResult.value = result;
	else errorMessage.value = retrievalAction.error.value ?? "召回测试失败";
}

function toggleImportDocument(documentId: string): void {
	selectedImportDocumentIds.value = toggleSelection(selectedImportDocumentIds.value, documentId);
}

async function importDocumentsToClass(): Promise<void> {
	const current = currentKnowledgeBase.value;
	if (!current || !canImport.value) return;
	const result = await importDocumentsAction.execute(() => props.session.importKnowledgeBaseDocuments({
			targetClassId: importClassId.value,
			items: [{ sourceKnowledgeBaseId: current.id, documentIds: selectedImportDocumentIds.value }],
			conflictStrategy: importConflictStrategy.value,
		}));
	if (!result) {
		errorMessage.value = importDocumentsAction.error.value ?? "文档导入失败";
		return;
	}
	selectedImportDocumentIds.value = [];
	notice.value = `已将 ${result.importedDocuments.length} 份原始文档导入教学班知识库。备课时可直接选择这些文档。`;
}

function changeTab(tab: WorkbenchTab): void {
	activeTab.value = tab;
	if (tab === "segments" && selectedKnowledgeBaseId.value) void loadSegments();
}

watch(
	[() => props.classes, () => props.activeClassId],
	([classes, activeClassId]) => {
		if (activeClassId && classes.some((item) => item.id === activeClassId)) {
			importClassId.value = activeClassId;
		} else if (!importClassId.value || !classes.some((item) => item.id === importClassId.value)) {
			importClassId.value = classes[0]?.id ?? "";
		}
	},
	{ immediate: true },
);
onMounted(() => {
	void loadKnowledgeBases();
});
onBeforeUnmount(() => {
	knowledgeBasesResource.reset();
	knowledgeBaseResource.reset();
});
</script>

<template>
	<section class="knowledge-base-page" aria-labelledby="knowledge-base-title">
		<header class="page-header knowledge-base-header">
			<div>
				<p class="eyebrow">我的课程 · 课程资料</p>
				<h1 id="knowledge-base-title">知识库</h1>
				<p class="muted">
					知识库是课程内容的长期资产；备课时从教学班知识库选择文档，不再重复上传。
				</p>
			</div>
			<div class="knowledge-base-header-actions">
				<button
					v-if="!activeClassId"
					type="button"
					class="button secondary"
					@click="emit('backToCourses')">
					返回我的课程
				</button>
				<button
					v-if="currentKnowledgeBase?.status !== 'archived'"
					type="button"
					class="button secondary"
					@click="startKnowledgeBaseEdit">
					编辑知识库
				</button>
			</div>
		</header>

		<p v-if="notice" class="success-card" role="status">{{ notice }}</p>
		<p v-if="errorMessage" class="error-card" role="alert">{{ errorMessage }}</p>

		<section v-if="state === 'loading'" class="knowledge-base-state card" aria-live="polite">
			<strong>正在加载知识库</strong>
			<p class="muted">正在读取真实文档、分段和索引状态。</p>
		</section>
		<section v-else-if="state === 'error'" class="knowledge-base-state card" role="alert">
			<strong>知识库加载失败</strong>
			<p class="muted">{{ errorMessage }}</p>
			<button type="button" class="button secondary" @click="() => loadKnowledgeBases()">
				重新加载
			</button>
		</section>

		<section v-else class="knowledge-base-layout">
			<aside class="knowledge-base-list card" aria-label="知识库列表">
				<div class="section-heading">
					<div>
						<p class="eyebrow">我的知识库</p>
						<h2>知识库列表</h2>
					</div>
					<span class="tag">{{ activeKnowledgeBases.length }}</span>
				</div>
				<button
					v-for="item in activeKnowledgeBases"
					:key="item.id"
					type="button"
					class="knowledge-base-list-item"
					:class="{ active: item.id === selectedKnowledgeBaseId }"
					@click="selectKnowledgeBase(item.id)">
					<strong>{{ item.name }}</strong
					><span>{{ item.documentCount }} 份文档</span>
				</button>
				<p v-if="!activeKnowledgeBases.length" class="muted">还没有可用知识库，先创建一个。</p>
				<div
					v-if="archivedKnowledgeBases.length"
					class="archived-knowledge-bases"
					aria-label="已归档知识库">
					<p class="eyebrow">已归档</p>
					<button
						v-for="item in archivedKnowledgeBases"
						:key="item.id"
						type="button"
						class="knowledge-base-list-item archived"
						:class="{ active: item.id === selectedKnowledgeBaseId }"
						@click="selectKnowledgeBase(item.id)">
						<strong>{{ item.name }}</strong
						><span>{{ item.documentCount }} 份文档 · 已归档</span>
					</button>
				</div>
				<form class="create-knowledge-base" @submit.prevent="createKnowledgeBase">
					<input
						v-model="newKnowledgeBaseName"
						type="text"
						placeholder="新建知识库名称"
						aria-label="新建知识库名称"
						maxlength="120" />
					<input
						v-model="newKnowledgeBaseDescription"
						type="text"
						placeholder="描述（可选）"
						aria-label="知识库描述"
						maxlength="200" />
					<button
						type="submit"
						class="button primary"
						:disabled="creating || loading || !newKnowledgeBaseName.trim()">
						新建知识库
					</button>
				</form>
			</aside>

			<div v-if="currentKnowledgeBase" class="knowledge-base-workspace">
				<section class="knowledge-base-summary card">
					<div>
						<p class="eyebrow">当前知识库</p>
						<h2>{{ currentKnowledgeBase.name }}</h2>
						<p class="muted">
							{{ currentKnowledgeBase.description || "暂无描述" }}
						</p>
						<p v-if="currentKnowledgeBase.status === 'archived'" class="muted">
							归档只读：不能再编辑、上传或重建内容。
						</p>
					</div>
					<div class="summary-actions">
						<span
							class="tag"
							:class="{
								good: currentKnowledgeBase.status !== 'archived',
								warning: currentKnowledgeBase.status === 'archived',
							}"
							>{{
								currentKnowledgeBase.status === "archived"
									? "已归档"
									: `${currentKnowledgeBase.documentCount} 份文档`
							}}</span
						><button
							v-if="currentKnowledgeBase.status !== 'archived'"
							type="button"
							class="button danger"
							:disabled="saving"
							@click="archiveKnowledgeBase">
							归档
						</button>
					</div>
				</section>

				<form
					v-if="editingKnowledgeBase"
					class="editor-card knowledge-base-editor"
					@submit.prevent="saveKnowledgeBase">
					<h3>编辑知识库</h3>
					<label>名称<input v-model="editingName" required maxlength="120" /></label
					><label
						>描述<textarea v-model="editingDescription" rows="2" maxlength="200" />
					</label>
					<div class="form-actions">
						<button type="submit" class="button primary" :disabled="saving">
							保存</button
						><button
							type="button"
							class="button secondary"
							@click="editingKnowledgeBase = false">
							取消
						</button>
					</div>
				</form>

				<section class="knowledge-base-index card">
					<div>
						<p class="eyebrow">索引状态</p>
						<h2>{{ indexStatus?.chunkCount ?? 0 }} 个分段</h2>
						<p class="muted">
							{{ indexStatus?.readyChunkCount ?? 0 }} 个分段可检索 ·
							{{ settings?.mode === "advanced" ? "高级分段" : "简单分段" }}
						</p>
					</div>
					<span
						class="tag"
						:class="{
							good:
								indexStatus?.embeddingStatus === 'ready' ||
								(indexStatus?.readyChunkCount ===
									indexStatus?.chunkCount &&
									Boolean(indexStatus?.chunkCount)),
						}"
						>{{
							indexStatus?.embeddingStatus === "ready"
								? "语义向量已就绪"
								: "关键词检索可用"
						}}</span
					>
				</section>

				<nav class="knowledge-base-tabs" aria-label="知识库工作台功能">
					<button
						v-for="tab in [
							{ id: 'documents', label: '文档' },
							{ id: 'segments', label: '分段' },
							{ id: 'retrieval', label: '召回测试' },
						]"
						:key="tab.id"
						type="button"
						:class="{ active: activeTab === tab.id }"
						@click="changeTab(tab.id as WorkbenchTab)">
						{{ tab.label }}
					</button>
				</nav>

				<KnowledgeBaseDocumentManagementPanel
					v-if="activeTab === 'documents' && currentKnowledgeBase"
					class="workbench-panel card"
					:knowledge-base-id="currentKnowledgeBase.id"
					:archived="currentKnowledgeBase.status === 'archived'"
					:documents="documents"
					:session="props.session"
					@changed="refreshCurrentKnowledgeBase"
					@notice="handleDocumentNotice"
					@error="handleDocumentError"
					@open-segments="openDocumentSegments" />

				<section v-else-if="activeTab === 'segments'" class="workbench-panel card">
					<div class="section-heading">
						<div>
							<h2>分段与索引</h2>
							<p class="muted">
								当前文档确定后，在这里调整规则、预览并重建它的分段。
							</p>
						</div>
						<button
							type="button"
							class="button secondary"
							:disabled="loading || !selectedSegmentDocument"
							@click="loadSegments()">
							刷新分段
						</button>
					</div>
					<p v-if="selectedSegmentDocument" class="selected-document-note">
						当前文档：{{ selectedSegmentDocument.originalFilename }} · v{{
							selectedSegmentDocument.version
						}}
					</p>
					<p v-else class="empty-hint">请先返回文档管理并点击一份文档。</p>
					<div
						v-if="
							currentKnowledgeBase?.status !== 'archived' &&
							selectedSegmentDocument &&
							settings
						"
						class="segment-rule-card">
						<label
							>分段方式<select v-model="settings.mode">
								<option value="simple">
									简单分段 · 按文档结构自动切分
								</option>
								<option value="advanced">
									高级分段 · 按一个分隔符切分
								</option>
							</select></label
						>
						<div
							v-if="settings.mode === 'advanced'"
							class="advanced-separator-picker">
							<label
								>选择分隔符<select v-model="advancedSeparator">
									<option
										v-for="option in ADVANCED_SEPARATOR_OPTIONS"
										:key="option.value"
										:value="option.value">
										{{ option.label }}
									</option>
								</select></label
							>
							<p class="muted">
								只能选择一个分隔符。点击“预览分段”后，下面的分段会按当前选择重新生成。
							</p>
						</div>
					</div>
					<div class="toolbar">
						<button
							type="button"
							class="button secondary"
							:disabled="previewing || !selectedSegmentDocument"
							@click="previewSegments">
							{{ previewing ? "预览中…" : "预览分段" }}</button
						><button
							v-if="currentKnowledgeBase?.status !== 'archived'"
							type="button"
							class="button primary"
							:disabled="rebuilding || !selectedSegmentDocument"
							@click="rebuildSegments">
							{{ rebuilding ? "重建中…" : "应用规则并重建" }}
						</button>
					</div>
					<div v-if="preview" class="preview-box">
						<strong
							>预览：{{ preview.segments.length }} 个分段{{
								preview.requiresRebuild ? " · 当前索引需要重建" : ""
							}}</strong
						>
						<article
							v-for="segment in preview.segments"
							:key="segment.id"
							class="segment-row">
							<span>#{{ segment.ordinal }}</span>
							<p>{{ segment.content }}</p>
						</article>
					</div>
					<div v-if="visibleSegments.length" class="segment-list">
						<h3>当前文档索引中的分段（{{ visibleSegments.length }}）</h3>
						<article
							v-for="segment in visibleSegments"
							:key="segment.id"
							class="segment-row">
							<span
								>#{{ segment.ordinal }} ·
								{{ segment.documentFilename }}</span
							>
							<p>{{ segment.content }}</p>
							<small class="muted"
								>{{ segment.indexStatus }} ·
								{{ segment.titlePath.join(" / ") }}</small
							>
						</article>
					</div>
					<p v-else class="empty-hint">
						打开文档后即可解析原文并预览分段；确认规则后点击“应用规则并重建”。
					</p>
				</section>

				<section v-else-if="activeTab === 'retrieval'" class="workbench-panel card">
					<div class="section-heading">
						<div>
							<h2>召回测试</h2>
							<p class="muted">
								输入教师真实问题，查看 Top{{
									retrievalTopK
								}}
								召回结果、分数和来源。
							</p>
						</div>
					</div>
					<form class="retrieval-form" @submit.prevent="testRetrieval">
						<label class="query-field"
							>测试问题<input
								v-model="retrievalQuery"
								type="search"
								placeholder="例如：具身智能和传统机器人的区别是什么？"
								required /></label
						><label
							>检索模式<select v-model="retrievalMode">
								<option value="hybrid">混合检索</option>
								<option value="keyword">关键词检索</option>
								<option value="vector">向量检索</option>
							</select></label
						><label
							>Top K<input
								v-model.number="retrievalTopK"
								type="number"
								min="1"
								max="20" /></label
						><label
							>最低分<input
								v-model.number="retrievalMinScore"
								type="number"
								min="0"
								step="0.01" /></label
						><button
							type="submit"
							class="button primary"
							:disabled="testingRetrieval || !retrievalQuery.trim()">
							{{ testingRetrieval ? "测试中…" : "开始召回测试" }}
						</button>
					</form>
					<div v-if="retrievalResult" class="retrieval-results">
						<div class="retrieval-result-summary">
							<strong>Top {{ retrievalResult.results.length }} 召回</strong
							><span
								>{{ retrievalResult.retrievalMode }} · 查询：{{
									retrievalResult.query
								}}</span
							><span
								v-if="retrievalResult.fallbackReason"
								class="tag warning"
								>{{ retrievalResult.fallbackReason }}</span
							>
						</div>
						<article
							v-for="(result, index) in retrievalResult.results"
							:key="result.chunkId"
							class="retrieval-result">
							<div class="retrieval-rank">{{ index + 1 }}</div>
							<div>
								<div class="retrieval-result-head">
									<strong>{{ result.documentFilename }}</strong
									><span class="score">{{
										result.score.toFixed(3)
									}}</span>
								</div>
								<p class="muted">
									{{
										result.titlePath.join(" / ") ||
										"未命名章节"
									}}
									· v{{ result.documentVersion }}
								</p>
								<p>{{ result.content }}</p>
							</div>
						</article>
						<p v-if="!retrievalResult.results.length" class="empty-hint">
							没有达到最低分的召回结果。
						</p>
					</div>
				</section>
			</div>
			<section v-else class="knowledge-base-empty card">
				<strong>还没有可用知识库</strong>
				<p class="muted">创建知识库后上传教材、配置分段，再将选中文档导入教学班。</p>
			</section>

			<section
				v-if="
					currentKnowledgeBase &&
					currentKnowledgeBase.status !== 'archived' &&
					activeTab === 'documents'
				"
				class="workbench-panel card import-panel">
				<div class="section-heading">
					<div>
						<h2>用于备课</h2>
						<p class="muted">
							把当前知识库中选中的原始文件复制到教学班知识库；不会把不同知识库混成一个教师库。
						</p>
					</div>
				</div>
				<div class="import-form">
					<label
						>教学班<select v-model="importClassId" :disabled="!classes.length">
							<option value="" disabled>
								{{
									classes.length
										? "选择教学班"
										: "请先在我的课程创建教学班"
								}}
							</option>
							<option
								v-for="classItem in classes"
								:key="classItem.id"
								:value="classItem.id">
								{{ classItem.name }}
							</option>
						</select></label
					><label
						>冲突处理<select v-model="importConflictStrategy">
							<option value="skip">同名时跳过</option>
							<option value="replace">同名时替换</option>
							<option value="copy">保留副本</option>
						</select></label
					>
				</div>
				<KnowledgeBaseDocumentPicker
					:documents="documents"
					:selected-ids="selectedImportDocumentIds"
					empty-text="当前知识库还没有文档，请先上传 Markdown 文档。"
					@toggle="toggleImportDocument" />
				<button
					type="button"
					class="button primary"
					:disabled="importing || !canImport"
					@click="importDocumentsToClass">
					{{
						importing
							? "导入中…"
							: `导入选中文档（${selectedImportDocumentIds.length}）`
					}}
				</button>
			</section>
		</section>
	</section>
</template>

<style scoped>
.knowledge-base-page {
	display: grid;
	gap: 20px;
	max-width: 1220px;
	color: var(--color-ink-strong);
}
.knowledge-base-header {
	display: flex;
	align-items: flex-end;
	justify-content: space-between;
	gap: 18px;
}
.knowledge-base-header h1 {
	margin: 0 0 8px;
}
.knowledge-base-header p {
	margin: 0;
}
.knowledge-base-layout {
	display: grid;
	grid-template-columns: 260px minmax(0, 1fr);
	gap: 18px;
	align-items: start;
}
.knowledge-base-list,
.knowledge-base-workspace,
.workbench-panel {
	display: grid;
	gap: 16px;
}
.knowledge-base-list {
	position: sticky;
	top: 18px;
}
.section-heading,
.summary-actions,
.toolbar,
.form-actions,
.retrieval-result-head,
.retrieval-result-summary {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	flex-wrap: wrap;
}
.section-heading h2,
.knowledge-base-summary h2 {
	margin: 0 0 5px;
}
.knowledge-base-list-item {
	display: grid;
	gap: 4px;
	width: 100%;
	padding: 12px;
	border: 1px solid var(--color-border);
	border-radius: 10px;
	background: var(--color-surface);
	color: var(--color-ink-strong);
	text-align: left;
	cursor: pointer;
}
.knowledge-base-list-item span,
.retrieval-result p {
	font-size: 12px;
}
.knowledge-base-list-item.active {
	border-color: var(--color-brand);
	background: var(--color-brand-soft);
	box-shadow: inset 3px 0 var(--color-brand);
}
.create-knowledge-base {
	display: grid;
	gap: 8px;
	padding-top: 8px;
	border-top: 1px solid var(--color-border-subtle);
}
.create-knowledge-base input,
.knowledge-base-editor input,
.knowledge-base-editor textarea,
.retrieval-form input,
.retrieval-form select,
.import-form select {
	width: 100%;
	box-sizing: border-box;
	padding: 9px 10px;
	font: inherit;
}
.knowledge-base-summary,
.knowledge-base-index {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16px;
}
.knowledge-base-tabs {
	display: flex;
	gap: 4px;
	padding: 4px;
	border: 1px solid var(--color-border);
	border-radius: 12px;
	background: var(--color-surface-muted);
}
.knowledge-base-tabs button {
	flex: 1;
	padding: 10px;
	border: 0;
	border-radius: 9px;
	background: transparent;
	color: var(--color-ink-muted);
	font-weight: 800;
	cursor: pointer;
}
.knowledge-base-tabs button.active {
	background: var(--color-surface);
	color: var(--color-brand);
	box-shadow: var(--shadow-xs);
}
.workbench-panel {
	min-width: 0;
}
.segment-list,
.retrieval-results {
	display: grid;
	gap: 10px;
}
.button.danger {
	color: var(--color-danger);
}
.knowledge-base-editor {
	grid-column: 1 / -1;
	display: grid;
	gap: 12px;
}
.editor-card {
	padding: 14px;
	border-width: 1px;
	border-style: solid;
}
.editor-card label,
.retrieval-form label,
.import-form label {
	display: grid;
	gap: 6px;
	color: var(--color-ink);
	font-weight: 800;
}
.preview-box,
.segment-list {
	display: grid;
	gap: 10px;
	padding-top: 12px;
	border-top: 1px solid var(--color-border-subtle);
}
.segment-row {
	display: grid;
	gap: 4px;
	padding: 12px;
	border: 1px solid var(--color-border-subtle);
	border-radius: 10px;
	background: var(--color-surface);
}
.segment-row span,
.segment-row small {
	font-size: 12px;
}
.segment-row p {
	margin: 0;
	white-space: pre-wrap;
	line-height: 1.65;
}
.retrieval-form {
	display: grid;
	grid-template-columns: minmax(220px, 2fr) 1fr 0.7fr 0.8fr auto;
	gap: 10px;
	align-items: end;
}
.query-field {
	grid-column: auto;
}
.retrieval-results {
	padding-top: 10px;
}
.retrieval-result {
	display: grid;
	grid-template-columns: 36px minmax(0, 1fr);
	gap: 12px;
	padding: 14px;
	border: 1px solid var(--color-border);
	border-radius: 12px;
}
.retrieval-rank {
	display: grid;
	place-items: center;
	width: 30px;
	height: 30px;
	border-radius: 50%;
	background: var(--color-surface-muted);
	color: var(--color-ink-muted);
	font-weight: 900;
}
.retrieval-result-head {
	justify-content: flex-start;
}
.score {
	padding: 3px 7px;
	border-radius: 999px;
	background: var(--color-warning-soft);
	color: var(--color-warning);
	font-weight: 800;
}
.retrieval-result p {
	margin: 6px 0 0;
	line-height: 1.6;
}
.import-panel {
	margin-top: 0;
}
.import-form {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 10px;
}
.empty-hint,
.knowledge-base-empty {
	padding: 20px;
	border-width: 1px;
	border-style: dashed;
	border-radius: 12px;
	color: var(--color-ink-muted);
}
.success-card {
	padding: 12px;
	border-radius: 10px;
	background: var(--color-success-soft);
	color: var(--color-success);
}
.knowledge-base-state {
	padding: 24px;
}
.knowledge-base-list.card,
.knowledge-base-summary.card,
.knowledge-base-index.card,
.workbench-panel.card {
	padding: 18px;
}
.knowledge-base-list-item.archived {
	background: var(--color-surface-muted);
	color: var(--color-ink-muted);
}
.knowledge-base-list-item.archived.active {
	border-color: var(--color-warning);
	background: var(--color-warning-soft);
	box-shadow: inset 3px 0 var(--color-warning);
}
.archived-knowledge-bases {
	display: grid;
	gap: 8px;
	padding-top: 12px;
	border-top: 1px solid var(--color-border-subtle);
}
.selected-document-note {
	margin: 0;
	padding: 10px 12px;
	border-left: 3px solid var(--color-brand);
	border-radius: 6px;
	background: var(--color-surface-muted);
	color: var(--color-ink);
	font-weight: 700;
}
@media (max-width: 900px) {
	.knowledge-base-layout {
		grid-template-columns: 1fr;
	}
	.knowledge-base-list {
		position: static;
	}
	.retrieval-form {
		grid-template-columns: 1fr 1fr;
	}
	.query-field {
		grid-column: 1/-1;
	}
}
.knowledge-base-header-actions {
	display: flex;
	align-items: center;
	gap: 10px;
	flex-wrap: wrap;
}
@media (max-width: 620px) {
	.knowledge-base-header,
	.knowledge-base-summary,
	.knowledge-base-index {
		align-items: flex-start;
		flex-direction: column;
	}
	.knowledge-base-tabs {
		overflow: auto;
	}
	.knowledge-base-tabs button {
		min-width: 90px;
	}
	.retrieval-form,
	.import-form {
		grid-template-columns: 1fr;
	}
}
.knowledge-base-page .import-panel {
	grid-column: 2;
}
@media (max-width: 900px) {
	.knowledge-base-page .import-panel {
		grid-column: 1;
	}
}
.segment-rule-card {
	display: grid;
	gap: 12px;
	padding: 14px;
	border: 1px solid var(--color-border);
	border-radius: 12px;
	background: var(--color-surface);
}
.segment-rule-card > label,
.advanced-separator-picker label {
	display: grid;
	gap: 6px;
	color: var(--color-ink);
	font-weight: 800;
}
.advanced-separator-picker {
	display: grid;
	gap: 7px;
	padding-top: 12px;
	border-top: 1px solid var(--color-border-subtle);
}
.advanced-separator-picker p {
	margin: 0;
	font-size: 13px;
}
</style>
