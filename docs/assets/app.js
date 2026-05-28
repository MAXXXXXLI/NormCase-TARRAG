"use strict";

const DATA_PATHS = {
  corpus: "data/corpus.json",
  sources: "data/sources.json",
  stats: "data/stats.json",
  cases: "data/cases.json",
  tasks: "data/case_tasks.json",
};

const LEGAL_LEVEL_PRIORITY = {
  法律: 100,
  行政法规: 90,
  司法解释: 85,
  部门规章: 80,
  地方性法规: 75,
  经济特区法规: 75,
  设区的市地方性法规: 75,
  地方政府规章: 70,
  地方行政规范性文件: 60,
  部门规范性文件: 60,
  部门公告: 58,
  "部门公告/通告": 58,
  强制性国家标准: 55,
  民航行业标准: 50,
  推荐性国家标准: 45,
  国务院政策文件: 40,
  部门政策文件: 35,
  政策文件: 30,
};

const CITY_ALIASES = [
  "北京",
  "上海",
  "深圳",
  "广州",
  "珠海",
  "苏州",
  "无锡",
  "南京",
  "武汉",
  "重庆",
  "四川",
  "山东",
  "湖南",
  "厦门",
  "黄石",
  "芜湖",
  "济南",
  "自贡",
  "达州",
  "共青城",
  "绍兴",
  "唐山",
  "河北",
  "余姚",
  "凤阳",
  "青田",
  "仙桃",
  "瓜州",
  "四平",
];

const FACET_KEYWORDS = {
  registration: ["登记", "实名", "激活", "国籍", "运行识别", "remote id"],
  airspace: ["空域", "起飞", "飞行计划", "飞行申请", "禁飞", "临时管制", "审批", "航线", "机场", "医院"],
  operation: ["运营", "运行", "操控员", "培训", "安全", "应急", "运行控制", "配送", "巡检", "文旅"],
  airworthiness: ["适航", "生产", "制造", "型号", "审定", "合格证", "中型", "多旋翼", "动力提升"],
  data_security: ["数据", "视频", "轨迹", "个人信息", "测绘", "地理信息", "隐私", "保密", "遥感", "存证"],
  local: CITY_ALIASES,
  standard: ["标准", "接口", "技术规范", "服务系统", "航行服务", "物流航线", "测试", "数据接口"],
  policy: ["补贴", "产业", "低空经济", "试点", "扶持", "政策", "发展"],
  future_rule: ["2025", "2026", "修订", "施行", "未来", "前瞻"],
  norm_authorization: ["可以", "有权", "权利", "申请", "请求", "投诉", "举报", "复评", "异议"],
  norm_obligation: ["应当", "必须", "需要", "义务", "履行", "合规准备", "清单", "要求"],
  norm_prohibition: ["不得", "禁止", "不能", "不可以", "禁飞", "限制"],
  norm_responsibility: ["责任", "处罚", "罚款", "警告", "责令", "追究", "后果", "风险"],
  norm_exception: ["但是", "除外", "另有规定", "不适用", "从其规定", "例外"],
  hierarchy_conflict: ["上位法", "下位法", "特别规定", "一般规定", "新规定", "旧规定", "国家", "地方", "标准", "政策", "当前", "未来", "冲突", "优先"],
  legal_reasoning: ["适用", "构成要件", "法律后果", "涵摄", "三段论", "大前提", "小前提", "结论", "依据"],
  case_public_safety: ["黑飞", "军方", "民航改航", "机场", "航道", "公共安全", "严重后果", "空防"],
  case_cyber: ["破解", "后台", "限高", "电子围栏", "飞控", "计算机信息系统", "程序", "工具"],
  case_secret: ["军事", "导弹", "战斗机", "国家秘密", "涉密", "军事设施", "军事管理区"],
  case_admin: ["行政处罚", "罚款", "责令改正", "轨道交通", "高架线路", "100米", "禁飞区域", "报备"],
  case_civil_tort: ["侵权", "赔偿", "损害", "受损", "减产", "碰撞", "剐蹭", "坠落", "误伤", "过错", "因果关系"],
  case_agri_spray: ["农药", "除草剂", "喷洒", "植保", "飞防", "水稻", "蔬菜", "瓜苗", "作物"],
  case_allocation: ["责任比例", "比例", "分配", "连带", "平均承担", "分别", "无法区分", "各自致害", "定作人", "承揽", "操作者", "所有人", "自担"],
  case_product: ["产品", "缺陷", "大疆", "产品说明", "说明书", "警示", "APP", "视觉系统", "暗光", "生产者"],
  case_insurance: ["保险", "第三者责任险", "免赔", "先行赔付", "保险公司", "责任险"],
};

const SCENARIO_HINTS = {
  "黑飞/公共安全": ["黑飞", "军方", "民航改航", "机场", "航道", "公共安全"],
  "飞控破解/网络安全": ["破解", "限高", "禁飞区", "飞控", "电子围栏", "计算机信息系统"],
  "军事设施/保密": ["军事", "导弹", "战斗机", "国家秘密", "涉密"],
  行政处罚: ["行政处罚", "罚款", "责令改正", "轨道交通", "报备"],
  无人机民事侵权: ["侵权", "赔偿", "碰撞", "剐蹭", "坠落", "受损", "减产"],
  农用无人机喷洒: ["农药", "除草剂", "植保", "飞防", "水稻", "蔬菜", "瓜苗"],
  产品责任: ["产品", "缺陷", "大疆", "产品说明", "说明书", "警示", "APP", "视觉系统"],
  保险理赔: ["保险", "第三者责任险", "免赔", "先行赔付"],
  城市配送: ["配送", "物流", "快递", "外卖", "货运"],
  城市巡检: ["巡检", "电力", "桥梁", "道路", "管线", "城市治理"],
  "文旅载人/观光": ["文旅", "观光", "载人", "eVTOL", "空中游览"],
  应急救援: ["应急", "救援", "消防", "灾害", "医疗"],
  农业植保: ["农业", "植保", "农用"],
  制造适航: ["制造", "生产", "适航", "型号", "审定"],
};

const ROLE_KEYWORDS = {
  manufacturer: ["生产", "制造", "适航", "型号", "审定"],
  operator: ["运营", "运行", "飞行", "操控员", "配送", "巡检"],
  platform: ["平台", "服务系统", "数据接口", "航行服务"],
  pilot: ["操控员", "飞手", "培训"],
  regulator: ["监管", "公安", "民航", "空管"],
};

const NORM_FACET_PRIORITY = {
  case_public_safety: -10,
  case_cyber: -9,
  case_secret: -8,
  case_admin: -7,
  case_civil_tort: -6,
  case_agri_spray: -5,
  case_allocation: -4,
  case_product: -3,
  case_insurance: -2,
  hierarchy_conflict: 0,
  norm_exception: 1,
  norm_responsibility: 2,
  norm_authorization: 3,
  norm_prohibition: 4,
  norm_obligation: 5,
  legal_reasoning: 6,
};

const SCENARIOS = [
  {
    label: "配送试点",
    question: "深圳做无人机城市配送试点，需要从哪些方面做合规准备？",
  },
  {
    label: "巡检采集",
    question: "在广州开展无人机道路和桥梁巡检，涉及视频与轨迹数据时，合规重点是什么？",
  },
  {
    label: "eVTOL文旅",
    question: "低空文旅观光项目使用载人 eVTOL，运营前要审查哪些法律边界？",
  },
  {
    label: "平台数据",
    question: "低空飞行服务平台处理飞行轨迹、视频和个人信息时，需要注意哪些数据合规要求？",
  },
  {
    label: "临近机场",
    question: "无人机在机场周边执行巡检任务，能否起飞以及需要核验哪些空域和审批事项？",
  },
  {
    label: "飞控破解",
    question: "为他人破解无人机后台禁飞区和限高限制并从中牟利，法律上应如何评价？",
  },
  {
    label: "植保责任",
    question: "承揽农用无人机喷洒导致相邻农田受损，责任主体和赔偿边界如何判断？",
  },
  {
    label: "保险理赔",
    question: "无人机碰撞第三人财产后，第三者责任险和操作者责任如何分配？",
  },
];

const SYSTEM_PROMPT = `你是低空经济合规法律问答助手，只回答低空经济、无人机、通用航空、低空服务平台、空域运行、数据合规、标准适用、行政处罚、民事侵权、刑事责任和保险理赔相关问题。遇到明显无关的问题，应简短说明本系统聚焦低空经济合规，并引导用户改问相关法律问题。

请严格基于给定证据回答，不要编造未给出的规则、平台入口、审批结果或临时禁飞信息。

你的法律审查方法不是把法规翻译成“义务清单”。成文法规范应同时审查授权性规范、义务性规范、禁止性规范、责任性规范和例外规则。

在形成结论前，还要处理规范位阶和冲突：先确认是否属于同地域、同主体、同事项、同期间的真实冲突；真实冲突再按上位法优于下位法、特别规定优于一般规定、新规定优于旧规定处理。政策文件和行政规范性文件不得突破上位法或违法增设义务/责任。

最终结论使用法律三段论：以已确认有效且适用的规范为大前提，以场景事实为小前提，通过构成要件涵摄推出法律效果、责任或合规风险。

当问题是案例责任预测时，你的目标是给出可与真实裁判/处罚/理赔结果对比的预测，而不是只写合规清单。每个关键结论后写引用，格式为 [article_id]。引用必须逐字使用证据中出现过的 article_id。`;

const HARD_CODED_API = {
  baseUrl: "https://api.siliconflow.cn/v1",
  model: "THUDM/GLM-4-9B-0414",
  apiKey: "sk-refvgkzpumrwnpngrrojiiezfgdahtxqixmllzkxjnaxzewp",
};

const state = {
  corpus: [],
  sources: [],
  stats: {},
  cases: [],
  tasks: [],
  articleById: new Map(),
  sourceById: new Map(),
  sourceArticles: new Map(),
  taskByCaseId: new Map(),
  searchMode: "quick",
  activeView: "home",
  selectedSourceId: "",
  selectedCaseId: "",
  lastReportText: "",
  modelStatus: "checking",
  dataReady: false,
  dataLoadPromise: null,
};

