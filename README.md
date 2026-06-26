# Digital Battery Passport — Eclipse BaSyx POC

A self-contained proof of concept that stands up an **Eclipse BaSyx v2 AAS
Environment** via Docker and registers a **Battery Regulation submodel**
(IDTA *Battery Pass*, IDTA-02023) compliant with the semantic model behind
**EU Battery Regulation (EU) 2023/1542**.

The submodel is seeded with a **sample battery passport derived from a
Schneider Electric Galaxy VS UPS** (a Secure Power product containing a
Li-ion battery module). All regulated values are plausible but **fictional**.

---

## Architecture

| Service | Image | Port | Purpose |
|---|---|---|---|
| AAS Environment | `eclipsebasyx/aas-environment` | **8081** | AAS + Submodel repos, AAS Part 2 REST API, native Swagger UI |
| AAS Registry | `eclipsebasyx/aas-registry-log-mem` | 8082 | AAS descriptor registry |
| Submodel Registry | `eclipsebasyx/submodel-registry-log-mem` | 8083 | Submodel descriptor registry |
| Seeder | `python:3.12-slim` (one-shot) | — | Runs `upload_aas.py` to register the sample |
| Frontend | `nginx:alpine` | **8088** | Single-page passport lookup UI |
| Swagger UI | `swaggerapi/swagger-ui` | **8089** | Interactive Battery Pass API client |

---

## Run it

```bash
docker compose up
```

That single command:
1. starts the AAS Environment + both registries,
2. waits until the environment is healthy, then the **seeder** registers the
   Schneider Electric Battery Pass sample,
3. serves the frontend and Swagger UI.

### Exposed URLs

| What | URL |
|---|---|
| **Frontend (passport lookup)** | http://localhost:8088 |
| **Swagger UI (curated Battery Pass API)** | http://localhost:8089 |
| **BaSyx native Swagger UI** | http://localhost:8081/swagger-ui/index.html |
| AAS REST API — list shells | http://localhost:8081/shells |
| AAS REST API — list submodels | http://localhost:8081/submodels |
| AAS Registry | http://localhost:8082 |
| Submodel Registry | http://localhost:8083 |

---

## Using the frontend

Open http://localhost:8088 and enter a product identifier:

- Serial number: `QB2145-001234`
- or the AAS id: `https://schneider-electric.com/ids/aas/galaxy-vs-20kva-2055016745678901`

The page renders the full battery passport (identification, manufacturer,
performance, state of health, carbon footprint, material composition /
recycled content) and shows the **GS1 Digital Link**:

```
https://id.gs1.org/01/03606489012345/21/QB2145-001234
```

It also links to both Swagger UIs.

---

## Smoke test

With the stack running:

```bash
python3 smoke_test.py
```

Queries the submodel over the BaSyx REST API and verifies the key regulated
properties are present. Re-seed manually at any time with:

```bash
AAS_ENV_BASE=http://localhost:8081 python3 upload_aas.py
```

Both scripts use only the Python standard library — no `pip install` needed.

---

## Files

| File | Description |
|---|---|
| `docker-compose.yml` | Full local stack |
| `seed/battery_pass_aas.json` | AAS + Battery Pass submodel (AAS v3 JSON), Schneider Electric sample |
| `upload_aas.py` | Registers the sample into the AAS Environment (idempotent) |
| `smoke_test.py` | Queries + verifies key passport properties |
| `frontend/index.html` | Single-page lookup UI (plain HTML/JS) |
| `swagger/swagger.yaml` | Curated OpenAPI spec for the Battery Pass endpoints |

---

## Compliance notes

- Submodel `semanticId`: `https://admin-shell.io/idta/SubmodelTemplate/BatteryPass/1/0`
- Property collections map to the IDTA Battery Pass template areas required by
  EU 2023/1542: **Battery Identification, Manufacturer, Performance &
  Durability, State of Health, Carbon Footprint, Material Composition**
  (recycled content for cobalt / lithium / nickel / lead, hazardous
  substances, critical raw materials).
- Each property carries an `https://admin-shell.io/idta/BatteryPass/...`
  `semanticId` IRI. These follow the template's naming; align them to the
  exact ECLASS/IDTA concept IRIs from the published IDTA-02023 spec before any
  non-POC use.
- All values are illustrative and **not** real Schneider Electric product data.

> Image tags are pinned to `2.0.0-milestone-05`. Bump to a newer BaSyx v2 tag
> if desired; the REST API surface used here is stable across v2 milestones.
