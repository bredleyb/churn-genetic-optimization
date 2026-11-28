/**
 * Intensidade independente das duas sombras. Nenhum overflow significa
 * nenhuma sombra; a transição completa ocorre em até 56 px em cada ponta.
 */
export function scrollCueStrengths(scrollTop, clientHeight, scrollHeight, rampPixels = 56) {
  const limit = Math.max(0, scrollHeight - clientHeight);
  if (limit <= 1) return { top: 0, bottom: 0 };
  const position = Math.max(0, Math.min(limit, scrollTop));
  const ramp = Math.max(1, Math.min(rampPixels, limit / 2));
  return {
    top: Math.min(1, position / ramp),
    bottom: Math.min(1, (limit - position) / ramp),
  };
}

/** Estado visual do botão, obtido da legenda oficial de st.button. */
export function predictionButtonState(label, disabled = false) {
  const text = String(label ?? "").trim();
  if (text === "Calculando" || text === "Calculando...") return "running";
  if (disabled) return "unavailable";
  if (text === "Recalcular previsão") return "complete";
  if (text === "Tentar novamente") return "retry";
  return "idle";
}

/**
 * Acesso ao DOM principal é documentado para components v2: o componente
 * JS-only é montado fora da grade fixa e não envia eventos ao Python.
 */