document.addEventListener("DOMContentLoaded", () => {
  initApp().catch((error) => {
    renderFatal(error);
  });
});

async function initApp() {
  bindStaticEvents();
  renderScenarios();
  setLoading("正在加载法规语料与案例数据");
  state.dataLoadPromise = loadAndRenderData();
  await state.dataLoadPromise;
  clearLoading();
  checkModelService();
  hydrateIcons();
}

function bindStaticEvents() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });

  document.querySelectorAll("[data-search-mode]").forEach((button) => {
    button.addEventListener("click", () => setSearchMode(button.dataset.searchMode));
  });

  byId("run-search").addEventListener("click", handleSearch);
  byId("clear-question").addEventListener("click", () => {
    byId("question-input").value = "";
    byId("trace-panel").innerHTML = "";
    byId("insight-output").innerHTML = "";
    byId("result-list").innerHTML = "";
    byId("answer-output").className = "answer-output empty-state";
    byId("answer-output").innerHTML = `<i data-lucide="scan-search"></i><p>输入低空经济合规问题、关键词或案例事实后开始。</p>`;
    byId("result-count").textContent = "待检索";
    setReportCopyVisible(false);
    hydrateIcons();
  });

  byId("question-input").addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      handleSearch();
    }
  });

  ["filter-level", "filter-jurisdiction", "filter-norm"].forEach((id) => {
    byId(id).addEventListener("change", () => {
      if (state.searchMode === "quick" && byId("question-input").value.trim()) {
        handleSearch();
      }
    });
  });

  byId("source-search").addEventListener("input", () => renderSourceList());
  byId("refresh-data").addEventListener("click", async () => {
    setLoading("正在重新加载数据");
    state.dataLoadPromise = loadAndRenderData();
    await state.dataLoadPromise;
    clearLoading();
  });

  byId("copy-report").addEventListener("click", async () => {
    if (!state.lastReportText) return;
    const copied = await copyText(state.lastReportText);
    if (copied) {
      showToast("报告已复制");
    } else {
      openReportDrawer();
      showToast("已打开报告文本");
    }
  });

  document.body.addEventListener("click", handleDelegatedClick);
}

async function checkModelService() {
  const statusText = byId("model-status-text");
  const statusDetail = byId("model-status-detail");
  const statusDot = byId("model-status-dot");
  if (!statusText || !statusDetail || !statusDot) return;

  if (!hasHardCodedApiKey()) {
    state.modelStatus = "offline";
    statusDot.className = "status-dot warning";
    statusText.textContent = "大模型未接入";
    statusDetail.textContent = "当前仍可使用本地法规证据问答；填入 API Key 后将自动调用快速问答模型。";
    return;
  }

  state.modelStatus = "checking";
  statusDot.className = "status-dot checking";
  statusText.textContent = "正在检查快速问答模型";
  statusDetail.textContent = "正在请求模型服务，确认在线问答是否可用。";
  try {
    await callModelHealthCheck();
    state.modelStatus = "online";
    statusDot.className = "status-dot online";
    statusText.textContent = "大模型服务正常";
    statusDetail.textContent = "快速问答模型已连通，法律问答将使用法规证据 + 在线模型生成回答。";
  } catch (error) {
    state.modelStatus = "error";
    statusDot.className = "status-dot warning";
    statusText.textContent = "模型服务暂不可用";
    statusDetail.textContent = `当前将回退到本地证据问答。错误：${String(error.message || error).slice(0, 120)}`;
  }
}

async function loadData() {
  const [corpus, sources, stats, cases, tasks] = await Promise.all(
    Object.values(DATA_PATHS).map((path) => fetchJson(path)),
  );
  state.corpus = corpus;
  state.sources = sources;
  state.stats = stats;
  state.cases = cases;
  state.tasks = tasks;
}

async function loadAndRenderData() {
  state.dataReady = false;
  await loadData();
  prepareIndexes();
  populateFilters();
  renderStats();
  renderSourceList();
  renderCaseList();
  state.dataReady = true;
}

async function ensureDataReady() {
  if (state.dataReady) return;
  if (state.dataLoadPromise) {
    await state.dataLoadPromise;
  }
  if (!state.dataReady || !state.corpus.length) {
    throw new Error("法规数据还没有加载完成，请稍后再试。");
  }
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`无法加载 ${path}: ${response.status}`);
  }
  return response.json();
}

function prepareIndexes() {
  state.articleById = new Map();
  state.sourceById = new Map();
  state.sourceArticles = new Map();
  state.taskByCaseId = new Map();

  for (const doc of state.corpus) {
    doc._search = normalizeText(
      [
        doc.article_id,
        doc.source_id,
        doc.title_zh,
        doc.jurisdiction,
        doc.issuing_authority,
        doc.source_type,
        doc.legal_level,
        doc.themes?.join(" "),
        doc.norm_types?.join(" "),
        doc.exception_markers?.join(" "),
        doc.article_no,
        doc.text,
      ].join(" "),
    );
    doc._title = normalizeText(doc.title_zh);
    doc._isFuture = isFuture(doc);
    state.articleById.set(doc.article_id, doc);
    if (!state.sourceArticles.has(doc.source_id)) {
      state.sourceArticles.set(doc.source_id, []);
    }
    state.sourceArticles.get(doc.source_id).push(doc);
  }

  for (const source of state.sources) {
    source._search = normalizeText(
      [source.source_id, source.title_zh, source.jurisdiction, source.issuing_authority, source.legal_level, source.themes?.join(" ")].join(" "),
    );
    state.sourceById.set(source.source_id, source);
  }

  for (const task of state.tasks) {
    if (task.case_id) {
      state.taskByCaseId.set(task.case_id, task);
    }
  }
}

function populateFilters() {
  fillSelect("filter-level", unique(state.sources.map((source) => source.legal_level).filter(Boolean)));
  fillSelect("filter-jurisdiction", unique(state.sources.map((source) => source.jurisdiction).filter(Boolean)));
}

function fillSelect(id, values) {
  const select = byId(id);
  const current = select.value;
  const first = select.querySelector("option[value='']")?.outerHTML || '<option value="">全部</option>';
  select.innerHTML = first + values.map((value) => `<option value="${escapeAttr(value)}">${escapeHtml(value)}</option>`).join("");
  select.value = values.includes(current) ? current : "";
}

function renderStats() {
  const stats = state.stats || {};
  const sideStats = byId("side-stats");
  sideStats.innerHTML = `
    <div class="side-stat"><span>法规来源</span><strong>${formatNumber(stats.source_count || state.sources.length)}</strong></div>
    <div class="side-stat"><span>条文切片</span><strong>${formatNumber(stats.chunk_count || state.corpus.length)}</strong></div>
    <div class="side-stat"><span>责任案例</span><strong>${formatNumber(stats.case_count || state.cases.length)}</strong></div>
  `;
}

function renderScenarios() {
  byId("scenario-grid").innerHTML = SCENARIOS.map(
    (item) => `<button class="scenario-button" type="button" data-scenario-question="${escapeAttr(item.question)}">${escapeHtml(item.label)}</button>`,
  ).join("");
}

function setSearchMode(mode) {
  state.searchMode = mode;
  document.querySelectorAll("[data-search-mode]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.searchMode === mode);
  });
  const label = byId("run-search")?.querySelector("span");
  if (label) label.textContent = mode === "quick" ? "开始找法" : "开始问答";
}

async function handleSearch() {
  const query = byId("question-input").value.trim();
  if (!query) {
    showToast("请输入问题或关键词");
    return;
  }
  const button = byId("run-search");
  button.disabled = true;
  button.querySelector("span").textContent = state.searchMode === "quick" ? "找法中" : "问答中";

  try {
    if (!state.dataReady) {
      setAnswerLoading("正在加载法规数据，请稍候");
      await ensureDataReady();
    }
    if (state.searchMode === "quick") {
      runQuickSearch(query);
    } else {
      await runDeepSearch(query);
    }
  } catch (error) {
    byId("answer-output").className = "answer-output";
    byId("answer-output").innerHTML = `<h3>暂时无法完成</h3><p>${escapeHtml(error.message || error)}</p>`;
    byId("result-count").textContent = "未完成";
    showToast("操作未完成");
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = state.searchMode === "quick" ? "开始找法" : "开始问答";
    hydrateIcons();
  }
}

function runQuickSearch(query) {
  const hits = searchDocs(query, 50, "general", null, true);
  byId("trace-panel").innerHTML = "";
  byId("insight-output").innerHTML = "";
  byId("results-title").textContent = "快速找法结果";
  byId("result-count").textContent = `${hits.length} 条`;
  state.lastReportText = "";
  setReportCopyVisible(false);
  byId("answer-output").className = "answer-output";
  byId("answer-output").innerHTML = `
    <h3>快速找法</h3>
    <p>按法规标题、条文、主题、地域和规范类型命中排序。法律问答会进一步做场景追踪、法源矩阵和规则边界消解。</p>
  `;
  renderResults(hits, query);
}

async function runDeepSearch(query) {
  setAnswerLoading("正在检索法规证据并生成法律回答");
  const trace = traceQuestion(query);
  const rawHits = retrieveTrace(trace, 24, 18);
  const cells = buildEvidenceMatrix(rawHits, trace);
  const hits = selectAlignedHits(cells, 14);
  const resolve = resolveConflicts(trace, cells);
  renderTrace(trace, resolve);
  renderInsightPanel(trace, hits, resolve);

  let answer = offlineAnswer(query, trace, hits, cells, resolve);
  let apiError = "";
  if (hasHardCodedApiKey()) {
    try {
      answer = await callChatApi(query, trace, hits, cells, resolve);
    } catch (error) {
      apiError = `API 调用失败，已回退离线答案：${error.message}`;
    }
  }

  byId("results-title").textContent = "低空经济法律问答";
  byId("result-count").textContent = `${hits.length} 条证据`;
  state.lastReportText = buildPlainReport(query, answer, hits, trace, resolve);
  setReportCopyVisible(true);
  const rendered = renderMarkdown(answer);
  byId("answer-output").className = "answer-output";
  byId("answer-output").innerHTML = apiError
    ? `<div class="trace-chip warning">${escapeHtml(apiError)}</div>${rendered}`
    : rendered;
  renderResults(hits, query);
}

