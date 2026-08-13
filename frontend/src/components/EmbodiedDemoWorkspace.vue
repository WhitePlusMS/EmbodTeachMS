<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import type { GLTF } from "three/addons/loaders/GLTFLoader.js";

type ViewerRole = "teacher" | "learner";
type AnimationName = "Idle" | "Walking" | "Wave" | "Yes" | "ThumbsUp";
type TargetKind = "shelf" | "crate";
type Point3 = [number, number, number];

type DemoStep = {
  id: string;
  label: string;
  title: string;
  description: string;
  sceneCue: string;
  learningPoint: string;
  observation: string[];
  action: AnimationName;
  robotPosition: Point3;
};

type DemoTask = {
  id: string;
  title: string;
  summary: string;
  targetName: string;
  targetKind: TargetKind;
  targetPosition: Point3;
  steps: DemoStep[];
};

const props = defineProps<{ viewerRole: ViewerRole }>();

// 任务内容是产品内置的教学演示素材，不来自后端，也不允许教师或学生在页面内修改。
const DEMO_TASKS: DemoTask[] = [
  {
    id: "warehouse-patrol",
    title: "仓库巡检与目标识别",
    summary: "观察场景、理解目标，再规划一条巡检路径。",
    targetName: "目标货架 A-01",
    targetKind: "shelf",
    targetPosition: [3.3, 0.12, -1.5],
    steps: [
      {
        id: "instruction",
        label: "任务指令",
        title: "先明确任务目标",
        description: "机器人需要在仓库中巡检，并找到标记为 A-01 的目标货架。",
        sceneCue: "机器人停在入口，画面聚焦右侧的 A-01 目标货架。",
        learningPoint: "具身智能任务从语言目标开始，但必须落到具体环境和动作。",
        observation: ["目标：找到 A-01", "场景：仓库通道", "输出：到达并指示目标"],
        action: "Idle",
        robotPosition: [-4.2, 0, 2.8],
      },
      {
        id: "observation",
        label: "场景观察",
        title: "从环境中获取可见线索",
        description: "机器人观察通道、货架和目标标记；高亮区域表示当前教学关注点。",
        sceneCue: "机器人保持待机，观察右侧货架与 A-01 标记，不提前执行移动。",
        learningPoint: "观察不是抽象输入，必须和环境中的位置、物体、关系对应起来。",
        observation: ["已发现两排货架", "通道保持可通行", "A-01 位于右侧货架"],
        action: "Idle",
        robotPosition: [-4.2, 0, 2.8],
      },
      {
        id: "understanding",
        label: "任务理解",
        title: "把目标转成可执行意图",
        description: "机器人确认 A-01 是需要到达和指示的目标，而不是任意一个货架。",
        sceneCue: "机器人用确认手势表示已经锁定 A-01 这一具体目标。",
        learningPoint: "任务理解连接语言目标与环境对象，是 VLA 教学中的关键中间层。",
        observation: ["目标对象：A-01", "目标关系：位于右侧货架", "当前动作：确认目标"],
        action: "ThumbsUp",
        robotPosition: [-4.2, 0, 2.8],
      },
      {
        id: "planning",
        label: "动作规划",
        title: "选择一条可行路径",
        description: "机器人规划从起点穿过中央通道，到达 A-01 前方的路径。",
        sceneCue: "机器人保持在起点，地面路线高亮表示即将执行的规划。",
        learningPoint: "决策不仅是说出下一步，还要考虑空间位置和行动顺序。",
        observation: ["起点：左侧入口", "路径：中央通道", "终点：A-01 前方"],
        action: "Idle",
        robotPosition: [-4.2, 0, 2.8],
      },
      {
        id: "execution",
        label: "执行动作",
        title: "沿规划路径靠近目标",
        description: "机器人播放行走动作并移动到目标货架前，展示决策如何落实为动作。",
        sceneCue: "机器人播放行走动作，沿高亮路线靠近 A-01 货架。",
        learningPoint: "具身智能的动作必须发生在环境中，才能产生新的反馈。",
        observation: ["动作：行走", "方向：靠近 A-01", "状态：沿路线靠近中"],
        action: "Walking",
        robotPosition: [3.3, 0, -0.1],
      },
      {
        id: "feedback",
        label: "环境反馈",
        title: "通过结果理解闭环",
        description: "目标区域被高亮，机器人挥手确认已找到目标；这里展示反馈，不进行完成判定。",
        sceneCue: "机器人到达目标前方并挥手，A-01 标记保持高亮。",
        learningPoint: "环境反馈会影响下一次决策，但本页面只用于理解，不负责评分。",
        observation: ["反馈：发现目标", "视觉提示：A-01 高亮", "本演示：不判定对错"],
        action: "Wave",
        robotPosition: [3.3, 0, -0.1],
      },
    ],
  },
  {
    id: "semantic-search",
    title: "语义目标搜索与指示",
    summary: "理解自然语言目标，并用动作把目标位置表达出来。",
    targetName: "蓝色周转箱",
    targetKind: "crate",
    targetPosition: [-2.8, 0.12, -1.5],
    steps: [
      {
        id: "instruction",
        label: "任务指令",
        title: "理解自然语言描述",
        description: "任务要求机器人找到仓库中的蓝色周转箱，并在发现后进行指示。",
        sceneCue: "机器人停在入口，画面展示左侧货架上的蓝色周转箱。",
        learningPoint: "语言描述需要被关联到可观察的物体特征。",
        observation: ["颜色：蓝色", "类别：周转箱", "动作：寻找并指示"],
        action: "Idle",
        robotPosition: [3.5, 0, 2.7],
      },
      {
        id: "observation",
        label: "场景观察",
        title: "对比场景中的候选物体",
        description: "机器人观察多个箱体，蓝色目标被高亮用于说明语义线索如何落到物体。",
        sceneCue: "机器人保持待机，对比场景中的箱体颜色和位置。",
        learningPoint: "视觉观察不仅是看见，还要提取与任务相关的特征。",
        observation: ["候选物体：多个箱体", "关键特征：蓝色", "目标位置：左侧货架"],
        action: "Idle",
        robotPosition: [3.5, 0, 2.7],
      },
      {
        id: "understanding",
        label: "任务理解",
        title: "确认目标与语言一致",
        description: "机器人确认左侧高亮物体符合“蓝色周转箱”的描述。",
        sceneCue: "机器人用确认手势表示语言目标已经对应到蓝色周转箱。",
        learningPoint: "多模态理解要把语言、视觉和空间位置放进同一个任务上下文。",
        observation: ["语言特征：蓝色", "视觉特征：箱体", "空间关系：左侧货架"],
        action: "ThumbsUp",
        robotPosition: [3.5, 0, 2.7],
      },
      {
        id: "planning",
        label: "动作规划",
        title: "规划靠近并指示的动作",
        description: "机器人先沿中央通道靠近目标，再用手势表达目标位置。",
        sceneCue: "机器人保持在起点，地面路线高亮表示先靠近、后指示的动作顺序。",
        learningPoint: "规划可以由多个基础动作组成，教学重点是理解动作顺序。",
        observation: ["第一步：靠近目标", "第二步：面向目标", "第三步：挥手指示"],
        action: "Idle",
        robotPosition: [3.5, 0, 2.7],
      },
      {
        id: "execution",
        label: "执行动作",
        title: "移动到目标观察位置",
        description: "机器人播放行走动作，移动到蓝色周转箱前方的观察位置。",
        sceneCue: "机器人播放行走动作，沿高亮路线移动到蓝色周转箱前方。",
        learningPoint: "动作执行会改变机器人和环境的相对位置。",
        observation: ["动作：行走", "目标：蓝色周转箱", "状态：沿路线移动中"],
        action: "Walking",
        robotPosition: [-2.1, 0, -0.1],
      },
      {
        id: "feedback",
        label: "环境反馈",
        title: "用手势表达发现结果",
        description: "蓝色周转箱保持高亮，机器人挥手表达发现结果；教师可暂停讲解反馈含义。",
        sceneCue: "机器人到达目标前方并挥手，蓝色周转箱保持高亮。",
        learningPoint: "反馈让学习者看到“理解—行动—结果”之间的关系。",
        observation: ["反馈：目标已定位", "动作：挥手指示", "本演示：不判定完成"],
        action: "Wave",
        robotPosition: [-2.1, 0, -0.1],
      },
    ],
  },
];

