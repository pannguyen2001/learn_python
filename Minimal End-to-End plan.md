# Mini Pipeline: Minimal End-to-End Draft (PLAN.md) - ChatGPT

https://chatgpt.com/c/6ae97bf5-1964-83ec-a0c7-1bc2384c381d


> Goal: one command takes a small dirty Excel file and produces Gold tables in cloud storage,
> writes a queryable run log, and gives the same result when run twice.
> Scope: single process, no multithreading, ~1k rows. Learn the whole flow first, go deep later.

---

## 0. How to use this plan

- Work **in order**. Do not start step N+1 until step N's "Done when" is true.
- Every step has the same sections: Goal, Input/Output, Build checklist, Test checklist, Security/Quality checklist, Observability checklist, Learn, Resources, Reference projects, Done when, Pitfalls.
- Time-box each step. Ship ugly, then improve. Write a 3-line "why I chose this" note in the README at the end of every step.
- Learning rule: **Problem -> Why -> First principles -> minimal version by hand -> then adopt a library -> then production concerns.**

## 1. Big picture

```
 sample.xlsx (dirty, 2 sheets, ~1k rows)
      | [1 EXTRACT]   Excel -> Parquet (all-string, 1 file per sheet)
      v
   data/staging/<run_id>/*.parquet
      | [2 LOAD]      append raw + metadata (_run_id, _source_file, _loaded_at)
      v
   data/bronze/<table>/        (immutable ledger)
      | [3 VALIDATE]  schema + null + duplicate + type + range rules
      |--> data/quarantine/<table>/  (rejected rows + _reject_reason)
      v
      | [4 CLEAN]     types, trim, dates, dedupe, null handling
      v
   data/silver/<table>/
      | [5 AGGREGATE] business metrics at a declared grain
      v
   data/gold/<metric>/
      | [6 PUBLISH]   upload silver + gold to object storage (MinIO -> real bucket)
      v
   cloud bucket / <run_id>/ ...

 Cross-cutting: [7 LOG] structured logs + pipeline_run_log  ->  [8 OBSERVE] queries + alert rule
 Runner: run_pipeline.py calls steps 1..6 in order, wrapped by logging (step 9)
```

Order note: clean **before** aggregate. Aggregating dirty data bakes errors into Gold.

## 2. Core principles (copy into README)

| Principle | Meaning in this project |
|---|---|
| Bronze is immutable | Never fix raw data in place; fix downstream so everything is replayable |
| Idempotent | Same `run_id` run twice = no duplicates, same output |
| Quarantine, don't delete | Rejected rows keep a reason and go to `quarantine/` |
| Reconcile | `rows_in = rows_out + rows_rejected` at every step, asserted |
| Config over code | Paths, rules, bucket names in `config/pipeline.yaml`; secrets only in env |
| Contract first | Schema/keys/nullability written down in YAML before code |
| Fail loudly | Hard failures stop the run and are logged; soft failures quarantine |
| Cloud is an adapter | Core logic never knows where files finally go |

## 3. Repo layout

```
mini_pipeline/
|-- config/
|   |-- pipeline.yaml          # paths, rules, bucket name (NO secrets)
|   `-- contract.yaml          # tables, columns, types, nullable, keys, ranges
|-- data/                      # gitignored
|   |-- raw/ staging/ bronze/ quarantine/ silver/ gold/
|-- src/mini_pipeline/
|   |-- config.py              # load + validate config
|   |-- extract.py             # step 1
|   |-- load_bronze.py         # step 2
|   |-- validate.py            # step 3
|   |-- clean.py               # step 4
|   |-- aggregate.py           # step 5
|   |-- publish.py             # step 6 (storage adapter)
|   |-- run_log.py             # step 7 (run-log table writer)
|   `-- logging_setup.py       # step 7
|-- scripts/
|   |-- make_dirty_sample.py   # step 0 sample generator
|   `-- observe.py             # step 8 queries/report
|-- tests/
|   |-- unit/ integration/ fixtures/
|-- run_pipeline.py            # step 9 runner
|-- .env.example               # template only; real .env gitignored
|-- .gitignore  pyproject.toml  README.md  PLAN.md
`-- .github/workflows/ci.yml   # pytest on push
```

## 4. Tool decisions (defaults, revisit later)

