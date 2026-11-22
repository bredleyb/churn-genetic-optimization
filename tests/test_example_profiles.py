"""Cobertura da criação e restauração independente de exemplos."""

from pathlib import Path

import pytest

from src.example_profiles import MAX_EXAMPLES, append_example, initial_examples, is_original
from src.ui_data import PROFILE_FILES, model_input

ROOT = Path(__file__).resolve().parents[1]


def test_defaults_preserve_both_reference_profiles():
    examples = initial_examples(ROOT)
    assert tuple(examples) == tuple(PROFILE_FILES) == ("Exemplo 1", "Exemplo 2")
    for name, entry in examples.items():
        assert entry["original"] == entry["values"]
        assert entry["original"] is not entry["values"]
        assert len(model_input(entry["values"])) == 19
        assert is_original(examples, name, entry["values"])


def test_additional_examples_snapshot_current_values_until_five():
    examples = initial_examples(ROOT)
    customer = examples["Exemplo 1"]["values"].copy()
    customer["tenure"] = 24
    for index in range(3, MAX_EXAMPLES + 1):
        name = append_example(examples, customer)
        assert name == f"Exemplo {index}"
        assert examples[name]["values"]["tenure"] == customer["tenure"]
        assert is_original(examples, name, examples[name]["values"])
        customer["tenure"] += 1
    assert len(examples) == MAX_EXAMPLES
    with pytest.raises(ValueError, match="Limite de 5"):
        append_example(examples, customer)


def test_edits_and_restoration_do_not_mutate_other_examples():
    examples = initial_examples(ROOT)
    created = append_example(examples, examples["Exemplo 2"]["values"])
    examples[created]["values"]["MonthlyCharges"] = 123.0
    assert not is_original(examples, created, examples[created]["values"])
    assert is_original(examples, "Exemplo 2", examples["Exemplo 2"]["values"])
    assert examples["Exemplo 2"]["values"]["MonthlyCharges"] != 123.0
    examples[created]["values"] = examples[created]["original"].copy()
    assert is_original(examples, created, examples[created]["values"])