const DEFAULT_TASK = DEMO_TASKS[0]!;
const sceneHost = ref<HTMLDivElement | null>(null);
const selectedTaskId = ref(DEFAULT_TASK.id);
const selectedStepIndex = ref(0);
const modelState = ref<"loading" | "ready" | "error">("loading");
const modelError = ref("");

const currentTask = computed(() => DEMO_TASKS.find((task) => task.id === selectedTaskId.value) ?? DEFAULT_TASK);
const currentStep = computed(() => currentTask.value.steps[selectedStepIndex.value] ?? currentTask.value.steps[0]!);
const currentStepNumber = computed(() => selectedStepIndex.value + 1);
const progressPercent = computed(() => (currentStepNumber.value / currentTask.value.steps.length) * 100);
const motionStatus = computed(() => {
  if (currentStep.value.action === "Walking") return "转向并行走";
  if (currentStep.value.id === "planning") return "朝向规划路线";
  if (currentStep.value.action === "Wave" || currentStep.value.action === "ThumbsUp") return "面向目标做手势";
  return "保持待机观察";
});

let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let renderer: THREE.WebGLRenderer | null = null;
let controls: OrbitControls | null = null;
let mixer: THREE.AnimationMixer | null = null;
let robotRoot: THREE.Group | null = null;
let animationFrameId = 0;
let resizeObserver: ResizeObserver | null = null;
let targetVisual: THREE.Group | null = null;
let shelfTargetVisual: THREE.Group | null = null;
let crateTargetVisual: THREE.Group | null = null;
let targetMarker: THREE.Mesh | null = null;
let targetRing: THREE.Mesh | null = null;
let targetMaterial: THREE.MeshStandardMaterial | null = null;
let routeLine: THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial> | null = null;
let teachingVisualGroup: THREE.Group | null = null;
let instructionVisual: THREE.Group | null = null;
let observationVisual: THREE.Group | null = null;
let understandingVisual: THREE.Group | null = null;
let instructionShelfLabel: THREE.Sprite | null = null;
let instructionCrateLabel: THREE.Sprite | null = null;
let observationPulse: THREE.Mesh | null = null;
let understandingPulse: THREE.Mesh | null = null;
let understandingHalo: THREE.Mesh | null = null;
let observationRays: THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial>[] = [];
let understandingLine: THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial> | null = null;
let activeAction: THREE.AnimationAction | null = null;
const actions = new Map<AnimationName, THREE.AnimationAction>();
const clock = new THREE.Clock();
const robotTarget = new THREE.Vector3();
let robotHeading = 0;
let robotTargetHeading = 0;

