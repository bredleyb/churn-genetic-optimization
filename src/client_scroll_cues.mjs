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
  if (text === "Recalcular previsão") return "complete";
  return disabled ? "unavailable" : "idle";
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
        phase === "stale" || phase === "error"
      );
      const earlyError = !busy.observedRunning &&
        currentHeading !== busy.startHeading && phase === "error";
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
    if (state !== "idle" && state !== "complete") return;
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
    attributes: true, attributeFilter: ["disabled", "data-run-state"],
  });
  document.addEventListener("click", onPredictionClick, { signal: abort.signal });
  window.addEventListener("resize", schedule, { signal: abort.signal });
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
    setNumberStepperHover(null);
    actionButton?.removeEventListener("pointerleave", onActionLeave);
    mutations?.disconnect();
    resizes.disconnect();
    clear(panel);
  };
}