function searchDocs(query, topK = 20, facet = "general", trace = null, useUiFilters = false) {
  const scored = [];
  const tokens = queryTokens(query);
  for (const doc of state.corpus) {
    if (useUiFilters && !passesUiFilters(doc)) {
      continue;
    }
    const score = scoreDoc(doc, query, tokens, facet, trace);
    if (score > 0) {
      scored.push(makeHit(doc, score, 0, query, facet));
    }
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK).map((hit, index) => ({ ...hit, rank: index + 1 }));
}

function scoreDoc(doc, query, tokens, facet, trace) {
  const normalizedQuery = normalizeText(query);
  const search = doc._search || "";
  let score = 0;

  if (normalizedQuery && search.includes(normalizedQuery)) {
    score += 120 + Math.min(80, normalizedQuery.length / 2);
  }
  if (normalizedQuery && doc._title?.includes(normalizedQuery)) {
    score += 80;
  }

  for (const token of tokens) {
    if (!token) continue;
    if (search.includes(token)) {
      score += token.length >= 4 ? 14 : token.length >= 3 ? 9 : 4;
    }
    if (doc._title?.includes(token)) {
      score += 18;
    }
  }

  if (doc.article_id && normalizedQuery.includes(normalizeText(doc.article_id))) {
    score += 200;
  }
  if (doc.source_id && normalizedQuery.includes(normalizeText(doc.source_id))) {
    score += 90;
  }

  score += normFacetBonus(facet, doc);
  score += semanticFacetBonus(facet, doc, trace);
  score += validityBonus(facet, doc);
  score += (doc.authority_rank || LEGAL_LEVEL_PRIORITY[doc.legal_level] || 0) / 18;

  return score;
}

function queryTokens(query) {
  const normalized = normalizeText(query);
  const found = [];
  const dictionary = unique(
    Object.values(FACET_KEYWORDS)
      .flat()
      .concat(CITY_ALIASES, ["无人机", "无人驾驶航空器", "低空经济", "空域", "飞行计划", "民法典", "刑法"]),
  );

  for (const keyword of dictionary) {
    const token = normalizeText(keyword);
    if (token && normalized.includes(token)) {
      found.push(token);
    }
  }

  const ascii = query.toLowerCase().match(/[a-z0-9_./-]+/g) || [];
  const chinese = query.replace(/[^\u4e00-\u9fff]/g, "");
  const grams = [];
  for (const size of [2, 3, 4]) {
    if (chinese.length < size) continue;
    for (let i = 0; i <= chinese.length - size; i += 1) {
      grams.push(chinese.slice(i, i + size));
    }
  }
  return unique([...found, ...ascii.map(normalizeText), ...grams]).slice(0, 80);
}

function passesUiFilters(doc) {
  const level = byId("filter-level").value;
  const jurisdiction = byId("filter-jurisdiction").value;
  const norm = byId("filter-norm").value;
  if (level && doc.legal_level !== level) return false;
  if (jurisdiction && doc.jurisdiction !== jurisdiction) return false;
  if (norm && !(doc.norm_types || []).includes(norm)) return false;
  return true;
}

function retrieveTrace(trace, prefetchK = 20, finalK = 12) {
  const merged = new Map();
  for (const facet of trace.facets) {
    const subqueries = trace.subqueries[facet] || [trace.original_question];
    for (const subquery of subqueries) {
      const hits = searchDocs(subquery, prefetchK, facet, trace, false);
      for (const hit of hits) {
        const existing = merged.get(hit.doc.article_id);
        const adjusted = { ...hit, score: hit.score + 0.1, facet, query: subquery };
        if (!existing || adjusted.score > existing.score) {
          merged.set(hit.doc.article_id, adjusted);
        }
      }
    }
  }
  const rankedAll = [...merged.values()].sort((a, b) => b.score - a.score);
  const ranked = applyCaseCoverage(rankedAll, trace, finalK);
  return ranked.map((hit, index) => ({ ...hit, rank: index + 1 }));
}

function applyCaseCoverage(rankedAll, trace, finalK) {
  if (!trace.facets.some((facet) => facet.startsWith("case_"))) {
    return rankedAll.slice(0, finalK);
  }

  const promoted = caseSourceRouter(trace);
  const facetFill = facetFillers(rankedAll, trace);
  const out = [];
  const seen = new Set();

  const add = (hit) => {
    if (out.length >= finalK) return;
    if (hit.doc._isFuture && !trace.facets.includes("future_rule")) return;
    if (seen.has(hit.doc.article_id)) return;
    out.push(hit);
    seen.add(hit.doc.article_id);
  };

  promoted.slice(0, 9).forEach(add);
  facetFill.forEach(add);
  rankedAll.forEach(add);
  return out.slice(0, finalK);
}

function facetFillers(rankedAll, trace) {
  const preferred = ["airspace", "operation", "registration", "local", "policy"];
  const out = [];
  const seenFacets = new Set();
  for (const facet of preferred) {
    if (!trace.facets.includes(facet)) continue;
    const hit = rankedAll.find((item) => item.facet === facet && !seenFacets.has(item.facet));
    if (hit) {
      out.push(hit);
      seenFacets.add(hit.facet);
    }
  }
  return out;
}

function caseSourceRouter(trace) {
  const facets = new Set(trace.facets);
  const specs = [];
  const spec = (sourceId, facet, articles, maxItems = 1) => specs.push({ sourceId, facet, articles, maxItems });

  if (facets.has("case_public_safety")) {
    spec("criminal_law_case_supplement", "case_public_safety", ["第一百一十四条", "第一百一十五条"], 2);
    spec("uas_interim_reg_2023", "case_public_safety", ["第二十六条", "第三十四条", "第五十一条", "第十六条"], 2);
    spec("general_flight_rules_current", "airspace", ["第二条", "第三条", "第八条"], 1);
    spec("public_security_administration_law_2025", "case_public_safety", ["第三条", "第八条"], 1);
  }
  if (facets.has("case_cyber")) {
    spec("criminal_law_case_supplement", "case_cyber", ["第二百八十五条"], 1);
    spec("cybercrime_interpretation_2011", "case_cyber", ["第二条", "第三条"], 2);
    spec("cybersecurity_law_2025_current", "case_cyber", ["第六条", "第二十七条", "第六十三条"], 1);
    spec("uas_interim_reg_2023", "case_cyber", ["第三十四条"], 1);
  }
  if (facets.has("case_secret")) {
    spec("criminal_law_case_supplement", "case_secret", ["第二百八十二条"], 1);
    spec("military_facilities_protection_law_2021", "case_secret", ["第二十二条", "第六十条"], 2);
    spec("state_secrets_law_2024", "case_secret", ["第五条", "第五十九条"], 1);
    spec("uas_interim_reg_2023", "case_secret", ["第三十四条"], 1);
  }
  if (facets.has("case_admin")) {
    spec("urban_rail_operation_reg_2018", "case_admin", ["第三十四条", "第五十三条"], 2);
    spec("uas_interim_reg_2023", "case_admin", ["第二十六条", "第五十一条", "第五十二条"], 1);
    if (trace.original_question.includes("深圳")) {
      spec("shenzhen_micro_light_uav_interim_2019", "local", ["第二十四条", "第四十条", "第三十四条"], 2);
    }
  }
  if (facets.has("case_civil_tort") || facets.has("case_agri_spray") || facets.has("case_allocation")) {
    spec("civil_code_tort_case_supplement", "case_civil_tort", ["第一千一百六十五条", "第一千一百七十二条", "第一千一百七十三条", "第一千一百九十三条"], 3);
    spec("uas_interim_reg_2023", "airspace", ["第二十六条", "第三十四条", "第五十一条"], 1);
    spec("ccar92_uas_operation_safety_2024", "operation", ["第92.1条", "第92.1103条"], 1);
    if (containsAny(trace.original_question, ["农药", "除草剂", "喷药", "喷洒", "飞防", "植保"])) {
      spec("ccar91_general_operation_flight_rules_2019", "case_agri_spray", ["chunk_186", "chunk_187"], 2);
    }
  }
  if (facets.has("case_product")) {
    spec("civil_code_tort_case_supplement", "case_product", ["第一千二百零二条", "第一千二百零三条", "第一千二百零六条"], 3);
    spec("uas_interim_reg_2023", "case_product", ["第九条"], 1);
    spec("uas_production_management_2024", "case_product", ["第四条"], 1);
    spec("caac_uas_airworthiness_class_safety_2022", "airworthiness", ["chunk_001"], 1);
  }
  if (facets.has("case_insurance")) {
    spec("insurance_law_case_supplement", "case_insurance", ["第六十五条", "第六十六条"], 2);
    spec("civil_code_tort_case_supplement", "case_civil_tort", ["第一千一百六十五条"], 1);
  }

  const hits = [];
  let rankedScore = 0;
  for (const item of specs) {
    const candidates = bestSourceHits(item.sourceId, item.facet, item.articles, trace, item.maxItems);
    for (const hit of candidates) {
      rankedScore += 1;
      hits.push({ ...hit, score: 10000 - rankedScore });
    }
  }
  return hits;
}

function bestSourceHits(sourceId, facet, articles, trace, maxItems) {
  const chunks = state.sourceArticles.get(sourceId) || [];
  const scored = [];
  for (const doc of chunks) {
    let articleScore = 0;
    articles.forEach((marker, index) => {
      if (marker && (`${doc.article_no} ${doc.article_id} ${doc.text}`).includes(marker)) {
        articleScore = Math.max(articleScore, 100 - index);
      }
    });
    if (articleScore === 0 && articles.length) continue;
    const keywordScore = caseKeywords(trace).filter((keyword) => doc._search.includes(normalizeText(keyword))).length;
    const score = articleScore + keywordScore + semanticFacetBonus(facet, doc, trace) + normFacetBonus("norm_responsibility", doc);
    scored.push(makeHit(doc, score, 0, "case_source_router", facet));
  }
  scored.sort((a, b) => b.score - a.score);
  const out = [];
  const seen = new Set();
  for (const hit of scored) {
    if (seen.has(hit.doc.article_id)) continue;
    out.push(hit);
    seen.add(hit.doc.article_id);
    if (out.length >= maxItems) break;
  }
  return out;
}