function makeMaterial(color: number, roughness = 0.78): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness: 0.08 });
}

function addBox(parent: THREE.Object3D, size: Point3, position: Point3, color: number): THREE.Mesh {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), makeMaterial(color));
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}

function createLabelSprite(text: string, backgroundColor: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("无法创建目标物标签画布");
  context.fillStyle = backgroundColor;
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#ffffff";
  context.font = "bold 54px Microsoft YaHei, sans-serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, canvas.width / 2, canvas.height / 2 + 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(1.45, 0.36, 1);
  return sprite;
}

function addWarehouseShelf(parent: THREE.Object3D, x: number, z: number, color: number): void {
  const shelf = new THREE.Group();
  shelf.position.set(x, 0, z);
  addBox(shelf, [0.18, 2.8, 0.18], [-1.45, 1.4, 0], color);
  addBox(shelf, [0.18, 2.8, 0.18], [1.45, 1.4, 0], color);
  addBox(shelf, [3.1, 0.16, 0.7], [0, 2.7, 0], color);
  addBox(shelf, [3.1, 0.16, 0.7], [0, 1.45, 0], color);
  addBox(shelf, [3.1, 0.16, 0.7], [0, 0.2, 0], color);
  addBox(shelf, [0.8, 0.52, 0.5], [-0.8, 1.75, -0.04], 0xd2a35d);
  addBox(shelf, [0.65, 0.52, 0.48], [0.55, 2.98, -0.04], 0x8fbd9d);
  parent.add(shelf);
}

function createTargetVisuals(): void {
  if (!scene) return;
  targetVisual = new THREE.Group();
  scene.add(targetVisual);

  targetMaterial = new THREE.MeshStandardMaterial({
    color: 0xe8b765,
    emissive: 0x9e591a,
    emissiveIntensity: 1,
    roughness: 0.4,
  });
  targetMarker = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.08, 32), targetMaterial);
  targetMarker.position.y = 0.12;
  targetMarker.castShadow = true;
  targetVisual.add(targetMarker);

  targetRing = new THREE.Mesh(
    new THREE.TorusGeometry(0.7, 0.035, 10, 40),
    new THREE.MeshBasicMaterial({ color: 0xffd483 }),
  );
  targetRing.rotation.x = -Math.PI / 2;
  targetRing.position.y = 0.08;
  targetVisual.add(targetRing);

  shelfTargetVisual = new THREE.Group();
  addBox(shelfTargetVisual, [0.08, 1.1, 0.08], [0, 0.58, 0], 0xd59b4f);
  addBox(shelfTargetVisual, [1.25, 0.5, 0.08], [0, 1.18, 0], 0xe8b765);
  const shelfLabel = createLabelSprite("A-01", "#8a5218");
  shelfLabel.position.set(0, 1.18, 0.06);
  shelfTargetVisual.add(shelfLabel);
  targetVisual.add(shelfTargetVisual);

  crateTargetVisual = new THREE.Group();
  addBox(crateTargetVisual, [0.95, 0.65, 0.72], [0, 0.38, 0], 0x2e82c3);
  addBox(crateTargetVisual, [1.02, 0.08, 0.08], [0, 0.38, 0.37], 0x9ed0f0);
  const crateLabel = createLabelSprite("蓝色周转箱", "#1e5b86");
  crateLabel.position.set(0, 0.92, 0);
  crateTargetVisual.add(crateLabel);
  targetVisual.add(crateTargetVisual);
}

function createTeachingLine(color: number, opacity: number): THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial> {
  return new THREE.Line(
    new THREE.BufferGeometry(),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthTest: false }),
  );
}

function setLinePoints(
  line: THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial>,
  points: THREE.Vector3[],
): void {
  line.geometry.dispose();
  line.geometry = new THREE.BufferGeometry().setFromPoints(points);
}

