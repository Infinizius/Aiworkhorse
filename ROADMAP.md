# AI-Workhorse v8 – Entwicklungsstatus & Roadmap (v1.1 stabil · Phase-2/3/4)

> **Stand:** April 2026 | **Branch:** `copilot/update-roadmap-readme-repo-info`

---

## 1. Projektüberblick

**AI-Workhorse** ist eine DSGVO-konforme KI-Assistenten-Plattform mit folgenden Kernfunktionen:

- **Sichere Chat-Completions** mit dreistufiger Prompt-Injection-Defense
- **Human-in-the-Loop (HITL)** Freigabe-System für Tool-Ausführungen via SSE (60s Timeout)
- **RAG (Retrieval-Augmented Generation)** mit PDF-Upload, pgvector-Embeddings und Ähnlichkeitssuche
- **Rate Limiting** via Token-Bucket-Algorithmus (Redis, 10 Req/Min/IP)
- **Open WebUI** als Chat-Interface (OpenAI-API-kompatibel)
- **Caddy Reverse Proxy** für automatisches HTTPS (Let's Encrypt) auf Hetzner VPS

**Tech-Stack:**
| Schicht | Technologie |
|---|---|
| Chat UI | Open WebUI (OpenAI-kompatibel, Port 3002) |
| Dashboard | Next.js 15 + React 19 + TypeScript + TailwindCSS v4 |
| Backend | FastAPI 0.110 + Python 3.11 + Uvicorn |
| Agent | LangGraph + ChatOpenAI (Requesty/MiniMax-M1) |
| Embeddings | NVIDIA NIM · `nvidia/llama-3.2-nv-embedqa-1b-v2` · 2048-dim |
| Datenbank | PostgreSQL 16 mit pgvector-Extension |
| Cache / Queue | Redis 7 |
| Containerisierung | Docker Compose (7 Core-Services + optionaler Caddy) |
| Reverse Proxy | Caddy 2 (automatisches HTTPS via Let's Encrypt) |
| Zielplattform | Hetzner VPS (ARM64, z.B. CAX21) |

---

## 2. Aktueller Entwicklungsstand (v1.1 Hardened · Phase-2/3/4)

### 2.1 Implementiert und funktionsfähig ✅

| Komponente | Status | Anmerkung |
|---|---|---|
| FastAPI-Backend-Grundstruktur | ✅ Fertig | Endpoints definiert, Pydantic-Modelle vorhanden |
| Strukturiertes JSON-Logging (JSONL) | ✅ Fertig | ISO-8601-Zeitstempel, Request-Kontext, Log-Rotation (7 Tage) |
| Token-Bucket Rate Limiter | ✅ Fertig | 10 Req/Min/User via Redis; Token-Hash bevorzugt |
| Dreistufige Prompt-Injection-Defense | ✅ Fertig | Unicode-Normalisierung + System-Anker + 20 Regex-Pattern |
| HITL Freigabe-System + SSE-Heartbeat | ✅ Fertig | 60s Timeout, Redis-persistent (überlebt Restarts) |
| PDF-Upload mit Path-Traversal-Schutz | ✅ Fertig | UUID-Dateinamen, pdfplumber-Parsing |
| SHA256-Prompt-Caching (Redis, 24h TTL) | ✅ Fertig | Nur für Non-RAG-Queries |
| Next.js-Dashboard | ✅ Fertig | Statusseite mit Service-Links und Feature-Übersicht |
| Dokumente-Seite (`/documents`) | ✅ Fertig | Liste (mit chunks/Vorschau), Löschen, Download (auth-aware) |
| TailwindCSS v4-Setup | ✅ Fertig | PostCSS konfiguriert |
| `useIsMobile`-Hook | ✅ Fertig | SSR-sicher, 768px-Breakpoint |
| `cn()`-Utility (clsx + tailwind-merge) | ✅ Fertig | Standard-Helfer |
| Docker-Compose (7 Core-Services + optionaler Caddy) | ✅ Fertig | db, redis, api, worker, goal-engine, openwebui, optional caddy – mit Volumes und Healthchecks |
| Caddy HTTPS Reverse Proxy | ✅ Fertig | `--profile prod` – automatisches TLS via Let's Encrypt |
| Backup-Skript (`backup.sh`) | ✅ Fertig | pg_dump + tar für uploads |
| Sync-Skript (`sync.sh`) | ✅ Fertig | Tablet-freundlicher Git-Push |
| Dev-Container (VSCode) | ✅ Fertig | Python 3.11, Extensions, psql-Client |
| Alembic-Konfiguration | ✅ Fertig | Auto-Run beim Start (`lifespan`); exclude_tables für LangGraph |
| **API-Key-Authentifizierung** | ✅ Fertig | Bearer Token; `verify_api_key`-Dependency; Auth deaktivierbar (Dev) |
| **Token-basiertes Rate-Limiting** | ✅ Fertig | `_get_user_id()` bevorzugt Token-Hash vor Client-IP; X-Forwarded-For-Support |
| **Erweiterte Prompt-Injection-Defense** | ✅ Fertig | 20 Patterns: Overrides, Jailbreaks, Role-Injection, Template-Injection |
| **SQLAlchemy ORM-Modelle** | ✅ Fertig | `UploadedFile`, `FileEmbedding`, `UserConfig`, `GoalTask`, `UserVault`, `CoreMemory` in `models.py` |
| **Alembic-Migrationen** | ✅ Fertig | 9 Migrationen: Initial-Schema, UserConfig, IVFFlat-Index-Fix, GoalTask, UserVault, CoreMemory, NVIDIA-Embeddings (1024 → 2048-dim) |
| **RAG-Pipeline** | ✅ Fertig | Chunking, NVIDIA `llama-3.2-nv-embedqa-1b-v2` (2048-dim), pgvector-Insert und -Suche |
| **Document Management API** | ✅ Fertig | GET (mit chunks/preview/total)/DELETE (mit 404-Check)/Download |
| **Web-Search Tool (Main-Chat)** | ✅ Fertig | Serper API (primär); kein Fallback im Main-Chat-Pfad (LIMIT-01) |
| **Open WebUI** | ✅ Fertig | Chat-UI auf Port 3002, OpenAI-API-kompatibel |
| **REACTIVE_MAX_ITERATIONS** | ✅ Fertig | Aus `.env` gelesen, in Chat-Loop verwendet |
| **GOAL_MAX_ITERATIONS** | ✅ Fertig | Aus `.env` gelesen und im Goal-Engine-Daemon verwendet |
| **Goal Management API** | ✅ Fertig | `POST /v1/goals`, `GET /v1/goals`, `GET /v1/goals/{goal_id}` |
| **Interner Tool-Server** | ✅ Fertig | `POST /internal/tools/execute` für Goal-Engine-Tooldelegation |
| **LangGraph Goal-Engine Daemon** | ✅ Fertig | Separater Service mit Postgres-Checkpointing und `X-Source: goal-engine` Guard |
| **Metadaten/Titel** | ✅ Fertig | `layout.tsx` und `metadata.json` korrekt befüllt |
| **Health-Endpoint `GET /health`** | ✅ Fertig | DB + Redis Verbindung geprüft (M7) |
| **Readiness-Probe `GET /readyz`** | ✅ Fertig | Kein API-Key nötig, für Docker-Healthchecks (M7) |
| **RFC 7807 Error-Format** | ✅ Fertig | Konsistente Fehlerstruktur mit `type`, `title`, `status`, `request_id` |
| **Request-ID Middleware** | ✅ Fertig | UUIDv4 per Request; `X-Request-ID`-Header in Response |
| **Backend-Tests (pytest)** | ✅ Fertig | ~80 Tests: health, security, chat, models, goals, file-ownership, agent, phase3/4 |
| **arq Worker** | ✅ Fertig | Asynchrone PDF-Embedding-Verarbeitung im Hintergrund |
| **Nutzerspezifische API-Keys** | ✅ Fertig | AES/Fernet-verschlüsselt in DB; Routing per User & Provider |
| **`google-genai` SDK** | ✅ Fertig | Migration auf neues Google SDK; Streaming + Non-Streaming |
| **Multi-Model Routing** | ✅ Fertig | Dynamisches Key-Routing pro User & Provider (Gemini/Mistral/DeepSeek/MaxClaw) |
| **HITL User-Binding** | ✅ Fertig | `execution_id` an Initiator gebunden (BUG-14); 403 bei Fremd-Zugriff |
| **Token Vault (`UserVault`)** | ✅ Fertig | `/v1/agent/register` speichert OpenWebUI API-Keys Fernet-verschlüsselt |
| **MaxClaw LangGraph-Agent** | ✅ Fertig | `agents/graph.py`: Supervisor-Knoten via ChatOpenAI (Requesty/MiniMax-M1); Tool-Schleife mit State-Machine |
| **Workspace-Tools** | ✅ Fertig | `agents/tools.py`: `web_search` (Serper+DDG-Fallback), `read/write_workspace_file` (Path-Traversal-Schutz), `update_core_memory` |
| **Core-Memory-Persistenz** | ✅ Fertig | `CoreMemory`-Tabelle; wird bei jedem MaxClaw-Aufruf in System-Prompt injiziert |
| **JWT Workspace-Dashboard** | ✅ Fertig | `dashboard.py`: Magic-Link via HMAC-SHA256 (1h TTL); `/dashboard`-HTML; `/workspace`-Chat-Befehl |
| **Workspace File API** | ✅ Fertig | `GET /v1/workspace/files`, `GET/DELETE /v1/workspace/files/{path}` |
| **`maxclaw-agent` Modell** | ✅ Fertig | Erscheint in `/v1/models`; wird in `chat/completions` zu LangGraph-Agent geroutet |
| **DuckDuckGo-Fallback (MaxClaw)** | ✅ Fertig | `agents/tools.py`: HTML-Scraper als kostenloser Fallback bei fehlendem Serper-Key |

### 2.2 Bekannte Limitierungen & offene Punkte ⚠️

| Komponente | Problem | Priorität |
|---|---|---|
| DuckDuckGo-Fallback (Main-Chat) | `tool_web_search()` in `main.py` hat keinen Fallback – bei Serper-Fehler nur Fehlerstring. Der MaxClaw-Agent hat den Fallback (`agents/tools.py`). | 🟡 Mittel |
| HITL-Trigger | `"search" in message.lower()` ist ein zu breites Heuristikum (False Positives); echtes Function Calling fehlt im regulären Chat-Pfad | 🟡 Mittel |
| SSE-Streaming Event Loop | `_convert_and_stream()` (sync Generator) wird direkt in async `sse_gen()` iteriert → blockiert Event Loop | 🟡 Mittel |
| Dashboard-Proxy Identity | Dashboard ruft Backend serverseitig auf; robuste Session/SSO für `X-User-Email`-Weitergabe bleibt optionale Härtung | 🟡 Niedrig |
| CI/CD-Pipeline | Keine GitHub Actions, kein automatisches Deployment | 🔵 Phase 5 |
| JWT-Authentifizierung | Übergang von statischem API-Key zu dynamischen, ablaufenden Token geplant | 🔵 Phase 5 |
| LangGraph-Agenten | Basis fertig; fortgeschrittene Planungslogik, mehrstufige Tool-Ketten und autonomes Triggering fehlen noch | 🟡 Mittel |

### 2.3 Gesamtfortschritt (v1.1 · Phase-2/3/4)

```
Infrastruktur      ███████████████████████  ~100%  (Caddy HTTPS, 7 Core-Services, arq Worker, Goal-Engine)
Backend-Logik      ██████████████████████░   ~97%  (Gemini/Mistral/DS/MaxClaw, RAG NVIDIA 2048-dim, HITL, UserKeys, Goal-Tasks, Tool-Server)
Frontend / UI      ████████████████████░░░   ~90%  (Dashboard + Dokumente-Seite + Workspace-Dashboard)
RAG-Pipeline       █████████████████████░░   ~93%  (Upload, NVIDIA-Embed async, Retrieve, Inject)
Sicherheit         █████████████████████░░   ~94%  (API-Key, Injection-Defense, Encryption, HITL-User-Binding, Path-Traversal, JWT)
Tests              ██████████████████████░   ~96%  (~80 Backend-Tests ✅; inkl. Phase-3/4, Agent, File-Ownership)
Dokumentation      ██████████████████████░   ~96%  (README, ROADMAP, SECURITY_AUDIT aktualisiert)
─────────────────────────────────────────────────────────────────
Gesamt             ██████████████████████░   ~96%  (v1.1 stabil; Phase-2/3/4 aktiv)
```

---

## 3. Bugs & Architekturprobleme

### 3.1 Behobene Bugs ✅

#### BUG-01: Keine echte LLM-Anbindung – ✅ BEHOBEN
- **Fix:** `google-genai>=0.8.0` in `requirements.txt`; echter `generate_content`-Call
  in `sse_generator()` und non-Streaming-Pfad; Startup-Check für `GEMINI_API_KEY`.

#### BUG-02: Keine Frontend-Seiten – ✅ BEHOBEN
- **Fix:** `app/page.tsx` (Dashboard), `app/documents/page.tsx` (Dokumentenverwaltung)
  mit vollständigem UI, Service-Links und Feature-Übersicht.

#### BUG-03: `pdf.pages` nach `with`-Block referenziert – ✅ BEHOBEN
- **Fix:** `page_count = len(pdf.pages)` wird jetzt korrekt innerhalb des `with`-Blocks
  berechnet, danach erst im Return-Wert verwendet.

#### BUG-04: `GET /v1/files` Response-Format inkompatibel mit Frontend – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `GET /v1/files` lieferte nur `{file_id, filename}`. Das Dokumente-Dashboard
  erwartete zusätzlich `page_count`, `chunks_embedded`, `uploaded_at`, `preview` und `total`.
  Alle erweiterten Felder wurden als undefined/null angezeigt.
- **Fix:** `list_files()` gibt nun alle Felder inklusive Embedding-Count und Text-Vorschau zurück.

#### BUG-05: Documents-Dashboard ohne Backend-Zugriffspfad – ✅ BEHOBEN (Audit April 2026)
- **Problem:** Das Dokumente-Dashboard griff direkt auf das FastAPI-Backend zu. Dadurch war
  Port 8000 hostseitig exponiert oder das Frontend brauchte einen Browser-Key.
- **Fix:** Das Dashboard nutzt jetzt serverseitige Proxy-Routen (`/api/backend`, `/docs`, `/redoc`,
  `/openapi.json`, `/health`). Der Proxy injiziert den `API_KEY` serverseitig und kann
  vertrauenswürdige User-Identity-Hinweise weiterreichen.

#### BUG-06: IVFFlat-Index nach Migration `c1c21ee5d1e1` nicht wiederhergestellt – ✅ BEHOBEN (Audit April 2026)
- **Problem:** Die Migration `c1c21ee5d1e1` (add_user_configs_table) löschte den IVFFlat-Index auf
  `file_embeddings.embedding`, ohne ihn neu zu erstellen. Alle RAG-Vektorsuchen degradierten
  dadurch zu einem vollständigen Sequential-Scan (drastischer Performanceverlust ab ~1000 Chunks).
- **Fix:** Neue Migration `d7f3a1b2c8e9_restore_ivfflat_index.py` recreiert den Index mit `IF NOT EXISTS`.

#### BUG-07: `DEFAULT_MODELS` in `docker-compose.yml` existierte nicht in `/v1/models` – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `DEFAULT_MODELS: gemini-3.1-flash-lite` – dieses Modell war nie im `/v1/models`-Endpoint
  vorhanden. Open WebUI nutzte standardmäßig ein nicht-existierendes Modell.
- **Fix:** Geändert auf `gemini-3-flash-preview`, das im `/v1/models`-Endpoint korrekt definiert ist.

#### BUG-08: HITL-Loop triggert nach erfolgreicher Tool-Ausführung erneut – ✅ BEHOBEN (Audit April 2026)
- **Problem:** In `sse_gen()` fehlte nach `approved=True` ein `break`-Statement. Da die REACTIVE_MAX_ITERATIONS-Schleife danach weiterläuft und `needs_tool` erneut geprüft wird, enthält die originale User-Nachricht weiterhin das Wort "search". Dadurch wurde für jede Iteration (bis zu 3×) ein neues HITL-Approval angefordert, obwohl die Web-Suche bereits ausgeführt worden war.
- **Fix:** `break` nach erfolgreichem Tool-Call in `sse_gen()` hinzugefügt. Außerdem wird der `hitl_owner`-Key explizit im `finally`-Block gelöscht.

#### BUG-09: Worker-Config-Validation-Fehler wurde nicht propagiert – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `worker.py` fing die `RuntimeError` aus `validate_config()` ab und druckte sie nur, anstatt sie weiterzuwerfen. Der Worker lief danach mit fehlender oder unsicherer Konfiguration weiter.
- **Fix:** `raise` nach dem `print()` hinzugefügt, damit arq den Start mit ungültiger Konfiguration verweigert.

#### BUG-10: `DELETE /v1/files/{file_id}` gab kein 404 für unbekannte IDs – ✅ BEHOBEN (Audit April 2026)
- **Problem:** Der Delete-Endpoint prüfte nicht, ob die angegebene `file_id` überhaupt in der DB existiert. Anfragen für nicht-existierende IDs liefen durch und gaben `{"status": "deleted"}` mit HTTP 200 zurück – inkonsistent mit `GET /v1/files/{id}` (404).
- **Fix:** Existenz-Check via `select()` vor dem Löschen; 404 bei unbekannter ID.

#### BUG-11: `ENCRYPTION_KEY`-Beispielwert aus `.env.example` nicht in Validierung geblockt – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `config.py` prüfte nur auf `"CHANGE_ME_STRONG_ENCRYPTION_KEY"`, nicht auf den konkreten Beispielwert `"f6-9E_zX_K-mX-Z-H-W-Y-G-m-X-Z-H-W-Y-G-m-X-Z-H-W-Y-G"` aus `.env.example`. Nutzer, die `.env.example` ohne Änderung kopierten, nutzten einen öffentlich bekannten Verschlüsselungsschlüssel.
- **Fix:** Beispielwert in `validate_config()` als weiterer geblocker Default-Wert aufgenommen.

#### BUG-12: `test_models.py` prüfte nur 7 von 10 Modellen – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `REQUIRED_MODELS` in `test_models.py` enthielt nicht `gemini-3-pro-preview`, `gemini-2.5-flash` und `gemini-2.5-pro`. Der Test `test_models_contains_all_providers` schlug für diese Modelle nicht an, auch wenn sie aus dem Endpoint entfernt worden wären.
- **Fix:** Alle 10 Modelle aus dem `/v1/models`-Endpoint in `REQUIRED_MODELS` aufgenommen.

#### BUG-13: `SECURITY_AUDIT.md` behauptete fälschlich "AES-256" für Fernet – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `SECURITY_AUDIT.md` nannte die Verschlüsselung "AES-256 (Fernet)". Fernet nutzt intern AES-128-CBC + HMAC-SHA256, nicht AES-256.
- **Fix:** Korrekte Beschreibung "Fernet (AES-128-CBC + HMAC-SHA256)" in `SECURITY_AUDIT.md`.

#### BUG-14: HITL-Approval-Endpoint band `execution_id` nicht an den Initiator – ✅ BEHOBEN (Audit April 2026, SECURITY)
- **Problem:** `POST /v1/tools/approve/{execution_id}` prüfte nur den globalen `API_KEY`, aber nicht ob der freigebende Nutzer auch der Initiator der Anfrage war. Jeder authentifizierte Nutzer konnte beliebige `execution_id`s approven (Insecure Direct Object Reference).
- **Fix:** Beim Erstellen jedes HITL-Requests wird `user_id` des Initiators unter `hitl_owner:{execution_id}` mit 65s TTL in Redis gespeichert. Der Approve-Endpoint prüft Übereinstimmung; bei Mismatch: HTTP 403.

#### BUG-15: Graceful Shutdown schloss Redis/arq-Verbindungen nicht explizit – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `redis_client` und `arq_pool` blieben beim `lifespan`-Shutdown offen.
- **Fix:** Shutdown-Pfad schließt nun beide Verbindungen explizit, bevor die DB-Engine disposed wird; ein Regressionstest deckt den Ablauf ab.

### 3.2 Behobene Architekturprobleme ✅

#### ARCH-02: Keine Datenbankmodelle – ✅ BEHOBEN
- `backend/models.py` enthält `UploadedFile`, `FileEmbedding` und `UserConfig` (SQLAlchemy ORM).
- Alembic-Migrationen legen pgvector-Extension, Tabellen und IVFFlat-Index an.

#### ARCH-03: pgvector nicht integriert – ✅ BEHOBEN
- Vollständige RAG-Pipeline: PDF-Text in Chunks aufteilen → `text-embedding-004` Embedding
  → pgvector-Insert → Cosine-Ähnlichkeitssuche bei `chat/completions` mit `file_ids`.

#### ARCH-04: `approval_events`-Dict ohne TTL – ✅ BEHOBEN
- HITL-Freigaben erhalten einen 60-Sekunden-Timeout; danach wird automatisch abgelehnt.
- Persistenz via Redis: Freigaben überleben Server-Restarts.

#### ARCH-06: `google-genai` fehlte – ✅ BEHOBEN
- `google-genai>=0.8.0` ist in `backend/requirements.txt` enthalten (neues SDK, nicht `google-generativeai`).

#### ARCH-07: Datenbank-Passwort hartkodiert – ✅ BEHOBEN
- `docker-compose.yml` liest `POSTGRES_PASSWORD` aus `.env` mit Pflicht-Validierung.

#### ARCH-08: Iterations-Limits nicht verwendet – ✅ BEHOBEN
- `REACTIVE_MAX_ITERATIONS` steuert die Tool-Call-Schleife in `sse_generator()`.
- `GOAL_MAX_ITERATIONS` aus `.env` gelesen und an den LangGraph-Goal-Engine-Daemon weitergereicht.

#### ARCH-10: Falscher Titel in `layout.tsx` – ✅ BEHOBEN
- Titel: `"AI-Workhorse v8"`, Beschreibung: DSGVO-konforme Plattformbeschreibung.

#### ARCH-11: Leere `metadata.json` – ✅ BEHOBEN
- `name` und `description` korrekt befüllt.

#### ARCH-12: Keine Tests – ✅ BEHOBEN (M8)
- ~80 Backend-Tests in `backend/tests/`: health, security, chat-routing, models, goals, file-ownership, agent (Phase 1+2), phase3/4 (Workspace, JWT, MaxClaw-Graph).

#### ARCH-13: Kein Health-Endpoint – ✅ BEHOBEN (M7)
- `GET /health` prüft DB- und Redis-Verbindung; `GET /readyz` als öffentliche Liveness-Probe.

### 3.3 Bekannte Limitierungen (nicht-kritisch) 🟡

#### LIMIT-01: DuckDuckGo-Fallback im regulären Chat-Pfad nicht implementiert
- **Problem:** `tool_web_search()` in `main.py` gibt bei Serper-Fehler nur einen Fehler-String zurück.
- **Teilbehoben (Phase 3):** `web_search` in `agents/tools.py` (MaxClaw-Agent) hat einen vollständigen DuckDuckGo HTML-Scraper-Fallback. Für den regulären Chat bleibt es Serper-only.
- **Status:** Für MaxClaw ✅ Behoben. Für den normalen Chat-Loop in `main.py` offen.

#### LIMIT-02: HITL-Trigger-Heuristik zu breit
- **Problem:** `"search" in message.lower()` löst HITL für jede Nachricht mit dem Wort "search" aus (False Positives: "I'm searching for...", "What's the binary search algorithm?").
- **Teilbehoben:** Das davon abgeleitete Re-Trigger-Problem (nach erfolgreicher Tool-Ausführung wurde HITL erneut ausgelöst) wurde mit BUG-08 gefixt. Die zu breite Heuristik selbst bleibt eine bekannte Einschränkung.
- **Status:** Die Goal-Engine nutzt bereits `/internal/tools/execute`; der normale User-Chat braucht weiterhin echten Function-Calling-Support.

#### LIMIT-03: SSE-Streaming blockiert Event Loop
- **Problem:** `_convert_and_stream()` ist ein synchroner Generator, der direkt in `sse_gen()` iteriert.
  Langsamere Gemini-Antworten blockieren den asyncio Event Loop für andere Requests.
- **Status:** Bekannte Einschränkung für Single-User/Low-Traffic. Fix bleibt für die nächste Phase-2-Ausbaustufe offen.

#### LIMIT-04: Fernet ≠ AES-256
- **Problem:** README beschreibt Verschlüsselung als "AES-256". Fernet nutzt intern AES-128-CBC.
- **Status:** Dokumentation in README korrigiert ("AES/Fernet-verschlüsselt"). Sicherheitsniveau bleibt hoch.

---

## 4. Roadmap zur stabilen v1.0

Die folgende Roadmap ist in Meilensteine (M) gegliedert, die aufeinander aufbauen.

---

### Meilenstein 0: Hotfixes & Cleanup ✅ ABGESCHLOSSEN
> **Ergebnis:** Saubere Codebasis ohne offensichtliche Bugs.

- [x] **BUG-03 fixen:** `len(pdf.pages)` innerhalb des `with`-Blocks berechnen
- [x] **ARCH-10 fixen:** Titel/Metadata in `app/layout.tsx` und `metadata.json` aktualisieren
- [x] **ARCH-07 fixen:** Datenbank-Passwort aus hartkodiertem Wert in `.env`-Variable auslagern
- [x] **ARCH-08 bereinigen:** Nicht verwendete Env-Variablen implementiert
- [x] **ARCH-11 fixen:** `metadata.json` Description ausgefüllt
- [x] **ARCH-09:** ESLint im Build aktivieren (`ignoreDuringBuilds: false`)

---

### Meilenstein 1: Lokale Infrastruktur vollständig lauffähig ✅ ABGESCHLOSSEN
> **Ergebnis:** `docker compose up` startet alle Services fehlerfrei.

- [x] `docker-compose.yml`: Datenbankpasswort aus `.env` einlesen
- [x] `backend/requirements.txt`: `google-genai>=0.8.0` hinzugefügt (neues SDK, nicht `google-generativeai`)
- [x] `backend/requirements.txt`: `sqlalchemy>=2.0`, `asyncpg`, `pgvector` hinzugefügt
- [x] Open WebUI als 4. Service integriert (Port 3002, OpenAI-kompatibel)
- [x] Caddy als optionaler 5. Service für HTTPS-Produktion (`--profile prod`)
- [x] Redis-Verbindungstest: Rate-Limiting funktionsfähig
- [x] PostgreSQL + pgvector: Extension wird beim Start automatisch aktiviert

**Abnahmekriterium:** ✅ `docker compose up && curl http://localhost:3001/docs` gibt Swagger-UI über den Dashboard-Proxy zurück.

---

### Meilenstein 2: Datenbankschema & Migrationen ✅ ABGESCHLOSSEN
> **Ergebnis:** Persistente Datenhaltung für Dateien, Embeddings, User-Konfiguration, Goals, Token-Vault und Core-Memory.

- [x] SQLAlchemy-ORM-Modelle (`backend/models.py`):
  - `UploadedFile` (id, user_id, filename, path, extracted_text, page_count, uploaded_at)
  - `FileEmbedding` (id, file_id, chunk_text, chunk_index, embedding VECTOR(2048))
  - `UserConfig` (id, user_id, provider, encrypted_key, updated_at)
  - `GoalTask` (id, user_id, goal, model, status, schedule_minutes, next_run_at, run_count, …)
  - `UserVault` (id, user_id, openwebui_api_key (Fernet), created_at, updated_at)
  - `CoreMemory` (id, user_id, content, updated_at)
- [x] Alembic-Migrationen (9 gesamt):
  - `0001_initial_schema.py` – Basistabellen + pgvector
  - `9e3b1f2a4c6d_add_uploaded_file_user_id.py` – user_id auf UploadedFile
  - `c1c21ee5d1e1_add_user_configs_table.py` – UserConfig
  - `d7f3a1b2c8e9_restore_ivfflat_index.py` – IVFFlat-Index-Fix (BUG-06)
  - `e4b7a9c2f6d1_add_goal_tasks_table.py` – GoalTask
  - `f1a2b3c4d5e6_add_user_vault_table.py` – UserVault
  - `a1b2c3d4e5f6_add_core_memories_table.py` – CoreMemory
  - `a3f2e1d0c9b8_switch_embedding_to_nvidia_1024dim.py` – NVIDIA 1024-dim
  - `b5c4d3e2f1a0_switch_embedding_to_llama_nv_2048dim.py` – NVIDIA 2048-dim
- [x] pgvector-Extension in Migration aktiviert
- [x] IVFFlat-Cosine-Index auf `file_embeddings.embedding` (via Migration `d7f3a1b2c8e9` nach Fix von BUG-06)
- [x] Async-SQLAlchemy-Session via `lifespan` in FastAPI integriert
- [x] Alembic-Migrationen beim Start automatisch ausführen (`alembic upgrade head` im `lifespan`-Hook)

**Abnahmekriterium:** ✅ Alle 6 Tabellen werden beim ersten Start automatisch erstellt.

---

### Meilenstein 3: Gemini-API-Integration ✅ ABGESCHLOSSEN
> **Ergebnis:** Echte KI-Antworten statt Mock-Strings.

- [x] `GEMINI_API_KEY` aus Umgebungsvariable einlesen
- [x] Startup-Warning: App loggt Warnung wenn `GEMINI_API_KEY` fehlt
- [x] `google-genai`-Client initialisieren (Singleton via `lifespan`)
- [x] Non-Streaming-Pfad: Echter `generate_content`-Call an `gemini-3-flash-preview`
- [x] Streaming-Pfad: `generate_content_stream` via Thread-Pool in `sse_generator()` integriert
- [x] OpenAI-Format → Gemini-Format Konvertierung (`_convert_messages_for_gemini`)
- [x] Multi-Model Routing: Gemini / Mistral / DeepSeek per Modell-Prefix
- [x] `REACTIVE_MAX_ITERATIONS` aus `.env` lesen und in Chat-Loop eingebaut
- [x] Error-Handling: Gemini-API-Fehler abgefangen, benutzerfreundliche Fehlermeldung
- [x] Kein Cache bei API-Fehlern

**Abnahmekriterium:** ✅ `POST /v1/chat/completions` gibt eine echte Gemini-Antwort zurück.

---

### Meilenstein 4: Chat-Frontend ✅ ABGESCHLOSSEN
> **Ergebnis:** Open WebUI als vollwertiges Chat-Interface.

- [x] Open WebUI als Docker-Service integriert (Port 3002)
- [x] Open WebUI kommuniziert direkt mit FastAPI-Backend (`/v1`-Endpunkte)
- [x] `GET /v1/models` implementiert (OpenAI-kompatible Model-Liste)
- [x] Next.js-Dashboard (`app/page.tsx`) mit Service-Links und Feature-Statusübersicht
- [x] Dokumente-Seite (`app/documents/page.tsx`) mit Liste, Vorschau, Download, Löschen
- [x] `app/layout.tsx`: Titel und Beschreibung korrekt gesetzt

**Abnahmekriterium:** ✅ Open WebUI öffnet sich im Browser, User kann mit Gemini chatten.

---

### Meilenstein 5: RAG-Pipeline ✅ ABGESCHLOSSEN
> **Ergebnis:** Hochgeladene PDFs werden vektorisiert und bei Queries genutzt.

- [x] Embedding-Modell: initial `text-embedding-004` (Google, 768 Dim.), dann migriert zu `nvidia/nv-embedqa-e5-v5` (1024 Dim.), zuletzt zu `nvidia/llama-3.2-nv-embedqa-1b-v2` (2048 Dim.) via NVIDIA NIM
- [x] Nach PDF-Upload: Text in Chunks aufteilen (500 Wörter, 50 Wörter Overlap)
- [x] Für jeden Chunk: Embedding erstellen (`embed_utils.nvidia_embed()`), in pgvector-Tabelle speichern
- [x] Chat-Completions: Wenn `file_ids` übergeben, Cosine-Ähnlichkeitssuche via pgvector
- [x] Top-5-Chunks als Kontext in System-Prompt eingefügt
- [x] Document-Management-API: `GET /v1/files`, `GET /v1/files/{id}`, `DELETE /v1/files/{id}`
- [x] Download-Endpoint: `GET /v1/files/{id}/download`
- [x] Web-Search-Tool (Main-Chat): Serper API (primär); DuckDuckGo-Fallback im Main-Chat-Pfad bleibt offen (im MaxClaw-Agent implementiert, s. M10)

**Abnahmekriterium:** ✅ PDF hochladen, Frage stellen, Antwort enthält PDF-Inhalte.

---

### Meilenstein 5.5: HTTPS für Hetzner VPS ✅ ABGESCHLOSSEN
> **Ergebnis:** Sichere, private HTTPS-Verbindung zu Open WebUI auf einem Hetzner VPS.

- [x] `caddy/Caddyfile` erstellt: `{$DOMAIN}` → `openwebui:8080`
- [x] Caddy-Service in `docker-compose.yml` (Profile `prod`), Ports 80/443/443-udp
- [x] TLS-Zertifikate via Let's Encrypt (HTTP-01 Challenge), persistent in `caddy_data`-Volume
- [x] `.env.example`: `DOMAIN`-Variable dokumentiert
- [x] `README.md`: Hetzner VPS HTTPS-Deployment Schritt-für-Schritt Anleitung

**Abnahmekriterium:** ✅ `docker compose --profile prod up -d` → Open WebUI unter `https://domain.tld` erreichbar.

---

### Meilenstein 6: Authentifizierung & Sicherheit ✅ ABGESCHLOSSEN
> **Ziel:** Sicherer Mehrnutzer-Betrieb.

- [x] Einfache API-Key-Authentifizierung (Bearer Token im Header)
  - `verify_api_key`-Dependency prüft `Authorization: Bearer <API_KEY>`
  - `API_KEY` aus `.env` konfigurierbar; leer = Auth deaktiviert (Dev-Modus)
- [x] Rate-Limiting auf Basis des User-Tokens statt IP
  - `_get_user_id()` bevorzugt gehashten Bearer-Token vor Client-IP
- [x] `X-Forwarded-For`-Header korrekt auswerten (hinter Caddy-Proxy)
  - `_get_client_ip()` liest `X-Forwarded-For`, Fallback auf `request.client.host`
- [x] HITL-Freigaben: User-ID aus Token statt IP
  - Alle Logs verwenden `user_id` (Token-Hash oder IP) statt roher IP
- [x] Prompt-Injection-Pattern erweitern (20 bekannte Bypass-Varianten)
  - `_INJECTION_PATTERNS`-Liste mit 20 Patterns (Overrides, Jailbreaks, Role-Injection, Template-Injection)
- [x] `ARCH-09` beheben: `ignoreDuringBuilds: false` in `next.config.ts`

**Abnahmekriterium:** ✅ Anfragen ohne gültigen API-Key werden mit HTTP 401 abgelehnt.

---

### Meilenstein 7: Fehlerbehandlung, Logging & Monitoring ✅ ABGESCHLOSSEN
> **Ergebnis:** Produktionsreifes Logging und nachvollziehbare Fehler.

- [x] Health-Check-Endpoint `GET /health` (DB + Redis Verbindung prüfen)
- [x] Öffentliche Liveness-Probe `GET /readyz` (kein API-Key, für Docker & Load-Balancer)
- [x] Konsistente HTTP-Fehlerstruktur für alle Endpoints (RFC 7807 Problem Details)
- [x] Request-ID in alle Log-Einträge (UUIDv4 per Request via Middleware)
- [x] Startup-Validation: Alle erforderlichen Env-Variablen beim Start prüfen
- [x] Alembic-Migrationen beim Start automatisch ausführen (`alembic upgrade head` in `lifespan`)
- [x] Log-Rotation konfigurieren (täglich, 7 Tage Retention via `TimedRotatingFileHandler`)
- [x] Stdout-Logging für Docker (`StreamHandler` → `docker logs ai-workhorse-api`)

**Abnahmekriterium:** ✅ `GET /readyz` liefert `{"status": "ok"}` ohne API-Key. `GET /health` gibt DB- und Redis-Status zurück.

---

### Meilenstein 8: Tests ✅ ABGESCHLOSSEN
> **Ergebnis:** ~80 Backend-Tests, alle grün (0 Fehler).

**Backend (pytest) – `backend/tests/` – ~80/~80 ✅:**
- [x] `requirements-dev.txt` + `pytest.ini` + `conftest.py` (Fixtures: Mock-Lifespan, Mock-Redis, Auth-Client)
- [x] `test_health.py`: `/readyz` (public), `/health` (auth), Redis-Down → 503
- [x] `test_security.py`: Auth-Guard (401), 17 Injection-Patterns (400), Unicode-Bypass, Rate-Limit (429)
- [x] `test_chat.py`: Gemini-Routing, Mistral-Routing, DeepSeek-Routing, RFC 7807 Error-Format
- [x] `test_models.py`: Format, Vollständigkeit aller Modelle (Gemini + Gemma + DeepSeek + Mistral + MaxClaw)
- [x] `test_goals.py`: Goal-API, interner Tool-Endpoint, Goal-Engine-Source-Guard
- [x] `test_file_security.py`: File-Ownership-Checks
- [x] `test_agent.py`: Token-Vault (`/v1/agent/register`), maxclaw-agent-Routing (Streaming + Non-Streaming), SSE-Adapter
- [x] `test_phase3_phase4.py`: Path-Traversal-Security (8 Tests), Core-Memory-Injektion, Dashboard-JWT, Workspace-Befehl, Dashboard-HTML, Workspace-File-API, Magic-Link, MaxClaw-Graph

**Frontend (vitest):**
- [ ] Verschoben auf Post-v1.1 (Next.js App Router-Komponenten erfordern separaten Audit)

**Abnahmekriterium:** ✅ `python -m pytest tests/ -v` → alle Tests grün

---

### Meilenstein 9: Dokumentation & Finale Qualitätssicherung ✅ ABGESCHLOSSEN
> **Ergebnis:** Onboarding-ready. Ein neuer Entwickler kann das Projekt in < 30 Minuten lokal starten.

- [x] `.env.example` auf Vollständigkeit geprüft: alle Variablen dokumentiert (MISTRAL_API_KEY, WEBUI_API_KEY, WEBUI_INTERNAL_URL, INTERNAL_API_URL, POSTGRES_*, REACTIVE_MAX_ITERATIONS, REQUESTY_API_KEY, DASHBOARD_JWT_SECRET, NVIDIA_API_KEY etc.)
- [x] Inline-Code-Kommentare überprüft und ergänzt (Rate-Limiter, RAG-Pipeline, Injection-Defense, Proxy-Routing)
- [x] ESLint-Konfiguration: `ignoreDuringBuilds: false` bestätigt aktiv in `next.config.ts`
- [x] Dead-Code aus `main.py` entfernt (M7-Vorbereitung)
- [x] End-to-End-Verifikation: Alle ~80 Backend-Tests grün, API-Endpunkte live und erreichbar
- [x] **Architektur-Audit (April 2026, Runde 1):** BUG-04–07 behoben (API-Response-Format, Auth-Header, IVFFlat-Index, DEFAULT_MODELS)
- [x] **Architektur-Audit (April 2026, Runde 2):** BUG-08–14 behoben (HITL Re-Trigger, Worker-Startup, DELETE 404, Encryption-Key-Validation, Test-Coverage, Doc-Accuracy, HITL-Security)
- [x] **Audit (April 2026, Runde 3):** BUG-15 behoben; README/ROADMAP-Claims gegen Code, Docker und Tests harmonisiert
- [x] **Phase-2 Foundation (April 2026):** GoalTask-Migration, Goal-API, interner Tool-Server und LangGraph-Daemon dokumentiert
- [x] **Audit (April 2026, Runde 4):** README/ROADMAP aktualisiert auf Phase-3/4 Implementierungsstand; Embedding-Modell korrigiert (NVIDIA 2048-dim); LIMIT-01 als "im MaxClaw-Agent behoben" dokumentiert; Testanzahl korrigiert (~80)

**Abnahmekriterium:** ✅ Alle Tests grün. `.env.example` dokumentiert vollständig den Onboarding-Pfad.

---

### Meilenstein 10: Phase-3 – MaxClaw LangGraph-Agent ✅ ABGESCHLOSSEN
> **Ergebnis:** Vollständiger autonomer Supervisor-Agent mit Workspace, Web-Suche und persistentem Gedächtnis.

- [x] `agents/graph.py`: LangGraph `StateGraph` mit `SupervisorState` (messages + user_id + core_memory)
- [x] `agents/graph.py`: ChatOpenAI via Requesty (`REQUESTY_API_KEY`, `REQUESTY_BASE_URL`, `AGENT_MODEL_NAME`)
- [x] `agents/graph.py`: Manueller `tool_node` (kompatibel mit pinned langgraph==1.1.4)
- [x] `agents/graph.py`: Core-Memory-Injektion in System-Prompt vor jedem LLM-Call
- [x] `agents/tools.py`: `web_search` – Serper (primär) + DuckDuckGo HTML-Scraper (kostenloser Fallback)
- [x] `agents/tools.py`: `read_workspace_file` / `write_workspace_file` – Path-Traversal-Schutz via `_safe_workspace_path()`
- [x] `agents/tools.py`: `update_core_memory` – schreibt `CoreMemory`-Record in PostgreSQL
- [x] `models.py`: `UserVault`-Tabelle (Fernet-verschlüsselter OpenWebUI API-Key)
- [x] `models.py`: `CoreMemory`-Tabelle (dauerhaftes Nutzer-Gedächtnis)
- [x] Alembic-Migrationen: `f1a2b3c4d5e6_add_user_vault_table.py`, `a1b2c3d4e5f6_add_core_memories_table.py`
- [x] `main.py`: `/v1/agent/register` – speichert OpenWebUI API-Key in `UserVault`
- [x] `main.py`: `maxclaw-agent` in `/v1/models`-Endpoint
- [x] `main.py`: `chat/completions` routet `model=maxclaw-agent` zum LangGraph-Supervisor

**Abnahmekriterium:** ✅ Im Open-WebUI-Chat `maxclaw-agent` auswählen → Recherche, Datei-Operationen und Gedächtnis-Updates funktionieren.

---

### Meilenstein 11: Phase-4 – JWT Workspace-Dashboard ✅ ABGESCHLOSSEN
> **Ergebnis:** Sicheres Workspace-Dashboard mit Magic-Link-Auth, direkt aus dem Chat erreichbar.

- [x] `dashboard.py`: Lightweight JWT (HMAC-SHA256, kein externer Dependency)
- [x] `dashboard.py`: `POST /v1/workspace/magic-link` – generiert JWT mit 1h TTL
- [x] `dashboard.py`: `GET /dashboard` – verifiziert JWT und liefert HTML-Dashboard
- [x] `dashboard.py`: `GET /v1/workspace/files` – listet Workspace-Dateien (JSON)
- [x] `dashboard.py`: `GET /v1/workspace/files/{path}` – liest Dateiinhalt (JSON)
- [x] `dashboard.py`: `DELETE /v1/workspace/files/{path}` – löscht Datei
- [x] `main.py`: `/workspace`-Chat-Befehl generiert Magic-Link und gibt ihn als Chat-Antwort zurück
- [x] `config.py`: `DASHBOARD_JWT_SECRET` (Fallback auf `ENCRYPTION_KEY`)
- [x] `dashboard.py`: `_sanitize_user_id()` schützt Workspace-Pfad vor Injection

**Abnahmekriterium:** ✅ `/workspace` im Chat → Magic-Link-URL → `/dashboard?token=...` → HTML-Dashboard mit Dateiliste.

---

## 5. Zusammenfassung der Roadmap

```
M0:  Hotfixes & Cleanup                  [✅ Fertig]  → Saubere Codebasis
M1:  Lokale Infrastruktur                [✅ Fertig]  → Docker läuft komplett (7 Core-Services inkl. Goal-Engine)
M2:  Datenbank & Migrationen             [✅ Fertig]  → Persistenz + 9 Migrationen
M3:  Gemini-API-Integration              [✅ Fertig]  → Echte KI-Antworten (google-genai SDK) ✓
M4:  Chat-Frontend                       [✅ Fertig]  → Open WebUI + Dashboard ✓
M5:  RAG-Pipeline                        [✅ Fertig]  → NVIDIA Embeddings (2048-dim), PDF-Kontext in Antworten ✓
M5.5: HTTPS für Hetzner VPS             [✅ Fertig]  → Caddy + Let's Encrypt ✓
M6:  Authentifizierung & Sicherheit      [✅ Fertig]  → API-Key-Auth, erweiterter Schutz ✓
M7:  Fehlerbehandlung & Logging          [✅ Fertig]  → /health, /readyz, Log-Rotation ✓
M8:  Tests                               [✅ Fertig]  → ~80 Backend-Tests, alle grün ✓
M9:  Dokumentation & QA                  [✅ Fertig]  → Onboarding-Ready, Audit-Fixes BUG-04–15, Phase-2/3/4 ✓
M10: Phase-3 MaxClaw Agent               [✅ Fertig]  → LangGraph-Supervisor, Workspace-Tools, Core-Memory ✓
M11: Phase-4 JWT Dashboard               [✅ Fertig]  → Magic-Link, /dashboard, Workspace-API ✓
─────────────────────────────────────────────────────────────────────────────────
🎉  v1.0 STABIL – Bereit für Produktion!
v1.1 HARDENED – arq Worker, User-Keys, Multi-Provider, IVFFlat-Fix, HITL-Security ✅
Phase 2 FOUNDATION – GoalTask, /v1/goals, interner Tool-Server, LangGraph-Daemon ✅
Phase 3 MAXCLAW – LangGraph-Supervisor, Workspace-Tools, Core-Memory, DuckDuckGo-Fallback ✅
Phase 4 DASHBOARD – JWT Magic-Link, HTML-Dashboard, Workspace-File-API ✅
```

> [!IMPORTANT]
> Mit Abschluss von **Meilenstein 9** ist die **stabile v1.0** erreicht.
> Das **v1.1 Hardened**-Release bringt: arq Worker, nutzerspezifische API-Keys (Fernet-verschlüsselt), Multi-Model Routing, persistentes HITL via Redis, HITL-User-Binding und BUG-04–15.
> **Meilenstein 10 (Phase 3)** liefert den MaxClaw LangGraph-Supervisor-Agent mit Workspace-Tools, Core-Memory und DuckDuckGo-Fallback.
> **Meilenstein 11 (Phase 4)** liefert JWT Magic-Link-Authentication und das Workspace HTML-Dashboard.

---

## 6. Was noch offen ist (Phase 5+)

Phase 2/3/4 sind implementiert. Die folgenden Ausbaustufen bleiben für zukünftige Versionen:

- **Erweiterte LangGraph-Agenten:** komplexere Planungslogik, mehrstufige Tool-Ketten und echte autonome Strategien
- **DuckDuckGo-Fallback im Main-Chat:** `tool_web_search()` in `main.py` hat noch keinen Fallback (im MaxClaw-Agent ✅ behoben).
- **Redis-Caching für RAG:** Dokumenten-basiertes Caching zur Beschleunigung identischer Anfragen und Kostensenkung.
- **SSE-Streaming Fix:** `_convert_and_stream()` in `asyncio.to_thread()` auslagern, um Event-Loop-Blocking zu vermeiden.
- **Nginx & Skalierung:** Reverse Proxy mit Lastverteilung (Load Balancing) bei steigender Nutzerzahl (>50).
- **Security-Härtung (Enterprise-Ready):**
  - **JWT/OAuth2:** Übergang von statischem API-Key zu dynamischen, ablaufenden Token.
  - **DB-Verschlüsselung:** TDE (Disk-at-rest) und optional `pgcrypto` für sensible PDF-Inhalte.
  - **PDF-Sandboxing:** Metadaten-Stripping (`exiftool`) und isoliertes Parsing (z. B. gVisor).
  - **Echter Tool-Call-Mechanismus im User-Chat:** Ersetzen der `"search"`-Heuristik durch Function-Calling API.
- **UX & Stabilität (Hoher Mehrwert):**
  - **Idempotenz & Safety:** Idempotenz-Tokens für API-Calls und dediziertes Rate Limiting für Daemons.
  - **Sentry-Integration:** Fehler-Monitoring und Alerts in Echtzeit.
- **CI/CD-Pipeline:** GitHub Actions für automatische Tests und Cloud-Run/Hetzner-Deployment
- **Monitoring & Alerting:** APM-Integration (z.B. OpenTelemetry, Sentry)
- **Erweiterte Sicherheit:** NLP-basierte Prompt-Injection-Erkennung statt reiner Regex
- **Skalierung:** Kubernetes-Konfiguration, Horizontal Pod Autoscaler
- **Chat-Session-Persistenz im Backend:** `ChatSession` und `ChatMessage` ORM-Modelle (Open WebUI hat eigene Persistenz, aber Backend-seitiger Verlauf für Audit-Logs)
