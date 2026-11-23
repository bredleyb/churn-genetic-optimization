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

// Edição numérica nativa: a unidade é texto não editável na MESMA caixa visual.
// Ctrl+A, Backspace e movimentação do cursor pertencem ao navegador.
export default function({ parentElement, data, setStateValue }) {
  const root = parentElement.querySelector(".n3-tenure");
  if (!root) return;
  const input = root.querySelector("input");
  const unit = root.querySelector(".n3-tenure-unit");
  const minus = root.querySelector('[data-step="-1"]');
  const plus = root.querySelector('[data-step="1"]');
  const controller = new AbortController();
  const { signal } = controller;
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
  return () => controller.abort();
}