function createTeachingVisuals(): void {
  if (!scene) return;

  teachingVisualGroup = new THREE.Group();
  scene.add(teachingVisualGroup);

  // 阶段1：把“任务是什么”放入三维空间，用场景内的指令牌指向当前目标。
  instructionVisual = new THREE.Group();
  const instructionBoard = addBox(instructionVisual, [2.9, 0.92, 0.08], [0, 2.72, 0], 0x285746);
  instructionBoard.castShadow = false;
  instructionBoard.receiveShadow = false;
  const instructionTitle = createLabelSprite("任务指令", "#0b3d31");
  instructionTitle.scale.set(1.2, 0.3, 1);
  instructionTitle.position.set(-0.78, 2.92, 0.08);
  instructionVisual.add(instructionTitle);
  instructionShelfLabel = createLabelSprite("找到货架 A-01", "#8a5218");
  instructionShelfLabel.scale.set(1.55, 0.39, 1);
  instructionShelfLabel.position.set(0.55, 2.72, 0.08);
  instructionVisual.add(instructionShelfLabel);
  instructionCrateLabel = createLabelSprite("寻找蓝色周转箱", "#1e5b86");
  instructionCrateLabel.scale.set(1.55, 0.39, 1);
  instructionCrateLabel.position.set(0.55, 2.72, 0.08);
  instructionVisual.add(instructionCrateLabel);
  teachingVisualGroup.add(instructionVisual);

  // 阶段2：从机器人“传感器位置”向候选物发出扫描射线，表现观察而不是静态文字。
  observationVisual = new THREE.Group();
  const sensorPulseMaterial = new THREE.MeshBasicMaterial({
    color: 0x74d6ad,
    transparent: true,
    opacity: 0.82,
    depthTest: false,
  });
  observationPulse = new THREE.Mesh(new THREE.RingGeometry(0.28, 0.36, 32), sensorPulseMaterial);
  observationPulse.rotation.x = -Math.PI / 2;
  observationPulse.position.y = 0.06;
  observationVisual.add(observationPulse);
  const sensorPoint = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 12), sensorPulseMaterial.clone());
  sensorPoint.position.set(0, 1.28, 0);
  observationVisual.add(sensorPoint);
  const observationLabel = createLabelSprite("观察候选目标", "#147052");
  observationLabel.scale.set(1.45, 0.36, 1);
  observationLabel.position.set(0, 1.72, 0);
  observationVisual.add(observationLabel);
  observationRays = [
    createTeachingLine(0x74d6ad, 0.9),
    createTeachingLine(0x8fc7b2, 0.5),
    createTeachingLine(0x6d9fc3, 0.42),
  ];
  observationRays.forEach((ray) => observationVisual?.add(ray));
  teachingVisualGroup.add(observationVisual);

  // 阶段3：将机器人与已识别目标连起来，并在目标上方显示“匹配”结果。
  understandingVisual = new THREE.Group();
  understandingLine = createTeachingLine(0xffd483, 0.95);
  understandingVisual.add(understandingLine);
  understandingHalo = new THREE.Mesh(
    new THREE.TorusGeometry(0.5, 0.055, 10, 40),
    new THREE.MeshBasicMaterial({ color: 0xffd483, transparent: true, opacity: 0.95, depthTest: false }),
  );
  understandingHalo.rotation.x = -Math.PI / 2;
  understandingVisual.add(understandingHalo);
  understandingPulse = new THREE.Mesh(
    new THREE.SphereGeometry(0.14, 16, 12),
    new THREE.MeshBasicMaterial({ color: 0xfff0b1, transparent: true, opacity: 0.95, depthTest: false }),
  );
  understandingVisual.add(understandingPulse);
  const understandingLabel = createLabelSprite("目标已匹配", "#8a5218");
  understandingLabel.scale.set(1.35, 0.34, 1);
  understandingVisual.add(understandingLabel);
  teachingVisualGroup.add(understandingVisual);

  updateTeachingVisuals();
}

function observationCandidates(): Point3[] {
  const target = currentTask.value.targetPosition;
  const distractor: Point3 = currentTask.value.targetKind === "shelf"
    ? [-2.8, 0.12, -1.5]
    : [3.3, 0.12, -1.5];
  return [target, distractor, [0, 0.12, 0.6]];
}

function updateTeachingVisuals(): void {
  if (!instructionVisual || !observationVisual || !understandingVisual) return;

  const stepId = currentStep.value.id;
  instructionVisual.visible = stepId === "instruction";
  observationVisual.visible = stepId === "observation";
  understandingVisual.visible = stepId === "understanding";
  if (instructionShelfLabel) instructionShelfLabel.visible = currentTask.value.targetKind === "shelf";
  if (instructionCrateLabel) instructionCrateLabel.visible = currentTask.value.targetKind === "crate";

  const [robotX, , robotZ] = currentStep.value.robotPosition;
  const [targetX, , targetZ] = currentTask.value.targetPosition;
  observationVisual.position.set(robotX, 0, robotZ);
  const sensorPoint = new THREE.Vector3(0, 1.28, 0);
  observationCandidates().forEach((candidate, index) => {
    const ray = observationRays[index];
    if (!ray) return;
    setLinePoints(ray, [
      sensorPoint.clone(),
      new THREE.Vector3(candidate[0] - robotX, 1.05, candidate[2] - robotZ),
    ]);
  });

  if (understandingLine && understandingHalo && understandingPulse) {
    const robotPoint = new THREE.Vector3(robotX, 1.28, robotZ);
    const targetPoint = new THREE.Vector3(targetX, 1.18, targetZ);
    setLinePoints(understandingLine, [robotPoint, targetPoint]);
    understandingHalo.position.set(targetX, 1.3, targetZ);
    understandingPulse.position.lerpVectors(robotPoint, targetPoint, 0.56);
    const label = understandingVisual.children.find((child) => child instanceof THREE.Sprite);
    if (label) label.position.set(targetX, 1.92, targetZ);
  }
}