function caseKeywords(trace) {
  return [
    "无人机",
    "无人驾驶航空器",
    "空域",
    "飞行计划",
    "公共安全",
    "军事设施",
    "国家秘密",
    "破解",
    "计算机信息系统",
    "轨道交通",
    "农药",
    "除草剂",
    "承揽",
    "定作人",
    "产品缺陷",
    "警示",
    "保险",
    "第三者责任险",
    "赔偿",
    "过错",
    "因果关系",
  ].filter((keyword) => trace.original_question.includes(keyword));
}

function normFacetBonus(facet, doc) {
  const normMap = {
    norm_authorization: "authorization",
    norm_obligation: "obligation",
    norm_prohibition: "prohibition",
    norm_responsibility: "responsibility",
    norm_exception: "exception",
  };
  const expected = normMap[facet];
  if (expected && (doc.norm_types || []).includes(expected)) return 12;
  if (facet === "hierarchy_conflict") return (doc.authority_rank || 0) >= 70 || (doc.exception_markers || []).length ? 8 : 0;
  if (facet === "legal_reasoning") return (doc.norm_types || []).length ? 5 : 0;
  return 0;
}

function semanticFacetBonus(facet, doc, trace) {
  const themes = new Set(doc.themes || []);
  const text = doc._search || "";
  const sourceId = doc.source_id;
  const original = trace?.original_question || "";
  if (facet === "local") {
    const loc = trace?.slots?.location || "";
    if (loc && loc !== "全国" && (doc.jurisdiction === loc || doc.jurisdiction?.includes(loc) || doc.title_zh?.includes(loc) || text.includes(normalizeText(loc)))) return 80;
    if (!["", "CN", "全国"].includes(doc.jurisdiction)) return 12;
  }
  if (facet === "standard") return doc.legal_level?.includes("标准") || themes.has("standard") || doc.title_zh?.includes("规范") ? 20 : 0;
  if (facet === "data_security") return intersects(themes, ["data_security", "personal_information", "surveying_mapping", "geographic_information"]) ? 20 : 0;
  if (facet === "operation") return intersects(themes, ["operation", "operator", "safety"]) ? 15 : 0;
  if (facet === "registration") return themes.has("registration") || text.includes("登记") || text.includes("运行识别") ? 15 : 0;
  if (facet === "airspace") return intersects(themes, ["airspace", "flight_application"]) || text.includes("空域") ? 15 : 0;
  if (facet === "case_public_safety") return sourceBonus(sourceId, ["criminal_law_case_supplement", "uas_interim_reg_2023", "general_flight_rules_current", "public_security_administration_law_2025"], 65) + keywordBonus(text, ["公共安全", "严重后果", "飞行计划", "管制空域", "危及公共"], 35);
  if (facet === "case_cyber") return sourceBonus(sourceId, ["criminal_law_case_supplement", "cybercrime_interpretation_2011", "cybersecurity_law_2025_current", "public_security_administration_law_2025"], 65) + keywordBonus(text, ["计算机信息系统", "侵入", "非法控制", "程序", "工具", "网络安全"], 35);
  if (facet === "case_secret") return sourceBonus(sourceId, ["criminal_law_case_supplement", "state_secrets_law_2024", "military_facilities_protection_law_2021", "uas_interim_reg_2023"], 65) + keywordBonus(text, ["军事设施", "国家秘密", "涉密", "违法拍摄"], 35);
  if (facet === "case_admin") return sourceBonus(sourceId, ["urban_rail_operation_reg_2018", "shenzhen_micro_light_uav_interim_2019", "uas_interim_reg_2023"], 65) + keywordBonus(text, ["城市轨道交通", "100米", "无人机等低空飞行器", "责令改正", "罚款", "报备"], 35);
  if (facet === "case_civil_tort") {
    let score = sourceBonus(sourceId, ["civil_code_tort_case_supplement", "uas_interim_reg_2023", "ccar91_general_operation_flight_rules_2019", "ccar92_uas_operation_safety_2024"], 55) + keywordBonus(text, ["侵权责任", "过错", "损害", "赔偿", "因果关系", "安全注意义务"], 35);
    if (themes.has("product_liability") && !containsAny(original, ["产品", "缺陷", "大疆", "说明", "APP", "视觉系统"])) score -= 45;
    return score;
  }
  if (facet === "case_agri_spray") return sourceBonus(sourceId, ["civil_code_tort_case_supplement", "ccar91_general_operation_flight_rules_2019", "ccar92_uas_operation_safety_2024"], 55) + keywordBonus(text, ["农林喷洒", "农药", "有毒药品", "作业区", "作业负责人", "植保"], 45);
  if (facet === "case_allocation") return sourceBonus(sourceId, ["civil_code_tort_case_supplement", "insurance_law_case_supplement"], 65) + keywordBonus(text, ["承揽", "定作人", "分别实施", "过错", "责任保险", "第三者"], 35);
  if (facet === "case_product") return sourceBonus(sourceId, ["civil_code_tort_case_supplement", "uas_interim_reg_2023"], 60) + keywordBonus(text, ["产品责任", "产品缺陷", "生产者", "缺陷", "警示", "说明"], 40);
  if (facet === "case_insurance") return sourceBonus(sourceId, ["insurance_law_case_supplement", "low_altitude_insurance_2026", "civil_aviation_law_2021_current", "civil_aviation_law_2025"], 60) + keywordBonus(text, ["责任保险", "保险人", "被保险人", "第三者", "保险金", "免赔"], 40);
  return 0;
}

function validityBonus(facet, doc) {
  if (!doc._isFuture) return 0;
  return facet === "future_rule" ? 15 : -45;
}

function sourceBonus(sourceId, sourceIds, value) {
  return sourceIds.includes(sourceId) ? value : 0;
}

function keywordBonus(text, keywords, value) {
  return keywords.some((keyword) => text.includes(normalizeText(keyword))) ? value : 0;
}

function traceQuestion(question, disabledFacets = []) {
  const location = detectLocation(question);
  const scenario = detectScenario(question);
  const dataActivity = ["视频", "轨迹", "测绘", "个人信息", "遥感", "平台调度数据"].filter((keyword) => question.includes(keyword));
  const actor = containsAny(question, ["企业", "运营", "试点", "配送", "巡检"]) ? "运营企业" : "个人或单位";
  const aircraft = containsAny(question, ["无人机", "无人驾驶航空器", "UAV"]) ? "民用无人驾驶航空器" : "低空航空器";
  const facets = detectFacets(question).filter((facet) => !disabledFacets.includes(facet));
  const slots = { location, actor, aircraft, scenario, data_activity: dataActivity };
  const warnings = [];
  if (containsAny(question, ["明天", "今天", "上午", "下午", "医院", "机场", "能不能起飞", "可以起飞"])) {
    warnings.push("question_requires_realtime_airspace_or_site_specific_check");
  }
  return {
    original_question: question,
    slots,
    facets,
    subqueries: buildSubqueries(question, slots, facets),
    warnings,
  };
}

function detectLocation(question) {
  return CITY_ALIASES.find((city) => question.includes(city)) || "全国";
}

function detectScenario(question) {
  for (const [name, keywords] of Object.entries(SCENARIO_HINTS)) {
    if (containsAny(question, keywords)) return name;
  }
  return "一般低空飞行/合规咨询";
}

function detectFacets(question) {
  const lower = question.toLowerCase();
  const facets = [];
  for (const [facet, keywords] of Object.entries(FACET_KEYWORDS)) {
    if (keywords.some((keyword) => lower.includes(String(keyword).toLowerCase()))) {
      facets.push(facet);
    }
  }
  for (const defaultFacet of ["operation", "airspace", "registration"]) {
    if (!facets.includes(defaultFacet)) facets.push(defaultFacet);
  }
  if (detectLocation(question) !== "全国" && !facets.includes("local")) facets.push("local");
  if (containsAny(question, ["视频", "轨迹", "数据", "测绘", "巡检"]) && !facets.includes("data_security")) facets.push("data_security");
  if (containsAny(question, ["配送", "物流", "航线", "服务系统"]) && !facets.includes("standard")) facets.push("standard");

  const broadReview = containsAny(question, ["合规", "准备", "哪些", "如何", "怎么", "是否", "能不能", "可不可以", "风险", "责任", "权利", "清单"]);
  if (broadReview) {
    for (const facet of ["norm_authorization", "norm_obligation", "norm_prohibition", "norm_responsibility", "norm_exception", "legal_reasoning"]) {
      if (!facets.includes(facet)) facets.push(facet);
    }
  }
  if (containsAny(question, ["冲突", "层级", "优先", "上位", "下位", "国家", "地方", "标准", "政策", "当前", "未来"]) && !facets.includes("hierarchy_conflict")) {
    facets.push("hierarchy_conflict");
  }
  if (containsAny(question, ["责任", "处罚", "赔偿", "判", "法院", "案", "罪", "构成", "法律上应如何评价"])) {
    for (const facet of ["case_civil_tort", "case_allocation"]) {
      if (!facets.includes(facet) && containsAny(question, FACET_KEYWORDS[facet])) facets.push(facet);
    }
  }
  if (facets.includes("case_cyber") && !containsAny(question, ["为他人", "提供", "程序", "工具", "服务", "牟利", "后台", "电子围栏"])) {
    return facets.filter((facet) => facet !== "case_cyber");
  }
  return facets;
}

