import { mobileApi } from "/mobile/assets/api.js";

const appRoot = document.getElementById("app");
const toastRoot = document.getElementById("toast-root");
const modalRoot = document.getElementById("modal-root");

const SESSION_POLL_INTERVAL_MS = 15000;
const PAGE_POLL_INTERVAL_MS = 12000;
const POLL_ERROR_COOLDOWN_MS = 15000;

const state = {
  route: null,
  pollHandle: null,
  pageDrafts: new Map(),
  currentSessionData: null,
  currentBlockPagesData: null,
  currentPageData: null,
  focusLineId: null,
  modal: null,
  lastPollErrorAt: 0,
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function htmlToElement(markup) {
  const template = document.createElement("template");
  template.innerHTML = markup.trim();
  return template.content.firstElementChild;
}

function parseRoute(pathname) {
  const cleanPath = pathname.replace(/\/+$/, "") || "/";
  if (cleanPath === "/mobile") {
    return { name: "home" };
  }
  if (cleanPath === "/mobile/blocks") {
    return { name: "blocks" };
  }
  const blockMatch = cleanPath.match(/^\/mobile\/block\/([^/]+)\/pages$/);
  if (blockMatch) {
    return { name: "block-pages", blockId: decodeURIComponent(blockMatch[1]) };
  }
  const pageMatch = cleanPath.match(/^\/mobile\/page\/([^/]+)$/);
  if (pageMatch) {
    return { name: "page", pageId: decodeURIComponent(pageMatch[1]) };
  }
  return { name: "not-found" };
}

function navigate(path, options = {}) {
  const targetRoute = parseRoute(path);
  if (!options.replace && window.location.pathname !== path) {
    window.history.pushState({}, "", path);
  } else if (options.replace) {
    window.history.replaceState({}, "", path);
  }
  if (state.route?.name !== "page" || targetRoute.name !== "page" || state.route.pageId !== targetRoute.pageId) {
    state.pageDrafts.clear();
  }
  state.modal = null;
  state.focusLineId = null;
  renderRoute(targetRoute, { silent: false });
}

function humanDateTime(value) {
  if (!value) {
    return "--";
  }
  try {
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(value));
  } catch (error) {
    return value;
  }
}

function statusTone(status, locked = false) {
  if (locked) {
    return "locked";
  }
  if (status === "waiting_publish") {
    return "waiting";
  }
  return status || "empty";
}

function statusLabel(status, locked = false) {
  if (locked) {
    return "Travada";
  }
  if (status === "complete") {
    return "Concluida";
  }
  if (status === "pending") {
    return "Pendente";
  }
  if (status === "waiting_publish") {
    return "No desktop";
  }
  return "Sem valores";
}

function progressPercent(filled, total) {
  if (!total) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((filled / total) * 100)));
}

function remainingValues(filled, total) {
  return Math.max(0, total - filled);
}

