"""Junta todos os concursos num único dist/concursos.json, pronto para apps, MCPs e análises.

Uso: python scripts/gerar.py
"""

from __future__ import annotations

import json
from pathlib import Path

from validar import DADOS, RAIZ, carregar


def main() -> None:
    concursos = [carregar(a) for a in sorted(DADOS.rglob("*.yaml"))]
    concursos.sort(key=lambda c: (c["orgao"]["sigla"], c["edicao"]))
    saida = RAIZ / "dist" / "concursos.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps({"concursos": concursos}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(concursos)} concurso(s) → {saida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