function updateRouteVisual(): void {
  if (!routeLine) return;
  const start = currentTask.value.steps[0]!.robotPosition;
  const execution = currentTask.value.steps[4]!.robotPosition;
  const points = [
    new THREE.Vector3(start[0], 0.05, start[2]),
    new THREE.Vector3(0, 0.05, 0.6),
    new THREE.Vector3(execution[0], 0.05, execution[2]),
  ];
  routeLine.geometry.dispose();
  routeLine.geometry = new THREE.BufferGeometry().setFromPoints(points);
  routeLine.visible = selectedStepIndex.value >= 3;
}

function headingForCurrentStep(): number {
  const step = currentStep.value;
  const stepIndex = selectedStepIndex.value;
  const nextWalkingStep = currentTask.value.steps.find(
    (candidate, index) => index > stepIndex && candidate.action === "Walking",
  );
  const destination = nextWalkingStep?.robotPosition ?? currentTask.value.targetPosition;
  const origin = stepIndex > 0 ? currentTask.value.steps[stepIndex - 1]!.robotPosition : step.robotPosition;
  const deltaX = destination[0] - origin[0];
  const deltaZ = destination[2] - origin[2];
  if (Math.abs(deltaX) < 0.01 && Math.abs(deltaZ) < 0.01) return robotHeading;
  return Math.atan2(deltaX, deltaZ);
}

function rotateTowards(current: number, target: number, maxStep: number): number {
  const fullTurn = Math.PI * 2;
  const difference = ((target - current + Math.PI) % fullTurn + fullTurn) % fullTurn - Math.PI;
  if (Math.abs(difference) <= maxStep) return target;
  return current + Math.sign(difference) * maxStep;
}

function createTeachingScene(): void {
  const host = sceneHost.value;
  if (!host) return;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x112b23);
  scene.fog = new THREE.Fog(0x112b23, 15, 30);

  camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
  // 所有步骤共享这一套全景视角，学习者可以持续看到入口、通道、货架和目标物。
  camera.position.set(8.6, 6.4, 11.8);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.setAttribute("aria-label", "具身智能三维教学演示场景");
  host.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 5;
  controls.maxDistance = 18;
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.target.set(0, 0.7, -0.4);

  scene.add(new THREE.HemisphereLight(0xddeee4, 0x18372c, 2.4));
  const keyLight = new THREE.DirectionalLight(0xfff0d4, 3.2);
  keyLight.position.set(5, 10, 6);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(1024, 1024);
  scene.add(keyLight);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(24, 20), makeMaterial(0x27453a));
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  const grid = new THREE.GridHelper(24, 24, 0x5b806f, 0x355b4c);
  grid.position.y = 0.012;
  scene.add(grid);

  addWarehouseShelf(scene, -3.2, -1.6, 0x6d9881);
  addWarehouseShelf(scene, 3.2, -1.6, 0x6d9881);
  addBox(scene, [0.25, 2.7, 0.25], [-5.7, 1.35, -1.6], 0x446d5b);
  addBox(scene, [0.25, 2.7, 0.25], [5.7, 1.35, -1.6], 0x446d5b);

  createTargetVisuals();
  createTeachingVisuals();
  routeLine = new THREE.Line(
    new THREE.BufferGeometry(),
    new THREE.LineBasicMaterial({ color: 0x9be5b8, transparent: true, opacity: 0.9 }),
  );
  routeLine.visible = false;
  scene.add(routeLine);
  updateRouteVisual();

  resizeObserver = new ResizeObserver(resizeRenderer);
  resizeObserver.observe(host);
  resizeRenderer();
  animationFrameId = requestAnimationFrame(renderFrame);
}

function resizeRenderer(): void {
  if (!sceneHost.value || !camera || !renderer) return;
  const { clientWidth, clientHeight } = sceneHost.value;
  const width = Math.max(clientWidth, 1);
  const height = Math.max(clientHeight, 1);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}

function createAnimationActions(gltf: GLTF): void {
  if (!robotRoot) return;
  mixer = new THREE.AnimationMixer(robotRoot);
  for (const clip of gltf.animations) {
    const name = clip.name as AnimationName;
    if (!["Idle", "Walking", "Wave", "Yes", "ThumbsUp"].includes(name)) continue;
    const action = mixer.clipAction(clip);
    action.setLoop(THREE.LoopRepeat, Infinity);
    actions.set(name, action);
  }
}

function playAnimation(name: AnimationName): void {
  const nextAction = actions.get(name) ?? actions.get("Idle");
  if (!nextAction || nextAction === activeAction) return;
  activeAction?.fadeOut(0.18);
  nextAction.reset().fadeIn(0.18).play();
  activeAction = nextAction;
}