| Decision | Default | Later |
|---|---|---|
| Dataframe engine | Polars | pandas only for comparison |
| SQL / query | DuckDB (query Parquet directly) | dbt |
| Validation | Hand-written checks first | Pandera, then maybe Great Expectations |
| Storage format | Parquet files | Delta / Iceberg |
| Cloud | MinIO (S3-compatible, Docker) first | one real bucket (S3 or GCS); check current free-tier terms |
| Orchestration | Plain Python runner | Airflow / Dagster / Kestra |
| Observability | `pipeline_run_log` table + SQL queries | dashboard, alerts |
| Logging | stdlib `logging` JSON formatter | loguru / structlog |
| Bronze CDC | Skip (append-only with run_id) | hashdiff CDC (you already prototyped this) |

---

## STEP 0: Setup, sample data, data contract

**Goal:** a repo that runs tests, a deliberately dirty Excel file, and a written contract.

**Input -> Output:** nothing -> `data/raw/sample.xlsx`, `config/contract.yaml`, `config/pipeline.yaml`.

**Build checklist**
- [ ] Create repo, virtualenv (or `uv`), `pyproject.toml`, pinned dependencies
- [ ] `.gitignore` includes `data/`, `.env`, `*.parquet`, `__pycache__`
- [ ] `.env.example` with placeholder names only (no real values)
- [ ] `scripts/make_dirty_sample.py` generates 2 sheets (`customers`, `orders`), ~1k rows, seeded random so it is reproducible
- [ ] Dirt included on purpose: null keys, duplicate keys, mixed date formats, leading/trailing spaces, negative amount, text in a numeric column, inconsistent casing (`vn`, `VN`, `Vietnam`)
- [ ] A second file `sample_bad_schema.xlsx` with a missing required column (for a negative test)
- [ ] `contract.yaml`: per table, per column: name, type, nullable, is_key, allowed range/values
- [ ] `pipeline.yaml`: paths per layer, bucket name, rejection-rate threshold
- [ ] `config.py` loads YAML and fails fast on missing keys

**Test checklist**
- [ ] Generator is deterministic (same seed = same file hash)
- [ ] Config loader raises a clear error on a missing key

**Security / quality checklist**
- [ ] Sample data is synthetic (Faker), contains no real names/emails
- [ ] Pre-commit hook or CI step scans for secrets (e.g. gitleaks)

**Observability checklist**
- [ ] Decide the `run_id` format now (e.g. `YYYYMMDDTHHMMSSZ-<short-uuid>`)

**Learn:** data contracts, YAML config patterns, `pathlib`, seeded randomness, project packaging.

**Resources**
- Twelve-Factor App, section on config (search: "12factor config")
- Faker docs
- gitleaks (search: "gitleaks pre-commit")
- Research task R10 (data contracts)

**Reference projects:** the local dbt + DuckDB medallion article (retail sales scenario) for how a small business scenario frames the data; OpenMedallion for config-driven layout.

**Done when:** `pytest` runs (even with one trivial test), sample files exist, contract is written.

**Pitfalls:** making the dirt too clever. 6 to 8 kinds of dirt is enough.

---

## STEP 1: Extract (Excel -> Parquet)

**Goal:** faithfully copy each sheet into Parquet with **all columns as string**.

**Input -> Output:** `data/raw/*.xlsx` -> `data/staging/<run_id>/<table>.parquet` + an extract manifest (file, sheet, rows, file hash).

**Build checklist**
- [ ] Read workbook, list sheets, map sheet name -> table name via config
- [ ] Read every cell as string (no type inference)
- [ ] Preserve column order and original header text
- [ ] Write Parquet with explicit string schema and compression (e.g. zstd)
- [ ] Compute SHA-256 of the source file and store it in the manifest
- [ ] Record `rows_read` per sheet
- [ ] Unknown sheet -> log warning and skip (config decides); missing sheet -> hard fail

**Test checklist**
- [ ] Parquet row count equals sheet row count
- [ ] All columns are string type
- [ ] Empty sheet, missing file, corrupt file each produce a clear error
- [ ] Header-only sheet produces an empty Parquet with the right schema

**Security / quality checklist**
- [ ] Never execute macros; read `.xlsx` only, reject `.xlsm` unless explicitly allowed
- [ ] File hash recorded for duplicate-run and tamper detection
- [ ] Do not log cell values

