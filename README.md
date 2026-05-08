# Fluxo Pessoal

Fluxo Pessoal é uma plataforma de controle financeiro mensal para uso pessoal, com organização próxima à contabilidade: múltiplas contas, saldo inicial, saldo calculado, importação de extratos, plano de contas, classificação automática, conciliação e exportação Excel.

## Tecnologias

Backend:
- Python, FastAPI, SQLAlchemy 2.0, Alembic
- PostgreSQL
- Pandas, OpenPyXL
- ofxparse
- Pydantic
- Docker

Frontend:
- React, TypeScript, Vite
- TailwindCSS
- Axios
- React Router
- TanStack Query

## Estrutura

```text
fluxo-pessoal/
  backend/
    app/
      core/
      models/
      schemas/
      routes/
      services/
        importers/
      repositories/
      utils/
    alembic/
    requirements.txt
    Dockerfile
  frontend/
    src/
      components/
      pages/
      routes/
      services/
      types/
  docker-compose.yml
```

## Rodar com Docker

Na raiz do projeto:

```bash
docker compose up --build
```

O `docker-compose.yml` sobe:
- PostgreSQL em `localhost:5432`
- Backend FastAPI em `http://localhost:8000`
- Frontend Vite em `http://localhost:5173`

O backend executa `alembic upgrade head` antes de iniciar o Uvicorn.

Swagger:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

## Rodar backend manualmente

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg://fluxo:fluxo@localhost:5432/fluxo_pessoal
alembic upgrade head
uvicorn app.main:app --reload
```

No Linux/macOS, troque `set` por `export`.

## Rodar frontend manualmente

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

Para apontar para outra API:

```bash
VITE_API_URL=http://localhost:8000/api npm run dev
```

## Migrações Alembic

Aplicar migrações:

```bash
cd backend
alembic upgrade head
```

Criar nova migração:

```bash
alembic revision --autogenerate -m "descricao"
```

## Plano de contas padrão

Após subir a API, popular o plano inicial:

```http
POST /api/chart-accounts/seed-default
```

Esse seed cria grupos para receitas, despesas fixas, despesas variáveis, dívidas, reservas, transferências internas e ajustes.

## Fluxo de importação

Importadores disponíveis:
- Nubank CSV: `POST /api/imports/nubank-csv`
- Nubank OFX: `POST /api/imports/nubank-ofx`
- Mercado Pago XLSX: `POST /api/imports/mercado-pago-xlsx`

Cada importação:
1. Recebe `account_id` e arquivo.
2. Lê o formato com Pandas ou ofxparse.
3. Normaliza data, descrição, valor, direção, origem e identificador externo.
4. Limpa a descrição.
5. Gera fingerprint por conta, data, valor, descrição limpa e external id.
6. Ignora duplicidades.
7. Aplica regras automáticas.
8. Salva o lote em `import_batches`.
9. Recalcula saldos.

Observações dos formatos já tratados:
- O importador Nubank CSV aceita CSV normal e também arquivo Excel com extensão `.csv` quando o conteúdo vem como linhas CSV em uma única coluna.
- O importador Nubank OFX lê OFX UTF-8 e possui fallback para extratos OFX SGML.
- O importador Mercado Pago XLSX ignora as linhas iniciais de resumo e identifica o cabeçalho real com `RELEASE_DATE`, `TRANSACTION_TYPE`, `REFERENCE_ID` e `TRANSACTION_NET_AMOUNT`.
- Textos com mojibake comum, como `TransferÃªncia` e `â€¢`, são reparados antes da normalização e geração de fingerprint.

## Classificação automática

As regras ficam em `classification_rules` e usam:
- `contains`
- `equals`
- `starts_with`
- `regex`

Ao importar ou lançar manualmente sem categoria, o `ClassifierService` busca regras ativas por prioridade. Se encontrar, define plano de contas, tipo e status `automatic`. Caso contrário, a movimentação fica `pending`.

Ao classificar manualmente uma pendência, a interface permite informar uma palavra-chave e criar regra automática para próximas importações.

## Saldos e conciliação

O saldo oficial é sempre:

```text
saldo inicial da conta + soma das movimentações
```

O campo `current_balance` é recalculado para consulta rápida.

Conciliação:

```http
POST /api/balances/reconcile
```

Compara saldo calculado com saldo real informado por conta e mês, gravando snapshots como `balanced` ou `divergent`.

## Exportação Excel

Endpoint:

```http
GET /api/reports/export-excel?month=YYYY-MM
```

A planilha contém:
1. Resumo Geral
2. Saldos por Conta
3. Movimentações
4. Plano de Contas
5. Categorias
6. Pendentes de Classificação
7. Regras Automáticas
8. Comparativo Mensal
9. Entradas
10. Saídas
11. Transferências
12. Ajustes

As abas possuem cabeçalho destacado, filtros, primeira linha congelada, colunas ajustadas e formatação de moeda/data.

## Endpoints principais

Contas:
- `POST /api/accounts`
- `GET /api/accounts`
- `GET /api/accounts/balances`
- `GET /api/accounts/consolidated-balance`

Movimentações:
- `POST /api/transactions/manual`
- `GET /api/transactions`
- `GET /api/transactions/pending`
- `PUT /api/transactions/{id}/classify`
- `POST /api/transactions/{id}/create-rule-from-classification`

Relatórios:
- `GET /api/reports/monthly?month=YYYY-MM`
- `GET /api/reports/categories?month=YYYY-MM`
- `GET /api/reports/comparison?start_month=YYYY-MM&end_month=YYYY-MM`
- `GET /api/reports/export-excel?month=YYYY-MM`