function loadRobotModel(): void {
  const loader = new GLTFLoader();
  loader.load(
    "/models/RobotExpressive.glb",
    (gltf) => {
      if (!scene) return;
      const modelBox = new THREE.Box3().setFromObject(gltf.scene);
      const modelSize = modelBox.getSize(new THREE.Vector3());
      const scale = 2.35 / Math.max(modelSize.y, 0.01);
      gltf.scene.scale.setScalar(scale);
      gltf.scene.position.y = -modelBox.min.y * scale;
      gltf.scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.castShadow = true;
          object.receiveShadow = true;
        }
      });

      robotRoot = new THREE.Group();
      robotRoot.rotation.y = robotHeading;
      robotRoot.add(gltf.scene);
      scene.add(robotRoot);
      createAnimationActions(gltf);
      modelState.value = "ready";
      modelError.value = "";
      applyCurrentStep();
    },
    undefined,
    () => {
      modelState.value = "error";
      modelError.value = "机器人模型加载失败，请检查本地模型资源。";
    },
  );
}

function applyCurrentStep(): void {
  const step = currentStep.value;
  robotTarget.set(...step.robotPosition);
  robotTargetHeading = headingForCurrentStep();
  playAnimation(step.action);

  if (targetVisual) {
    targetVisual.position.set(currentTask.value.targetPosition[0], 0, currentTask.value.targetPosition[2]);
  }
  if (shelfTargetVisual) {
    shelfTargetVisual.visible = currentTask.value.targetKind === "shelf";
  }
  if (crateTargetVisual) {
    crateTargetVisual.visible = currentTask.value.targetKind === "crate";
  }
  updateTeachingVisuals();
  updateRouteVisual();
}

function renderFrame(): void {
  const delta = clock.getDelta();
  mixer?.update(delta);
  robotHeading = rotateTowards(robotHeading, robotTargetHeading, delta * 3.2);
  if (robotRoot) {
    robotRoot.position.lerp(robotTarget, Math.min(delta * 3.2, 1));
    robotRoot.rotation.y = robotHeading;
  }
  if (targetMaterial) targetMaterial.emissiveIntensity = 0.75 + Math.sin(performance.now() / 240) * 0.25;
  const pulse = 0.9 + Math.sin(performance.now() / 260) * 0.14;
  observationPulse?.scale.setScalar(pulse);
  understandingHalo?.scale.setScalar(0.94 + Math.sin(performance.now() / 320) * 0.12);
  understandingPulse?.scale.setScalar(0.9 + Math.sin(performance.now() / 220) * 0.18);
  controls?.update();
  if (scene && camera && renderer) renderer.render(scene, camera);
  animationFrameId = requestAnimationFrame(renderFrame);
}

function selectTask(taskId: string): void {
  selectedTaskId.value = taskId;
  selectedStepIndex.value = 0;
}

function selectStep(index: number): void {
  selectedStepIndex.value = index;
}

function resetCurrentTask(): void {
  selectedStepIndex.value = 0;
}

function goToPreviousStep(): void {
  if (selectedStepIndex.value > 0) selectedStepIndex.value -= 1;
}

function goToNextStep(): void {
  if (selectedStepIndex.value < currentTask.value.steps.length - 1) selectedStepIndex.value += 1;
}

function disposeMaterial(material: THREE.Material): void {
  const materialWithMap = material as THREE.Material & { map?: THREE.Texture | null };
  materialWithMap.map?.dispose();
  material.dispose();
}

function disposeScene(): void {
  if (scene) {
    scene.traverse((object) => {
      if (object instanceof THREE.Sprite) {
        disposeMaterial(object.material);
        return;
      }
      if (object instanceof THREE.Line) {
        object.geometry.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach(disposeMaterial);
        return;
      }
      if (object instanceof THREE.Mesh) {
        object.geometry.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach(disposeMaterial);
      }
    });
  }
  controls?.dispose();
  renderer?.dispose();
  renderer?.domElement.remove();
  resizeObserver?.disconnect();
  cancelAnimationFrame(animationFrameId);
  actions.clear();
  scene = null;
  camera = null;
  renderer = null;
  controls = null;
  mixer = null;
  robotRoot = null;
  targetVisual = null;
  shelfTargetVisual = null;
  crateTargetVisual = null;
  targetMarker = null;
  targetRing = null;
  targetMaterial = null;
  routeLine = null;
  teachingVisualGroup = null;
  instructionVisual = null;
  observationVisual = null;
  understandingVisual = null;
  instructionShelfLabel = null;
  instructionCrateLabel = null;
  observationPulse = null;
  understandingPulse = null;
  understandingHalo = null;
  observationRays = [];
  understandingLine = null;
  activeAction = null;
}

watch([currentTask, currentStep], applyCurrentStep);

onMounted(() => {
  createTeachingScene();
  loadRobotModel();
  applyCurrentStep();
});

onBeforeUnmount(disposeScene);
</script>

