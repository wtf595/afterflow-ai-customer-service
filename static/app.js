const state = {
  data: null,
  evaluation: null,
  selectedTicketId: null,
  filter: "all",
  processing: false,
  view: "dashboard",
};

const viewMeta = {
  dashboard: ["工作台 / 今日概览", "售后运营总览"],
  tickets: ["工作台 / 工单处理", "AI 辅助处理台"],
  evaluation: ["验证 / 效果评测", "方案对比实验"],
  method: ["验证 / 方案说明", "产品决策记录"],
};

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `请求失败：${response.status}`);
  return data;
}

async function load() {
  try {
    const [bootstrap, evaluation] = await Promise.all([
      api("/api/bootstrap"),
      api("/api/evaluation"),
    ]);
    state.data = bootstrap;
    state.evaluation = evaluation;
    document.getElementById("engine-mode").textContent = bootstrap.engine.mode;
    document.getElementById("engine-detail").textContent = bootstrap.engine.detail;
    renderAll();
  } catch (error) {
    showToast(`加载失败：${error.message}`);
    document.getElementById("engine-mode").textContent = "服务未连接";
    document.getElementById("engine-detail").textContent = "请检查本地服务是否启动";
  }
}

function renderAll() {
  renderNavigation();
  renderDashboard();
  renderTicketList();
  renderTicketDetail();
  renderEvaluation();
}

