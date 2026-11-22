"""Testes do ZIP de diagnóstico gerado após os testes visuais."""

import json
from pathlib import Path
from zipfile import ZipFile

from scripts.package_visual_results import ARCHIVE_NAME, package


def test_package_includes_evidence_and_excludes_local_training_data(tmp_path):
    (tmp_path / "results/playwright-report").mkdir(parents=True)
    (tmp_path / "results/playwright-artifacts").mkdir(parents=True)
    (tmp_path / "tests/visual/interface.spec.mjs-snapshots").mkdir(parents=True)
    (tmp_path / "results/playwright-report/index.html").write_text("relatório", encoding="utf-8")
    (tmp_path / "results/playwright-artifacts/diff.png").write_bytes(b"fakepng")
    (tmp_path / "results/playwright-results.json").write_text(json.dumps({
        "stats": {"expected": 3, "unexpected": 1, "flaky": 0, "skipped": 0}
    }), encoding="utf-8")
    (tmp_path / "results/playwright-console.log").write_text("Teste falhou", encoding="utf-8")
    (tmp_path / "tests/visual/interface.spec.mjs-snapshots/mono-01-inicial-1280x720-win32.png").write_bytes(b"ref")
    (tmp_path / "tests/visual/interface.spec.mjs-snapshots/dashboard-03-concluido-390-win32.png").write_bytes(b"obsoleto")
    (tmp_path / "tests/visual/interface.spec.mjs").write_text("teste", encoding="utf-8")
    (tmp_path / "results/baseline.joblib").write_bytes(b"modelo privado")
    (tmp_path / "data/raw").mkdir(parents=True)
    (tmp_path / "data/raw/clientes.csv").write_text("dados locais", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")

    archive = package(tmp_path, exit_code=1, mode="comparacao")
    assert archive == tmp_path / "results" / ARCHIVE_NAME
    with ZipFile(archive) as zipped:
        names = set(zipped.namelist())
        assert "manifesto.json" in names
        assert "relatorio-html/index.html" in names
        assert "artefatos/diff.png" in names
        assert "referencias-visuais/interface.spec.mjs-snapshots/mono-01-inicial-1280x720-win32.png" in names
        assert "resultados.json" in names
        assert "execucao.log" in names
        assert not any("dashboard-03" in name for name in names)
        assert "configuracao/interface.spec.mjs" in names
        assert all("joblib" not in name and "clientes.csv" not in name for name in names)
        manifest = json.loads(zipped.read("manifesto.json"))
        assert manifest["status"] == "falhou"
        assert manifest["resumo_playwright"]["falhas"] == 1


def test_package_created_even_when_reports_are_missing(tmp_path):
    archive = package(tmp_path, exit_code=1, mode="comparacao")
    assert archive.is_file()
    with ZipFile(archive) as zipped:
        manifest = json.loads(zipped.read("manifesto.json"))
        assert manifest["status"] == "falhou"
        assert manifest["resumo_playwright"] == {"disponivel": False}
        assert "LEIA-PRIMEIRO.txt" in zipped.namelist()