function buildSubqueries(question, slots, facets) {
  const loc = slots.location || "全国";
  const scenario = slots.scenario || "";
  const templates = {
    registration: [`${question} 实名登记 激活 运行识别`, `民用无人驾驶航空器 实名登记 运行识别 ${scenario}`],
    airspace: [`${question} 空域 飞行申请 飞行计划 管制`, `${loc} 无人机 空域 飞行安全 临时管制`],
    operation: [`${question} 运行安全 运营人 操控员 应急`, `民用无人驾驶航空器 运行安全 管理规则 ${scenario}`],
    airworthiness: [`${question} 适航 审定 合格证 生产 制造`, "无人驾驶航空器 适航 审定 分级分类"],
    data_security: [`${question} 数据安全 个人信息 测绘 保密`, `无人机 ${scenario} 视频 轨迹 数据 合规`],
    local: [`${loc} 无人驾驶航空器 管理 低空经济 条例`, `${loc} 低空经济 无人机 飞行安全`],
    standard: [`${question} 技术标准 低空飞行服务 数据接口 航线`, `无人机 ${scenario} 行业标准 技术规范`],
    policy: [`${question} 低空经济 政策 试点 扶持`, "低空经济 标准体系 产业政策"],
    future_rule: [`${question} 施行日期 未来 修订 当前有效`, "民用航空法 2025 2026 施行 当前有效"],
    norm_authorization: [`${question} 可以 有权 申请 请求 投诉 举报 复评 权利`, `低空经济 无人机 权利 救济 申请 投诉 举报 ${scenario}`],
    norm_obligation: [`${question} 应当 必须 义务 履行 建立 采取 提交 申报`, `民用无人驾驶航空器 应当 义务 合规要求 ${scenario}`],
    norm_prohibition: [`${question} 不得 禁止 限制 不适用 禁飞`, `无人驾驶航空器 不得 禁止 限制 活动 ${scenario}`],
    norm_responsibility: [`${question} 责任 处罚 罚款 警告 责令 追究 法律后果`, `无人驾驶航空器 法律责任 主体责任 处罚 风险 ${scenario}`],
    norm_exception: [`${question} 但是 除外 另有规定 不适用 从其规定 例外`, `低空经济 无人机 一般规则 例外规则 另有规定 ${scenario}`],
    hierarchy_conflict: [`${question} 法律 行政法规 部门规章 地方性法规 标准 政策 上位法 特别规定 新旧规定`, `${loc} 国家规则 地方规则 强制标准 行业标准 政策文件 冲突处理`],
    legal_reasoning: [`${question} 适用 条件 构成要件 法律后果 涵摄 结论`, `低空经济 法律三段论 事实 条件 法律效果 ${scenario}`],
    case_public_safety: [`${question} 以危险方法危害公共安全 刑法 第一百一十四条 第一百一十五条`, "无人驾驶航空器 黑飞 未申请空域 飞行计划 公共安全 刑事责任", "无人驾驶航空器飞行管理暂行条例 第三十四条 第五十六条 公共安全"],
    case_cyber: [`${question} 提供侵入 非法控制 计算机信息系统 程序 工具 第二百八十五条`, "破解无人机 禁飞 限高 电子围栏 飞控系统 网络安全 刑事责任", "计算机信息系统安全 司法解释 程序 工具 情节严重"],
    case_secret: [`${question} 非法获取国家秘密 刑法 第二百八十二条 军事设施`, "无人机 违法拍摄 军事设施 涉密场所 国家秘密 保密义务", "军事设施保护法 保守国家秘密法 无人机 航拍 传播"],
    case_admin: [`${question} 行政处罚 责令改正 罚款 无人机`, "城市轨道交通运营管理规定 第三十四条 第五十三条 100米 无人机", `${loc} 民用无人机 禁飞 报备 超高 罚款`],
    case_civil_tort: [`${question} 民法典 过错 侵权责任 因果关系 赔偿`, "无人机 运行安全 注意义务 财产损害 民事赔偿", "受害人过错 因果关系 事故调查报告 赔偿责任"],
    case_agri_spray: [`${question} 农药 喷洒 作业 勘察 安全处理 有毒药品 因果关系`, "农林喷洒 作业负责人 农药 作物 受损 赔偿", "植保无人机 飞防 农药漂移 相邻农田 损害"],
    case_allocation: [`${question} 民法典 承揽 定作人 选任 指示 过错 责任`, "分别实施侵权 平均承担 连带责任 过错比例 受害人过错", "责任主体 操作者 所有人 定作人 承揽人 保险公司"],
    case_product: [`${question} 民法典 产品责任 产品缺陷 生产者 说明 警示`, "无人机 产品质量 说明书 APP 提示 暗光 视觉系统 缺陷", "产品缺陷 生产者责任 用户操作 免责 证据"],
    case_insurance: [`${question} 保险法 责任保险 第三者 直接赔偿 免赔 保险限额`, "低空保险 第三者责任险 无人机 保险公司 先行赔付", "责任保险 被保险人 第三者损害 保险金"],
  };
  return Object.fromEntries(facets.map((facet) => [facet, templates[facet] || [question]]));
}

function buildEvidenceMatrix(hits) {
  const groups = new Map();
  for (const hit of hits) {
    const doc = hit.doc;
    const role = inferRole(doc._search);
    const key = [hit.facet, doc.legal_level, doc.jurisdiction, doc.source_type, doc.validity, role].join("||");
    if (!groups.has(key)) {
      groups.set(key, {
        facet: hit.facet,
        legal_level: doc.legal_level,
        jurisdiction: doc.jurisdiction,
        source_type: doc.source_type,
        validity: doc.validity,
        role,
        hits: [],
      });
    }
    groups.get(key).hits.push(hit);
  }

  const cells = [...groups.values()];
  for (const cell of cells) {
    cell.hits.sort((a, b) => b.score - a.score);
  }
  cells.sort((a, b) => {
    const ap = NORM_FACET_PRIORITY[a.facet] ?? 20;
    const bp = NORM_FACET_PRIORITY[b.facet] ?? 20;
    if (ap !== bp) return ap - bp;
    if (a.facet !== b.facet) return a.facet.localeCompare(b.facet, "zh-Hans-CN");
    return (LEGAL_LEVEL_PRIORITY[b.legal_level] || 0) - (LEGAL_LEVEL_PRIORITY[a.legal_level] || 0);
  });
  return cells;
}

function selectAlignedHits(cells, topK = 12) {
  const selected = [];
  const seen = new Set();
  for (const cell of cells) {
    const routerHits = cell.hits.filter((hit) => hit.query === "case_source_router");
    const ordered = cell.facet.startsWith("case_") && routerHits.length > 1
      ? routerHits.concat(cell.hits.filter((hit) => hit.query !== "case_source_router"))
      : cell.hits;
    const perCell = cell.facet.startsWith("case_") && routerHits.length > 1 ? 2 : 1;
    let picked = 0;
    for (const hit of ordered) {
      if (seen.has(hit.doc.article_id)) continue;
      selected.push(hit);
      seen.add(hit.doc.article_id);
      picked += 1;
      if (picked >= perCell) break;
    }
  }
  const allHits = cells.flatMap((cell) => cell.hits).sort((a, b) => b.score - a.score);
  for (const hit of allHits) {
    if (selected.length >= topK) break;
    if (!seen.has(hit.doc.article_id)) {
      selected.push(hit);
      seen.add(hit.doc.article_id);
    }
  }
  return selected.slice(0, topK).map((hit, index) => ({ ...hit, rank: index + 1 }));
}

function resolveConflicts(trace, cells) {
  const rulesApplied = [];
  const warnings = [];
  let mustAbstain = false;
  let abstainReason = null;

  const hasLocal = cells.some((cell) => !["", "CN", "全国"].includes(cell.jurisdiction) && cell.facet === "local");
  const hasNational = cells.some((cell) => ["CN", "全国"].includes(cell.jurisdiction));
  const hasStandard = cells.some((cell) => cell.legal_level?.includes("标准") || cell.facet === "standard");
  const hasLawOrRule = cells.some((cell) => ["法律", "行政法规", "部门规章", "地方性法规", "经济特区法规", "地方政府规章"].includes(cell.legal_level));
  const hasFuture = cells.some((cell) => isFuture({ validity: cell.validity }));
  const facets = new Set(cells.map((cell) => cell.facet));
  const topChunks = cells.map((cell) => cell.hits[0]?.doc).filter(Boolean);
  const normTypes = new Set(topChunks.flatMap((doc) => doc.norm_types || []));
  const hasException = normTypes.has("exception") || topChunks.some((doc) => (doc.exception_markers || []).length);
  const broadReview = trace.facets.some((facet) => facet.startsWith("norm_"));

  if (hasLocal && hasNational) {
    rulesApplied.push("local_specific_over_general");
    warnings.push("地方规则应作为属地执行要求，与国家规则共同适用，而不是替代国家底线。");
  }
  if (hasStandard && hasLawOrRule) {
    rulesApplied.push("law_over_standard");
    warnings.push("法律、行政法规和规章给出义务边界；技术标准主要补充技术实现、接口或流程细节。");
  }
  if (hasFuture) {
    rulesApplied.push("current_over_future");
    warnings.push("检索到未来施行规则；当前合规判断不能直接把未来施行文本当作现行依据。");
  }
  const roles = new Set(cells.map((cell) => cell.role));
  if ([...roles].filter((role) => role !== "general").length >= 2) {
    rulesApplied.push("role_separation");
    warnings.push("制造商、运营人、平台、操控员的义务应分开说明，避免职责混用。");
  }
  if (broadReview) {
    rulesApplied.push("norm_type_completeness");
    const required = {
      norm_authorization: ["authorization", "授权/权利/可为事项"],
      norm_obligation: ["obligation", "义务/命令性要求"],
      norm_prohibition: ["prohibition", "禁止性要求"],
      norm_responsibility: ["responsibility", "责任/处罚/救济后果"],
      norm_exception: ["exception", "例外或但书"],
    };
    const missing = Object.entries(required)
      .filter(([facet, [normType]]) => !facets.has(facet) && !normTypes.has(normType))
      .map(([, [, label]]) => label);
    warnings.push(missing.length ? `完整规范审查不能只列义务；当前证据矩阵缺少：${missing.join("、")}。` : "已按授权、义务、禁止、责任和例外五类规范组织证据，后续结论需逐项引用。");
  }
  if (trace.facets.includes("norm_exception") || hasException) {
    rulesApplied.push("exception_rule_check");
    warnings.push("存在但书、另有规定、除外或不适用结构；结论应先说明一般规则，再审查例外是否改变适用结果。");
  }
  if (trace.facets.includes("hierarchy_conflict") || (hasLocal && hasNational) || (hasStandard && hasLawOrRule)) {
    rulesApplied.push("hierarchy_conflict_order");
    warnings.push("冲突处理顺序：先确认同地域、同主体、同事项、同期间是否构成真实冲突；真实冲突再按上位法优于下位法、特别规定优于一般规定、新规定优于旧规定处理。");
  }
  if (broadReview) {
    rulesApplied.push("deductive_subsumption");
    warnings.push("最终结论应采用法律三段论：以已确认有效且适用的规范为大前提，以场景事实为小前提，经构成要件涵摄推出法律效果、责任或合规风险。");
  }
  if (trace.warnings.length) {
    rulesApplied.push("abstain_when_realtime");
    mustAbstain = true;
    abstainReason = "问题涉及具体时间、点位、临时管制、医院/机场周边或实时空域，静态法规语料不能直接判断是否允许起飞。";
    warnings.push(abstainReason);
  }
  return { rules_applied: rulesApplied, warnings, must_abstain: mustAbstain, abstain_reason: abstainReason };
}