**Observability checklist**
- [ ] Log: file, sheet, rows_read, duration, output path
- [ ] Write a `run_log` row for the step (status, rows_in, rows_out)

**Learn:** why all-string at the edge, Parquet basics (columnar layout, schema, row groups, compression), Excel pitfalls (dates stored as numbers, merged cells, hidden sheets, leading zeros).

**Resources**
- Apache Parquet documentation (format overview)
- Polars user guide: reading Excel / writing Parquet
- `fastexcel` and `openpyxl` docs
- Research task R3

**Reference projects:** forja-lakehouse (bronze ingest -> Parquet); quantmini (landing -> bronze flow and storage management).

**Done when:** one command converts both sample files; counts match; tests pass.

**Pitfalls:** letting the library infer types (silent data loss such as `00123` -> `123`); cleaning during extract.

---

## STEP 2: Load to Bronze

**Goal:** append staged data into Bronze with lineage metadata, safely re-runnable.

**Input -> Output:** `staging/<run_id>/*.parquet` -> `bronze/<table>/run_id=<run_id>/part.parquet`.

**Build checklist**
- [ ] Add columns `_run_id`, `_source_file`, `_source_sheet`, `_loaded_at`, `_row_number`
- [ ] Partition by `run_id`
- [ ] Idempotency: if `bronze/<table>/run_id=<run_id>` exists, skip and log
- [ ] Write to a temp path then atomic rename (no half-written partitions)
- [ ] Never modify existing Bronze partitions
- [ ] Add a helper to read "all of Bronze" or "latest run only" via DuckDB

**Test checklist**
- [ ] Run twice with the same `run_id` -> row count unchanged
- [ ] Run twice with different `run_id` and the same file -> decision is explicit (allow, or skip via file hash); write the rule down
- [ ] Interrupted write leaves no partial partition

**Security / quality checklist**
- [ ] Bronze folder treated as read-only after write
- [ ] Metadata columns clearly separated from business columns (prefix `_`)

**Observability checklist**
- [ ] Log rows loaded per table, partition path, skipped-because-exists
- [ ] `run_log` row per table

**Learn:** append-only vs overwrite, partitioning, atomic writes (temp + rename), idempotent load patterns, lineage metadata.

**Resources**
- Databricks medallion architecture docs (Bronze layer rules)
- DuckDB docs: reading Parquet, hive partitioning
- Research tasks R2, R4

**Reference projects:** forja-lakehouse; OpenMedallion (bronze config incl. incremental cursor state); your own earlier snapshot/CDC work for later extension.

**Done when:** double run proves idempotency; bronze is queryable with one DuckDB SQL statement.

**Pitfalls:** overwriting Bronze "to fix" bad rows; forgetting row numbers (you will want them for reject reports).

---

## STEP 3: Validate

**Goal:** split Bronze data into `valid` and `quarantine`, with reasons, and decide whether the run may continue.

**Input -> Output:** bronze (current run) -> in-memory `valid` frames + `quarantine/<table>/run_id=<run_id>/` + validation summary.

**Build checklist**
- [ ] Rule type 1: schema/column presence vs contract (missing column = hard fail; extra column = warn)
- [ ] Rule type 2: not-null on required columns and keys
- [ ] Rule type 3: duplicate business key (composite keys supported)
- [ ] Rule type 4: type-castability (can this string become int/decimal/date?)
- [ ] Rule type 5: range / allowed values (amount >= 0, country in list)
- [ ] Each failing row gets `_reject_reason` (rule name, column), a row can have several
- [ ] Severity model: `hard` (stop run) vs `soft` (quarantine and continue)
- [ ] Rejection-rate threshold from config; above it = hard fail
- [ ] Validation summary table: rule, table, rows_failed, severity
- [ ] Reconciliation assert: `rows_in == rows_valid + rows_quarantined` (count a row once)

**Test checklist**
- [ ] One unit test per rule using tiny hand-made frames
- [ ] Composite-key duplicate test
- [ ] Row failing two rules is counted once in reconciliation
- [ ] `sample_bad_schema.xlsx` triggers a hard fail with a clear message
- [ ] Threshold breach fails the run

