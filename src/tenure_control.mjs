export function clampMonths(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.min(999, Math.trunc(number))) : 0;
}

export function displayMonths(value) {
  const number = clampMonths(value);
  return number + (number === 1 ? " mês" : " meses");
}

export function replaceMonthDigits(current, start, end, insert) {
  const digits = String(clampMonths(current));
  const from = Math.max(0, Math.min(digits.length, start));
  const to = Math.max(from, Math.min(digits.length, end));
  if (!/^\d*$/.test(insert)) return clampMonths(current);
  return clampMonths(digits.slice(0, from) + insert + digits.slice(to));
}

// A single native text input contains both number and immutable suffix.
// Only numeric characters are editable; the caret stays before the unit.
export default function({ parentElement, data, setStateValue }) {
  const root = parentElement.querySelector(".n3-tenure");
  if (!root) return;
  const input = root.querySelector("input");
  const minus = root.querySelector('[data-step="-1"]');
  const plus = root.querySelector('[data-step="1"]');
  const controller = new AbortController();
  const signal = controller.signal;
  let value = clampMonths(data?.value ?? 0);
  const digitsLength = () => String(value).length;
  const placeCaret = () => {
    if (document.activeElement === input) input.setSelectionRange(digitsLength(), digitsLength());
  };
  const render = () => {
    input.value = displayMonths(value);
    minus.disabled = value <= 0;
    plus.disabled = value >= 999;
    placeCaret();
  };
  const commit = next => {
    const clamped = clampMonths(next);
    const changed = clamped !== value;
    value = clamped;
    render();
    if (changed) setStateValue("value", value);
  };
  const bounds = () => {
    const n = digitsLength();
    return [
      Math.max(0, Math.min(n, input.selectionStart ?? n)),
      Math.max(0, Math.min(n, input.selectionEnd ?? n)),
    ];
  };
  const insert = text => {
    const [start, end] = bounds();
    commit(replaceMonthDigits(value, start, end, text));
  };
  const remove = backwards => {
    const [start, end] = bounds();
    const n = digitsLength();
    if (end > start) commit(replaceMonthDigits(value, start, end, ""));
    else if (backwards && start > 0) commit(replaceMonthDigits(value, start - 1, start, ""));
    else if (!backwards && start < n) commit(replaceMonthDigits(value, start, start + 1, ""));
    else placeCaret();
  };
  render();
  input.addEventListener("focus", placeCaret, { signal });
  input.addEventListener("pointerup", placeCaret, { signal });
  input.addEventListener("keydown", event => {
    const key = event.key;
    if ((event.ctrlKey || event.metaKey) && key.toLowerCase() === "a") {
      event.preventDefault();
      input.setSelectionRange(0, digitsLength());
    } else if (key === "ArrowUp" || key === "ArrowDown") {
      event.preventDefault();
      commit(value + (key === "ArrowUp" ? 1 : -1));
    } else if (key === "Home" || key === "End" || key === "ArrowLeft" || key === "ArrowRight") {
      event.preventDefault();
      placeCaret();
    }
  }, { signal });
  input.addEventListener("beforeinput", event => {
    if (event.inputType === "insertText" || event.inputType === "insertReplacementText") {
      event.preventDefault();
      if (/^\d+$/.test(event.data ?? "")) insert(event.data);
    } else if (event.inputType.startsWith("delete")) {
      event.preventDefault();
      remove(event.inputType.includes("Backward"));
    } else {
      // Includes IME insertions, suffix edits, drag and content replacement.
      event.preventDefault();
    }
  }, { signal });
  input.addEventListener("paste", event => {
    event.preventDefault();
    const text = (event.clipboardData?.getData("text") ?? "").trim();
    const match = /^(\d+)(?:\s+meses?)?$/i.exec(text);
    if (match) {
      const [start, end] = bounds();
      // Paste over selected numeric part, or replace the number as a whole.
      commit(start === 0 && end === digitsLength()
        ? Number(match[1]) : replaceMonthDigits(value, start, end, match[1]));
    }
  }, { signal });
  input.addEventListener("drop", event => event.preventDefault(), { signal });
  input.addEventListener("input", () => {
    // Defensive fallback for browser/assistive input events without beforeinput.
    const match = /^(\d{1,3})(?:\s+meses?)?$/i.exec(input.value.trim());
    if (match) commit(Number(match[1]));
    else render();
  }, { signal });
  minus.addEventListener("click", () => commit(value - 1), { signal });
  plus.addEventListener("click", () => commit(value + 1), { signal });
  return () => controller.abort();
}