function offlineAnswer(question, trace, hits, cells, resolve) {
  const slots = trace.slots;
  const lines = [];
  lines.push("## 1. 场景识别");
  lines.push(`地点：${slots.location}；角色：${slots.actor}；航空器：${slots.aircraft}；场景：${slots.scenario}；数据活动：${(slots.data_activity || []).join("、") || "未明确"}。`);
  lines.push("\n## 2. 结论摘要");
  if (resolve.must_abstain) {
    lines.push(`不能仅凭静态法规语料判断最终能否执行；原因：${resolve.abstain_reason}`);
  } else {
    lines.push("该场景通常需要先确认规则层级和适用条件，再分别核验可为事项、义务、禁止、责任、例外，以及航空器登记/运行识别、空域或飞行计划、运营安全管理、地方属地要求、数据安全和技术标准要求。");
  }
  lines.push("\n## 3. 法律规范结构审查");
  const normRows = [
    ["授权/权利/可为事项", ["norm_authorization", "authorization"]],
    ["义务/命令性要求", ["norm_obligation", "obligation"]],
    ["禁止性要求", ["norm_prohibition", "prohibition"]],
    ["责任/处罚/救济后果", ["norm_responsibility", "responsibility"]],
    ["例外/但书/不适用", ["norm_exception", "exception"]],
  ];
  for (const [label, facets] of normRows) {
    const cites = citationsFor(hits, facets);
    if (cites) lines.push(`- ${label}：需要在相应证据下单独判断，避免把全部规则压缩成义务清单。${cites}`);
  }
  const hierarchyCites = citationsFor(hits, ["hierarchy_conflict"]);
  if (hierarchyCites) {
    lines.push(`- 位阶与冲突：先确认是否存在同地域、同主体、同事项、同期间的真实冲突，再处理上位法/特别法/新旧法关系。${hierarchyCites}`);
  }
  lines.push("\n## 4. 分步骤合规工作流");
  const stepMap = [
    ["航空器与主体准备", ["registration", "operation"]],
    ["空域/飞行计划/审批核验", ["airspace"]],
    ["运行安全管理", ["operation"]],
    ["地方属地规则核验", ["local"]],
    ["数据安全与测绘/个人信息评估", ["data_security"]],
    ["技术标准/接口/航线设计", ["standard"]],
  ];
  let stepNo = 1;
  for (const [name, facets] of stepMap) {
    const evs = stepHits(hits, trace, facets);
    if (!evs.length) continue;
    const cites = evs.slice(0, 2).map((hit) => `[${hit.doc.article_id}]`).join("，");
    lines.push(`${stepNo}. ${name}：依据相关证据进行核验和准备。${cites}`);
    stepNo += 1;
  }
  lines.push("\n## 5. 法律三段论涵摄");
  lines.push("大前提：仅采用已检索到且经层级、地域、时间和例外审查后的有效规范。");
  lines.push("小前提：以场景中的地点、主体、航空器、业务活动、数据活动和时间为事实要素。");
  lines.push("涵摄结论：逐项判断事实是否落入授权、义务、禁止和责任规范的构成要件；证据不足时保留人工核验或拒答。");
  lines.push("\n## 6. 证据引用");
  const displayHits = hits.filter((hit) => locationCompatible(hit, trace));
  for (const hit of (displayHits.length ? displayHits : hits).slice(0, 8)) {
    const doc = hit.doc;
    lines.push(`- [${doc.article_id}] ${doc.title_zh}（${doc.legal_level}，${doc.jurisdiction}，${doc.validity}，${(doc.norm_types || []).join("、")}）：${doc.text.slice(0, 120)}`);
  }
  lines.push("\n## 7. 规则冲突与边界");
  if (resolve.warnings.length) {
    resolve.warnings.forEach((warning) => lines.push(`- ${warning}`));
  } else {
    lines.push("- 未发现明显的层级、地方或施行时间冲突；仍需结合实际点位和主管部门平台核验。");
  }
  lines.push("\n## 8. 需要人工核验的事项");
  if (resolve.must_abstain) lines.push(`- ${resolve.abstain_reason}`);
  lines.push("- 实际飞行前应核验实时空域、临时管制、属地平台入口、审批结果、具体起降点周边敏感区域。");
  lines.push("\n## 9. 免责声明");
  lines.push("以上为基于给定静态语料的合规研究与工作流建议，不替代正式法律意见或主管部门审批结果。");
  return lines.join("\n");
}

function citationsFor(hits, facets, limit = 3) {
  const normTypeNames = new Set(["authorization", "obligation", "prohibition", "responsibility", "exception"]);
  const cites = [];
  for (const hit of hits) {
    if ((hit.doc.norm_types || []).some((norm) => facets.includes(norm))) {
      cites.push(`[${hit.doc.article_id}]`);
    } else if (!facets.some((facet) => normTypeNames.has(facet)) && facets.includes(hit.facet)) {
      cites.push(`[${hit.doc.article_id}]`);
    }
  }
  return unique(cites).slice(0, limit).join("，");
}

function locationCompatible(hit, trace) {
  const loc = trace.slots.location || "";
  const jurisdiction = hit.doc.jurisdiction;
  if (!loc || loc === "全国") return true;
  return ["", "CN", "全国", loc].includes(jurisdiction);
}

function stepHits(hits, trace, facets) {
  const loc = trace.slots.location || "";
  const rows = [];
  for (const hit of hits) {
    if (!locationCompatible(hit, trace)) continue;
    const doc = hit.doc;
    const themes = new Set(doc.themes || []);
    if (facets.includes(hit.facet)) rows.push(hit);
    else if (facets.includes("local") && (doc.jurisdiction === loc || themes.has("local"))) rows.push(hit);
    else if (facets.includes("standard") && (doc.legal_level?.includes("标准") || themes.has("standard"))) rows.push(hit);
    else if (facets.includes("data_security") && intersects(themes, ["data_security", "personal_information", "surveying_mapping", "geographic_information"])) rows.push(hit);
    else if (facets.includes("registration") && (themes.has("registration") || doc.text.includes("登记"))) rows.push(hit);
    else if (facets.includes("operation") && intersects(themes, ["operation", "operator", "safety"])) rows.push(hit);
    else if (facets.includes("airspace") && (intersects(themes, ["airspace", "flight_application"]) || doc.text.includes("空域"))) rows.push(hit);
  }
  const seen = new Set();
  return rows.filter((hit) => {
    if (seen.has(hit.doc.article_id)) return false;
    seen.add(hit.doc.article_id);
    return true;
  });
}

