# concursos-data

**Base de dados aberta de concursos públicos brasileiros**, feita para quem constrói ferramentas de estudo:
apps, assistentes de IA, servidores MCP, painéis, planilhas.

> 🚧 **v0, começando pela PRF.** O próximo concurso da PRF é esperado para 2027, então ela é o
> primeiro concurso coberto. Contribuições para outros órgãos são bem-vindas.

## O que tem aqui

Um arquivo YAML por concurso (uma edição), em `data/concursos/<orgao>/<ano>.yaml`:

- órgão, banca e situação (`previsto` → `edital_publicado` → `realizado` → `homologado`…)
- cargos, requisitos, vagas (ampla, negros, PcD, por UF) e etapas
- datas: edital, inscrições, prova, gabaritos
- **links para os documentos oficiais** (edital, retificações, provas, gabaritos)
- **fontes** de cada informação, e uma lista `a_verificar` com o que ainda não foi confirmado em fonte oficial

```yaml
id: prf-2018
orgao: { sigla: PRF, nome: Polícia Rodoviária Federal, esfera: federal }
edicao: 2018
banca: Cebraspe
situacao: realizado
cargos:
  - id: policial-rodoviario-federal
    vagas: { total: 500, ampla: 367, negros: 100, pcd: 33, por_uf: { PA: 81, RO: 74, … } }
documentos:
  - tipo: retificacao
    url: https://cdn.cebraspe.org.br/concursos/PRF_18/arquivos/ED_2_PRF_2018_RET2.PDF
```

O formato está em [`schema/concurso.schema.json`](schema/concurso.schema.json).

## Cobertura

| Órgão | Edições |
|---|---|
| PRF | 2018, 2021, 2027 (previsto) |

## Questões

Para cada prova, `data/provas/<orgao>/<ano>-<etapa>.yaml` guarda os **links dos cadernos oficiais** e, para
cada item, **matéria, assunto e gabarito definitivo** (C, E ou X para anulado). O texto das questões **não fica
no repositório**: um script baixa os PDFs do site da banca e monta o banco completo na sua máquina.

```bash
.venv/bin/python scripts/baixar_questoes.py prf-2021-objetiva   # → questoes/prf-2021-objetiva.jsonl
.venv/bin/python scripts/baixar_questoes.py --todas
```

Cada linha do `.jsonl`:

```json
{"prova": "prf-2021-objetiva", "caderno": "geral", "n": 40, "materia": "fisica",
 "assunto": "Mecânica clássica", "gabarito": "C",
 "contexto": "Um projétil foi lançado obliquamente… julgue os itens que se seguem.",
 "enunciado": "Durante todo o movimento, a aceleração vetorial do projétil será constante.",
 "pagina": 2, "fonte": "https://cdn.cebraspe.org.br/…/578_PRF_001_01.PDF"}
```

Limitações: figuras, tabelas e índices de fórmulas (o "n" de qₙ) não são extraídos. Confira com o PDF oficial.

| Prova | Itens | Anulados |
|---|---|---|
| PRF 2021, objetiva (Cebraspe, Certo/Errado) | 120 (1–8 em inglês **ou** espanhol) | 11 |

## Como usar

Os arquivos prontos ficam em `dist/`: `concursos.json` (todos os concursos) e `provas.json` (itens com
matéria, assunto e gabarito). Para gerar:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/validar.py   # schema + regras (vagas somam, datas em ordem, ids)
.venv/bin/python scripts/gerar.py     # gera dist/concursos.json e dist/provas.json
```

## Princípios

1. **Fonte em tudo.** Cada fato importante tem uma fonte. Oficial (banca, órgão, Diário Oficial) vale mais que
   imprensa ou cursinho. O que só veio de fonte não oficial vai para `a_verificar`.
2. **Links, não cópias.** O repositório aponta para os PDFs oficiais e não guarda cópias de provas, editais
   ou do texto das questões. O texto é montado na máquina de quem usa, direto da fonte oficial.
3. **Nada de conteúdo de plataformas.** Não copie questões, comentários, classificações ou estatísticas do
   TecConcursos, QConcursos, Gran, Estratégia ou outras plataformas: são trabalho e conteúdo delas.
4. **Previsão não é fato.** Concurso sem portaria é `previsto`, e números da imprensa ficam em `a_verificar`.

## Próximos passos

- [ ] Completar PRF 2018 (Edital nº 1, prova e gabaritos oficiais)
- [ ] Outros concursos policiais: PF, PCs, polícias científicas
- [ ] Taxonomia aberta de matérias e assuntos
- [x] Camada de questões: gabarito definitivo, matéria e assunto por item; texto montado localmente
- [ ] Edições anteriores da PRF; marcar itens desatualizados por mudança de lei
- [ ] Análise jurídica antes de qualquer redistribuição do texto das provas
- [ ] Servidor MCP lendo esta base

## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md). Corrigir uma data, adicionar um link oficial ou um concurso novo
já ajuda muito.

## Licença

- Código (`scripts/`, `schema/`): [MIT](LICENSE)
- Dados (`data/`, `dist/`): [CC BY 4.0](LICENSE-DATA). Use à vontade, citando o concursos-data.

Projeto independente, sem vínculo com bancas, órgãos ou plataformas de questões.
