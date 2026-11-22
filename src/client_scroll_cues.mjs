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
  // Streamlit reruns may replace the scroll viewport without remounting this
  // JS-only component. Watch only node additions/removals, never style changes.
  const structure = new MutationObserver(queueBind);
  structure.observe(document.body, { childList: true, subtree: true });
  window.addEventListener("resize", schedule, { signal: abort.signal });
  bind();

  return () => {
    abort.abort();
    if (frame) cancelAnimationFrame(frame);
    if (locatorFrame) cancelAnimationFrame(locatorFrame);
    structure.disconnect();
    mutations?.disconnect();
    resizes.disconnect();
    clear(panel);
  };
}
