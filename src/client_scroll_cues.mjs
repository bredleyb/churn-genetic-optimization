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
    setNumberStepperHover(numberStepperAt(event.target));
  };
  // O pointerdown sempre descarrega o estado, mesmo que o React mantenha
  // o cursor sobre o componente ou substitua o botão antes do pointerup.
  const onNumberPointerDown = () => setNumberStepperHover(null);


  // Ao concluir a execução, o cursor pode continuar sobre o botão e manter
  // :hover ativo. Só habilitar novamente o hover após sair da área clicável.
  const onActionLeave = () => {
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
    if (!next) return;
    const state = predictionButtonState(next.textContent, next.disabled);
    if (state !== actionState) {
      if (state === "running") {
        suppressHover = false;
      } else if (state === "complete" && next.matches(":hover")) {
        suppressHover = true;
      } else if (actionState === "running" && next.matches(":hover")) {
        suppressHover = true;
      }
      actionState = state;
    } else if (changedElement && state === "complete" && next.matches(":hover")) {
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
  });
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