function countLabel(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function renderSummaryPill(label, value, tone = "neutral") {
  return `
    <div class="summary-pill summary-pill--compact" data-tone="${tone}">
      <span class="summary-label">${escapeHtml(label)}</span>
      <span class="summary-value">${escapeHtml(value)}</span>
    </div>
  `;
}

function renderContextHeadline(label, value) {
  return `
    <div class="context-headline">
      <span class="context-label">${escapeHtml(label)}</span>
      <strong class="context-value">${escapeHtml(value)}</strong>
    </div>
  `;
}

function renderProgress(filled, total, label = "Valores preenchidos") {
  const remaining = remainingValues(filled, total);
  const helperText = !total
    ? "Sem valores disponiveis"
    : remaining === 0
      ? "Tudo preenchido"
      : `Faltam ${remaining}`;
  return `
    <div class="progress-block">
      <div class="progress-label">
        <span>${escapeHtml(label)}</span>
        <strong>${filled}/${total}</strong>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${progressPercent(filled, total)}%"></div>
      </div>
      <p class="progress-caption">${escapeHtml(helperText)}</p>
    </div>
  `;
}

function lineStatusMeta(line) {
  if (line.status === "filled") {
    return { tone: "complete", label: "Lancado" };
  }
  if (line.status === "pending") {
    return { tone: "pending", label: "Pendente" };
  }
  return { tone: "invalid", label: "Revisar" };
}

function isLineActive(line) {
  return state.focusLineId === line.line_id;
}

function showToast(message, tone = "info") {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.dataset.tone = tone;
  toast.textContent = message;
  toastRoot.appendChild(toast);
  window.setTimeout(() => {
    toast.remove();
  }, 3000);
}

function renderTopbar(title, subtitle, options = {}) {
  const backButton = options.backAction
    ? `<button type="button" class="ghost-button ghost-button--compact topbar-button" data-action="${options.backAction}">${escapeHtml(options.backLabel || "Voltar")}</button>`
    : "";
  const trailingButton = options.trailingAction
    ? `<button type="button" class="ghost-button ghost-button--compact topbar-button" data-action="${options.trailingAction}">${escapeHtml(options.trailingLabel || "Atualizar")}</button>`
    : "";
  return `
    <div class="topbar">
      ${backButton}
      <div class="topbar-title">
        <p class="eyebrow">${escapeHtml(options.eyebrow || "Conferix mobile")}</p>
        <h1 class="title">${escapeHtml(title)}</h1>
        ${subtitle ? `<p class="subtitle">${escapeHtml(subtitle)}</p>` : ""}
      </div>
      ${trailingButton ? `<div class="toolbar-spacer"></div>${trailingButton}` : ""}
    </div>
  `;
}

function lineBadgeMarkup(line) {
  const meta = lineStatusMeta(line);
  return `<span class="status-badge status-badge--compact line-badge" data-tone="${meta.tone}">${meta.label}</span>`;
}

function lineNote(line, page) {
  if (line.error_message) {
    return line.error_message;
  }
  if (!line.editable) {
    return page.lock_message || "Linha travada no celular.";
  }
  return "";
}

function getDraftValue(line) {
  const draft = state.pageDrafts.get(line.line_id);
  if (draft) {
    return draft.value;
  }
  return line.value_display || "";
}

function lineSignature(line, page) {
  return JSON.stringify([
    line.bet,
    line.value_display,
    line.placeholder,
    line.pending,
    line.editable,
    line.status,
    line.error_message,
    page.locked,
    page.lock_message,
  ]);
}

function renderBlockCard(block) {
  const tone = statusTone(block.status, block.money_locked);
  const helperText = block.money_locked
    ? "Travado para lancamento no celular."
    : block.status === "complete"
      ? "Bloco concluido."
      : block.status === "pending"
        ? "Toque para abrir as paginas pendentes."
        : "Sem valores para lancar.";
  return `
    <article
      class="card clickable card--summary"
      data-tone="${escapeHtml(tone)}"
      data-action="open-block"
      data-block-id="${escapeHtml(block.block_id)}"
      data-key="${escapeHtml(block.block_id)}"
      data-revision="${escapeHtml(block.block_revision)}"
      tabindex="0"
    >
      <div class="card-head">
        <div class="card-main">
          ${renderContextHeadline("Bloco", block.number)}
          <p class="card-copy">${countLabel(block.page_count, "pagina", "paginas")} - ${countLabel(block.pending_pages, "pendente", "pendentes")}</p>
        </div>
        <span class="status-badge status-badge--compact" data-tone="${escapeHtml(tone)}">${escapeHtml(statusLabel(block.status, block.money_locked))}</span>
      </div>
      <div class="summary-grid summary-grid--compact summary-grid--cards">
        ${renderSummaryPill("Paginas", block.page_count, "neutral")}
        ${renderSummaryPill("Faltam", remainingValues(block.filled_values, block.total_values), block.pending_pages ? "warning" : "complete")}
        ${renderSummaryPill("Valores", `${block.filled_values}/${block.total_values}`, tone === "complete" ? "complete" : tone === "locked" ? "locked" : "neutral")}
      </div>
      ${renderProgress(block.filled_values, block.total_values, "Progresso do bloco")}
      <p class="section-hint">${escapeHtml(helperText)}</p>
    </article>
  `;
}

function renderPageCard(page) {
  const tone = statusTone(page.status, page.locked);
  const helperText = page.locked
    ? "Pagina travada no celular."
    : page.status === "complete"
      ? "Pagina pronta."
      : page.status === "pending"
        ? "Toque para preencher os valores."
        : "Sem linhas para preencher.";
  return `
    <article
      class="card clickable card--summary"
      data-tone="${escapeHtml(tone)}"
      data-action="open-page"
      data-page-id="${escapeHtml(page.page_id)}"
      data-key="${escapeHtml(page.page_id)}"
      data-revision="${escapeHtml(page.page_revision)}"
      tabindex="0"
    >
      <div class="card-head">
        <div class="card-main">
          ${renderContextHeadline("Pagina", page.number)}
          <p class="card-copy">${countLabel(page.bet_count, "aposta", "apostas")} - ${countLabel(page.pending_values, "valor faltando", "valores faltando")}</p>
        </div>
        <span class="status-badge status-badge--compact" data-tone="${escapeHtml(tone)}">${escapeHtml(statusLabel(page.status, page.locked))}</span>
      </div>
      <div class="summary-grid summary-grid--compact summary-grid--cards">
        ${renderSummaryPill("Apostas", page.bet_count, "neutral")}
        ${renderSummaryPill("Faltam", remainingValues(page.filled_values, page.total_values), page.pending_values ? "warning" : "complete")}
        ${renderSummaryPill("Valores", `${page.filled_values}/${page.total_values}`, tone === "complete" ? "complete" : tone === "locked" ? "locked" : "neutral")}
      </div>
      ${renderProgress(page.filled_values, page.total_values, "Progresso da pagina")}
      <p class="section-hint">${escapeHtml(page.warning || helperText)}</p>
    </article>
  `;
}

function renderPageHeaderMarkup(payload) {
  const page = payload.page;
  const tone = statusTone(page.status, page.locked);
  const actionHint = page.locked
    ? page.warning || "Esta pagina esta travada para lancamento no celular."
    : page.pending_values > 0
      ? "Proxima acao: preencha a linha destacada e toque em OK."
      : "Pagina concluida. Voce pode seguir para a proxima.";
  return `
    <article class="hero-card hero-card--compact hero-card--page" data-section="page-hero" data-tone="${escapeHtml(tone)}">
      <div class="hero-row hero-row--compact">
        <div class="hero-main">
          <div class="hero-context">
            ${renderContextHeadline("Bloco", payload.block.number)}
            ${renderContextHeadline("Pag.", page.number)}
          </div>
          <p class="subtitle subtitle--compact">${countLabel(page.bet_count, "aposta", "apostas")} nesta pagina</p>
        </div>
        <span class="status-badge status-badge--compact" data-tone="${escapeHtml(tone)}">${escapeHtml(statusLabel(page.status, page.locked))}</span>
      </div>
      <div class="summary-grid summary-grid--compact summary-grid--page">
        ${renderSummaryPill("Preenchidos", `${page.filled_values}/${page.total_values}`, "neutral")}
        ${renderSummaryPill("Faltam", remainingValues(page.filled_values, page.total_values), page.pending_values ? "warning" : "complete")}
        ${renderSummaryPill("Status", statusLabel(page.status, page.locked), tone)}
      </div>
      ${renderProgress(page.filled_values, page.total_values, "Progresso da pagina")}
      <p class="section-hint ${page.locked ? "danger-copy" : ""}">${escapeHtml(actionHint)}</p>
      <div class="page-actions page-actions--compact">
        <button
          type="button"
          class="ghost-button ghost-button--compact"
          data-action="open-fill-modal"
          ${!page.can_edit_values || page.pending_values === 0 ? "disabled" : ""}
        >
          Preencher pagina
        </button>
        ${
          page.status === "complete"
            ? `<button type="button" class="ghost-button ghost-button--compact" data-action="goto-next-pending">Proxima pendente</button>`
            : ""
        }
      </div>
    </article>
  `;
}

function renderLineCardMarkup(line, page) {
  const value = getDraftValue(line);
  const placeholder = !value ? line.placeholder : "";
  const signature = lineSignature(line, page);
  const note = lineNote(line, page);
  const active = isLineActive(line) && line.editable;
  return `
    <article
      class="line-card"
      data-line-id="${escapeHtml(line.line_id)}"
      data-status="${escapeHtml(line.status)}"
      data-active="${active ? "true" : "false"}"
      data-signature="${escapeHtml(signature)}"
    >
      <div class="line-row">
        <div class="line-main">
          <span class="line-order">${line.order}</span>
          <div class="line-bet">
            <div class="line-head">
              <strong>${escapeHtml(line.bet)}</strong>
              ${lineBadgeMarkup(line)}
            </div>
            ${note ? `<p class="line-note ${line.error_message ? "danger-copy" : !line.editable ? "warning-copy" : ""}">${escapeHtml(note)}</p>` : ""}
          </div>
        </div>
        <div class="line-entry">
          ${
            line.editable
              ? `
                <label class="sr-only" for="value-${escapeHtml(line.line_id)}">Valor da linha ${line.order}</label>
                <input
                  id="value-${escapeHtml(line.line_id)}"
                  class="value-input value-input--compact"
                  type="text"
                  inputmode="decimal"
                  enterkeyhint="next"
                  autocomplete="off"
                  spellcheck="false"
                  data-line-id="${escapeHtml(line.line_id)}"
                  data-saved-value="${escapeHtml(line.value_display || "")}"
                  value="${escapeHtml(value)}"
                  placeholder="${escapeHtml(placeholder)}"
                >
                <button type="button" class="ok-button ok-button--compact" data-action="save-line" data-line-id="${escapeHtml(line.line_id)}">OK</button>
              `
              : `<span class="line-readonly">${escapeHtml(note || "Linha nao editavel no mobile.")}</span>`
          }
        </div>
      </div>
    </article>
  `;
}

function renderHomeScreen(payload) {
  const session = payload.session;
  const disabled = session.blocks_count === 0;
  const homeHint = session.status === "waiting_publish"
    ? "Aguarde a publicacao do proximo bloco no desktop."
    : disabled
      ? "Sem valores disponiveis no celular agora."
      : "Proximo passo: toque em Blocos e abra o primeiro pendente.";
  const stateMarkup = session.status === "waiting_publish"
    ? `
      <article class="empty-card" data-section="session-state">
        <h3>Bloco atual ainda no desktop</h3>
        <p class="muted-copy">O bloco em digitacao no PC aparece aqui quando o proximo bloco for aberto.</p>
      </article>
    `
    : disabled
      ? `
        <article class="empty-card" data-section="session-state">
          <h3>Nenhum valor para lancar agora</h3>
          <p class="muted-copy">Abra ou crie uma sessao no desktop para liberar blocos no celular.</p>
        </article>
      `
      : `
        <article class="card card--compact" data-section="session-state">
          <div class="card-head">
            <div class="card-main">
              <h3 class="card-title">O que precisa de atencao</h3>
              <p class="card-copy">${countLabel(session.pending_blocks, "bloco pendente", "blocos pendentes")} - ${countLabel(session.pending_pages, "pagina aberta", "paginas abertas")}</p>
            </div>
          </div>
          ${session.draft_block_hidden ? `<p class="muted-copy">O bloco em digitacao no desktop continua oculto para manter o mobile estavel.</p>` : `<p class="section-hint">Abra os blocos e siga pela primeira pagina pendente.</p>`}
        </article>
      `;
  return `
    <section class="screen screen-session" data-screen="home" data-revision="${escapeHtml(session.session_revision)}">
      ${renderTopbar("Sessao ativa", session.updated_at ? `Atualizada ${humanDateTime(session.updated_at)}` : "Sem sincronizacao recente", {
        trailingAction: "refresh-route",
        trailingLabel: "Atualizar",
      })}
      <article class="hero-card hero-card--compact" data-section="hero" data-tone="${escapeHtml(statusTone(session.status))}">
        <div class="hero-row hero-row--compact">
          <div class="hero-main">
            <p class="eyebrow">Sessao</p>
            <h2 class="title title--compact">${escapeHtml(session.name)}</h2>
            <p class="subtitle subtitle--compact">Lance valores no celular. Estrutura e revisoes continuam no desktop.</p>
          </div>
          <span class="status-badge status-badge--compact" data-tone="${statusTone(session.status)}">${escapeHtml(statusLabel(session.status))}</span>
        </div>
        <div class="summary-grid summary-grid--compact">
          ${renderSummaryPill("Blocos", session.blocks_count, "neutral")}
          ${renderSummaryPill("Paginas", session.page_count, "neutral")}
          ${renderSummaryPill("Faltam", remainingValues(session.filled_values, session.total_values), session.pending_pages ? "warning" : "complete")}
        </div>
        <div data-field="session-progress">${renderProgress(session.filled_values, session.total_values, "Progresso geral")}</div>
        <p class="section-hint">${escapeHtml(homeHint)}</p>
        <div class="cta-row">
          <button type="button" class="primary-button primary-button--compact" data-action="go-blocks" ${disabled ? "disabled" : ""}>Abrir blocos</button>
        </div>
      </article>
      ${stateMarkup}
    </section>
  `;
}

function renderBlocksScreen(payload) {
  const session = payload.session;
  const emptyMarkup = session.status === "waiting_publish"
    ? `
      <article class="empty-card">
        <h2>Bloco atual ainda nao publicado</h2>
        <p class="muted-copy">O mobile so recebe blocos consolidados. Assim que um novo bloco comecar no desktop, o anterior aparece aqui.</p>
      </article>
    `
    : `
      <article class="empty-card">
        <h2>Sem blocos publicados</h2>
        <p class="muted-copy">Ainda nao ha blocos disponiveis para lancamento no mobile.</p>
      </article>
    `;
  return `
    <section class="screen screen-blocks" data-screen="blocks" data-revision="${escapeHtml(session.session_revision)}">
      ${renderTopbar("Blocos", `${escapeHtml(session.name)} - ${humanDateTime(session.updated_at)}`, {
        backAction: "go-home",
        trailingAction: "refresh-route",
        trailingLabel: "Atualizar",
      })}
      <article class="hero-card hero-card--compact" data-tone="${escapeHtml(statusTone(session.status))}">
        <div class="hero-row hero-row--compact">
          <div class="hero-main">
            <p class="eyebrow">Blocos publicados</p>
            <h2 class="title title--compact">${countLabel(session.blocks_count, "bloco", "blocos")}</h2>
            <p class="subtitle subtitle--compact">${countLabel(session.pending_blocks, "bloco com pendencia", "blocos com pendencia")}</p>
          </div>
          <span class="status-badge status-badge--compact" data-tone="${statusTone(session.status)}">${escapeHtml(statusLabel(session.status))}</span>
        </div>
        <div class="summary-grid summary-grid--compact">
          ${renderSummaryPill("Paginas", session.page_count, "neutral")}
          ${renderSummaryPill("Faltam", remainingValues(session.filled_values, session.total_values), session.pending_pages ? "warning" : "complete")}
          ${renderSummaryPill("Progresso", `${session.filled_values}/${session.total_values}`, "neutral")}
        </div>
        ${renderProgress(session.filled_values, session.total_values, "Progresso dos blocos")}
        <p class="section-hint">${session.draft_block_hidden ? "O bloco em digitacao no desktop continua oculto para evitar confusao." : "Toque no bloco que estiver pendente para seguir."}</p>
      </article>
      ${
        payload.blocks.length
          ? `<div class="card-list" data-layout="double" data-list="blocks">${payload.blocks.map(renderBlockCard).join("")}</div>`
          : emptyMarkup
      }
    </section>
  `;
}

function renderBlockPagesScreen(payload) {
  const block = payload.block;
  const tone = statusTone(block.status, block.money_locked);
  return `
    <section class="screen screen-pages" data-screen="block-pages" data-block-id="${escapeHtml(block.block_id)}" data-revision="${escapeHtml(block.block_revision)}">
      ${renderTopbar("Paginas do bloco", `${payload.session_name} - ${humanDateTime(payload.session_updated_at)}`, {
        backAction: "go-blocks",
        trailingAction: "refresh-route",
        trailingLabel: "Atualizar",
      })}
      <article class="hero-card hero-card--compact" data-tone="${escapeHtml(tone)}">
        <div class="hero-row hero-row--compact">
          <div class="hero-main">
            ${renderContextHeadline("Bloco", block.number)}
            <p class="subtitle subtitle--compact">${countLabel(block.page_count, "pagina", "paginas")} - ${countLabel(block.pending_pages, "pendente", "pendentes")}</p>
          </div>
          <span class="status-badge status-badge--compact" data-tone="${escapeHtml(tone)}">${escapeHtml(statusLabel(block.status, block.money_locked))}</span>
        </div>
        <div class="summary-grid summary-grid--compact">
          ${renderSummaryPill("Paginas", block.page_count, "neutral")}
          ${renderSummaryPill("Faltam", remainingValues(block.filled_values, block.total_values), block.pending_pages ? "warning" : "complete")}
          ${renderSummaryPill("Valores", `${block.filled_values}/${block.total_values}`, "neutral")}
        </div>
        ${renderProgress(block.filled_values, block.total_values, "Progresso do bloco")}
        <p class="section-hint">${block.money_locked ? "Bloco travado para lancamento no celular." : "Escolha a pagina pendente para continuar."}</p>
      </article>
      ${
        payload.pages.length
          ? `<div class="card-list" data-list="pages">${payload.pages.map(renderPageCard).join("")}</div>`
          : `
            <article class="empty-card">
              <h2>Sem paginas operacionais</h2>
              <p class="muted-copy">Este bloco ainda nao possui paginas disponiveis para o mobile.</p>
            </article>
          `
      }
    </section>
  `;
}

function renderPageScreen(payload) {
  const firstPendingLineId = findNextPendingLineId(payload.lines, null);
  if (!state.focusLineId && firstPendingLineId) {
    state.focusLineId = firstPendingLineId;
  }
  return `
    <section
      class="screen screen-page"
      data-screen="page"
      data-page-id="${escapeHtml(payload.page.page_id)}"
      data-page-revision="${escapeHtml(payload.page.page_revision)}"
      data-block-revision="${escapeHtml(payload.block.block_revision)}"
    >
      ${renderTopbar("Lancar valores", `${payload.session_name} - ${humanDateTime(payload.session_updated_at)}`, {
        backAction: "go-block-pages",
        trailingAction: "refresh-route",
        trailingLabel: "Atualizar",
      })}
      <section class="page-header" data-section="page-header">
        ${renderPageHeaderMarkup(payload)}
      </section>
      ${
        payload.lines.length
          ? `<div class="line-list" data-list="lines">${payload.lines.map((line) => renderLineCardMarkup(line, payload.page)).join("")}</div>`
          : `
            <article class="empty-card" data-empty="page-lines">
              <h2>Nenhuma linha visivel</h2>
              <p class="muted-copy">Esta pagina ainda nao possui apostas operacionais para o mobile.</p>
            </article>
          `
      }
    </section>
  `;
}

function patchKeyedCards(container, items, keyField, renderer, revisionField) {
  const existing = new Map(Array.from(container.children).map((element) => [element.dataset.key, element]));
  const seen = new Set();
  for (const item of items) {
    const key = String(item[keyField]);
    const revision = String(item[revisionField] || "");
    let element = existing.get(key);
    if (!element) {
      element = htmlToElement(renderer(item));
      container.appendChild(element);
    } else if (element.dataset.revision !== revision) {
      const replacement = htmlToElement(renderer(item));
      element.replaceWith(replacement);
      element = replacement;
    }
    element.dataset.key = key;
    element.dataset.revision = revision;
    container.appendChild(element);
    seen.add(key);
  }
  for (const [key, element] of existing.entries()) {
    if (!seen.has(key)) {
      element.remove();
    }
  }
}

function ensureScreen(screenName, markup) {
  const current = appRoot.querySelector("[data-screen]");
  if (!current || current.dataset.screen !== screenName) {
    appRoot.innerHTML = markup;
    return appRoot.querySelector("[data-screen]");
  }
  return current;
}

function patchHomeScreen(payload) {
  const session = payload.session;
  const screen = ensureScreen("home", renderHomeScreen(payload));
  if (!screen || screen.dataset.revision === session.session_revision) {
    return;
  }
  screen.replaceWith(htmlToElement(renderHomeScreen(payload)));
}

function patchBlocksScreen(payload) {
  const session = payload.session;
  const screen = ensureScreen("blocks", renderBlocksScreen(payload));
  if (!screen || screen.dataset.revision === session.session_revision) {
    return;
  }
  screen.dataset.revision = session.session_revision;
  const topbarSubtitle = screen.querySelector(".subtitle");
  if (topbarSubtitle) {
    topbarSubtitle.textContent = `${session.name} - ${humanDateTime(session.updated_at)}`;
  }
  const hero = screen.querySelector(".hero-card");
  if (hero) {
    hero.replaceWith(htmlToElement(renderBlocksScreen(payload)).querySelector(".hero-card"));
  }
  const existingList = screen.querySelector('[data-list="blocks"]');
  const emptyCard = screen.querySelector(".empty-card");
  if (!payload.blocks.length) {
    if (existingList) {
      existingList.remove();
    }
    const nextEmpty = htmlToElement(renderBlocksScreen(payload)).querySelector(".empty-card");
    if (emptyCard) {
      emptyCard.replaceWith(nextEmpty);
    } else if (nextEmpty) {
      screen.appendChild(nextEmpty);
    }
    return;
  }
  if (emptyCard) {
    emptyCard.remove();
  }
  const list = existingList || htmlToElement('<div class="card-list" data-layout="double" data-list="blocks"></div>');
  if (!existingList) {
    screen.appendChild(list);
  }
  patchKeyedCards(list, payload.blocks, "block_id", renderBlockCard, "block_revision");
}

function patchBlockPagesScreen(payload) {
  const block = payload.block;
  const screen = ensureScreen("block-pages", renderBlockPagesScreen(payload));
  if (!screen || screen.dataset.revision === block.block_revision) {
    return;
  }
  screen.dataset.revision = block.block_revision;
  const topbarSubtitle = screen.querySelector(".subtitle");
  if (topbarSubtitle) {
    topbarSubtitle.textContent = `${payload.session_name} - ${humanDateTime(payload.session_updated_at)}`;
  }
  const hero = screen.querySelector(".hero-card");
  if (hero) {
    hero.replaceWith(htmlToElement(renderBlockPagesScreen(payload)).querySelector(".hero-card"));
  }
  const existingList = screen.querySelector('[data-list="pages"]');
  const emptyCard = screen.querySelector(".empty-card");
  if (!payload.pages.length) {
    if (existingList) {
      existingList.remove();
    }
    const nextEmpty = htmlToElement(renderBlockPagesScreen(payload)).querySelector(".empty-card");
    if (emptyCard) {
      emptyCard.replaceWith(nextEmpty);
    } else if (nextEmpty) {
      screen.appendChild(nextEmpty);
    }
    return;
  }
  if (emptyCard) {
    emptyCard.remove();
  }
  const list = existingList || htmlToElement('<div class="card-list" data-list="pages"></div>');
  if (!existingList) {
    screen.appendChild(list);
  }
  patchKeyedCards(list, payload.pages, "page_id", renderPageCard, "page_revision");
}

function patchLineElement(element, line, page) {
  const input = element.querySelector(".value-input");
  const isProtected = input && (document.activeElement === input || state.pageDrafts.has(line.line_id));
  const nextSignature = lineSignature(line, page);
  if (!isProtected && element.dataset.signature !== nextSignature) {
    const replacement = htmlToElement(renderLineCardMarkup(line, page));
    element.replaceWith(replacement);
    return replacement;
  }
  element.dataset.signature = nextSignature;
  element.dataset.status = line.status;
  element.dataset.active = isLineActive(line) && line.editable ? "true" : "false";
  const bet = element.querySelector(".line-bet strong");
  if (bet) {
    bet.textContent = line.bet;
  }
  const badge = element.querySelector(".line-badge");
  if (badge) {
    const meta = lineStatusMeta(line);
    badge.dataset.tone = meta.tone;
    badge.textContent = meta.label;
  }
  const note = element.querySelector(".line-note, .line-readonly");
  const nextNote = lineNote(line, page);
  if (note) {
    note.textContent = nextNote;
  }
  if (input) {
    const draft = state.pageDrafts.get(line.line_id);
    input.dataset.savedValue = line.value_display || "";
    input.placeholder = !draft?.value ? line.placeholder : "";
    if (!draft && document.activeElement !== input) {
      input.value = line.value_display || "";
    }
    input.disabled = !line.editable;
  }
  return element;
}

function patchPageLines(screen, payload) {
  let list = screen.querySelector('[data-list="lines"]');
  const emptyCard = screen.querySelector('[data-empty="page-lines"]');
  if (!payload.lines.length) {
    if (list) {
      list.remove();
    }
    if (!emptyCard) {
      screen.appendChild(
        htmlToElement(`
          <article class="empty-card" data-empty="page-lines">
            <h2>Nenhuma linha visivel</h2>
            <p class="muted-copy">Esta pagina ainda nao possui apostas operacionais para o mobile.</p>
          </article>
        `),
      );
    }
    return;
  }
  if (emptyCard) {
    emptyCard.remove();
  }
  if (!list) {
    list = htmlToElement('<div class="line-list" data-list="lines"></div>');
    screen.appendChild(list);
  }
  const existing = new Map(Array.from(list.children).map((element) => [element.dataset.lineId, element]));
  const seen = new Set();
  for (const line of payload.lines) {
    let element = existing.get(line.line_id);
    if (!element) {
      element = htmlToElement(renderLineCardMarkup(line, payload.page));
    } else {
      element = patchLineElement(element, line, payload.page);
    }
    list.appendChild(element);
    seen.add(line.line_id);
  }
  for (const [lineId, element] of existing.entries()) {
    if (!seen.has(lineId)) {
      element.remove();
    }
  }
}

function patchPageScreen(payload, options = {}) {
  const screen = ensureScreen("page", renderPageScreen(payload));
  if (!screen) {
    return;
  }
  const samePage =
    screen.dataset.pageId === payload.page.page_id &&
    screen.dataset.pageRevision === payload.page.page_revision &&
    screen.dataset.blockRevision === payload.block.block_revision;
  if (samePage && options.silent) {
    return;
  }
  screen.dataset.pageId = payload.page.page_id;
  screen.dataset.pageRevision = payload.page.page_revision;
  screen.dataset.blockRevision = payload.block.block_revision;
  const nextScreen = htmlToElement(renderPageScreen(payload));
  const nextTopbar = nextScreen.querySelector(".topbar");
  const currentTopbar = screen.querySelector(".topbar");
  if (nextTopbar && currentTopbar) {
    currentTopbar.replaceWith(nextTopbar);
  }
  const nextHeader = nextScreen.querySelector('[data-section="page-header"]');
  const currentHeader = screen.querySelector('[data-section="page-header"]');
  if (nextHeader && currentHeader) {
    currentHeader.replaceWith(nextHeader);
  }
  patchPageLines(screen, payload);
  syncActiveLineState(screen);
  renderModal();
  if (options.focusLineId) {
    focusLineInput(options.focusLineId, { smooth: options.smoothFocus });
  }
}

function renderErrorState(title, message, options = {}) {
  appRoot.innerHTML = `
    <section class="screen" data-screen="error">
      ${renderTopbar(title, options.subtitle || "", {
        backAction: options.backAction,
        trailingAction: "refresh-route",
        trailingLabel: "Tentar de novo",
      })}
      <article class="empty-card">
        <h2>${escapeHtml(title)}</h2>
        <p class="muted-copy">${escapeHtml(message)}</p>
        <div class="cta-row">
          ${options.primaryAction ? `<button type="button" class="primary-button primary-button--compact" data-action="${options.primaryAction.action}">${escapeHtml(options.primaryAction.label)}</button>` : ""}
        </div>
      </article>
    </section>
  `;
  renderModal();
}

function renderNotFound() {
  renderErrorState("Tela nao encontrada", "A rota solicitada nao existe na interface mobile.", {
    backAction: "go-home",
    primaryAction: { action: "go-home", label: "Voltar ao inicio" },
  });
}

function renderModal() {
  if (!state.modal || state.modal.type !== "fill-page") {
    modalRoot.innerHTML = "";
    return;
  }
  const page = state.modal.page;
  const block = state.modal.block;
  modalRoot.innerHTML = `
    <div class="modal-scrim">
      <form class="modal-card modal-card--compact" data-form="fill-page">
        <div>
          <p class="eyebrow">Preencher pagina</p>
          <h2 class="modal-title">Bloco ${escapeHtml(block.number)} - Pag. ${page.number}</h2>
          <p class="muted-copy">O valor sera aplicado somente nas linhas editaveis ainda pendentes desta pagina.</p>
        </div>
        <label class="sr-only" for="fill-page-input">Valor da pagina</label>
        <input id="fill-page-input" class="value-input value-input--compact" type="text" inputmode="decimal" enterkeyhint="done" placeholder="Ex.: 2,20" autocomplete="off" spellcheck="false">
        <div class="modal-actions">
          <button type="button" class="ghost-button ghost-button--compact" data-action="close-fill-modal">Cancelar</button>
          <button type="submit" class="primary-button primary-button--compact">Aplicar valor</button>
        </div>
      </form>
    </div>
  `;
  const input = modalRoot.querySelector("#fill-page-input");
  if (input) {
    input.focus();
    input.select();
  }
}

async function renderRoute(route = parseRoute(window.location.pathname), options = {}) {
  stopPolling();
  state.route = route;
  try {
    if (route.name === "home") {
      const payload = await mobileApi.getSession();
      state.currentSessionData = payload;
      patchHomeScreen(payload);
    } else if (route.name === "blocks") {
      const payload = await mobileApi.getSession();
      state.currentSessionData = payload;
      patchBlocksScreen(payload);
    } else if (route.name === "block-pages") {
      const payload = await mobileApi.getBlockPages(route.blockId);
      state.currentBlockPagesData = payload;
      patchBlockPagesScreen(payload);
    } else if (route.name === "page") {
      const payload = await mobileApi.getPage(route.pageId);
      state.currentPageData = payload;
      patchPageScreen(payload, { silent: options.silent, focusLineId: options.focusLineId || null, smoothFocus: false });
      if (!options.silent && !state.focusLineId) {
        const firstPending = findNextPendingLineId(payload.lines, null);
        if (firstPending) {
          state.focusLineId = firstPending;
          focusLineInput(firstPending, { smooth: false });
        }
      }
    } else {
      renderNotFound();
    }
  } catch (error) {
    if (options.silent) {
      if (Date.now() - state.lastPollErrorAt > POLL_ERROR_COOLDOWN_MS) {
        state.lastPollErrorAt = Date.now();
        showToast(error.message, "error");
      }
      startPolling();
      return;
    }
    if (error.code === "no_active_session") {
      renderErrorState("Sem sessao ativa", "Abra ou crie a sessao no desktop para operar os valores pelo celular.", {
        backAction: "go-home",
        primaryAction: { action: "refresh-route", label: "Atualizar" },
      });
    } else if (error.code === "not_mobile_visible") {
      renderErrorState("Ainda nao publicado", error.message, {
        backAction: route.name === "page" ? "go-block-pages" : "go-blocks",
        primaryAction: { action: "go-blocks", label: "Voltar aos blocos" },
      });
    } else {
      renderErrorState("Falha ao carregar", error.message, {
        backAction: route.name === "page" ? "go-block-pages" : "go-home",
        primaryAction: { action: "refresh-route", label: "Atualizar" },
      });
    }
  } finally {
    renderModal();
    startPolling();
  }
}

function stopPolling() {
  if (state.pollHandle) {
    window.clearInterval(state.pollHandle);
    state.pollHandle = null;
  }
}

function hasUnsavedPageInput() {
  return Array.from(state.pageDrafts.values()).some((draft) => draft.dirty);
}

function isPageIdle() {
  return state.route?.name === "page" && !hasUnsavedPageInput() && !state.modal && !document.hidden;
}

function startPolling() {
  stopPolling();
  if (!state.route || state.route.name === "not-found") {
    return;
  }
  const interval = state.route.name === "page" ? PAGE_POLL_INTERVAL_MS : SESSION_POLL_INTERVAL_MS;
  state.pollHandle = window.setInterval(() => {
    if (document.hidden) {
      return;
    }
    if (state.route?.name === "page" && !isPageIdle()) {
      return;
    }
    renderRoute(state.route, { silent: true });
  }, interval);
}

function updateDraft(lineId, value, savedValue) {
  const dirty = value.trim() !== savedValue.trim();
  if (!dirty) {
    state.pageDrafts.delete(lineId);
    return;
  }
  state.pageDrafts.set(lineId, { value, dirty });
}

function findLineById(lines, lineId) {
  return lines.find((line) => line.line_id === lineId) || null;
}

function findNextPendingLineId(lines, currentLineId) {
  const current = findLineById(lines, currentLineId);
  const pendingLines = lines.filter((line) => line.editable && line.pending);
  if (!pendingLines.length) {
    return null;
  }
  if (!current) {
    return pendingLines[0].line_id;
  }
  const afterCurrent = pendingLines.find((line) => line.order > current.order);
  return afterCurrent ? afterCurrent.line_id : pendingLines[0].line_id;
}

function syncActiveLineState(root = appRoot) {
  for (const card of root.querySelectorAll(".line-card[data-line-id]")) {
    const lineId = card.dataset.lineId;
    const input = card.querySelector(".value-input");
    const active = Boolean(lineId && lineId === state.focusLineId && input && !input.disabled);
    card.dataset.active = active ? "true" : "false";
  }
}

function focusLineInput(lineId, options = {}) {
  syncActiveLineState();
  window.requestAnimationFrame(() => {
    const input = appRoot.querySelector(`.value-input[data-line-id="${CSS.escape(lineId)}"]`);
    if (!input) {
      return;
    }
    if (options.scroll !== false) {
      input.scrollIntoView({ block: "center", behavior: options.smooth ? "smooth" : "auto" });
    }
    try {
      input.focus({ preventScroll: true });
    } catch (error) {
      input.focus();
    }
    if (options.select === false) {
      const caret = input.value.length;
      if (typeof input.setSelectionRange === "function") {
        input.setSelectionRange(caret, caret);
      }
      return;
    }
    input.select();
  });
}

async function findNextPendingPageId(currentBlockId, currentPageId) {
  const currentBlockPayload =
    state.currentBlockPagesData && state.currentBlockPagesData.block.block_id === currentBlockId
      ? state.currentBlockPagesData
      : await mobileApi.getBlockPages(currentBlockId);
  state.currentBlockPagesData = currentBlockPayload;
  const currentIndex = currentBlockPayload.pages.findIndex((page) => page.page_id === currentPageId);
  const pendingSameBlock = currentBlockPayload.pages.filter((page) => page.status === "pending" && page.can_edit_values);
  if (pendingSameBlock.length) {
    const laterCandidate = pendingSameBlock.find((page) => {
      const pageIndex = currentBlockPayload.pages.findIndex((item) => item.page_id === page.page_id);
      return pageIndex > currentIndex;
    });
    if (laterCandidate) {
      return laterCandidate.page_id;
    }
    return pendingSameBlock[0].page_id;
  }
  const sessionPayload = state.currentSessionData || (await mobileApi.getSession());
  state.currentSessionData = sessionPayload;
  const currentBlockIndex = sessionPayload.blocks.findIndex((block) => block.block_id === currentBlockId);
  const laterBlocks = currentBlockIndex >= 0 ? sessionPayload.blocks.slice(currentBlockIndex + 1) : sessionPayload.blocks;
  const nextBlock = laterBlocks.find((block) => block.next_pending_page_id);
  return nextBlock ? nextBlock.next_pending_page_id : null;
}

async function saveLine(lineId) {
  const row = appRoot.querySelector(`[data-line-id="${CSS.escape(lineId)}"]`);
  const input = row?.querySelector(".value-input");
  const button = row?.querySelector('[data-action="save-line"]');
  if (!input || !button) {
    return;
  }
  button.disabled = true;
  const value = input.value;
  try {
    const payload = await mobileApi.setLineValue(lineId, value);
    state.currentPageData = payload;
    state.currentSessionData = null;
    state.currentBlockPagesData = null;
    state.pageDrafts.delete(lineId);
    const nextLineId = findNextPendingLineId(payload.lines, lineId);
    state.focusLineId = nextLineId;
    patchPageScreen(payload, { focusLineId: nextLineId, smoothFocus: false });
    showToast(payload.message || "Valor atualizado.", "success");
    if (nextLineId) {
      return;
    }
    if (payload.page.status === "complete") {
      const nextPageId = await findNextPendingPageId(payload.block.block_id, payload.page.page_id);
      if (nextPageId) {
        showToast("Pagina concluida. Indo para a proxima pendente.", "success");
        navigate(`/mobile/page/${encodeURIComponent(nextPageId)}`);
        return;
      }
      showToast("Sessao de valores concluida.", "success");
    }
  } catch (error) {
    showToast(error.message, "error");
    input.focus();
    input.select();
  } finally {
    button.disabled = false;
  }
}

async function applyFillPage(form) {
  const input = form.querySelector("#fill-page-input");
  if (!input || !state.currentPageData) {
    return;
  }
  const submitButton = form.querySelector('button[type="submit"]');
  if (submitButton) {
    submitButton.disabled = true;
  }
  try {
    const payload = await mobileApi.fillPage(state.currentPageData.page.page_id, input.value);
    state.currentPageData = payload;
    state.currentSessionData = null;
    state.currentBlockPagesData = null;
    state.pageDrafts.clear();
    state.modal = null;
    state.focusLineId = findNextPendingLineId(payload.lines, null);
    patchPageScreen(payload, { focusLineId: state.focusLineId, smoothFocus: false });
    showToast(payload.message || "Pagina preenchida.", "success");
  } catch (error) {
    showToast(error.message, "error");
    input.focus();
    input.select();
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
    }
  }
}

