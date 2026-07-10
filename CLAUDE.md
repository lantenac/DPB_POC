# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A self-contained proof of concept that stands up an **Eclipse BaSyx v2 AAS Environment**
via Docker and registers a **Battery Regulation submodel** (IDTA *Battery Pass*,
IDTA-02023) compliant with the semantic model behind **EU Battery Regulation (EU)
2023/1542**. The submodel is seeded with a sample battery passport derived from a
Schneider Electric Galaxy VS UPS (Li-ion battery module). All regulated values are
plausible but fictional — not real Schneider Electric product data.

There is no application code to compile: this repo is Docker Compose config, one seed
JSON document, two stdlib-only Python scripts, a static HTML/JS frontend, and an OpenAPI
spec.

## Commands

```bash
# Start the full stack (AAS Environment + registries + seeder + frontend + Swagger UI)
docker compose up

# Tear down
docker compose down

# Re-seed manually (idempotent: POST, falls back to PUT on 409) against a running stack
AAS_ENV_BASE=http://localhost:8081 python3 upload_aas.py

# Smoke test: queries the seeded submodel over REST and verifies key regulated properties
python3 smoke_test.py
```

Both Python scripts (`upload_aas.py`, `smoke_test.py`) use only the standard library —
no `pip install`, no virtualenv, no requirements file. There is no separate test
framework; `smoke_test.py` (exit 0/1) is the only automated check, and it requires the
Docker stack to be running against real BaSyx containers.

### Exposed endpoints once running

| What | URL |
|---|---|
| Frontend (passport lookup) | http://localhost:8088 |
| Swagger UI (curated Battery Pass API) | http://localhost:8089 |
| BaSyx native Swagger UI | http://localhost:8081/swagger-ui/index.html |
| AAS REST API | http://localhost:8081/shells, /submodels |
| AAS Registry | http://localhost:8082 |
| Submodel Registry | http://localhost:8083 |

Sample identifiers to look up in the frontend: serial `QB2145-001234`, or AAS id
`https://schneider-electric.com/ids/aas/galaxy-vs-20kva-2055016745678901`.

## Architecture

Five Docker Compose services (`docker-compose.yml`), diagrammed in
`docs/architecture.mmd` (component view) and `docs/high-level-architecture.mmd`
(layered view — Presentation / API / Domain / Data):

- **aas-environment** (`eclipsebasyx/aas-environment`, :8081) — the core BaSyx v2 server:
  AAS + Submodel repositories, AAS Part 2 HTTP/REST API, in-memory backend
  (`BASYX_BACKEND=InMemory`, volatile — swappable for MongoDB/CouchDB in a real
  deployment). Ships without `curl`, so it has **no Docker healthcheck**; readiness is
  instead polled by the seeder itself.
- **aas-registry** / **submodel-registry** (`*-log-mem`, :8082/:8083) — separate
  descriptor registries, in-memory. The AAS environment *may* register descriptors into
  these but the POC's core read path (frontend → `/shells` → `/submodels`) does not
  depend on them.
- **seeder** (one-shot `python:3.12-slim` container, `restart: on-failure`) — runs
  `upload_aas.py`, which polls `GET /shells` until the environment answers (up to 60 ×
  5s = 5 min, since BaSyx cold start can be slow), then loads **every `*.json` file in
  `seed/`** (glob, sorted, all merged) and upserts every submodel and shell found across
  them. Upsert = POST first, and on HTTP 409 fall back to PUT against the
  base64url-encoded id path — this is what makes reseeding idempotent. Drop a new
  `seed/*.json` file (same `assetAdministrationShells` + `submodels` shape) to register
  another sample; no code change needed.
- **frontend** (`nginx:alpine`, :8088) — serves `frontend/index.html` as static files.
  All logic is inline vanilla JS: `findShell()` fetches `/shells` and matches the query
  against either the AAS `id` or any `specificAssetIds` value (serial, GTIN, commercial
  reference); it then resolves the shell's submodel reference and fetches
  `/submodels/{base64url(id)}`, recursively rendering `SubmodelElementCollection` /
  `Property` elements into a table. It also derives the **GS1 Digital Link**
  (`https://id.gs1.org/01/{GTIN}/21/{serial}`) from the shell's specific asset IDs.
  Calls the AAS Environment directly from the browser via CORS
  (`BASYX_CORS_ALLOWED_ORIGINS=*` in compose), using `http://${location.hostname}:8081`
  — so the frontend and API must be reachable under the same hostname the browser used.
- **swagger-ui** (`swaggerapi/swagger-ui`, :8089) — serves the curated
  `swagger/swagger.yaml` (distinct from BaSyx's own native Swagger UI at
  `:8081/swagger-ui`, which reflects the full generic AAS API rather than the
  Battery-Pass-specific curated surface).

### Data model (`seed/*.json`)

Each file holds one `AssetAdministrationShell` referencing one or more `Submodel`s
(AAS v3 JSON per the BaSyx v2 API). The Battery Pass submodel's `semanticId` is
`https://admin-shell.io/idta/SubmodelTemplate/BatteryPass/1/0`; its
`submodelElements` are `SubmodelElementCollection`s matching IDTA Battery Pass template
areas required by EU 2023/1542: **Battery Identification, Manufacturer, Performance &
Durability, State of Health, Carbon Footprint, Material Composition** (recycled content
for cobalt/lithium/nickel/lead, hazardous substances, critical raw materials). Every leaf
`Property` carries its own `https://admin-shell.io/idta/BatteryPass/...` `semanticId`
IRI — these follow the template's naming convention as a POC approximation and should be
aligned to the exact ECLASS/IDTA concept IRIs from the published IDTA-02023 spec before
any non-POC use.

Identifiers throughout the API are base64url-encoded (`b64()` helpers appear in
`upload_aas.py`, `smoke_test.py`, and the frontend JS) — this is required by the BaSyx v2
REST path syntax for any `{id}` path segment.

### Reference schemas (`json-schemas/`)

`aasJSONSchema.json` and `Stationary_Industrial_Above_2kWh.json` are reference/validation
schemas, not consumed at runtime by any script in this repo.

## Conventions

- BaSyx image tags are pinned to `2.0.0-milestone-05` across all four BaSyx containers in
  `docker-compose.yml`; bump deliberately and together, not per-service.
- Keep `upload_aas.py`'s upsert semantics (POST → on 409 fall back to PUT) when adding
  seed entities, so reseeding an already-running stack stays idempotent.