**Security / quality checklist**
- [ ] Reject reasons never include raw sensitive values
- [ ] Quarantine is stored, not discarded, and access-controlled like Bronze
- [ ] Rules live in `contract.yaml`, not scattered in code

**Observability checklist**
- [ ] Log per-rule failure counts, never row contents
- [ ] Persist validation summary into the run log

**Learn:** hard vs soft failure, severity, reconciliation, null semantics, composite keys, building rules as data.

**Resources**
- Dagster tutorial pages on asset checks (concept of checks that run when an asset is materialized)
- Pandera docs (for phase 2, after your hand-written version works)
- Great Expectations docs (read concepts only)
- Research task R6

**Reference projects:** Dagster ETL tutorial (asset checks); quantmini (schema enforcement and type checking at the bronze boundary).

**Done when:** dirty sample splits into valid and quarantine with correct reasons and a passing reconciliation test.

**Pitfalls:** silently dropping rows; validating on already-cleaned data; putting business rules in the code instead of the contract.

---

## STEP 4: Clean (-> Silver)

**Goal:** turn valid rows into typed, standardized, deduplicated data.

**Input -> Output:** valid frames -> `silver/<table>/run_id=<run_id>/part.parquet` (or merged table, see checklist).

**Build checklist**
- [ ] Cast to contract types (int, decimal, date, bool)
- [ ] Trim whitespace; normalize case and known aliases (`vn`/`VN`/`Vietnam` -> `VN`)
- [ ] Parse mixed date formats into one ISO format; unparseable -> already quarantined in step 3, otherwise log
- [ ] Explicit null policy per column (drop / default / flag), documented in contract
- [ ] Deterministic dedupe rule (e.g. keep latest `_loaded_at`, tie-break on `_row_number`)
- [ ] Decide Silver write mode: per-run partitions vs merged current table; write the decision in README
- [ ] Count how many rows each cleaning rule changed

**Test checklist**
- [ ] Cleaning twice equals cleaning once (idempotent transform)
- [ ] Before/after golden-file test on the dirty sample
- [ ] Dedupe is deterministic across repeated runs
- [ ] Each cleaning rule has one focused unit test

**Security / quality checklist**
- [ ] Mask or hash direct identifiers if Silver is going to a shared bucket
- [ ] No rule depends on row order unless it is made explicit

**Observability checklist**
- [ ] Log per-rule "rows changed" counts
- [ ] Reconciliation: `rows_in = rows_out + rows_dropped_by_dedupe`

**Learn:** type casting pitfalls, date parsing, deterministic dedupe, null semantics, standardization/reference data, schema evolution basics.

**Resources**
- Polars user guide: expressions, string and datetime namespaces
- DuckDB docs: `TRY_CAST`, window functions (`ROW_NUMBER` for dedupe)
- Research task R5

**Reference projects:** OpenMedallion (silver as composable UDFs: rename, cast, filter); forja-lakehouse (Polars cleaning into silver); dbt + DuckDB article (silver layer modelling).

**Done when:** Silver matches a hand-checked expected file for the sample, and the idempotency test passes.

**Pitfalls:** "clever" regex cleaning without tests; changing business meaning (e.g. defaulting a missing amount to 0).

---

## STEP 5: Aggregate (-> Gold)

**Goal:** produce 2 to 3 business-ready tables at a clearly declared grain.

**Input -> Output:** silver -> `gold/<metric>/` Parquet.

**Build checklist**
- [ ] Write the grain of each Gold table in one sentence (e.g. "one row per month per country")
- [ ] Gold 1: sales by month and country (sum, count, average)
- [ ] Gold 2: top customers by revenue (window/rank)
- [ ] Gold 3: data-quality summary (rows valid / rejected per run and rule)
- [ ] Use DuckDB SQL files under `sql/gold/*.sql`, loaded by `aggregate.py`
- [ ] Include `_run_id` / `_built_at` columns for traceability

**Test checklist**
- [ ] Hand-compute one aggregate from the sample and assert equality
- [ ] Sum of Gold totals equals sum of Silver (reconciliation)
- [ ] Empty Silver input produces empty Gold, not a crash

**Security / quality checklist**
- [ ] Gold contains aggregates, not raw identifiers, where possible
- [ ] Check for double-counting caused by joins

**Observability checklist**
- [ ] Log rows per Gold table and build duration