function routeBackAction() {
  if (!state.route) {
    return "go-home";
  }
  if (state.route.name === "page") {
    return "go-block-pages";
  }
  if (state.route.name === "block-pages") {
    return "go-blocks";
  }
  if (state.route.name === "blocks") {
    return "go-home";
  }
  return "go-home";
}

appRoot.addEventListener("click", async (event) => {
  const actionElement = event.target.closest("[data-action]");
  if (!actionElement) {
    return;
  }
  const action = actionElement.dataset.action;
  if (action === "go-home") {
    navigate("/mobile");
  } else if (action === "go-blocks") {
    navigate("/mobile/blocks");
  } else if (action === "go-block-pages" && state.currentPageData) {
    navigate(`/mobile/block/${encodeURIComponent(state.currentPageData.block.block_id)}/pages`);
  } else if (action === "refresh-route" && state.route) {
    renderRoute(state.route, { silent: false });
  } else if (action === "open-block") {
    navigate(`/mobile/block/${encodeURIComponent(actionElement.dataset.blockId)}/pages`);
  } else if (action === "open-page") {
    navigate(`/mobile/page/${encodeURIComponent(actionElement.dataset.pageId)}`);
  } else if (action === "open-fill-modal" && state.currentPageData) {
    state.modal = {
      type: "fill-page",
      page: state.currentPageData.page,
      block: state.currentPageData.block,
    };
    renderModal();
  } else if (action === "goto-next-pending" && state.currentPageData) {
    const nextPageId = await findNextPendingPageId(
      state.currentPageData.block.block_id,
      state.currentPageData.page.page_id,
    );
    if (nextPageId) {
      navigate(`/mobile/page/${encodeURIComponent(nextPageId)}`);
    } else {
      showToast("Nao ha outra pagina pendente.", "success");
    }
  } else if (action === "save-line") {
    await saveLine(actionElement.dataset.lineId);
  } else if (action === routeBackAction()) {
    if (state.route?.name === "page" && state.currentPageData) {
      navigate(`/mobile/block/${encodeURIComponent(state.currentPageData.block.block_id)}/pages`);
    } else if (state.route?.name === "block-pages") {
      navigate("/mobile/blocks");
    } else {
      navigate("/mobile");
    }
  }
});