async function callChatApi(question, trace, hits, cells, resolve) {
  const baseUrl = HARD_CODED_API.baseUrl.replace(/\/+$/, "");
  const payload = {
    model: HARD_CODED_API.model,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: buildApiUserPrompt(question, trace, hits, cells, resolve) },
    ],
    temperature: 0.1,
    max_tokens: 1500,
  };
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${HARD_CODED_API.apiKey}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text.slice(0, 180) || `${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  return data?.choices?.[0]?.message?.content || "";
}

async function callModelHealthCheck() {
  const baseUrl = HARD_CODED_API.baseUrl.replace(/\/+$/, "");
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${HARD_CODED_API.apiKey}`,
    },
    body: JSON.stringify({
      model: HARD_CODED_API.model,
      messages: [
        { role: "system", content: "你是服务健康检查助手。只回复 OK。" },
        { role: "user", content: "OK" },
      ],
      temperature: 0,
      max_tokens: 8,
    }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text.slice(0, 160) || `${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content) throw new Error("模型没有返回内容");
  return content;
}

function hasHardCodedApiKey() {
  const key = HARD_CODED_API.apiKey.trim();
  return Boolean(key && key !== "your_api_key_here" && key !== "PASTE_YOUR_API_KEY_HERE");
}

function buildApiUserPrompt(question, trace, hits, cells, resolve) {
  return `问题：${question}

场景槽位：${JSON.stringify(trace.slots)}
触发 facets：${trace.facets.join(", ")}
Resolve 规则：${resolve.rules_applied.join(", ")}
Resolve 警告：${resolve.warnings.join("；")}

请输出精炼但完整的回答，控制在 900-1300 字。优先给结论、依据、风险和核验清单，不要展开与问题无关的背景。

Evidence matrix:
${matrixToMarkdown(cells)}

证据：
${formatEvidence(hits.slice(0, 10))}`;
}

function matrixToMarkdown(cells) {
  const lines = [
    "| facet | legal_level | jurisdiction | validity | role | norm_types | top evidence |",
    "| --- | --- | --- | --- | --- | --- | --- |",
  ];
  for (const cell of cells) {
    const top = cell.hits[0]?.doc;
    if (!top) continue;
    lines.push(`| ${cell.facet} | ${top.legal_level} | ${top.jurisdiction} | ${top.validity} | ${cell.role} | ${(top.norm_types || []).join(", ")} | ${top.article_id}: ${top.title_zh} ${top.article_no} |`);
  }
  return lines.join("\n");
}

function formatEvidence(hits) {
  return hits
    .map((hit) => {
      const doc = hit.doc;
      const text = String(doc.text || "");
      const clippedText = text.length > 900 ? `${text.slice(0, 900)}...` : text;
      return `[${doc.article_id}] ${doc.title_zh}｜${doc.legal_level}｜${doc.jurisdiction}｜${doc.validity}｜${doc.article_no}｜norm=${(doc.norm_types || []).join(",")}\n${clippedText}`;
    })
    .join("\n\n");
}

function renderTrace(trace, resolve) {
  const slotChips = [
    `地点：${trace.slots.location}`,
    `角色：${trace.slots.actor}`,
    `航空器：${trace.slots.aircraft}`,
    `场景：${trace.slots.scenario}`,
    `facets：${trace.facets.slice(0, 8).join(" / ")}${trace.facets.length > 8 ? " ..." : ""}`,
  ];
  const warnings = (resolve?.warnings || []).slice(0, 2);
  byId("trace-panel").innerHTML = `
    <div>${slotChips.map((chip) => `<span class="trace-chip">${escapeHtml(chip)}</span>`).join(" ")}</div>
    ${warnings.length ? `<div>${warnings.map((warning) => `<span class="trace-chip warning">${escapeHtml(warning)}</span>`).join(" ")}</div>` : ""}
  `;
}

function renderInsightPanel(trace, hits, resolve) {
  const currentHits = hits.filter((hit) => !hit.doc._isFuture).length;
  const localHits = hits.filter((hit) => !["", "CN", "全国"].includes(hit.doc.jurisdiction)).length;
  const riskText = resolve.must_abstain ? "需实时核验" : resolve.warnings.length >= 3 ? "边界较多" : "可形成初判";
  const riskKind = resolve.must_abstain ? "future" : resolve.warnings.length >= 3 ? "case" : "level";
  const cards = [
    ["场景", trace.slots.scenario || "一般合规"],
    ["地域", trace.slots.location || "全国"],
    ["证据", `${currentHits}/${hits.length} 条现行或有效`],
    ["判断", riskText, riskKind],
  ];
  const actions = buildActionItems(trace, hits);
  byId("insight-output").innerHTML = `
    <div class="insight-grid">
      ${cards
        .map(
          ([label, value, kind]) => `
            <div class="insight-card">
              <span>${escapeHtml(label)}</span>
              <strong class="${escapeAttr(kind || "")}">${escapeHtml(value)}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
    <div class="checklist-strip">
      ${actions.map((item) => `<span class="trace-chip">${escapeHtml(item)}</span>`).join("")}
      ${localHits ? `<span class="trace-chip warning">含 ${localHits} 条地方/属地证据</span>` : ""}
    </div>
  `;
}

function buildActionItems(trace, hits) {
  const facets = new Set(trace.facets);
  const items = [];
  if (facets.has("registration")) items.push("核验登记/实名/运行识别");
  if (facets.has("airspace")) items.push("核验空域/飞行计划/临时管制");
  if (facets.has("operation")) items.push("核验运营人与操控员安全义务");
  if (facets.has("local")) items.push("核验属地规则和主管部门要求");
  if (facets.has("data_security")) items.push("核验数据、测绘、个人信息边界");
  if (facets.has("standard")) items.push("核验技术标准和接口要求");
  if (trace.facets.some((facet) => facet.startsWith("case_"))) items.push("分析责任主体和法律后果");
  if (hits.some((hit) => hit.doc._isFuture)) items.push("区分现行规则和未来施行规则");
  return unique(items).slice(0, 6);
}

function buildPlainReport(question, answer, hits, trace, resolve) {
  const evidence = hits
    .slice(0, 12)
    .map((hit, index) => `${index + 1}. [${hit.doc.article_id}] ${hit.doc.title_zh} ${hit.doc.article_no}`)
    .join("\n");
  const warnings = resolve.warnings.length ? resolve.warnings.map((item) => `- ${item}`).join("\n") : "- 未发现明显规则边界提醒";
  return `低空经济法律问答报告

问题：
${question}

场景识别：
地点：${trace.slots.location}
角色：${trace.slots.actor}
航空器：${trace.slots.aircraft}
场景：${trace.slots.scenario}

回答：
${answer}

关键边界：
${warnings}

引用证据：
${evidence}`;
}

function setReportCopyVisible(visible) {
  byId("copy-report")?.classList.toggle("is-hidden", !visible);
}

function renderResults(hits, query) {
  if (!hits.length) {
    byId("result-list").innerHTML = `<div class="empty-state"><i data-lucide="file-search"></i><p>没有找到匹配条文。</p></div>`;
    hydrateIcons();
    return;
  }
  byId("result-list").innerHTML = hits
    .map((hit) => {
      const doc = hit.doc;
      return `
        <article class="result-item">
          <div class="result-top">
            <h3 class="result-title">
              <button type="button" data-article-id="${escapeAttr(doc.article_id)}">${escapeHtml(doc.title_zh)} ${escapeHtml(doc.article_no)}</button>
            </h3>
            <span class="result-count">#${hit.rank}</span>
          </div>
          <div class="result-meta">
            ${badge(doc.legal_level, "level")}
            ${badge(doc.jurisdiction || "全国")}
            ${badge(doc.validity, doc._isFuture ? "future" : "")}
            ${badge(hit.facet)}
            ${(doc.norm_types || []).slice(0, 3).map((norm) => badge(norm)).join("")}
          </div>
          <p class="result-text">${makeSnippet(doc.text, query)}</p>
        </article>
      `;
    })
    .join("");
}

function renderSourceList() {
  const q = normalizeText(byId("source-search").value || "");
  const filtered = q ? state.sources.filter((source) => source._search.includes(q)) : state.sources;
  byId("source-list").innerHTML = filtered
    .map((source) => `
      <button class="source-item ${state.selectedSourceId === source.source_id ? "is-active" : ""}" type="button" data-source-id="${escapeAttr(source.source_id)}">
        <div class="source-top">
          <h3 class="source-title">${escapeHtml(source.title_zh)}</h3>
          <span class="result-count">${source.article_count}</span>
        </div>
        <div class="source-meta">
          ${badge(source.legal_level, "level")}
          ${badge(source.jurisdiction || "全国")}
          ${badge(source.validity, isFuture(source) ? "future" : "")}
        </div>
      </button>
    `)
    .join("");
}

function renderSourceDetail(sourceId) {
  const source = state.sourceById.get(sourceId);
  const docs = state.sourceArticles.get(sourceId) || [];
  if (!source) return;
  state.selectedSourceId = sourceId;
  renderSourceList();
  byId("source-detail").className = "source-detail";
  byId("source-detail").innerHTML = `
    <div class="source-top">
      <div>
        <p class="eyebrow">${escapeHtml(source.source_id)}</p>
        <h2>${escapeHtml(source.title_zh)}</h2>
      </div>
      <span class="result-count">${docs.length} 条</span>
    </div>
    <div class="source-meta">
      ${badge(source.legal_level, "level")}
      ${badge(source.jurisdiction || "全国")}
      ${badge(source.issuing_authority || "未知机关")}
      ${badge(source.validity, isFuture(source) ? "future" : "")}
    </div>
    <div class="source-actions">
      ${source.landing_url ? `<a class="secondary-button" href="${escapeAttr(source.landing_url)}" target="_blank" rel="noreferrer"><i data-lucide="external-link"></i><span>原始页面</span></a>` : ""}
      ${source.url ? `<a class="secondary-button" href="${escapeAttr(source.url)}" target="_blank" rel="noreferrer"><i data-lucide="file-down"></i><span>原始文件</span></a>` : ""}
    </div>
    <div class="inline-search">
      <i data-lucide="search"></i>
      <input id="article-search" type="search" placeholder="搜索本法规条文" />
    </div>
    <div class="article-list" id="article-list"></div>
  `;
  byId("article-search").addEventListener("input", () => renderArticleList(docs, byId("article-search").value));
  renderArticleList(docs, "");
  hydrateIcons();
}

function renderArticleList(docs, query) {
  const q = normalizeText(query || "");
  const filtered = q ? docs.filter((doc) => doc._search.includes(q)) : docs;
  byId("article-list").innerHTML = filtered
    .map((doc) => `
      <article class="article-item">
        <div class="article-top">
          <button class="article-title-button" type="button" data-article-id="${escapeAttr(doc.article_id)}">${escapeHtml(doc.article_no || doc.article_id)}</button>
          <span class="result-count">${doc.char_len || doc.text.length} 字</span>
        </div>
        <div class="article-meta">
          ${(doc.norm_types || []).slice(0, 4).map((norm) => badge(norm)).join("")}
        </div>
        <p class="article-text">${escapeHtml(doc.text)}</p>
      </article>
    `)
    .join("");
}

function renderCaseList() {
  byId("case-list").innerHTML = state.cases
    .map((item) => `
      <button class="case-item ${state.selectedCaseId === item.case_id ? "is-active" : ""}" type="button" data-case-id="${escapeAttr(item.case_id)}">
        <div class="case-top">
          <h3 class="case-title">${escapeHtml(item.case_name)}</h3>
        </div>
        <div class="case-meta">
          ${badge(item.case_type, "case")}
          ${(item.topic || []).slice(0, 2).map((topic) => badge(topic)).join("")}
        </div>
      </button>
    `)
    .join("");
}

function renderCaseDetail(caseId) {
  const item = state.cases.find((row) => row.case_id === caseId);
  if (!item) return;
  state.selectedCaseId = caseId;
  renderCaseList();
  const task = state.taskByCaseId.get(caseId);
  const question = task?.question || item.rag_question || item.facts;
  byId("case-detail").className = "case-detail";
  byId("case-detail").innerHTML = `
    <p class="eyebrow">${escapeHtml(item.case_id)}</p>
    <h2>${escapeHtml(item.case_name)}</h2>
    <div class="case-meta">
      ${badge(item.case_type, "case")}
      ${badge(item.court || "法院待核验")}
      ${badge(item.case_no || "案号待核验")}
      ${(item.topic || []).map((topic) => badge(topic)).join("")}
    </div>
    <div class="case-actions">
      <button class="primary-button" type="button" data-case-question="${escapeAttr(question)}">
        <i data-lucide="sparkles"></i>
        <span>送入法律问答</span>
      </button>
      ${item.source_url ? `<a class="secondary-button" href="${escapeAttr(item.source_url)}" target="_blank" rel="noreferrer"><i data-lucide="external-link"></i><span>案例来源</span></a>` : ""}
    </div>
    <h3>事实</h3>
    <p class="case-text">${escapeHtml(item.facts || "")}</p>
    <h3>裁判/处理规则</h3>
    <p class="case-text">${escapeHtml(item.court_rule || "")}</p>
    <h3>结果</h3>
    <p class="case-text">${escapeHtml(item.outcome || item.gold_result_summary || "")}</p>
    <h3>研判问题</h3>
    <p class="case-text">${escapeHtml(question || "")}</p>
  `;
  hydrateIcons();
}

function openArticle(articleId) {
  const doc = state.articleById.get(articleId);
  if (!doc) return;
  const drawer = byId("article-drawer");
  drawer.classList.add("is-open");
  drawer.innerHTML = `
    <div class="drawer-head">
      <div>
        <p class="eyebrow">${escapeHtml(doc.article_id)}</p>
        <h2>${escapeHtml(doc.title_zh)} ${escapeHtml(doc.article_no)}</h2>
      </div>
      <button class="icon-button" type="button" data-close-drawer title="关闭" aria-label="关闭">
        <i data-lucide="x"></i>
      </button>
    </div>
    <div class="result-meta">
      ${badge(doc.legal_level, "level")}
      ${badge(doc.jurisdiction || "全国")}
      ${badge(doc.validity, doc._isFuture ? "future" : "")}
      ${(doc.norm_types || []).map((norm) => badge(norm)).join("")}
    </div>
    <div class="drawer-actions">
      <button class="secondary-button" type="button" data-copy-article="${escapeAttr(doc.article_id)}"><i data-lucide="copy"></i><span>复制引用</span></button>
      ${doc.landing_url ? `<a class="secondary-button" href="${escapeAttr(doc.landing_url)}" target="_blank" rel="noreferrer"><i data-lucide="external-link"></i><span>原始页面</span></a>` : ""}
      ${doc.url ? `<a class="secondary-button" href="${escapeAttr(doc.url)}" target="_blank" rel="noreferrer"><i data-lucide="file-down"></i><span>原始文件</span></a>` : ""}
    </div>
    <p class="drawer-text">${escapeHtml(doc.text)}</p>
  `;
  hydrateIcons();
}

function openReportDrawer() {
  if (!state.lastReportText) return;
  const drawer = byId("article-drawer");
  drawer.classList.add("is-open");
  drawer.innerHTML = `
    <div class="drawer-head">
      <div>
        <p class="eyebrow">Compliance Report</p>
        <h2>低空经济法律问答报告</h2>
      </div>
      <button class="icon-button" type="button" data-close-drawer title="关闭" aria-label="关闭">
        <i data-lucide="x"></i>
      </button>
    </div>
    <p class="drawer-text">${escapeHtml(state.lastReportText)}</p>
  `;
  hydrateIcons();
}

function handleDelegatedClick(event) {
  const startTarget = event.target.closest("[data-start-view]");
  if (startTarget) {
    switchView(startTarget.dataset.startView);
    return;
  }

  const homeQuestion = event.target.closest("[data-home-question]");
  if (homeQuestion) {
    switchView("qa");
    setSearchMode("deep");
    byId("question-input").value = homeQuestion.dataset.homeQuestion;
    handleSearch();
    return;
  }

  const scenario = event.target.closest("[data-scenario-question]");
  if (scenario) {
    byId("question-input").value = scenario.dataset.scenarioQuestion;
    setSearchMode("deep");
    return;
  }

  const article = event.target.closest("[data-article-id]");
  if (article) {
    openArticle(article.dataset.articleId);
    return;
  }

  const source = event.target.closest("[data-source-id]");
  if (source) {
    renderSourceDetail(source.dataset.sourceId);
    return;
  }

  const caseButton = event.target.closest("[data-case-id]");
  if (caseButton) {
    renderCaseDetail(caseButton.dataset.caseId);
    return;
  }

  const caseQuestion = event.target.closest("[data-case-question]");
  if (caseQuestion) {
    byId("question-input").value = caseQuestion.dataset.caseQuestion;
    setSearchMode("deep");
    switchView("qa");
    handleSearch();
    return;
  }

  if (event.target.closest("[data-close-drawer]")) {
    byId("article-drawer").classList.remove("is-open");
    return;
  }

  const copyButton = event.target.closest("[data-copy-article]");
  if (copyButton) {
    const doc = state.articleById.get(copyButton.dataset.copyArticle);
    if (doc) {
      navigator.clipboard?.writeText(`[${doc.article_id}] ${doc.title_zh} ${doc.article_no}\n${doc.text}`);
      showToast("引用已复制");
    }
  }
}

function switchView(view) {
  state.activeView = view;
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("is-active", section.id === `view-${view}`);
  });
  const titles = {
    home: "低空经济法律合规助手",
    qa: "法律问答",
    library: "法规库",
    cases: "案例研判",
  };
  byId("view-title").textContent = titles[view] || "低空经济法律合规助手";
}