**Learn:** grain, facts vs dimensions (star schema basics), group-by, window functions, reconciliation between layers.

**Resources**
- Kimball dimensional modeling basics (search: "Kimball four-step dimensional design")
- DuckDB docs: aggregates and window functions
- *Fundamentals of Data Engineering* (Reis & Housley), serving/analytics chapters

**Reference projects:** OpenMedallion (YAML-declared group-by metrics); dbt + DuckDB article (sales totals Gold layer); quantmini (gold as consumer-ready format).

**Done when:** Gold numbers match your hand calculation and reconcile with Silver.

**Pitfalls:** unclear grain; joining before deduping; adding dashboards before the numbers are right.

---

## STEP 6: Publish to cloud

**Goal:** upload Silver and Gold to object storage and verify the upload.

**Input -> Output:** local `silver/`, `gold/` -> `s3://<bucket>/<run_id>/...` (or GCS equivalent).

**Build checklist**
- [ ] Docker Compose file for MinIO (local S3-compatible) first
- [ ] `publish.py` exposes one interface: `upload(local_path, remote_key)`; storage backend chosen by config (local, MinIO, real cloud)
- [ ] Credentials only from environment variables
- [ ] Upload with `run_id` prefix; never overwrite previous runs
- [ ] Verify after upload: list objects, compare count and size (or checksum) with local
- [ ] Retry with backoff on transient failures (simple, max 3)
- [ ] Then repeat against one real bucket

**Test checklist**
- [ ] Unit tests with a mocked storage layer (e.g. `moto` for S3)
- [ ] Verification fails loudly if a file is missing or size differs
- [ ] One manual integration test against MinIO documented in README

**Security / quality checklist (most important step for this)**
- [ ] No keys in code, config, logs or Git history; `.env` gitignored
- [ ] IAM user/key scoped to one bucket with least privilege
- [ ] Bucket is private, public access blocked
- [ ] Encryption at rest enabled; HTTPS only
- [ ] Budget/billing alert set on any real account
- [ ] Rotate the key after the experiment

**Observability checklist**
- [ ] Log object count, bytes uploaded, duration, destination prefix (never credentials)
- [ ] Run-log row with status and bytes

**Learn:** object storage concepts (bucket, key, prefix), IAM and least privilege, `fsspec` abstraction, eventual consistency basics, cost model (storage, requests, egress).

**Resources**
- Data Engineering Zoomcamp: GCP, Docker, infrastructure modules (video playlist and repo)
- Your chosen cloud's official docs on IAM and bucket policies
- MinIO quickstart docs
- Research task R7, R8

**Reference projects:** Data Engineering Zoomcamp (cloud + Terraform + warehouse); quantmini (credentials handling guidance); OpenMedallion (swap filesystem for S3 with one config change).

**Done when:** the same pipeline publishes to MinIO and then to a real bucket by changing config only.

**Pitfalls:** hardcoded keys; making the bucket public "just to test"; forgetting to delete cloud resources.

---

## STEP 7: Logging

**Goal:** every run is traceable from one `run_id`.

**Build checklist**
- [ ] `logging_setup.py`: JSON formatter, `run_id` injected into every log line (via filter or adapter)
- [ ] Levels used consistently: INFO progress, WARNING recoverable, ERROR failed step
- [ ] `pipeline_run_log` table (DuckDB or SQLite): `run_id, step, table, status, started_at, ended_at, duration_s, rows_in, rows_out, rows_rejected, error_message, source_file_hash`
- [ ] Context manager `with step("validate", table):` that records start/end/status automatically and writes the row even on exceptions
- [ ] Log to console and to a file under `logs/` (gitignored)
- [ ] Redaction helper for anything that could contain sensitive values

**Test checklist**
- [ ] One run-log row per step per table per run
- [ ] A forced exception still produces a `failed` row with the error message
- [ ] A test asserts no sample value from the dataset appears in the log output

**Security / quality checklist**
- [ ] No secrets, tokens or raw PII in logs
- [ ] Log files rotated or size-limited

**Observability checklist**
- [ ] `run_id` is searchable across logs, run-log and Gold quality table

**Learn:** log levels, structured vs plain logs, correlation IDs, what to log vs what never to log, context managers for instrumentation.