appRoot.addEventListener("input", (event) => {
  const input = event.target.closest(".value-input");
  if (!input || input.id === "fill-page-input") {
    return;
  }
  updateDraft(input.dataset.lineId, input.value, input.dataset.savedValue || "");
});

appRoot.addEventListener("focusin", (event) => {
  const input = event.target.closest(".value-input");
  if (!input || input.id === "fill-page-input") {
    return;
  }
  state.focusLineId = input.dataset.lineId;
  syncActiveLineState();
});

appRoot.addEventListener("pointerdown", (event) => {
  const actionElement = event.target.closest('[data-action="save-line"]');
  if (!actionElement) {
    return;
  }
  event.preventDefault();
  const lineId = actionElement.dataset.lineId;
  const input = appRoot.querySelector(`.value-input[data-line-id="${CSS.escape(lineId)}"]`);
  if (!input) {
    return;
  }
  state.focusLineId = lineId;
  try {
    input.focus({ preventScroll: true });
  } catch (error) {
    input.focus();
  }
  if (typeof input.setSelectionRange === "function") {
    const caret = input.value.length;
    input.setSelectionRange(caret, caret);
  }
});

appRoot.addEventListener("keydown", async (event) => {
  const input = event.target.closest(".value-input");
  if (!input || input.id === "fill-page-input" || event.key !== "Enter") {
    return;
  }
  event.preventDefault();
  await saveLine(input.dataset.lineId);
});

modalRoot.addEventListener("click", (event) => {
  const actionElement = event.target.closest("[data-action]");
  if (!actionElement) {
    return;
  }
  if (actionElement.dataset.action === "close-fill-modal") {
    state.modal = null;
    renderModal();
  }
});

modalRoot.addEventListener("submit", async (event) => {
  if (!(event.target instanceof HTMLFormElement)) {
    return;
  }
  if (event.target.dataset.form !== "fill-page") {
    return;
  }
  event.preventDefault();
  await applyFillPage(event.target);
});

window.addEventListener("popstate", () => {
  state.modal = null;
  renderRoute(parseRoute(window.location.pathname), { silent: false });
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden || !state.route) {
    return;
  }
  if (state.route.name === "page" && !isPageIdle()) {
    return;
  }
  renderRoute(state.route, { silent: true });
});

renderRoute(parseRoute(window.location.pathname), { silent: false });