function renderMarkdown(text) {
  const lines = String(text || "").split(/\n/);
  let html = "";
  let inList = false;
  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      continue;
    }
    if (line.startsWith("## ")) {
      closeList();
      html += `<h3>${renderInline(line.slice(3))}</h3>`;
    } else if (/^\d+\.\s/.test(line)) {
      closeList();
      html += `<h4>${renderInline(line)}</h4>`;
    } else if (line.startsWith("- ")) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += `<li>${renderInline(line.slice(2))}</li>`;
    } else {
      closeList();
      html += `<p>${renderInline(line)}</p>`;
    }
  }
  closeList();
  return html;
}

function renderInline(text) {
  const escaped = escapeHtml(text);
  return escaped.replace(/\[([^\]]+)\]/g, (match, articleId) => {
    const unescaped = articleId.replace(/&amp;/g, "&");
    if (state.articleById.has(unescaped)) {
      return `<button class="citation" type="button" data-article-id="${escapeAttr(unescaped)}">[${escapeHtml(unescaped)}]</button>`;
    }
    return match;
  });
}

function makeSnippet(text, query) {
  const tokens = queryTokens(query).filter((token) => token.length >= 2);
  const normalized = normalizeText(text);
  let pos = -1;
  for (const token of tokens) {
    pos = normalized.indexOf(token);
    if (pos >= 0) break;
  }
  const start = pos >= 0 ? Math.max(0, pos - 55) : 0;
  const end = Math.min(text.length, start + 230);
  return `${start > 0 ? "..." : ""}${escapeHtml(text.slice(start, end))}${end < text.length ? "..." : ""}`;
}

function badge(text, kind = "") {
  if (!text) return "";
  return `<span class="badge ${escapeAttr(kind)}">${escapeHtml(text)}</span>`;
}

function setLoading(message) {
  byId("answer-output").className = "answer-output";
  byId("answer-output").innerHTML = renderLoading(message);
}

function setAnswerLoading(message) {
  byId("answer-output").className = "answer-output";
  byId("answer-output").innerHTML = renderLoading(message);
  byId("result-list").innerHTML = "";
  byId("result-count").textContent = "处理中";
}

function renderLoading(message) {
  return `
    <div class="loading-state" aria-live="polite">
      <div class="loading-spinner" aria-hidden="true"></div>
      <p>${escapeHtml(message)}</p>
      <div class="loading-steps" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;
}

function clearLoading() {
  byId("answer-output").className = "answer-output empty-state";
  byId("answer-output").innerHTML = `<i data-lucide="scan-search"></i><p>输入低空经济合规问题、关键词或案例事实后开始。</p>`;
  byId("result-count").textContent = "待检索";
}

function renderFatal(error) {
  byId("answer-output").className = "answer-output";
  byId("answer-output").innerHTML = `<h3>数据加载失败</h3><p>${escapeHtml(error.message)}</p><p>请通过本地服务器或 GitHub Pages 打开网页。</p>`;
  hydrateIcons();
}

function showToast(message) {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();
  const node = document.createElement("div");
  node.className = "toast trace-chip";
  node.textContent = message;
  node.style.position = "fixed";
  node.style.left = "50%";
  node.style.bottom = "24px";
  node.style.transform = "translateX(-50%)";
  node.style.zIndex = "50";
  document.body.appendChild(node);
  window.setTimeout(() => node.remove(), 1800);
}

async function copyText(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall through to textarea copy.
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  const ok = document.execCommand("copy");
  textarea.remove();
  return ok;
}

function inferRole(text) {
  for (const [role, keywords] of Object.entries(ROLE_KEYWORDS)) {
    if (keywords.some((keyword) => text.includes(normalizeText(keyword)))) return role;
  }
  return "general";
}

function makeHit(doc, score, rank, query, facet) {
  return { doc, score, rank, query, facet };
}

function isFuture(doc) {
  const validity = String(doc?.validity || "").toLowerCase();
  return validity.includes("future") || validity.includes("not_yet_effective") || validity.includes("尚未施行");
}

function normalizeText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[，。；：、（）《》“”‘’！？”]/g, "");
}

function containsAny(text, keywords) {
  return keywords.some((keyword) => String(text || "").includes(keyword));
}

function intersects(set, values) {
  return values.some((value) => set.has(value));
}

function unique(values) {
  return [...new Set(values.filter((value) => value !== undefined && value !== null && value !== ""))];
}

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value || 0);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("\n", " ");
}

function byId(id) {
  return document.getElementById(id);
}

function hydrateIcons() {
  if (window.lucide?.createIcons) {
    window.lucide.createIcons();
  }
}
