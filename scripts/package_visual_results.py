"""Gera um ZIP de revisão com as evidências dos testes visuais.

Inclui somente artefatos do Playwright e arquivos da própria suíte de testes.
O CSV bruto e os modelos de aprendizagem de máquina ficam fora do arquivo.
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ARCHIVE_NAME = "testes-visuais-para-revisao.zip"
SOURCES = (
    ("results/playwright-report", "relatorio-html"),
    ("results/playwright-artifacts", "artefatos"),
    ("results/playwright-results.json", "resultados.json"),
    ("results/playwright-console.log", "execucao.log"),
    ("tests/visual", "referencias-visuais"),
    ("playwright.config.mjs", "configuracao/playwright.config.mjs"),
    ("package.json", "configuracao/package.json"),
    ("docs/roteiro_testes_cliente.md", "configuracao/roteiro_testes_cliente.md"),
    ("tests/visual/client.helpers.mjs", "configuracao/client.helpers.mjs"),
    ("tests/visual/client.layout.spec.mjs", "configuracao/client.layout.spec.mjs"),
    ("tests/visual/client.profiles.spec.mjs", "configuracao/client.profiles.spec.mjs"),
    ("tests/visual/client.fields.spec.mjs", "configuracao/client.fields.spec.mjs"),
    ("tests/visual/client.scroll.spec.mjs", "configuracao/client.scroll.spec.mjs"),
    ("tests/visual/client.prediction.spec.mjs", "configuracao/client.prediction.spec.mjs"),
)


def _files_in(directory: Path):
    """Percorre arquivos reais, evitando symlinks e arquivos temporários."""
    if directory.is_file() and not directory.is_symlink():
        yield directory, None
    elif directory.is_dir() and not directory.is_symlink():
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not path.is_symlink():
                yield path, path.relative_to(directory)


def _summary(report_file: Path) -> dict:
    if not report_file.is_file():
        return {"disponivel": False}
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError, OSError) as exc:
        return {"disponivel": False, "erro": str(exc)}
    stats = report.get("stats", {})
    metadata = report.get("config", {}).get("metadata", {})
    return {
        "git_head_testado": metadata.get("gitHead"),
        "arquivos_versionados_sem_alteracoes": metadata.get("trackedTreeClean"),
        "disponivel": True,
        "aprovados": stats.get("expected"),
        "falhas": stats.get("unexpected"),
        "instaveis": stats.get("flaky"),
        "ignorados": stats.get("skipped"),
        "duracao_ms": stats.get("duration"),
    }


def package(project_root: Path, *, exit_code: int | None, mode: str) -> Path:
    """Cria pacote completo mesmo quando o navegador ou os testes falharam."""
    root = project_root.resolve()
    output = root / "results" / ARCHIVE_NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.with_name(output.name + ".tmp")
    if staging.exists():
        staging.unlink()

    candidates = []
    archived = set()
    specs = tuple((path.relative_to(root).as_posix(), f"configuracao/{path.name}")
                  for path in sorted((root / "tests" / "visual").glob("*.spec.mjs")))
    for source, destination in (*SOURCES, *specs):
        path = root / source
        for file, relative in _files_in(path):
            if relative is not None:
                # A pasta tests/visual contém specs, mas aqui só interessam baselines.
                if source == "tests/visual":
                    # Não distribuir snapshots herdados da suíte antiga.
                    # Capturas desta auditoria são anexadas ao relatório Playwright;
                    # baselines opcionais devem começar com client-.
                    if (not any(part.endswith("-snapshots") for part in relative.parts)
                            or not relative.name.startswith("client-")
                            or relative.suffix.lower() != ".png"):
                        continue
                name = f"{destination}/{relative.as_posix()}"
            else:
                name = destination
            if name not in archived:
                archived.add(name)
                candidates.append((file, name))

    manifest = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "modo": mode,
        "status": "aprovado" if exit_code == 0 else ("falhou" if exit_code is not None else "nao_informado"),
        "codigo_saida_testes": exit_code,
        "larguras_previstas_px": [1440, 1366, 1280, 1024, 768, 390, 320],
        "resolucoes_previstas": ["1440x768", "1440x900", "1366x768", "1280x720", "1024x768", "768x1024", "768x900", "390x844", "390x900", "320x720"],
        "estados_previstos": ["inicial", "processamento", "concluido", "alterado",
                              "perfil_editado", "rolagem_inicio", "rolagem_meio", "rolagem_fim"],
        "roteiro": "configuracao/roteiro_testes_cliente.md",
        "escopo": "auditoria Cliente e Previsão; resultados de ML também têm suíte Python separada",
        "resumo_playwright": _summary(root / "results" / "playwright-results.json"),
        "arquivos": [name for _, name in candidates],
    }
    readme = (
        "PACOTE DE TESTES VISUAIS — PROJETO N3\n\n"
        "Envie este ZIP ao ChatGPT para revisar a interface.\n"
        "manifesto.json: status e lista de arquivos incluídos.\n"
        "execucao.log: saída completa dos testes no terminal.\n"
        "resultados.json: resultados estruturados de cada teste.\n"
        "relatorio-html/: relatório navegável, screenshots e anexos.\n"
        "artefatos/: traces, vídeos e imagens de diferença, quando gerados.\n"
        "referencias-visuais/: baselines opcionais da suíte Client.\n"
        "configuracao/: roteiro, specs e parâmetros para reproduzir cada desvio.\n"
        "As capturas CL-* são anexadas aos testes, consultáveis no relatório HTML.\n\n"
        "Se houver falhas, o ZIP continua sendo produzido para diagnóstico.\n"
        "Dados CSV, modelos .joblib e arquivos pessoais não são incluídos.\n"
    )

    try:
        with ZipFile(staging, "w", compression=ZIP_DEFLATED, compresslevel=6) as zipped:
            zipped.writestr("LEIA-PRIMEIRO.txt", readme)
            zipped.writestr("manifesto.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            for source, name in candidates:
                zipped.write(source, arcname=name)
        try:
            os.replace(staging, output)
        except PermissionError:
            # O Windows impede substituir um ZIP aberto por outro programa.
            # Guardar as evidências atuais com nome distinto evita enviar
            # acidentalmente o pacote antigo depois de uma falha de testes.
            suffix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
            output = output.with_name(f"{output.stem}-{suffix}{output.suffix}")
            os.replace(staging, output)
            print("Aviso: o ZIP anterior está bloqueado; resultado salvo com outro nome.")
    finally:
        if staging.exists():
            staging.unlink()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Empacota evidências do Playwright em um ZIP.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--test-exit-code", type=int, default=None)
    parser.add_argument("--mode", default="empacotamento-manual")
    args = parser.parse_args()
    path = package(args.project_root, exit_code=args.test_exit_code, mode=args.mode)
    print(f"\nZIP pronto para envio: {path}")
    print(f"Tamanho: {path.stat().st_size / 1024 / 1024:.1f} MiB")


if __name__ == "__main__":
    main()
