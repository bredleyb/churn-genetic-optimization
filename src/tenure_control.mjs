export function clampMonths(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.min(999, Math.trunc(number))) : 0;
}

export function displayMonths(value) {
  const number = clampMonths(value);
  return number + (number === 1 ? " mês" : " meses");
}

export function parseMonthInput(raw) {
  const digits = String(raw ?? "").trim();
  if (!/^\d{1,3}$/.test(digits)) return null;
  return clampMonths(digits);
}

// Uma remontagem v2 pode ocorrer antes do cleanup do renderer anterior.
// O slot fica no nó da interface; duas instâncias jamais escutam o mesmo input.
const ACTIVE_MOUNT = Symbol.for("n3.tenure.activeMount");

// Edição numérica nativa: a unidade é texto não editável na MESMA caixa visual.
// Ctrl+A, Backspace e movimentação do cursor pertencem ao navegador.
export default function({ parentElement, data, setStateValue }) {
  const root = parentElement.querySelector(".n3-tenure");
  if (!root) return;
  const input = root.querySelector("input");
  const unit = root.querySelector(".n3-tenure-unit");
  const minus = root.querySelector('[data-step="-1"]');
  const plus = root.querySelector('[data-step="1"]');
  // Garante idempotência mesmo se o framework remontar sem chamar cleanup.
  root[ACTIVE_MOUNT]?.abort();
  const controller = new AbortController();
  root[ACTIVE_MOUNT] = controller;
  const { signal } = controller;
  const steppers = [minus, plus];
  const showPointerHover = active => {
    for (const button of steppers) {
      if (button === active && !button.disabled) {
        button.dataset.n3PointerHover = "true";
      } else {
        delete button.dataset.n3PointerHover;
      }
    }
  };
  // CSS :hover pode ficar associado a um irmão após rerender com o ponteiro
  // imóvel. Só o pointermove real arma o destaque; o clique limpa ambos.
  showPointerHover(null);
  root.addEventListener("pointermove", event => {
    if (event.pointerType === "touch") return;
    const button = event.target instanceof Element
      ? event.target.closest('button[data-step]') : null;
    showPointerHover(steppers.includes(button) ? button : null);
  }, { signal });
  root.addEventListener("pointerdown", () => showPointerHover(null),
    { capture:true, signal });
  root.addEventListener("pointerleave", () => showPointerHover(null), { signal });
  const isFocused = () => input.getRootNode().activeElement === input ||
    document.activeElement === input;

  // Com a key estável, o rascunho nativo em foco tem precedência sobre data
  // de um rerun anterior. Trocas de perfil criam uma revisão/key diferente.
  const existing = parseMonthInput(input.value);
  let value = isFocused() && existing !== null
    ? existing : clampMonths(data?.value ?? 0);

  const render = ({force = false} = {}) => {
    const digits = String(value);
    if (force || !isFocused()) {
      if (input.value !== digits) input.value = digits;
    }
    unit.textContent = value === 1 ? " mês" : " meses";
    input.style.setProperty("--n3-tenure-digit-count",
      String(Math.max(1, input.value.length)));
    minus.disabled = value <= 0;
    plus.disabled = value >= 999;
  };
  const commit = (next, {force = false} = {}) => {
    const normalized = clampMonths(next);
    const changed = normalized !== value;
    value = normalized;
    render({force});
    if (changed) setStateValue("value", value);
  };
  render();

  // beforeinput apenas rejeita caracteres não numéricos. Eventos de seleção
  // e o texto válido não são interceptados ou reposicionados.
  input.addEventListener("beforeinput", event => {
    if (event.inputType === "insertText" &&
        event.data && !/^\d+$/.test(event.data)) event.preventDefault();
  }, { signal });
  input.addEventListener("input", () => {
    const raw = input.value;
    const digits = raw.replace(/\D/g, "").slice(0, 3);
    if (digits !== raw) {
      const cursor = Math.min(input.selectionStart ?? digits.length, digits.length);
      input.value = digits;
      input.setSelectionRange(cursor, cursor);
    }
    // Vazio é um rascunho transitório. A normalização ocorre no blur.
    commit(digits === "" ? 0 : Number(digits));
  }, { signal });
  input.addEventListener("blur", () => render({force: true}), { signal });
  input.addEventListener("keydown", event => {
    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault();
      commit(value + (event.key === "ArrowUp" ? 1 : -1), {force: true});
    }
  }, { signal });
  input.addEventListener("paste", event => {
    const text = (event.clipboardData?.getData("text") ?? "").trim();
    const match = /^(\d+)(?:\s+(?:mês|meses))?$/i.exec(text);
    event.preventDefault();
    if (!match) return;
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? start;
    input.setRangeText(match[1], start, end, "end");
    input.dispatchEvent(new Event("input", {bubbles:true}));
  }, { signal });
  input.addEventListener("drop", event => event.preventDefault(), { signal });
  minus.addEventListener("click", () => commit(value - 1, {force:true}), { signal });
  plus.addEventListener("click", () => commit(value + 1, {force:true}), { signal });
  return () => {
    controller.abort();
    if (root[ACTIVE_MOUNT] === controller) showPointerHover(null);
    // Um cleanup atrasado nunca deve desmontar a instância mais recente.
    if (root[ACTIVE_MOUNT] === controller) delete root[ACTIVE_MOUNT];
  };
}
