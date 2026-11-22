# Como contribuir

1. Faça um fork e crie um branch.
2. Edite ou crie `data/concursos/<orgao>/<ano>.yaml` (pasta em minúsculo, ex.: `pf/2021.yaml`).
   O `id` é `<orgao>-<ano>`. Copie um arquivo existente como modelo.
3. Para **cada informação nova, adicione a fonte** em `fontes`, com `acessado_em`.
   - Prefira o edital, o site da banca ou o Diário Oficial (`tipo: oficial` ou `diario_oficial`).
   - Se só achou em notícia ou cursinho, use `tipo: imprensa`/`cursinho` e liste o fato em `a_verificar`.
4. Rode a validação:
   ```bash
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   .venv/bin/python scripts/validar.py
   ```
5. Abra o pull request. A validação roda automaticamente.

## Regras

- Links para documentos **oficiais**. Não suba PDFs para o repositório.
- **Não copie** questões, comentários, classificações ou estatísticas de plataformas de questões.
- Não coloque dados pessoais de candidatos (nomes, notas, inscrições).
- Datas em `AAAA-MM-DD`. Valores em reais, sem símbolo (`9899.88`).
- Na dúvida, abra uma issue.
