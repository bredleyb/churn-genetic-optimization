"""Perfis locais do formulário: dois exemplos de referência e até três cópias.

Cada exemplo mantém a fotografia original e os valores editados somente na sessão.
Os arquivos de referência JSON permanecem imutáveis.
"""

from pathlib import Path

from src.ui_data import PROFILE_FILES, load_profile

MAX_EXAMPLES = 5


def initial_examples(root: Path) -> dict[str, dict[str, dict]]:
    result = {}
    for name in PROFILE_FILES:
        values = load_profile(root, name)
        result[name] = {"original": values.copy(), "values": values.copy()}
    return result


def append_example(examples: dict, customer: dict) -> str:
    """Cria um exemplo com os valores atuais como referência restaurável."""
    if len(examples) >= MAX_EXAMPLES:
        raise ValueError(f"Limite de {MAX_EXAMPLES} exemplos atingido.")
    name = f"Exemplo {len(examples) + 1}"
    if name in examples:
        raise ValueError(f"Exemplo já existente: {name}")
    values = customer.copy()
    examples[name] = {"original": values.copy(), "values": values.copy()}
    return name


def is_original(examples: dict, name: str, values: dict) -> bool:
    return values == examples[name]["original"]
