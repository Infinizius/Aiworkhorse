# AI-Workhorse v8 – Entwicklungsstatus & Roadmap zur stabilen v1.0

> **Stand:** April 2026 | **Branch:** `copilot/setup-secure-connection-workhorse`

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
| Datenbank | PostgreSQL 16 mit pgvector-Extension |
| Cache / Queue | Redis 7 |
| Containerisierung | Docker Compose (5 Services + optionaler Caddy) |
| Reverse Proxy | Caddy 2 (automatisches HTTPS via Let's Encrypt) |
| Zielplattform | Hetzner VPS (ARM64, z.B. CAX21) |

---

## 2. Aktueller Entwicklungsstand (v1.1 Hardened)

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
| Docker-Compose (6 Services) | ✅ Fertig | db, redis, api, worker, openwebui, caddy – mit Volumes und Healthchecks |
| Caddy HTTPS Reverse Proxy | ✅ Fertig | `--profile prod` – automatisches TLS via Let's Encrypt |
| Backup-Skript (`backup.sh`) | ✅ Fertig | pg_dump + tar für uploads |
| Sync-Skript (`sync.sh`) | ✅ Fertig | Tablet-freundlicher Git-Push |
| Dev-Container (VSCode) | ✅ Fertig | Python 3.11, Extensions, psql-Client |
| Alembic-Konfiguration | ✅ Fertig | Auto-Run beim Start (`lifespan`); exclude_tables für LangGraph |
| **API-Key-Authentifizierung** | ✅ Fertig | Bearer Token; `verify_api_key`-Dependency; Auth deaktivierbar (Dev) |
| **Token-basiertes Rate-Limiting** | ✅ Fertig | `_get_user_id()` bevorzugt Token-Hash vor Client-IP; X-Forwarded-For-Support |
| **Erweiterte Prompt-Injection-Defense** | ✅ Fertig | 20 Patterns: Overrides, Jailbreaks, Role-Injection, Template-Injection |
| **SQLAlchemy ORM-Modelle** | ✅ Fertig | `UploadedFile`, `FileEmbedding`, `UserConfig` in `models.py` |
| **Alembic-Migrationen** | ✅ Fertig | 3 Migrationen: Initial-Schema, UserConfig, IVFFlat-Index-Fix |
| **RAG-Pipeline** | ✅ Fertig | Chunking, `text-embedding-004`, pgvector-Insert und -Suche |
| **Document Management API** | ✅ Fertig | GET (mit chunks/preview/total)/DELETE (mit 404-Check)/Download |
| **Web-Search Tool** | ✅ Fertig | Serper API (primär) |
| **Open WebUI** | ✅ Fertig | Chat-UI auf Port 3002, OpenAI-API-kompatibel |
| **REACTIVE_MAX_ITERATIONS** | ✅ Fertig | Aus `.env` gelesen, in Chat-Loop verwendet |
| **GOAL_MAX_ITERATIONS** | ✅ Fertig | Aus `.env` gelesen (für Phase-2 Goal-Engine vorbereitet) |
| **Metadaten/Titel** | ✅ Fertig | `layout.tsx` und `metadata.json` korrekt befüllt |
| **Health-Endpoint `GET /health`** | ✅ Fertig | DB + Redis Verbindung geprüft (M7) |
| **Readiness-Probe `GET /readyz`** | ✅ Fertig | Kein API-Key nötig, für Docker-Healthchecks (M7) |
| **RFC 7807 Error-Format** | ✅ Fertig | Konsistente Fehlerstruktur mit `type`, `title`, `status`, `request_id` |
| **Request-ID Middleware** | ✅ Fertig | UUIDv4 per Request; `X-Request-ID`-Header in Response |
| **Backend-Tests (pytest)** | ✅ Fertig | 40 Tests: health, security (auth + injection + rate-limit), chat-routing, alle 10 models |
| **arq Worker** | ✅ Fertig | Asynchrone PDF-Embedding-Verarbeitung im Hintergrund |
| **Nutzerspezifische API-Keys** | ✅ Fertig | AES/Fernet-verschlüsselt in DB; Routing per User & Provider |
| **`google-genai` SDK** | ✅ Fertig | Migration auf neues Google SDK; Streaming + Non-Streaming |
| **Multi-Model Routing** | ✅ Fertig | Dynamisches Key-Routing pro User & Provider (Gemini/Mistral/DeepSeek) |
| **HITL User-Binding** | ✅ Fertig | `execution_id` an Initiator gebunden (BUG-14); 403 bei Fremd-Zugriff |

### 2.2 Bekannte Limitierungen & offene Punkte ⚠️

| Komponente | Problem | Priorität |
|---|---|---|
| DuckDuckGo-Fallback | `tool_web_search()` hat keinen echten Fallback – bei Serper-Fehler wird nur ein Fehlerstring zurückgegeben (ROADMAP-Claim war falsch) | 🟡 Mittel |
| HITL-Trigger | `"search" in message.lower()` ist ein zu breites Heuristikum (False Positives bei Wörtern wie "searching"); Re-Trigger-Bug nach Tool-Call behoben (BUG-08) | 🟡 Mittel |
| SSE-Streaming Event Loop | `_convert_and_stream()` (sync Generator) wird direkt in async `sse_gen()` iteriert → blockiert Event Loop | 🟡 Mittel |
| NEXT_PUBLIC_API_KEY im Browser | Dashboard-Frontend nutzt `NEXT_PUBLIC_API_KEY` – Key im Browser-Bundle sichtbar; nur für private Netzwerke akzeptabel | 🟡 Niedrig |
| CI/CD-Pipeline | Keine GitHub Actions, kein automatisches Deployment | 🔵 Phase 2 |
| JWT-Authentifizierung | Übergang von statischem API-Key zu dynamischen Token für Phase 2 geplant | 🔵 Phase 2 |
| LangGraph-Agenten | Für Phase 2 geplant (`GOAL_MAX_ITERATIONS`) | 🔵 Phase 2 |

### 2.3 Gesamtfortschritt (v1.1)

```
Infrastruktur      ███████████████████████  ~100%  (Caddy HTTPS, 6 Services, arq Worker)
Backend-Logik      █████████████████████░░   ~93%  (Gemini/Mistral/DS, RAG, HITL, UserKeys, BUG-08/09/10/14 behoben)
Frontend / UI      ████████████████████░░░   ~90%  (Dashboard + Dokumente-Seite, auth-aware)
RAG-Pipeline       ████████████████████░░░   ~90%  (Upload, Embed async, Retrieve, Inject)
Sicherheit         █████████████████████░░   ~93%  (API-Key, Injection-Defense, Encryption, HITL-User-Binding BUG-14)
Tests              █████████████████████░░   ~93%  (40 Backend-Tests ✅; alle 10 Modelle geprüft; Frontend-Tests: Phase 2)
Dokumentation      █████████████████████░░   ~93%  (README, ROADMAP, SECURITY_AUDIT, Swagger aktualisiert)
─────────────────────────────────────────────────────────────────
Gesamt (v1.1)      █████████████████████░░   ~93%  (v1.0 stabil; v1.1 gehärtet; April-2026-Audit BUG-08–15 behoben)
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

#### BUG-05: Documents-Dashboard ohne Auth-Header – ✅ BEHOBEN (Audit April 2026)
- **Problem:** `app/documents/page.tsx` sendete keine `Authorization`-Header bei `fetch()`-Calls.
  Bei gesetztem `API_KEY` lieferten alle Requests 401. Download-Link via `<a href>` konnte
  keinen Bearer-Token senden.
- **Fix:** `apiHeaders()`-Hilfsfunktion liest `NEXT_PUBLIC_API_KEY` (aus `.env`); alle API-Calls
  und Downloads verwenden den Header. `.env.example` dokumentiert die neue Variable.

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
- `GOAL_MAX_ITERATIONS` aus `.env` gelesen, für Phase-2-Goal-Engine vorbereitet.

#### ARCH-10: Falscher Titel in `layout.tsx` – ✅ BEHOBEN
- Titel: `"AI-Workhorse v8"`, Beschreibung: DSGVO-konforme Plattformbeschreibung.

#### ARCH-11: Leere `metadata.json` – ✅ BEHOBEN
- `name` und `description` korrekt befüllt.

#### ARCH-12: Keine Tests – ✅ BEHOBEN (M8)
- 40 Backend-Tests in `backend/tests/`: health, security, chat-routing, models.

#### ARCH-13: Kein Health-Endpoint – ✅ BEHOBEN (M7)
- `GET /health` prüft DB- und Redis-Verbindung; `GET /readyz` als öffentliche Liveness-Probe.

### 3.3 Bekannte Limitierungen (nicht-kritisch) 🟡

#### LIMIT-01: DuckDuckGo-Fallback nicht implementiert
- **Problem:** ROADMAP und frühere README-Version behaupteten "DuckDuckGo (Fallback) – echte Implementierung".
  Tatsächlich gibt `tool_web_search()` bei Serper-Fehler nur einen Fehler-String zurück.
- **Status:** Dokumentation korrigiert. Echte Implementierung für Phase 2 vorgesehen.

#### LIMIT-02: HITL-Trigger-Heuristik zu breit
- **Problem:** `"search" in message.lower()` löst HITL für jede Nachricht mit dem Wort "search" aus (False Positives: "I'm searching for...", "What's the binary search algorithm?").
- **Teilbehoben:** Das davon abgeleitete Re-Trigger-Problem (nach erfolgreicher Tool-Ausführung wurde HITL erneut ausgelöst) wurde mit BUG-08 gefixt. Die zu breite Heuristik selbst bleibt eine bekannte Einschränkung.
- **Status:** Für Phase 2: Echter Tool-Call-Mechanismus via Function Calling API.

#### LIMIT-03: SSE-Streaming blockiert Event Loop
- **Problem:** `_convert_and_stream()` ist ein synchroner Generator, der direkt in `sse_gen()` iteriert.
  Langsamere Gemini-Antworten blockieren den asyncio Event Loop für andere Requests.
- **Status:** Bekannte Einschränkung für Single-User/Low-Traffic. Fix: `asyncio.to_thread()` für Phase 2.

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

**Abnahmekriterium:** ✅ `docker compose up && curl http://localhost:8000/docs` gibt Swagger-UI zurück.

---

### Meilenstein 2: Datenbankschema & Migrationen ✅ ABGESCHLOSSEN
> **Ergebnis:** Persistente Datenhaltung für Dateien und Embeddings.

- [x] SQLAlchemy-ORM-Modelle angelegt (`backend/models.py`):
  - `UploadedFile` (id, filename, path, extracted_text, page_count, uploaded_at)
  - `FileEmbedding` (id, file_id, chunk_text, chunk_index, embedding VECTOR(768))
  - `UserConfig` (id, user_id, provider, encrypted_key, updated_at)
- [x] Alembic-Migrationen: `0001_initial_schema.py`, `c1c21ee5d1e1_add_user_configs_table.py`, `d7f3a1b2c8e9_restore_ivfflat_index.py`
- [x] pgvector-Extension in Migration aktiviert
- [x] IVFFlat-Cosine-Index auf `file_embeddings.embedding` (via Migration `d7f3a1b2c8e9` nach Fix von BUG-06)
- [x] Async-SQLAlchemy-Session via `lifespan` in FastAPI integriert
- [x] Alembic-Migrationen beim Start automatisch ausführen (`alembic upgrade head` im `lifespan`-Hook)

**Abnahmekriterium:** ✅ Tabellen werden beim ersten Start automatisch erstellt.

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

- [x] Embedding-Modell: `text-embedding-004` (Google, 768 Dim.) via `google-genai`
- [x] Nach PDF-Upload: Text in Chunks aufteilen (500 Wörter, 50 Wörter Overlap)
- [x] Für jeden Chunk: Embedding erstellen, in pgvector-Tabelle speichern
- [x] Chat-Completions: Wenn `file_ids` übergeben, Cosine-Ähnlichkeitssuche via pgvector
- [x] Top-5-Chunks als Kontext in System-Prompt eingefügt
- [x] Document-Management-API: `GET /v1/files`, `GET /v1/files/{id}`, `DELETE /v1/files/{id}`
- [x] Download-Endpoint: `GET /v1/files/{id}/download`
- [x] Web-Search-Tool: Serper API (primär); DuckDuckGo-Fallback bleibt bewusst Phase 2

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
> **Ergebnis:** 40 Backend-Tests, alle grün (0 Fehler).

**Backend (pytest) – `backend/tests/` – 40/40 ✅:**
- [x] `requirements-dev.txt` + `pytest.ini` + `conftest.py` (Fixtures: Mock-Lifespan, Mock-Redis, Auth-Client)
- [x] `test_health.py`: `/readyz` (public), `/health` (auth), Redis-Down → 503
- [x] `test_security.py`: Auth-Guard (401), 17 Injection-Patterns (400), Unicode-Bypass, Rate-Limit (429)
- [x] `test_chat.py`: Gemini-Routing, Mistral-Routing, DeepSeek-Routing, RFC 7807 Error-Format
- [x] `test_models.py`: Format, Vollständigkeit aller 10 Modelle (Gemini 4× + Gemma + DeepSeek 2× + Mistral 3×)

**Frontend (vitest):**
- [ ] Verschoben auf M9 oder Post-v1.0 (Next.js App Router-Komponenten erfordern separaten Audit)

**Abnahmekriterium:** ✅ `python -m pytest tests/ -v` → `40 passed in <1s`

---

### Meilenstein 9: Dokumentation & Finale Qualitätssicherung ✅ ABGESCHLOSSEN
> **Ergebnis:** Onboarding-ready. Ein neuer Entwickler kann das Projekt in < 30 Minuten lokal starten.

- [x] `.env.example` auf Vollständigkeit geprüft: alle Variablen dokumentiert (MISTRAL_API_KEY, WEBUI_API_KEY, WEBUI_INTERNAL_URL, POSTGRES_*, REACTIVE_MAX_ITERATIONS, NEXT_PUBLIC_API_KEY, etc.)
- [x] Inline-Code-Kommentare überprüft und ergänzt (Rate-Limiter, RAG-Pipeline, Injection-Defense, Proxy-Routing)
- [x] ESLint-Konfiguration: `ignoreDuringBuilds: false` bestätigt aktiv in `next.config.ts`
- [x] Dead-Code aus `main.py` entfernt (M7-Vorbereitung)
- [x] End-to-End-Verifikation: Alle 40 Backend-Tests grün, API-Endpunkte live und erreichbar
- [x] **Architektur-Audit (April 2026, Runde 1):** BUG-04–07 behoben (API-Response-Format, Auth-Header, IVFFlat-Index, DEFAULT_MODELS)
- [x] **Architektur-Audit (April 2026, Runde 2):** BUG-08–14 behoben (HITL Re-Trigger, Worker-Startup, DELETE 404, Encryption-Key-Validation, Test-Coverage, Doc-Accuracy, HITL-Security)
- [x] **Audit (April 2026, Runde 3):** BUG-15 behoben; README/ROADMAP-Claims gegen Code, Docker und Tests harmonisiert

**Abnahmekriterium:** ✅ Alle Tests grün. `.env.example` dokumentiert vollständig den Onboarding-Pfad.

---

## 5. Zusammenfassung der Roadmap

```
M0: Hotfixes & Cleanup                  [✅ Fertig]  → Saubere Codebasis
M1: Lokale Infrastruktur                [✅ Fertig]  → Docker läuft komplett (6 Services inkl. Worker)
M2: Datenbank & Migrationen             [✅ Fertig]  → Persistenz + 3 Migrationen
M3: Gemini-API-Integration              [✅ Fertig]  → Echte KI-Antworten (google-genai SDK) ✓
M4: Chat-Frontend                       [✅ Fertig]  → Open WebUI + Dashboard ✓
M5: RAG-Pipeline                        [✅ Fertig]  → PDF-Kontext in Antworten ✓
M5.5: HTTPS für Hetzner VPS             [✅ Fertig]  → Caddy + Let's Encrypt ✓
M6: Authentifizierung & Sicherheit      [✅ Fertig]  → API-Key-Auth, erweiterter Schutz ✓
M7: Fehlerbehandlung & Logging          [✅ Fertig]  → /health, /readyz, Log-Rotation ✓
M8: Tests                               [✅ Fertig]  → 40 Backend-Tests, alle grün ✓
M9: Dokumentation & QA                  [✅ Fertig]  → Onboarding-Ready, Audit-Fixes BUG-04–15 ✓
─────────────────────────────────────────────────────────────────────────────
🎉  v1.0 STABIL – Bereit für Produktion!
v1.1 HARDENED – arq Worker, User-Keys, Multi-Provider, IVFFlat-Fix, HITL-Security ✅
```

> [!IMPORTANT]
> Mit Abschluss von **Meilenstein 9** ist die **stabile v1.0** erreicht.
> Das **v1.1 Hardened**-Release bringt zusätzlich: arq Worker, nutzerspezifische
> API-Keys (Fernet-verschlüsselt), Multi-Model Routing (Gemini/Mistral/DeepSeek),
> persistentes HITL via Redis, HITL-User-Binding (Security) und mehrere kritische
> Bug-Fixes aus dem dreistufigen April-2026-Audit (BUG-04–15).

---

## 6. Was für Phase 2 geplant ist (nach v1.1)

Die folgenden Features sind bereits in der Architektur angedeutet (Alembic `checkpoints`-Tabellen, `GOAL_MAX_ITERATIONS`), aber explizit für nach der ersten stabilen Version vorgesehen:

- **LangGraph-Agenten:** Autonome, mehrstufige Goal-Engine (`GOAL_MAX_ITERATIONS=10`)
- **DuckDuckGo-Fallback:** Echter Web-Search-Fallback wenn Serper-Key fehlt (aktuell: Fehler-String).
- **Redis-Caching für RAG:** Dokumenten-basiertes Caching (z.B. arXiv-Paper) zur Beschleunigung identischer Anfragen und Kostensenkung.
- **SSE-Streaming Fix:** `_convert_and_stream()` in `asyncio.to_thread()` auslagern, um Event-Loop-Blocking zu vermeiden.
- **Nginx & Skalierung:** Reverse Proxy mit Lastverteilung (Load Balancing) bei steigender Nutzerzahl (>50).
- **Security-Härtung (Enterprise-Ready):**
  - **JWT/OAuth2:** Übergang von statischem API-Key zu dynamischen, ablaufenden Token.
  - **DB-Verschlüsselung:** TDE (Disk-at-rest) und optional `pgcrypto` für sensible PDF-Inhalte.
  - **PDF-Sandboxing:** Metadaten-Stripping (`exiftool`) und isoliertes Parsing (z. B. gVisor).
  - **Echter Tool-Call-Mechanismus:** Ersetzen der `"search"`-Heuristik durch Function-Calling API.
- **UX & Stabilität (Hoher Mehrwert):**
  - **Idempotenz & Safety:** Idempotenz-Tokens für API-Calls und dediziertes Rate Limiting für Daemons.
  - **Sentry-Integration:** Fehler-Monitoring und Alerts in Echtzeit.
- **CI/CD-Pipeline:** GitHub Actions für automatische Tests und Cloud-Run/Hetzner-Deployment
- **Monitoring & Alerting:** APM-Integration (z.B. OpenTelemetry, Sentry)
- **Erweiterte Sicherheit:** NLP-basierte Prompt-Injection-Erkennung statt reiner Regex
- **Skalierung:** Kubernetes-Konfiguration, Horizontal Pod Autoscaler
- **Chat-Session-Persistenz im Backend:** `ChatSession` und `ChatMessage` ORM-Modelle (Open WebUI hat eigene Persistenz, aber Backend-seitiger Verlauf für Audit-Logs)