<template>
  <section class="embodied-demo-workspace" aria-labelledby="embodied-demo-title">
    <header class="page-header demo-page-header">
      <div>
        <p class="eyebrow">可交互的三维教学演示场景</p>
        <h1 id="embodied-demo-title">具身智能三维演示</h1>
        <p class="muted">通过固定任务、预制动作和步骤讲解，理解机器人如何观察环境、形成意图并执行动作。</p>
      </div>
      <span class="demo-role-badge">{{ props.viewerRole === "teacher" ? "教师课堂演示" : "学生自主查看" }}</span>
    </header>

    <div class="demo-layout">
      <aside class="demo-panel demo-task-panel card">
        <div class="demo-panel-heading">
          <div>
            <p class="eyebrow">固定内容</p>
            <h2>演示任务</h2>
          </div>
          <span class="tag learner">{{ DEMO_TASKS.length }} 个</span>
        </div>
        <button
          v-for="task in DEMO_TASKS"
          :key="task.id"
          type="button"
          class="demo-task-button"
          :class="{ active: currentTask.id === task.id }"
          @click="selectTask(task.id)"
        >
          <strong>{{ task.title }}</strong>
          <span>{{ task.summary }}</span>
        </button>
        <p class="demo-readonly-note">任务和场景为课程内置内容，教师与学生都只选择和查看，不编辑场景。</p>
      </aside>

      <section class="demo-stage card" aria-label="三维演示画布">
        <div ref="sceneHost" class="scene-host">
          <div class="scene-caption">{{ currentTask.targetName }} · {{ currentStep.label }}</div>
          <div class="scene-teaching-card">
            <span>当前步骤 {{ currentStepNumber }}/{{ currentTask.steps.length }}</span>
            <strong>{{ currentStep.title }}</strong>
            <small>{{ currentStep.sceneCue }}</small>
          </div>
          <p v-if="modelState === 'loading'" class="scene-status">正在加载可动机器人模型…</p>
          <p v-else-if="modelState === 'error'" class="scene-status scene-status-error">{{ modelError }}</p>
          <div class="scene-hint">固定全景视角 · 可手动旋转</div>
        </div>
        <div class="stage-footer">
          <div>
            <span class="stage-label">运动状态</span>
            <strong>{{ motionStatus }}</strong>
          </div>
          <div>
            <span class="stage-label">机器人动画</span>
            <strong>{{ currentStep.action }}</strong>
          </div>
          <div>
            <span class="stage-label">场景关注</span>
            <strong>{{ selectedStepIndex >= 3 ? '路线与目标' : currentTask.targetName }}</strong>
          </div>
        </div>
      </section>

      <aside class="demo-panel demo-step-panel card">
        <div class="demo-panel-heading">
          <div>
            <p class="eyebrow">{{ currentStepNumber }}/{{ currentTask.steps.length }}</p>
            <h2>演示步骤</h2>
          </div>
          <button type="button" class="button ghost small" @click="resetCurrentTask">从头看</button>
        </div>
        <div class="step-progress" aria-hidden="true"><span :style="{ width: `${progressPercent}%` }"></span></div>
        <ol class="demo-step-list">
          <li v-for="(step, index) in currentTask.steps" :key="step.id">
            <button
              type="button"
              class="demo-step-button"
              :class="{ active: selectedStepIndex === index }"
              :aria-current="selectedStepIndex === index ? 'step' : undefined"
              @click="selectStep(index)"
            >
              <span class="step-number">{{ index + 1 }}</span>
              <span><strong>{{ step.label }}</strong><small>{{ step.title }}</small></span>
            </button>
          </li>
        </ol>
        <div class="step-navigation">
          <button type="button" class="button secondary small" :disabled="selectedStepIndex === 0" @click="goToPreviousStep">上一步</button>
          <button type="button" class="button primary small" :disabled="selectedStepIndex === currentTask.steps.length - 1" @click="goToNextStep">下一步</button>
        </div>
      </aside>
    </div>

    <div class="demo-explanation-grid">
      <article class="card demo-explanation-card">
        <p class="eyebrow">当前阶段</p>
        <h2>{{ currentStep.title }}</h2>
        <p>{{ currentStep.description }}</p>
      </article>
      <article class="card demo-explanation-card">
        <p class="eyebrow">场景观察</p>
        <ul>
          <li v-for="item in currentStep.observation" :key="item">{{ item }}</li>
        </ul>
      </article>
      <article class="card demo-explanation-card learning-point-card">
        <p class="eyebrow">教学提示</p>
        <p>{{ currentStep.learningPoint }}</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.embodied-demo-workspace { max-width: 1400px; }