**Resources**
- Python `logging` how-to (docs.python.org)
- Twelve-Factor App: logs as event streams
- loguru and structlog docs (after the stdlib version works)
- Note: you hit Loguru/multiprocessing sink problems before; this draft is single-process so keep it simple and revisit when you add parallelism

**Reference projects:** Dagster (per-asset run metadata); OpenMedallion (per-task observability via the Kestra flow it generates).

**Done when:** you can reconstruct exactly what happened in any run using only the log table and log file.

**Pitfalls:** logging only on success; logging row contents; free-text logs you cannot query.

---

## STEP 8: Observe

**Goal:** answer "is the pipeline healthy?" in under a minute, and fail on bad quality.

**Build checklist**
- [ ] Query 1: last run status per step
- [ ] Query 2: row-count trend per step across runs (volume)
- [ ] Query 3: rejection rate per rule across runs (quality)
- [ ] Query 4: duration per step across runs (performance)
- [ ] Query 5 (freshness): time since last successful run
- [ ] Alert rule v1: rejection rate above threshold or missing step = non-zero exit code + printed alert
- [ ] `scripts/observe.py` prints a text report; optional single HTML or Streamlit page later
- [ ] Schema-drift check: compare current columns to contract and log differences

**Test checklist**
- [ ] Inject a bad file and confirm the alert fires
- [ ] Inject an unchanged file twice and confirm freshness/volume queries behave as expected

**Security / quality checklist**
- [ ] Reports contain aggregates only, no row values

**Observability checklist**
- [ ] Write down 3 SLIs/SLOs (e.g. "pipeline succeeds daily", "rejection rate under 5 percent", "runtime under N seconds")

**Learn:** logs vs metrics vs traces, data observability dimensions (freshness, volume, schema, quality, lineage), basic SLI/SLO thinking, alert fatigue.

**Resources**
- Research task R10 (data observability pillars)
- Dagster docs on asset checks and run metadata
- *Fundamentals of Data Engineering*, undercurrents chapter (DataOps, observability)

**Reference projects:** Dagster ETL tutorial (checks + UI for health); OpenMedallion (Kestra flow with retries and observability).

**Done when:** a deliberately broken run is visible in your report and fails the command.

**Pitfalls:** building a dashboard before defining what "unhealthy" means.

---

## STEP 9: Runner, CI, documentation

**Goal:** one reproducible command, automated tests, and a README that explains the design.

**Build checklist**
- [ ] `run_pipeline.py`: steps 1..6 in order, stop on hard failure, always write run-log
- [ ] CLI options: `--config`, `--run-id`, `--from-step`, `--dry-run`
- [ ] Exit codes: 0 success, 1 hard failure, 2 quality-threshold breach
- [ ] GitHub Actions: install, lint, `pytest` (unit + integration on the sample), secret scan
- [ ] README: flow diagram, run instructions, design decisions, known limits, "what I would do for production"
- [ ] Makefile or task runner: `make sample`, `make run`, `make test`

**Test checklist**
- [ ] Full integration test: sample in -> expected Gold out
- [ ] Negative integration test: bad schema -> run fails with exit code 1
- [ ] Re-run test: second run changes nothing

**Security / quality checklist**
- [ ] CI uses repo secrets only for the optional cloud test; default CI uses mocks/MinIO service container
- [ ] Dependencies pinned; run a vulnerability check (e.g. `pip-audit`)

**Observability checklist**
- [ ] CI uploads the run log as an artifact on failure

**Learn:** CLI design (argparse/typer), exit codes, CI basics for data projects, README as design documentation.

**Resources**
- GitHub Actions docs
- `typer` or `argparse` docs
- Data Engineering Zoomcamp: testing and deployment module

**Reference projects:** Data Engineering Zoomcamp (end-to-end project structure); OpenMedallion (`init` / `run` command design).

**Done when:** a fresh clone can run `make sample && make run && make test` successfully.

---

## 5. Reference projects (easy -> hard)

