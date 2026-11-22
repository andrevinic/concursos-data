"""Gera dist/concursos.json e dist/provas.json (itens com matéria, assunto e gabarito, sem texto).

Uso: python scripts/gerar.py
"""

from __future__ import annotations

import json
from pathlib import Path

from validar import DADOS, PROVAS, RAIZ, carregar


def main() -> None:
    concursos = [carregar(a) for a in sorted(DADOS.rglob("*.yaml"))]
    concursos.sort(key=lambda c: (c["orgao"]["sigla"], c["edicao"]))
    saida = RAIZ / "dist" / "concursos.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps({"concursos": concursos}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(concursos)} concurso(s) → {saida.relative_to(RAIZ)}")
    provas = [carregar(a) for a in sorted(PROVAS.rglob("*.yaml"))]
    saida = RAIZ / "dist" / "provas.json"
    saida.write_text(json.dumps({"provas": provas}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(provas)} prova(s), {sum(len(p['itens']) for p in provas)} itens → {saida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