.demo-page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
.demo-page-header h1 { margin-bottom: 8px; }
.demo-page-header p:last-child { max-width: 760px; margin-bottom: 0; line-height: 1.7; }
.demo-role-badge { flex: 0 0 auto; padding: 8px 12px; border: 1px solid #c9dfd1; border-radius: 999px; color: #176044; background: #edf8f1; font-size: 13px; font-weight: 800; }
.demo-layout { display: grid; grid-template-columns: minmax(190px, 0.75fr) minmax(420px, 2fr) minmax(210px, 0.85fr); gap: 16px; align-items: stretch; }
.demo-panel, .demo-stage { min-width: 0; }
.demo-panel { display: grid; align-content: start; gap: 12px; padding: 18px; }
.demo-panel-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.demo-panel h2 { margin: 0; font-size: 20px; }
.demo-panel .eyebrow { margin-bottom: 5px; }
.demo-task-button { display: grid; gap: 6px; padding: 13px; border: 1px solid var(--line); border-radius: 12px; color: var(--ink); background: #fbfcfb; text-align: left; }
.demo-task-button:hover, .demo-task-button.active { border-color: #7fb398; background: #eff8f2; }
.demo-task-button span { color: var(--muted); font-size: 12px; line-height: 1.55; }
.demo-readonly-note { margin: 2px 0 0; color: var(--muted); font-size: 12px; line-height: 1.65; }
.demo-stage { display: grid; grid-template-rows: minmax(410px, 1fr) auto; overflow: hidden; padding: 0; }
.scene-host { position: relative; min-height: 410px; overflow: hidden; border-radius: 18px 18px 0 0; }
.scene-host canvas { display: block; width: 100%; height: 100%; }
.scene-caption, .scene-hint, .scene-status, .scene-teaching-card { position: absolute; z-index: 1; margin: 0; }
.scene-caption { top: 14px; left: 16px; padding: 7px 10px; border: 1px solid rgb(255 255 255 / 16%); border-radius: 999px; color: #f1f7f3; background: rgb(16 42 33 / 74%); font-size: 12px; font-weight: 800; }
.scene-teaching-card { top: 56px; left: 16px; display: grid; gap: 5px; width: min(330px, calc(100% - 32px)); padding: 12px 14px; border: 1px solid rgb(255 255 255 / 18%); border-radius: 12px; color: #f2faf5; background: rgb(16 42 33 / 82%); box-shadow: 0 8px 20px rgb(0 0 0 / 18%); }
.scene-teaching-card span { color: #b9d7c5; font-size: 11px; font-weight: 800; }
.scene-teaching-card strong { font-size: 14px; }
.scene-teaching-card small { color: #d8e9df; font-size: 12px; line-height: 1.55; }
.scene-hint { right: 16px; bottom: 14px; color: rgb(238 249 242 / 78%); font-size: 11px; }
.scene-status { top: 50%; left: 50%; padding: 10px 14px; border-radius: 10px; color: #f8fff9; background: rgb(16 42 33 / 82%); transform: translate(-50%, -50%); font-size: 13px; }
.scene-status-error { color: #ffe3dd; background: rgb(123 45 40 / 88%); }
.stage-footer { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; padding: 14px 16px; background: #f8fbf8; }
.stage-footer > div { display: grid; gap: 4px; }
.stage-label { color: var(--muted); font-size: 11px; }
.stage-footer strong { font-size: 13px; }
.step-progress { height: 6px; overflow: hidden; border-radius: 999px; background: #e7ece8; }
.step-progress span { display: block; height: 100%; border-radius: inherit; background: var(--green); transition: width 0.2s ease; }
.demo-step-list { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }
.demo-step-button { display: grid; grid-template-columns: 28px minmax(0, 1fr); gap: 9px; align-items: center; width: 100%; padding: 8px; border: 1px solid transparent; border-radius: 10px; color: var(--ink); background: transparent; text-align: left; }
.demo-step-button:hover, .demo-step-button.active { border-color: #c5dfcf; background: #eff8f2; }
.step-number { display: grid; width: 24px; height: 24px; place-items: center; border-radius: 50%; color: #416055; background: #e7efe9; font-size: 12px; font-weight: 800; }
.demo-step-button.active .step-number { color: #ffffff; background: var(--green); }
.demo-step-button strong, .demo-step-button small { display: block; }
.demo-step-button strong { font-size: 12px; }
.demo-step-button small { margin-top: 3px; overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.step-navigation { display: flex; justify-content: space-between; gap: 8px; margin-top: 2px; }
.demo-explanation-grid { display: grid; grid-template-columns: 1.25fr 1fr 1fr; gap: 16px; margin-top: 16px; }
.demo-explanation-card { min-width: 0; padding: 18px; }
.demo-explanation-card h2 { margin: 0 0 8px; font-size: 19px; }
.demo-explanation-card > p:last-child { margin-bottom: 0; color: #40534a; line-height: 1.7; }
.demo-explanation-card ul { display: grid; gap: 7px; margin: 0; padding-left: 18px; color: #40534a; font-size: 13px; line-height: 1.55; }
.learning-point-card { background: #f4faf6; }

@media (max-width: 1100px) {
  .demo-layout { grid-template-columns: 1fr 1.8fr; }
  .demo-step-panel { grid-column: 1 / -1; }
  .demo-step-list { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 760px) {
  .demo-page-header { flex-direction: column; }
  .demo-layout, .demo-explanation-grid { grid-template-columns: 1fr; }
  .demo-stage { grid-row: 1; }
  .demo-task-panel { grid-row: 2; }
  .demo-step-panel { grid-column: auto; grid-row: 3; }
  .scene-host { min-height: 340px; }
  .demo-stage { grid-template-rows: 340px auto; }
  .demo-step-list { grid-template-columns: 1fr; }
}
</style>
