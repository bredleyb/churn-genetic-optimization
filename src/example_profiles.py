"""Perfis locais do formulário: dois exemplos de referência e até três cópias.

Cada exemplo mantém a fotografia original e os valores editados somente na sessão.
Os arquivos de referência JSON permanecem imutáveis.
"""

from pathlib import Path

from src.ui_data import PROFILE_FILES, load_profile

MAX_EXAMPLES = 5
PROTECTED_EXAMPLES = tuple(PROFILE_FILES)


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


def can_delete_example(examples: dict, name: str) -> bool:
    """Somente exemplos adicionais presentes na sessão podem ser excluídos."""
    return name in examples and name not in PROTECTED_EXAMPLES


def delete_example(examples: dict, name: str) -> str:
    """Exclui um exemplo adicional e renumera os restantes sem alterar os dados.

    A seleção retorna ao exemplo imediatamente anterior na ordem original.
    Cada entrada mantém suas próprias referências ``original`` e ``values``.
    """
    if name not in examples:
        raise ValueError(f"Exemplo desconhecido: {name}")
    if not can_delete_example(examples, name):
        raise ValueError(f"Exemplo protegido contra exclusão: {name}")

    names = tuple(examples)
    previous_name = names[names.index(name) - 1]
    survivors = [entry for current, entry in examples.items() if current != name]
    examples.clear()
    for index, entry in enumerate(survivors, start=1):
        examples[f"Exemplo {index}"] = entry
    return previous_name