function switchView(view) {
  state.view = view;
  document.querySelectorAll(".view").forEach((element) => {
    element.classList.toggle("active", element.id === `view-${view}`);
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  const [eyebrow, title] = viewMeta[view];
  document.getElementById("page-eyebrow").textContent = eyebrow;
  document.getElementById("page-title").textContent = title;
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (view === "evaluation") animateEvaluationBars();
}

function renderNavigation() {
  if (!state.data) return;
  document.getElementById("pending-count").textContent = state.data.dashboard.pending;
}

function renderDashboard() {
  if (!state.data) return;
  const { dashboard, tickets } = state.data;
  document.getElementById("metric-pending").textContent = dashboard.pending;
  document.getElementById("metric-risk").textContent = dashboard.high_risk;
  document.getElementById("metric-success").textContent = `${dashboard.workflow_success}%`;
  document.getElementById("metric-success-note").textContent =
    `${dashboard.evaluation_total} 条离线回归样本`;
  document.getElementById("metric-critical").textContent =
    `${dashboard.critical_error_rate}%`;
  document.getElementById("pending-count").textContent = dashboard.pending;

  const priorityOrder = { 紧急: 0, 较高: 1, 普通: 2 };
  const queue = [...tickets]
    .filter((ticket) => ["待处理", "待确认"].includes(ticket.status))
    .sort((a, b) => (priorityOrder[a.priority] ?? 3) - (priorityOrder[b.priority] ?? 3))
    .slice(0, 4);
  const queueElement = document.getElementById("dashboard-queue");
  if (!queue.length) {
    queueElement.innerHTML = `
      <div class="run-empty" style="margin-top: 18px">
        <div><h4>队列已处理完</h4><p>可以重置演示数据，再体验一次完整处理流程。</p></div>
      </div>`;
  } else {
    queueElement.innerHTML = queue
      .map(
        (ticket) => `
        <div class="mini-ticket" data-open-ticket="${escapeHtml(ticket.id)}">
          <span class="customer-avatar">${escapeHtml(ticket.customer.slice(0, 1))}</span>
          <div>
            <div class="mini-title">${escapeHtml(ticket.customer)} · ${escapeHtml(ticket.message)}</div>
            <div class="mini-meta">${escapeHtml(ticket.channel)} · ${escapeHtml(ticket.created_at)}</div>
          </div>
          <span class="priority-badge ${priorityClass(ticket.priority)}">${escapeHtml(ticket.priority)}</span>
        </div>`
      )
      .join("");
  }

  const methods = state.evaluation?.methods || [];
  document.getElementById("preview-methods").innerHTML = methods
    .map(
      (method) => `
      <div class="preview-method">
        <header>
          <strong>${escapeHtml(method.name)}</strong>
          <span>${method.task_success_rate}%</span>
        </header>
        <div class="bar-track">
          <i data-bar-value="${method.task_success_rate}" style="width:${method.task_success_rate}%"></i>
        </div>
      </div>`
    )
    .join("");
}

function priorityClass(priority) {
  if (priority === "紧急") return "urgent";
  if (priority === "较高") return "medium";
  return "normal";
}

function renderTicketList() {
  if (!state.data) return;
  const tickets = state.data.tickets.filter((ticket) => {
    if (state.filter === "pending") {
      return ["待处理", "待确认"].includes(ticket.status);
    }
    if (state.filter === "risk") return ["较高", "紧急"].includes(ticket.priority);
    return true;
  });
  const pending = state.data.tickets.filter((ticket) =>
    ["待处理", "待确认"].includes(ticket.status)
  ).length;
  document.getElementById("inbox-summary").textContent = `${pending} 个待处理`;
  document.getElementById("ticket-list").innerHTML = tickets.length
    ? tickets
        .map(
          (ticket) => `
        <button class="ticket-row ${ticket.id === state.selectedTicketId ? "active" : ""}"
          data-ticket-id="${escapeHtml(ticket.id)}">
          <div class="ticket-row-top">
            <div class="ticket-person">
              <span class="customer-avatar">${escapeHtml(ticket.customer.slice(0, 1))}</span>
              <strong>${escapeHtml(ticket.customer)}</strong>
              <span>${escapeHtml(ticket.id)}</span>
            </div>
            <span class="priority-badge ${priorityClass(ticket.priority)}">${escapeHtml(ticket.priority)}</span>
          </div>
          <div class="ticket-preview">${escapeHtml(ticket.message)}</div>
          <div class="ticket-row-bottom">
            <span>${escapeHtml(ticket.channel)} · ${escapeHtml(ticket.created_at)}</span>
            <span class="ticket-status">${escapeHtml(ticket.status)}</span>
          </div>
        </button>`
        )
        .join("")
    : `
      <div class="empty-state" style="min-height:260px">
        <h3>没有符合条件的工单</h3>
        <p>切换筛选条件后重新查看。</p>
      </div>`;
}

function selectedTicket() {
  return state.data?.tickets.find((ticket) => ticket.id === state.selectedTicketId);
}

function renderTicketDetail() {
  const container = document.getElementById("ticket-detail");
  const ticket = selectedTicket();
  if (!ticket) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-illustration">
          <svg viewBox="0 0 64 64"><path d="M13 17h38v32H13z"/><path d="M21 25h22M21 33h16M21 41h10"/><circle cx="48" cy="15" r="8"/><path d="M45 15h6M48 12v6"/></svg>
        </div>
        <h3>选择一张工单开始</h3>
        <p>系统会依次完成意图识别、订单核验、政策检索、草稿生成和风险审阅。</p>
      </div>`;
    return;
  }

  container.innerHTML = `
    <div class="detail-content">
      <header class="detail-header">
        <div class="detail-person">
          <span class="customer-avatar">${escapeHtml(ticket.customer.slice(0, 1))}</span>
          <div>
            <h3>${escapeHtml(ticket.customer)} · ${escapeHtml(ticket.id)}</h3>
            <span>${escapeHtml(ticket.channel)} · ${escapeHtml(ticket.created_at)} · ${escapeHtml(ticket.status)}</span>
          </div>
        </div>
        <div class="detail-actions">
          <span class="priority-badge ${priorityClass(ticket.priority)}">${escapeHtml(ticket.priority)}优先级</span>
          <button class="secondary-button run-button" id="run-ticket" ${state.processing ? "disabled" : ""}>
            <svg viewBox="0 0 20 20" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
              <path d="m8 5 6 5-6 5z"/>
            </svg>
            ${ticket.result ? "重新运行" : "运行 AI 辅助"}
          </button>
        </div>
      </header>
      <div class="detail-body">
        <div class="message-block">
          <label>客户原始消息</label>
          <p>${escapeHtml(ticket.message)}</p>
        </div>
        ${state.processing ? processingHtml() : ticket.result ? resultHtml(ticket.result) : runEmptyHtml(ticket)}
      </div>
    </div>`;
}

function runEmptyHtml(ticket) {
  return `
    <div class="run-empty">
      <div>
        <h4>这张工单还没有运行辅助流程</h4>
        <p>订单 ${escapeHtml(ticket.order_id)} 已关联。运行后将展示判断依据、建议草稿和风险结论，不会自动对客发送。</p>
      </div>
      <button class="primary-button" id="run-ticket-inline">
        开始处理
        <svg viewBox="0 0 20 20"><path d="M4 10h11m-4-4 4 4-4 4"/></svg>
      </button>
    </div>`;
}

function processingHtml() {
  return `
    <div class="processing-wrap">
      <div class="processing-head">
        <span class="processing-spinner"></span>
        <div>
          <strong>正在执行五步工作流</strong>
          <span>读取订单事实、检索政策并检查高风险边界</span>
        </div>
      </div>
      <div class="processing-steps" aria-label="处理进度">
        ${Array.from({ length: 5 }, () => `<div class="processing-step"><i></i></div>`).join("")}
      </div>
    </div>`;
}

function resultHtml(result) {
  const isRisk = result.risk.requires_review;
  const confidencePercent = Math.round(result.confidence * 100);
  const riskReasons = result.risk.reasons.length
    ? result.risk.reasons.join("；")
    : "未命中高风险规则";
  return `
    <div class="result-banner ${isRisk ? "risk" : ""}">
      <span class="result-banner-icon">
        ${
          isRisk
            ? `<svg viewBox="0 0 20 20"><path d="M10 2.5 18 16.5H2z"/><path d="M10 7v4.5M10 14v.2"/></svg>`
            : `<svg viewBox="0 0 20 20"><path d="M10 2.5 17 6v4.3c0 4.2-3 6.3-7 7.2-4-.9-7-3-7-7.2V6z"/><path d="m7.3 10 1.7 1.7 3.8-3.8"/></svg>`
        }
      </span>
      <div>
        <strong>${escapeHtml(result.decision)}</strong>
        <span>${escapeHtml(result.guardrail)}</span>
      </div>
      <span class="soft-badge">${escapeHtml(result.generation_mode)} · ${result.elapsed_ms}ms</span>
    </div>

    <section class="result-section">
      <div class="result-section-title">
        <h4>判断与事实</h4>
        <span>${result.steps.length} 个步骤完成</span>
      </div>
      <div class="intent-result">
        <div class="intent-card">
          <div class="intent-card-top">
            <span class="intent-pill">${escapeHtml(result.intent_label)}</span>
            <span class="confidence">置信度 ${confidencePercent}%</span>
          </div>
          <div class="confidence-track"><i style="width:${confidencePercent}%"></i></div>
          <p>命中信号：${escapeHtml(result.matched_keywords.join("、") || "未命中明确关键词，按兜底路径处理")}</p>
        </div>
        <div class="order-card">
          <dl>
            <dt>订单号</dt><dd>${escapeHtml(result.order.order_id)}</dd>
            <dt>商品</dt><dd>${escapeHtml(result.order.items)}</dd>
            <dt>订单状态</dt><dd>${escapeHtml(result.order.status)}</dd>
            <dt>当前轨迹</dt><dd>${escapeHtml(result.order.logistics)}</dd>
          </dl>
        </div>
      </div>
    </section>

    <section class="result-section">
      <div class="result-section-title">
        <h4>政策依据</h4>
        <span>BM25 检索 + 意图映射</span>
      </div>
      <div class="policy-cards">
        ${result.policies
          .map(
            (policy) => `
          <article class="policy-card">
            <header>
              <strong>${escapeHtml(policy.title)}</strong>
              <span class="policy-code">${escapeHtml(policy.id)}</span>
            </header>
            <p>${escapeHtml(policy.content)}</p>
            <span class="policy-section">${escapeHtml(policy.section)} · 相关性分 ${policy.score}</span>
          </article>`
          )
          .join("")}
      </div>
    </section>

    <section class="result-section">
      <div class="result-section-title">
        <h4>建议客服草稿</h4>
        <span>可直接编辑，不会自动发送</span>
      </div>
      <div class="draft-card">
        <textarea id="draft-text" aria-label="建议客服草稿">${escapeHtml(result.draft)}</textarea>
        <div class="draft-footer">
          <span class="guardrail">
            <svg viewBox="0 0 20 20"><path d="M10 2.5 17 6v4.3c0 4.2-3 6.3-7 7.2-4-.9-7-3-7-7.2V6z"/><path d="m7.3 10 1.7 1.7 3.8-3.8"/></svg>
            ${isRisk ? escapeHtml(riskReasons) : "事实约束检查通过"}
          </span>
          <span id="draft-count">${result.draft.length} 字</span>
        </div>
      </div>
    </section>

    <div class="result-actions">
      <button class="secondary-button" id="handoff-ticket">转人工审核</button>
      <button class="primary-button" id="adopt-ticket" ${isRisk ? "disabled title='高风险工单须先人工审核'" : ""}>
        ${isRisk ? "等待人工审核" : "采纳草稿"}
      </button>
    </div>`;
}

async function runSelectedTicket() {
  const ticket = selectedTicket();
  if (!ticket || state.processing) return;
  state.processing = true;
  renderTicketDetail();
  try {
    const [response] = await Promise.all([
      api("/api/process", {
        method: "POST",
        body: JSON.stringify({ ticket_id: ticket.id, use_llm: false }),
      }),
      sleep(850),
    ]);
    ticket.result = response.result;
    ticket.status = response.ticket.status;
    state.data.dashboard = {
      ...state.data.dashboard,
      ...response.dashboard,
    };
    showToast(
      response.result.risk.requires_review
        ? "高风险工单已停止自动化流程，并标记为转人工"
        : "草稿已生成，等待客服确认"
    );
  } catch (error) {
    showToast(`处理失败：${error.message}`);
  } finally {
    state.processing = false;
    renderAll();
  }
}

async function ticketAction(action) {
  const ticket = selectedTicket();
  if (!ticket) return;
  try {
    const response = await api("/api/action", {
      method: "POST",
      body: JSON.stringify({ ticket_id: ticket.id, action }),
    });
    ticket.status = response.ticket.status;
    state.data.dashboard = { ...state.data.dashboard, ...response.dashboard };
    showToast(action === "adopt" ? "草稿已采纳，记录已归档" : "工单已转人工审核");
    renderAll();
  } catch (error) {
    showToast(`操作失败：${error.message}`);
  }
}

function renderEvaluation() {
  if (!state.evaluation) return;
  const evaluation = state.evaluation;
  const best = [...evaluation.methods].sort(
    (a, b) => b.task_success_rate - a.task_success_rate
  )[0];
  document.getElementById("eval-total").textContent = evaluation.dataset.total;
  document.getElementById("eval-risk-cases").textContent = evaluation.dataset.risk_cases;
  document.getElementById("eval-best").textContent = best.name;
  document.getElementById("eval-critical").textContent = `${best.critical_error_rate}%`;

  document.getElementById("method-bars").innerHTML = evaluation.methods
    .map(
      (method) => `
      <div class="method-bar-row">
        <div class="method-bar-label">
          <strong>${escapeHtml(method.name)}</strong>
          <span>${escapeHtml(method.description)}</span>
        </div>
        <div class="bar-track"><i data-eval-bar="${method.task_success_rate}" style="width:0"></i></div>
        <span class="method-bar-value">${method.task_success_rate}%</span>
      </div>`
    )
    .join("");

  document.getElementById("comparison-grid").innerHTML = evaluation.methods
    .map(
      (method) => `
      <article class="comparison-method">
        <h4>${escapeHtml(method.name)}</h4>
        <dl>
          <dt>意图准确率</dt><dd>${method.intent_accuracy}%</dd>
          <dt>政策覆盖</dt><dd>${method.policy_coverage}%</dd>
          <dt>风险判断准确</dt><dd>${method.risk_accuracy}%</dd>
          <dt>关键错误率</dt><dd>${method.critical_error_rate}%</dd>
          <dt>平均政策数</dt><dd>${method.avg_policies}</dd>
          <dt>估算 Token</dt><dd>${method.avg_tokens}</dd>
        </dl>
      </article>`
    )
    .join("");

  document.getElementById("intent-breakdown").innerHTML = evaluation.per_intent
    .map(
      (item) => `
      <div class="intent-row">
        <span>${escapeHtml(item.label)}</span>
        <div class="bar-track"><i style="width:${item.workflow_success_rate}%;background:var(--brand)"></i></div>
        <span>${item.workflow_success_rate}%</span>
      </div>`
    )
    .join("");
}

function animateEvaluationBars() {
  requestAnimationFrame(() => {
    document.querySelectorAll("[data-eval-bar]").forEach((bar) => {
      bar.style.width = `${bar.dataset.evalBar}%`;
    });
  });
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2600);
}

async function resetDemo() {
  try {
    await api("/api/reset", { method: "POST", body: "{}" });
    state.selectedTicketId = null;
    state.processing = false;
    const [bootstrap, evaluation] = await Promise.all([
      api("/api/bootstrap"),
      api("/api/evaluation"),
    ]);
    state.data = bootstrap;
    state.evaluation = evaluation;
    showToast("演示数据已重置");
    renderAll();
  } catch (error) {
    showToast(`重置失败：${error.message}`);
  }
}

document.addEventListener("click", async (event) => {
  const navButton = event.target.closest(".nav-item");
  if (navButton) {
    switchView(navButton.dataset.view);
    return;
  }

  if (event.target.closest("#hero-start") || event.target.closest("[data-go-tickets]")) {
    switchView("tickets");
    const firstPending = state.data?.tickets.find((ticket) =>
      ["待处理", "待确认"].includes(ticket.status)
    );
    if (!state.selectedTicketId && firstPending) {
      state.selectedTicketId = firstPending.id;
      renderTicketList();
      renderTicketDetail();
    }
    return;
  }

  if (event.target.closest("[data-go-evaluation]")) {
    switchView("evaluation");
    return;
  }

  const miniTicket = event.target.closest("[data-open-ticket]");
  if (miniTicket) {
    state.selectedTicketId = miniTicket.dataset.openTicket;
    switchView("tickets");
    renderTicketList();
    renderTicketDetail();
    return;
  }

  const ticketRow = event.target.closest("[data-ticket-id]");
  if (ticketRow) {
    state.selectedTicketId = ticketRow.dataset.ticketId;
    state.processing = false;
    renderTicketList();
    renderTicketDetail();
    return;
  }

  const filterButton = event.target.closest("[data-filter]");
  if (filterButton) {
    state.filter = filterButton.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((button) => {
      button.classList.toggle("active", button === filterButton);
    });
    renderTicketList();
    return;
  }

  if (event.target.closest("#run-ticket") || event.target.closest("#run-ticket-inline")) {
    await runSelectedTicket();
    return;
  }

  if (event.target.closest("#adopt-ticket")) {
    await ticketAction("adopt");
    return;
  }

  if (event.target.closest("#handoff-ticket")) {
    await ticketAction("handoff");
    return;
  }

  if (event.target.closest("#reset-demo")) {
    await resetDemo();
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "draft-text") {
    const count = document.getElementById("draft-count");
    if (count) count.textContent = `${event.target.value.length} 字`;
  }
});

load();