| # | Project | What it is | Use it for | Level |
|---|---|---|---|---|
| 1 | Local medallion with dbt + DuckDB (article, dataengineerthings blog) | Retail sales ELT into Bronze/Silver/Gold on a laptop | Seeing the layers end to end | Easy |
| 2 | forja-lakehouse (PyPI) | Scaffold: bronze Parquet, silver Polars -> Delta, gold DuckDB | Folder structure and layer split | Easy-Medium |
| 3 | OpenMedallion (PyPI) | Declarative YAML pipelines with dlt, Polars, Kestra flow | Config-over-code, runner design | Medium |
| 4 | Dagster ETL tutorial with DuckDB (docs.dagster.io) | Assets, resources and asset checks | Validation gates, orchestration concepts | Medium-Hard |
| 5 | Data Engineering Zoomcamp (DataTalksClub, GitHub + YouTube) | 9-week course: Docker, GCP, Terraform, orchestration, dbt, BigQuery, testing | Cloud, infra, whole-project structure | Hard (broad) |
| Bonus | quantmini (PyPI) | Landing -> Bronze -> Silver -> Gold pipeline for market data | Schema enforcement, credential hygiene | Medium-Hard |

Caution: these were identified from search snippets. Skim each README before investing time, and verify current maintenance status.

## 6. Named research tasks

| ID | Task | Output | Needed by |
|---|---|---|---|
| R1 | Read the dbt + DuckDB article; map its layers to steps 1-5 | 10-line mapping note | Step 0 |
| R2 | Databricks medallion docs: what belongs in each layer | One-page layer rules for README | Step 2 |
| R3 | Parquet format basics: row groups, schema, compression | 5 facts affecting Step 1 | Step 1 |
| R4 | DuckDB docs: query Parquet, `COPY ... TO` Parquet, hive partitions | Working snippets | Steps 2, 5 |
| R5 | Polars user guide: expressions, lazy vs eager | Cheat sheet | Steps 3-4 |
| R6 | Pandera vs Great Expectations: pick one for phase 2 | Short comparison + choice | After Step 3 |
| R7 | DE Zoomcamp: GCP, Docker, orchestration modules only | Notes for Step 6 and runner | Step 6 |
| R8 | Object storage + IAM least privilege (your cloud's docs) | Written bucket-key policy | Step 6 |
| R9 | Book chapters: *Fundamentals of Data Engineering* (lifecycle, storage); *Designing Data-Intensive Applications* (batch processing, data formats) | Reading notes | Ongoing |
| R10 | "Data observability pillars" and "data contracts" | Definitions you can explain aloud | Steps 0, 8 |

## 7. Skills and mindset summary

**Knowledge:** medallion layers, Parquet, idempotency, data contracts, grain and star-schema basics, object storage and IAM, observability dimensions.

**Skills:** Polars/DuckDB SQL, writing rules as data, pytest (fixtures, parametrize, tmp_path), structured logging, Docker basics, GitHub Actions, secret handling.

**Tools:** Python, Polars, DuckDB, PyArrow, pytest, Docker (MinIO), boto3 or gcsfs + fsspec, gitleaks, GitHub Actions, optional Pandera.

**Mindset:** small vertical slice first; make it correct before fast; every step explainable in one sentence; test the failure paths as hard as the happy path (your QA background is an advantage); document the "why".

## 8. Milestones

| Milestone | Done when |
|---|---|
| M0 | Repo, config, contract, dirty sample generator |
| M1 | Excel -> Parquet with row-count test |
| M2 | Bronze load idempotent |
| M3 | Validation splits valid/quarantine; reconciliation test passes |
| M4 | Silver produced; cleaning tests pass |
| M5 | Gold matches hand-computed numbers |
| M6 | Upload verified on MinIO, then a real bucket |
| M7 | Run log + structured logs working |
| M8 | Observability queries + alert on bad data |
| M9 | One-command run, CI green, README with diagram |

## 9. Risks

- Scope creep in Steps 3 and 6: time-box them.
- Adding Airflow, Delta or dbt too early hides the concepts: defer to phase 2.
- Testing only the happy path: keep a bad-schema file and a high-rejection file in fixtures.
- Cloud surprise bills: MinIO first, billing alert on real accounts, delete resources after.

## 10. Phase 2 backlog (do NOT start yet)

- Incremental loads and hashdiff CDC into Bronze
- Pandera / Great Expectations integration
- Delta or Iceberg for Silver
- Orchestrator (Airflow, Dagster or Kestra)
- dbt for Silver/Gold SQL
- Parallelism for large files
- Secrets manager, lineage, cost controls