export default function () {
  const abort = new AbortController();
  const resizes = new ResizeObserver(schedule);
  let mutations = null;
  let panel = null;
  let scrolling = null;
  let frame = 0;
  let locatorFrame = 0;
  let actionButton = null;
  let actionState = null;
  let suppressHover = false;
  let activeNumberStepper = null;
  let lastPointerPosition = null;
  // Consulta a geometria real: durante o estado inert, :hover pode
  // desaparecer temporariamente, mesmo com o ponteiro sobre o botão.
  const pointerInsideButton = (button, x, y) => {
    if (!button) return false;
    const rect = button.getBoundingClientRect();
    return x >= rect.left && x < rect.right && y >= rect.top && y < rect.bottom;
  };
  const pointerOverAction = button => lastPointerPosition
    ? pointerInsideButton(button, lastPointerPosition.x, lastPointerPosition.y)
    : Boolean(button?.matches(":hover"));
  // A solicitação persiste entre remontagens do componente durante reruns.
  const busyKey = Symbol.for("n3.client.interactionLock");
  const busy = window[busyKey] ??= {
    pending: false, observedRunning: false, startHeading: null, panel: null,
  };
  const heading = () => document.querySelector(".churn-workspace-heading");
  const lockPanel = locked => {
    const next = document.querySelector(".st-key-dashboard-client");
    if (busy.panel && busy.panel !== next) {
      busy.panel.inert = false;
      busy.panel.removeAttribute("data-n3-interaction-locked");
      busy.panel.removeAttribute("aria-busy");
    }
    busy.panel = next;
    if (!next) return;
    if (locked) {
      next.dataset.n3InteractionLocked = "true";
      next.setAttribute("aria-busy", "true");
      next.inert = true;
    } else if (next.inert || next.hasAttribute("data-n3-interaction-locked")) {
      next.inert = false;
      next.removeAttribute("data-n3-interaction-locked");
      next.removeAttribute("aria-busy");
    }
  };
  const syncInteractionLock = state => {
    const currentHeading = heading();
    const phase = currentHeading?.dataset.runState;
    if (state === "running" || phase === "running") {
      busy.pending = true;
      busy.observedRunning = true;
    } else if (busy.pending) {
      // Antes da primeira resposta do servidor, o botão anterior continua
      // presente: não liberar o overlay ao observar esse estado transitório.
      const completed = busy.observedRunning && (
        state === "complete" || phase === "complete" ||
        phase === "stale" || phase === "error" || phase === "invalid"
      );
      const earlyError = !busy.observedRunning &&
        currentHeading !== busy.startHeading && (phase === "error" || phase === "invalid");
      if (completed || earlyError) {
        busy.pending = false;
        busy.observedRunning = false;
        busy.startHeading = null;
      }
    }
    lockPanel(busy.pending);
  };
  // O listener em document recebe o click DEPOIS do React, evitando que
  // inert suprima o próprio clique que solicita a execução ao Streamlit.
  const onPredictionClick = event => {
    const button = event.target instanceof Element ? event.target.closest(
      '.st-key-dashboard-client-footer [data-testid="stButton"] button'
    ) : null;
    if (!button || button.disabled) return;
    const state = predictionButtonState(button.textContent, false);
    if (state !== "idle" && state !== "complete" && state !== "retry") return;
    busy.pending = true;
    busy.observedRunning = false;
    busy.startHeading = heading();
    lockPanel(true);
  };

  // Hover dos steppers nativos: usar movimento real do ponteiro elimina
  // :hover que o React pode reatribuir ao irmão depois de uma atualização.
  const setNumberStepperHover = next => {
    if (next === activeNumberStepper) return;
    activeNumberStepper?.removeAttribute("data-n3-pointer-hover");
    activeNumberStepper = next;
    if (next && !next.disabled) next.dataset.n3PointerHover = "true";
  };
  const numberStepperAt = target => target instanceof Element
    ? target.closest('.st-key-dashboard-client [data-testid="stNumberInput"] button')
    : null;
  const onNumberPointerMove = event => {
    if (event.pointerType === "touch") return;
    lastPointerPosition = {x: event.clientX, y: event.clientY};
    setNumberStepperHover(numberStepperAt(event.target));
  };
  // O pointerdown sempre descarrega o estado, mesmo que o React mantenha
  // o cursor sobre o componente ou substitua o botão antes do pointerup.
  const onNumberPointerDown = () => setNumberStepperHover(null);


  // Ao concluir a execução, o cursor pode continuar sobre o botão e manter
  // :hover ativo. Só habilitar novamente o hover após sair da área clicável.
  const onActionLeave = event => {
    // Ao tirar inert, o navegador pode emitir pointerleave sem deslocamento.
    // Só reativar o hover quando o ponteiro realmente sair do retângulo.
    if (pointerInsideButton(actionButton, event.clientX, event.clientY)) return;
    suppressHover = false;
    if (actionButton) actionButton.dataset.n3HoverReady = "true";
  };
  const syncPredictionButton = () => {
    const next = document.querySelector(
      '.st-key-dashboard-client-footer [data-testid="stButton"] button'
    );
    const changedElement = next !== actionButton;
    if (changedElement) {
      actionButton?.removeEventListener("pointerleave", onActionLeave);
      actionButton = next;
      next?.addEventListener("pointerleave", onActionLeave, { signal: abort.signal });
    }
    if (!next) {
      syncInteractionLock(null);
      return;
    }
    const state = predictionButtonState(next.textContent, next.disabled);
    syncInteractionLock(state);
    if (state !== actionState) {
      if (state === "running") {
        suppressHover = false;
      } else if (state === "complete" && pointerOverAction(next)) {
        suppressHover = true;
      } else if (actionState === "running" && pointerOverAction(next)) {
        suppressHover = true;
      }
      actionState = state;
    } else if (changedElement && state === "complete" && pointerOverAction(next)) {
      suppressHover = true;
    }
    if (next.dataset.n3PredictionState !== state) {
      next.dataset.n3PredictionState = state;
    }
    const ready = !suppressHover && state !== "running" ? "true" : "false";
    if (next.dataset.n3HoverReady !== ready) next.dataset.n3HoverReady = ready;
  };

  // Os erros vêm da validação Python, inclusive quando a aba está oculta.
  // Nenhum evento de edição é sintetizado; o foco só muda por ação explícita.
  const markedFields = new Map();
  const findErrorField = label => {
    const client = document.querySelector(".st-key-dashboard-client");
    if (!client) return null;
    const locate = root => Array.from(root.querySelectorAll("input[aria-label]"))
      .find(input => input.getAttribute("aria-label") === label);
    let input = locate(client);
    if (!input && label === "Tempo como cliente") {
      const tenure = client.querySelector(".st-key-dashboard-tenure-control");
      for (const host of tenure?.querySelectorAll("*") ?? []) {
        if (host.shadowRoot && (input = locate(host.shadowRoot))) break;
      }
    }
    if (!input) return null;
    const group = input.closest('[data-testid="stSelectbox"],[data-testid="stNumberInput"],.n3-tenure');
    return group ? {input, group} : null;
  };
  const restoreMark = (input, saved) => {
    saved.group.removeAttribute("data-n3-invalid");
    for (const [name, old] of Object.entries(saved.attributes)) {
      if (old === null) input.removeAttribute(name);
      else input.setAttribute(name, old);
    }
    markedFields.delete(input);
  };
  const validationMarkers = () => Array.from(document.querySelectorAll(
    ".n3-client-validation [data-n3-error-label]"
  ));
  const syncValidation = () => {
    const active = new Set();
    for (const marker of validationMarkers()) {
      const field = findErrorField(marker.dataset.n3ErrorLabel);
      if (!field) continue;
      const {input, group} = field;
      active.add(input);
      if (!markedFields.has(input)) {
        markedFields.set(input, {group, attributes: {
          "aria-invalid": input.getAttribute("aria-invalid"),
          "aria-describedby": input.getAttribute("aria-describedby"),
          "aria-description": input.getAttribute("aria-description"),
        }});
      }
      group.dataset.n3Invalid = "true";
      input.setAttribute("aria-invalid", "true");
      const saved = markedFields.get(input);
      if (input.getRootNode() === marker.getRootNode()) {
        const ids = new Set((saved.attributes["aria-describedby"] || "").split(/\s+/).filter(Boolean));
        ids.add(marker.id);
        input.setAttribute("aria-describedby", Array.from(ids).join(" "));
      } else {
        input.setAttribute("aria-description", marker.textContent);
      }
    }
    for (const [input, saved] of markedFields) {
      if (!active.has(input)) restoreMark(input, saved);
    }
  };
  const jumpKey = Symbol.for("n3.client.validationJump");
  const jump = window[jumpKey] ??= {label: null, tab: null, expires: 0};
  const focusInvalidField = () => {
    if (!jump.label) return;
    if (Date.now() > jump.expires) {
      jump.label = null;
      return;
    }
    const client = document.querySelector(".st-key-dashboard-client");
    if (!client || client.inert) return;
    if (jump.tab) {
      const tab = Array.from(client.querySelectorAll('[role="tab"]'))
        .find(item => item.textContent.trim() === jump.tab);
      if (!tab || tab.getAttribute("aria-selected") !== "true") return;
    }
    const field = findErrorField(jump.label);
    if (!field || !field.input.getClientRects().length) return;
    jump.label = null;
    field.group.scrollIntoView({block: "nearest", inline: "nearest", behavior: "instant"});
    // Controles dependentes desabilitados não podem receber foco.
    const focus = field.input.disabled
      ? client.querySelector('[role="tab"][aria-selected="true"]') : field.input;
    focus?.focus({preventScroll: true});
  };
  const onValidationClick = event => {
    const link = event.target instanceof Element
      ? event.target.closest("a.n3-validation-jump") : null;
    if (!link) return;
    event.preventDefault();
    const marker = validationMarkers()[0];
    if (!marker) return;
    jump.label = marker.dataset.n3ErrorLabel;
    jump.tab = marker.dataset.n3ErrorTab;
    jump.expires = Date.now() + 5000;
    const client = document.querySelector(".st-key-dashboard-client");
    if (jump.tab) {
      const tab = Array.from(client?.querySelectorAll('[role="tab"]') ?? [])
        .find(item => item.textContent.trim() === jump.tab);
      if (tab && tab.getAttribute("aria-selected") !== "true") tab.click();
    }
    queueBind();
  };

  // A seleção de Previsão fica no navegador: navegação não interrompe
  // o processamento síncrono. Preservar a aba se o Streamlit remontar o DOM.
  const predictionTabKey = Symbol.for("n3.prediction.activeTab");
  const predictionTabs = () => Array.from(document.querySelectorAll(
    '.st-key-dashboard-prediction-tabs [role="tab"]'
  ));
  let predictionTabList = null;
  const rememberPredictionTab = () => {
    const selected = predictionTabs().find(tab => tab.getAttribute("aria-selected") === "true");
    if (selected) window[predictionTabKey] = selected.textContent.trim();
  };
  const syncPredictionTab = () => {
    const tabs = predictionTabs();
    if (!tabs.length) return;
    const list = tabs[0].closest('[role="tablist"]');
    if (predictionTabList !== list) {
      predictionTabList = list;
      const wanted = tabs.find(tab => tab.textContent.trim() === window[predictionTabKey]);
      if (wanted && wanted.getAttribute("aria-selected") !== "true") wanted.click();
      else rememberPredictionTab();
    } else rememberPredictionTab();
  };
  const onWorkspaceNavigation = event => {
    const link = event.target instanceof Element
      ? event.target.closest("[data-n3-prediction-tab]") : null;
    if (!link) return;
    event.preventDefault();
    const target = predictionTabs().find(tab => tab.textContent.trim() === link.dataset.n3PredictionTab);
    if (target) { window[predictionTabKey] = target.textContent.trim(); target.click(); target.focus(); }
  };

  // Estado de leitura independente por console. Não mexer na posição
  // de abas ocultas; restaurar quando voltarem a ter área visível.
  const logKey = Symbol.for("n3.log.reading");
  const reading = window[logKey] ??= {
    terminal: {element:null,count:0,top:0,follow:true},
    monitor: {element:null,count:0,top:0,follow:true},
  };
  const logSelectors = {terminal:".n3-terminal-log", monitor:".churn-console-lines"};
  const logVisible = el => Boolean(el?.getClientRects().length && el.clientHeight);
  const onLogScroll = event => {
    for (const [kind, selector] of Object.entries(logSelectors)) {
      const el = event.target;
      if (!(el instanceof Element) || !el.matches(selector) || !logVisible(el)) continue;
      const state = reading[kind];
      state.top = el.scrollTop;
      state.follow = kind === "terminal"
        ? el.scrollHeight - el.clientHeight - el.scrollTop <= 4
        : el.scrollTop <= 4;
    }
  };
  const syncLogs = () => {
    for (const [kind, selector] of Object.entries(logSelectors)) {
      const el = document.querySelector(selector);
      if (!logVisible(el)) continue;
      const state = reading[kind];
      const count = Number(el.dataset.n3LogCount || 0);
      if (count < state.count) { state.top = 0; state.follow = true; }
      if (el !== state.element || count !== state.count) {
        el.scrollTop = state.follow
          ? (kind === "terminal" ? el.scrollHeight : 0)
          : state.top;
        state.element = el;
        state.count = count;
        state.top = el.scrollTop;
      }
    }
  };

  // Um único tooltip portado para body, com texto fornecido pelo Python.
  const tip = document.createElement("div");
  tip.id = "n3-workspace-tooltip";
  tip.className = "n3-tooltip";
  tip.setAttribute("role", "tooltip");
  tip.hidden = true;
  const tipTitle = document.createElement("strong");
  const tipBody = document.createElement("p");
  tip.append(tipTitle, tipBody);
  document.body.append(tip);
  let tipAnchor = null, tipTimer = 0, tipPinned = false, tipMode = "";
  const findTip = target => target instanceof Element ? target.closest("[data-n3-tip]") : null;
  const cancelTipClose = () => { if (tipTimer) clearTimeout(tipTimer); tipTimer = 0; };
  const closeTip = () => {
    cancelTipClose();
    if (tipAnchor) {
      tipAnchor.removeAttribute("data-n3-tip-open");
      const ids = (tipAnchor.getAttribute("aria-describedby") || "").split(/\s+/).filter(x => x && x !== tip.id);
      if (ids.length) tipAnchor.setAttribute("aria-describedby", ids.join(" "));
      else tipAnchor.removeAttribute("aria-describedby");
    }
    tipAnchor = null;
    tipPinned = false;
    tipMode = "";
    tip.hidden = true;
  };
  const placeTip = () => {
    if (!tipAnchor) return;
    if (!tipAnchor.isConnected || !tipAnchor.getClientRects().length) { closeTip(); return; }
    const r = tipAnchor.getBoundingClientRect();
    const clipping = tipAnchor.closest('[role="tabpanel"]')?.getBoundingClientRect();
    const top = Math.max(0, clipping?.top ?? 0), bottom = Math.min(innerHeight, clipping?.bottom ?? innerHeight);
    if (r.bottom <= top || r.top >= bottom || r.right <= 0 || r.left >= innerWidth) { closeTip(); return; }
    const w = tip.offsetWidth, h = tip.offsetHeight;
    const x = Math.max(8, Math.min(innerWidth - w - 8, r.left + (r.width-w)/2));
    const preferred = r.bottom + 6 + h <= innerHeight-8 ? r.bottom + 6 : r.top-h-6;
    const y = Math.max(8, Math.min(innerHeight - h - 8, preferred));
    tip.style.left = x + "px";
    tip.style.top = y + "px";
  };
  const openTip = (anchor, mode) => {
    if (!anchor) return;
    cancelTipClose();
    if (tipAnchor !== anchor) closeTip();
    tipAnchor = anchor;
    tipMode = mode;
    tipPinned = mode === "click";
    tip.dataset.kind = anchor.dataset.n3Tip;
    tipTitle.textContent = anchor.dataset.n3TipTitle || "";
    tipBody.textContent = anchor.dataset.n3TipBody || "";
    anchor.setAttribute("data-n3-tip-open","true");
    const ids = new Set((anchor.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
    ids.add(tip.id);
    anchor.setAttribute("aria-describedby", Array.from(ids).join(" "));
    tip.hidden = false;
    placeTip();
  };
  const deferTipClose = () => {
    cancelTipClose();
    if (tipPinned || tipMode === "focus") return;
    tipTimer = setTimeout(closeTip, 180);
  };
  const onTipOver = event => {
    if (event.pointerType === "touch") return;
    if (tip.contains(event.target)) { cancelTipClose(); return; }
    const anchor = findTip(event.target);
    if (anchor && anchor !== tipAnchor) openTip(anchor, "hover");
    else if (anchor) cancelTipClose();
  };
  const onTipOut = event => {
    if (!tipAnchor || event.pointerType === "touch") return;
    if (tipAnchor.contains(event.relatedTarget) || tip.contains(event.relatedTarget)) return;
    if (tipAnchor.contains(event.target) || tip.contains(event.target)) deferTipClose();
  };
  const onTipFocus = event => {
    const anchor = findTip(event.target);
    if (anchor) openTip(anchor, "focus");
    else if (tipAnchor && !tip.contains(event.target)) closeTip();
  };
  const onTipBlur = event => {
    if (tipAnchor && tipAnchor.contains(event.target) && !tipAnchor.contains(event.relatedTarget) && !tip.contains(event.relatedTarget)) closeTip();
  };
  const onTipClick = event => {
    const anchor = findTip(event.target);
    if (anchor) {
      if (tipAnchor === anchor && tipPinned) closeTip();
      else openTip(anchor, "click");
    } else if (tipAnchor && !tip.contains(event.target)) closeTip();
  };
  const onTipKey = event => {
    if (event.key === "Escape" && tipAnchor) { closeTip(); event.preventDefault(); }
    else if (["Enter"," "].includes(event.key)) {
      const anchor = findTip(event.target);
      if (anchor && anchor.tagName.toLowerCase() !== "button") {
        event.preventDefault();
        if (tipAnchor === anchor && tipPinned) closeTip();
        else openTip(anchor,"click");
      }
    }
  };

  const clear = element => {
    element?.style.removeProperty("--n3-client-shadow-top");
    element?.style.removeProperty("--n3-client-shadow-bottom");
  };
  const update = () => {
    frame = 0;
    if (!panel || !scrolling || !scrolling.isConnected) return;
    const { top, bottom } = scrollCueStrengths(
      scrolling.scrollTop, scrolling.clientHeight, scrolling.scrollHeight
    );
    panel.style.setProperty("--n3-client-shadow-top", String(top));
    panel.style.setProperty("--n3-client-shadow-bottom", String(bottom));
  };
  function schedule() {
    if (!frame && !abort.signal.aborted) frame = requestAnimationFrame(update);
  }
  const bind = () => {
    locatorFrame = 0;
    if (abort.signal.aborted) return;
    syncPredictionButton();
    syncPredictionTab();
    syncLogs();
    placeTip();
    syncValidation();
    focusInvalidField();
    const nextPanel = document.querySelector(".st-key-dashboard-client");
    const nextScrolling = nextPanel?.querySelector(".st-key-dashboard-client-fields");
    if (nextScrolling === scrolling && nextPanel === panel) {
      schedule();
      return;
    }
    if (scrolling) scrolling.removeEventListener("scroll", schedule);
    resizes.disconnect();
    mutations?.disconnect();
    clear(panel);
    panel = nextPanel;
    scrolling = nextScrolling;
    if (!scrolling) return;
    scrolling.addEventListener("scroll", schedule, { passive: true, signal: abort.signal });
    resizes.observe(scrolling);
    if (scrolling.firstElementChild) resizes.observe(scrolling.firstElementChild);
    mutations = new MutationObserver(schedule);
    mutations.observe(scrolling, {
      childList: true, subtree: true, attributes: true,
      attributeFilter: ["hidden", "class", "style", "aria-selected"],
    });
    schedule();
  };
  const queueBind = () => {
    if (!locatorFrame && !abort.signal.aborted) locatorFrame = requestAnimationFrame(bind);
  };
  // Reruns podem substituir o scroller ou alterar a legenda do mesmo botão.
  // Observar somente nós e conteúdo textual: nossos atributos CSS não geram
  // mutações recursivas nem comunicações com Python.
  const structure = new MutationObserver(queueBind);
  structure.observe(document.body, {
    childList: true, characterData: true, subtree: true,
    attributes: true, attributeFilter: ["disabled", "data-run-state", "aria-selected", "hidden", "data-n3-log-count"],
  });
  document.addEventListener("click", onPredictionClick, { signal: abort.signal });
  document.addEventListener("click", onValidationClick, { signal: abort.signal });
  document.addEventListener("click", onWorkspaceNavigation, { signal: abort.signal });
  document.addEventListener("pointerover", onTipOver, {signal:abort.signal});
  document.addEventListener("pointerout", onTipOut, {signal:abort.signal});
  document.addEventListener("focusin", onTipFocus, {signal:abort.signal});
  document.addEventListener("focusout", onTipBlur, {signal:abort.signal});
  document.addEventListener("click", onTipClick, {signal:abort.signal});
  document.addEventListener("keydown", onTipKey, {signal:abort.signal});
  document.addEventListener("scroll", placeTip, {capture:true,passive:true,signal:abort.signal});
  document.addEventListener("scroll", onLogScroll, {capture:true, passive:true, signal:abort.signal});
  window.addEventListener("resize", queueBind, { signal: abort.signal });
  document.addEventListener("pointermove", onNumberPointerMove,
    { capture:true, signal:abort.signal });
  document.addEventListener("pointerdown", onNumberPointerDown,
    { capture:true, signal:abort.signal });
  window.addEventListener("blur", onNumberPointerDown, { signal:abort.signal });
  bind();

  return () => {
    abort.abort();
    if (frame) cancelAnimationFrame(frame);
    if (locatorFrame) cancelAnimationFrame(locatorFrame);
    structure.disconnect();
    closeTip();
    tip.remove();
    for (const [input, saved] of markedFields) restoreMark(input, saved);
    setNumberStepperHover(null);
    actionButton?.removeEventListener("pointerleave", onActionLeave);
    mutations?.disconnect();
    resizes.disconnect();
    clear(panel);
  };
}
