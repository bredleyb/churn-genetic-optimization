import json
import subprocess
import sys

from src.analysis import profile_as_markdown, profile_dataset
from src.data import normalize_dataset


def test_profile_contains_only_aggregated_statistics(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    profile = profile_dataset(data)
    assert profile["registros"] == 40
    assert profile["caracteristicas_candidatas"] == 19
    assert profile["classes"]["Yes"]["clientes"] == 10
    assert profile["classes"]["No"]["clientes"] == 30
    assert profile["qualidade"]["ausentes_por_coluna"]["TotalCharges"] == 1
    assert profile["cancelamentos_por_contrato"]
    content = json.dumps(profile, ensure_ascii=False)
    assert "TESTE-0000" not in content
    markdown = profile_as_markdown(profile)
    assert "Cancelamentos por tipo de contrato" in markdown
    assert "As taxas apresentadas são descritivas" in markdown


def test_cli_generates_json_and_markdown(tmp_path, sample_raw_data):
    file = tmp_path / "telco.csv"
    out = tmp_path / "relatorios"
    sample_raw_data.to_csv(file, index=False)
    cmd = [
        sys.executable,
        "-m",
        "scripts.analyze_data",
        "--data",
        str(file),
        "--output",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "Desenvolvimento: 32 | Teste: 8" in result.stdout
    content = json.loads((out / "analise_dados.json").read_text(encoding="utf-8"))
    assert content["divisao"]["desenvolvimento_registros"] == 32
    assert content["divisao"]["teste_registros"] == 8
    assert (out / "analise_dados.md").is_file()
