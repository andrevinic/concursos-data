"""Valida todos os arquivos de data/concursos/ contra o schema e regras de consistência.

Uso: python scripts/validar.py
Sai com código 1 se houver erro. Avisos não falham a validação.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

RAIZ = Path(__file__).resolve().parent.parent
SCHEMA = RAIZ / "schema" / "concurso.schema.json"
SCHEMA_PROVA = RAIZ / "schema" / "prova.schema.json"
DADOS = RAIZ / "data" / "concursos"
PROVAS = RAIZ / "data" / "provas"
MATERIAS = RAIZ / "data" / "taxonomia" / "materias.yaml"


class _Loader(yaml.SafeLoader):
    """SafeLoader que mantém datas como texto (o schema espera AAAA-MM-DD em string)."""


_Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def carregar(arquivo: Path) -> dict:
    with arquivo.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=_Loader)


def checar_regras(c: dict, arquivo: Path) -> tuple[list[str], list[str]]:
    erros: list[str] = []
    avisos: list[str] = []

    esperado = f"{arquivo.parent.name}-{arquivo.stem}"
    if c["id"] != esperado:
        erros.append(f"id '{c['id']}' deveria ser '{esperado}' (pasta-arquivo)")
    if str(c["edicao"]) != arquivo.stem:
        erros.append(f"edicao {c['edicao']} não bate com o nome do arquivo {arquivo.name}")

    ids_cargo = [cg["id"] for cg in c.get("cargos", [])]
    if len(ids_cargo) != len(set(ids_cargo)):
        erros.append("ids de cargo repetidos")
    for cg in c.get("cargos", []):
        v = cg.get("vagas") or {}
        if "total" in v:
            partes = [v[k] for k in ("ampla", "negros", "pcd") if k in v]
            if len(partes) == 3 and sum(partes) != v["total"]:
                erros.append(f"{cg['id']}: ampla+negros+pcd = {sum(partes)} ≠ total {v['total']}")
            if v.get("por_uf") and sum(v["por_uf"].values()) != v["total"]:
                erros.append(f"{cg['id']}: soma por UF = {sum(v['por_uf'].values())} ≠ total {v['total']}")
    for d in c.get("documentos", []):
        if d.get("cargo") and d["cargo"] not in ids_cargo:
            erros.append(f"documento '{d['titulo']}' cita cargo inexistente '{d['cargo']}'")

    datas = c.get("datas", {})
    ordem = ["edital", "inscricoes_inicio", "inscricoes_fim", "prova_objetiva", "gabarito_preliminar", "gabarito_definitivo", "homologacao"]
    presentes = [(k, datas[k]) for k in ordem if k in datas]
    for (k1, d1), (k2, d2) in zip(presentes, presentes[1:]):
        if d1 > d2:
            erros.append(f"datas fora de ordem: {k1} {d1} > {k2} {d2}")

    tipos = {f["tipo"] for f in c["fontes"]}
    if c["situacao"] != "previsto" and not tipos & {"oficial", "diario_oficial"}:
        avisos.append("nenhuma fonte oficial; marque os fatos em a_verificar")
    return erros, avisos


def checar_prova(p: dict, arquivo: Path, concursos: dict[str, dict], materias: set[str]) -> list[str]:
    erros: list[str] = []
    esperado = f"{arquivo.parent.name}-{arquivo.stem}"
    if p["id"] != esperado:
        erros.append(f"id '{p['id']}' deveria ser '{esperado}' (pasta-arquivo)")
    c = concursos.get(p["concurso"])
    if c is None:
        return erros + [f"concurso '{p['concurso']}' não existe em data/concursos"]
    if p["cargo"] not in {cg["id"] for cg in c["cargos"]}:
        erros.append(f"cargo '{p['cargo']}' não existe em {p['concurso']}")
    cadernos = {cd["id"]: cd for cd in p["cadernos"]}
    vistos: set[tuple[str, int]] = set()
    for it in p["itens"]:
        cd = cadernos.get(it["caderno"])
        chave = (it["caderno"], it["n"])
        if cd is None:
            erros.append(f"item {it['n']}: caderno '{it['caderno']}' não declarado")
            continue
        if chave in vistos:
            erros.append(f"item {it['n']} repetido no caderno {it['caderno']}")
        vistos.add(chave)
        ini, fim = cd["itens"]
        if not ini <= it["n"] <= fim:
            erros.append(f"item {it['n']} fora da faixa {ini}-{fim} do caderno {it['caderno']}")
        if it["materia"] not in materias:
            erros.append(f"item {it['n']}: matéria '{it['materia']}' não está em data/taxonomia/materias.yaml")
        if p["formato"] == "certo_errado" and it["gabarito"] not in {"C", "E", "X"}:
            erros.append(f"item {it['n']}: gabarito '{it['gabarito']}' inválido para certo/errado")
    for cd in cadernos.values():
        ini, fim = cd["itens"]
        faltando = [n for n in range(ini, fim + 1) if (cd["id"], n) not in vistos]
        if faltando:
            erros.append(f"caderno {cd['id']}: faltam os itens {faltando}")
    return erros


def validar_provas(concursos: dict[str, dict]) -> int:
    validador = Draft202012Validator(json.loads(SCHEMA_PROVA.read_text(encoding="utf-8")), format_checker=FormatChecker())
    materias = set(carregar(MATERIAS)["materias"])
    total = 0
    for arq in sorted(PROVAS.rglob("*.yaml")):
        rel = arq.relative_to(RAIZ)
        p = carregar(arq)
        erros = [f"{'/'.join(map(str, e.absolute_path)) or '(raiz)'}: {e.message}" for e in validador.iter_errors(p)]
        if not erros:
            erros = checar_prova(p, arq, concursos, materias)
        for e in erros:
            print(f"✗ {rel}: {e}")
        if not erros:
            print(f"✓ {rel} ({len(p['itens'])} itens)")
        total += len(erros)
    return total


def main() -> int:
    validador = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker())
    arquivos = sorted(DADOS.rglob("*.yaml"))
    total_erros = 0
    ids: dict[str, Path] = {}
    validos: dict[str, dict] = {}
    for arq in arquivos:
        rel = arq.relative_to(RAIZ)
        try:
            c = carregar(arq)
        except yaml.YAMLError as e:
            print(f"✗ {rel}: YAML inválido: {e}")
            total_erros += 1
            continue
        erros = [f"{'/'.join(map(str, e.absolute_path)) or '(raiz)'}: {e.message}" for e in validador.iter_errors(c)]
        avisos: list[str] = []
        if not erros:
            erros, avisos = checar_regras(c, arq)
            if c["id"] in ids:
                erros.append(f"id repetido, também em {ids[c['id']].relative_to(RAIZ)}")
            ids[c["id"]] = arq
            validos[c["id"]] = c
        for a in avisos:
            print(f"⚠ {rel}: {a}")
        if erros:
            total_erros += len(erros)
            for e in erros:
                print(f"✗ {rel}: {e}")
        else:
            print(f"✓ {rel}")
    total_erros += validar_provas(validos)
    print(f"\n{total_erros} erro(s)")
    return 1 if total_erros else 0


if __name__ == "__main__":
    sys.exit(main())
