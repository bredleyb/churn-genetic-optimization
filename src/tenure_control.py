"""Controle de permanência: um campo visual com número e unidade protegida.

O componente v2 apresenta um único input nativo contendo só os dígitos.
A unidade fixa fica visualmente na mesma caixa, em um span inacessível
à edição. O Python recebe meses inteiros de 0 a 999.
"""

from pathlib import Path


_COMPONENT_HTML = """
<div class="n3-tenure">
  <label for="n3-tenure-value">Tempo como cliente</label>
  <div class="n3-tenure-field">
    <input id="n3-tenure-value" type="text" inputmode="numeric"
           pattern="[0-9]*" maxlength="3" autocomplete="off" spellcheck="false"
           aria-label="Tempo como cliente" aria-describedby="n3-tenure-unit" />
    <span id="n3-tenure-unit" class="n3-tenure-unit"> meses</span>
    <span class="n3-tenure-spacer" aria-hidden="true"></span>
    <button type="button" data-step="-1" aria-label="Diminuir um mês">−</button>
    <button type="button" data-step="1" aria-label="Aumentar um mês">+</button>
  </div>
</div>
"""

_COMPONENT_CSS = """
:host {display:block;width:100%;min-width:0;box-sizing:border-box;}
.n3-tenure {display:flex;flex-direction:column;gap:6px;min-width:0;
  font-family:var(--n3-font-ui,"Familjen Grotesk",sans-serif);}
.n3-tenure label {display:block;min-height:20px;color:var(--n3-secondary,#d8d8d8);
  font-size:15px;line-height:20px;font-weight:400;white-space:nowrap;
  transform:translateY(var(--n3-field-text-shift,-1px));}
.n3-tenure-field {box-sizing:border-box;display:flex;align-items:stretch;
  width:100%;height:var(--n3-field-height,42px);min-width:0;overflow:hidden;
  background:var(--n3-field-fill,#0e1013);border:1px solid var(--n3-outline,#55585d);
  border-radius:var(--n3-field-radius,4px);}
/* O painel pai recorta overflow-x; o anel de foco deve caber DENTRO da borda. */
.n3-tenure-field:focus-within {
  outline:none;border-color:var(--n3-text,#f5f5f5);
  box-shadow:inset 0 0 0 1px var(--n3-text,#f5f5f5);
}
/* O input seleciona somente dígitos; o sufixo ocupa a mesma caixa ao lado
   sem pertencer ao texto editável. Isso elimina a gestão manual do caret. */
.n3-tenure-field input {box-sizing:content-box;flex:0 0 auto;min-width:0;
  width:calc(var(--n3-tenure-digit-count,1)*1ch);
  height:100%;padding:0 0 0 10px;outline:0;border:0;border-radius:0;
  background:transparent;color:var(--n3-text,#f5f5f5);
  font:400 var(--n3-field-text-size,14px)/var(--n3-field-text-line,20px)
    var(--n3-font-ui,"Familjen Grotesk",sans-serif);
  font-variant-numeric:tabular-nums;
  transform:translateY(var(--n3-field-text-shift,-1px));}
.n3-tenure-unit {box-sizing:border-box;flex:0 0 auto;align-self:center;
  color:var(--n3-text,#f5f5f5);white-space:pre;pointer-events:none;
  font:400 var(--n3-field-text-size,14px)/var(--n3-field-text-line,20px)
    var(--n3-font-ui,"Familjen Grotesk",sans-serif);
  /* O texto do input nativo e um span usam referências de linha distintas.
     Um pixel abaixo alinha a base visível do sufixo à base dos dígitos. */
  transform:translateY(calc(var(--n3-field-text-shift,-1px) + 1px));}
.n3-tenure-spacer {flex:1;min-width:0;}
.n3-tenure-field button {box-sizing:border-box;flex:0 0 32px;width:32px;
  height:100%;padding:0;border:0;border-radius:0;
  display:flex;align-items:center;justify-content:center;
  font:500 17px/20px var(--n3-font-ui,"Familjen Grotesk",sans-serif);
  background:var(--n3-field-action-fill,#0e1013);color:var(--n3-secondary,#d8d8d8);
  cursor:pointer;}
.n3-tenure-field button:hover:not(:disabled) {background:var(--n3-elevated,#202124);}
.n3-tenure-field button:disabled {opacity:.45;cursor:default;}
.n3-tenure-field button:focus-visible {outline:2px solid var(--n3-text,#f5f5f5);outline-offset:-2px;}
"""


def render_tenure_control(st, *, value: int, revision: int, on_change) -> int:
    """Renderiza o campo numérico e retorna meses sincronizados do componente."""
    widget = st.components.v2.component(
        "n3_tenure_control",
        html=_COMPONENT_HTML,
        css=_COMPONENT_CSS,
        js=Path(__file__).with_suffix(".mjs").read_text(encoding="utf-8"),
    )
    key = f"n3-tenure-{revision}"
    # A propriedade do componente é a origem do valor entre reruns.
    current_state = st.session_state.get(key, {})
    live_value = current_state.get("value", value) if hasattr(current_state, "get") else value
    result = widget(
        key=key,
        data={"value": int(live_value if live_value is not None else value)},
        default={"value": int(value)},
        on_value_change=on_change,
    )
    return max(0, min(999, int(result.value if result.value is not None else value)))
