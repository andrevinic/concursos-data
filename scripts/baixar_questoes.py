"""Monta o banco de questões de uma prova NA SUA MÁQUINA, a partir dos PDFs oficiais da banca.

O repositório guarda só os fatos de cada item (matéria, assunto, gabarito definitivo) e os links
oficiais. Este script baixa os cadernos do site da banca, extrai o texto de cada item e junta
com os dados do repositório.

Uso:
    python scripts/baixar_questoes.py prf-2021-objetiva            # grava questoes/prf-2021-objetiva.jsonl
    python scripts/baixar_questoes.py --todas                      # todas as provas cadastradas
    python scripts/baixar_questoes.py prf-2021-objetiva --saida -  # imprime na tela

Formato de cada linha (JSON): prova, concurso, cargo, caderno, n, materia, assunto, gabarito,
contexto (texto-base e comando do bloco), enunciado, pagina, fonte.

Limitações: figuras, tabelas e fórmulas não são extraídas. Extração testada no layout Cebraspe
(itens Certo/Errado em duas colunas); confira com o PDF oficial em caso de dúvida.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

import pdfplumber

from validar import PROVAS, RAIZ, carregar

CACHE = Path.home() / ".cache" / "concursos-data"
SAIDA = RAIZ / "questoes"
RUIDO = re.compile(r"^(CEBRASPE\s*[–-]|Espaço livre|-- \d+ of \d+ --$)", re.I)
RECUO_MIN, RECUO_MAX = 10, 24  # recuo (pt) das linhas de continuação de um item, em relação ao número


def baixar(url: str, destino: Path) -> Path:
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "concursos-data (+https://github.com/andrevinic/concursos-data)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dados = r.read()
    if not dados.startswith(b"%PDF"):
        raise RuntimeError(f"{url} não devolveu um PDF")
    destino.write_bytes(dados)
    return destino


def linhas_em_ordem(pdf_path: Path) -> list[dict]:
    """Linhas de texto na ordem de leitura: página por página, coluna esquerda e depois a direita."""
    saida = []
    with pdfplumber.open(pdf_path) as pdf:
        for num, pg in enumerate(pdf.pages, start=1):
            meio = pg.width / 2
            for x0, x1 in ((0, meio), (meio, pg.width)):
                for ln in pg.crop((x0, 0, x1, pg.height)).extract_text_lines():
                    texto = ln["text"].strip()
                    if texto and not RUIDO.match(texto):
                        saida.append({"x": ln["x0"], "texto": texto, "pagina": num})
    return saida


def extrair_itens(linhas: list[dict], ini: int, fim: int) -> dict[int, dict]:
    """Encontra os itens ini..fim em sequência. Cada item leva o contexto (texto-base + comando) que o precede."""
    itens: dict[int, dict] = {}
    esperado, atual, contexto, pendente = ini, None, "", []
    for ln in linhas:
        m = re.match(rf"^{esperado}(?:\s+(.*))?$", ln["texto"]) if esperado <= fim else None
        if m:
            if pendente:
                contexto = " ".join(pendente)
                pendente = []
            atual = {"enunciado": [m.group(1) or ""], "x": ln["x"], "contexto": contexto, "pagina": ln["pagina"]}
            itens[esperado] = atual
            esperado += 1
            continue
        if atual is not None:
            recuo = ln["x"] - atual["x"]
            if RECUO_MIN <= recuo <= RECUO_MAX or (atual["enunciado"] == [""]):
                atual["enunciado"].append(ln["texto"])
                continue
            if len(ln["texto"]) <= 3 and recuo > RECUO_MAX:
                continue  # índice/expoente de fórmula (ex.: o "n" de q_n) solto numa linha própria
            atual = None
        pendente.append(ln["texto"])
    for it in itens.values():
        it["enunciado"] = re.sub(r"\s+", " ", " ".join(it["enunciado"])).strip()
        del it["x"]
    return itens


def montar(prova_id: str) -> list[dict]:
    arq = next((a for a in PROVAS.rglob("*.yaml") if carregar(a)["id"] == prova_id), None)
    if arq is None:
        raise SystemExit(f"Prova '{prova_id}' não encontrada em data/provas")
    p = carregar(arq)
    por_caderno: dict[str, dict[int, dict]] = {}
    for cd in p["cadernos"]:
        pdf = baixar(cd["prova"], CACHE / prova_id / Path(cd["prova"]).name)
        ini, fim = cd["itens"]
        por_caderno[cd["id"]] = extrair_itens(linhas_em_ordem(pdf), ini, fim)
        faltando = [n for n in range(ini, fim + 1) if n not in por_caderno[cd["id"]]]
        if faltando:
            print(f"⚠ {prova_id}/{cd['id']}: não achei o texto dos itens {faltando}", file=sys.stderr)
    fontes = {cd["id"]: cd["prova"] for cd in p["cadernos"]}
    questoes = []
    for it in p["itens"]:
        texto = por_caderno[it["caderno"]].get(it["n"], {})
        questoes.append({
            "prova": p["id"], "concurso": p["concurso"], "cargo": p["cargo"],
            "caderno": it["caderno"], "n": it["n"],
            "materia": it["materia"], "assunto": it.get("assunto"), "gabarito": it["gabarito"],
            "contexto": texto.get("contexto"), "enunciado": texto.get("enunciado"),
            "pagina": texto.get("pagina"), "fonte": fontes[it["caderno"]],
        })
    return questoes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("prova", nargs="?", help="id da prova, ex.: prf-2021-objetiva")
    ap.add_argument("--todas", action="store_true", help="todas as provas de data/provas")
    ap.add_argument("--saida", help="arquivo .jsonl de saída, ou - para a tela")
    args = ap.parse_args()
    ids = [carregar(a)["id"] for a in sorted(PROVAS.rglob("*.yaml"))] if args.todas else [args.prova]
    if not ids or ids == [None]:
        ap.error("informe uma prova ou --todas")
    for pid in ids:
        questoes = montar(pid)
        linhas = "".join(json.dumps(q, ensure_ascii=False) + "\n" for q in questoes)
        if args.saida == "-":
            sys.stdout.write(linhas)
            continue
        destino = Path(args.saida) if args.saida and not args.todas else SAIDA / f"{pid}.jsonl"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(linhas, encoding="utf-8")
        com_texto = sum(1 for q in questoes if q["enunciado"])
        print(f"{pid}: {len(questoes)} questões ({com_texto} com texto) → {destino}")


if __name__ == "__main__":
    main()
