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

## 2. Aktueller Entwicklungsstand

### 2.1 Implementiert und funktionsfähig ✅

| Komponente | Status | Anmerkung |
|---|---|---|
| FastAPI-Backend-Grundstruktur | ✅ Fertig | Endpoints definiert, Pydantic-Modelle vorhanden |
| Strukturiertes JSON-Logging (JSONL) | ✅ Fertig | ISO-8601-Zeitstempel, Request-Kontext |
| Token-Bucket Rate Limiter | ✅ Fertig | 10 Req/Min/IP via Redis |
| Dreistufige Prompt-Injection-Defense | ✅ Fertig | Unicode-Normalisierung + System-Anker + Regex |
| HITL Freigabe-System + SSE-Heartbeat | ✅ Fertig | 60s Timeout, Memory-Leak-Schutz im finally-Block |
| PDF-Upload mit Path-Traversal-Schutz | ✅ Fertig | UUID-Dateinamen, pdfplumber-Parsing |
| SHA256-Prompt-Caching (Redis, 24h TTL) | ✅ Fertig | Nur für Non-RAG-Queries |
| Next.js-Dashboard | ✅ Fertig | Statusseite mit Service-Links und Feature-Übersicht |
| Dokumente-Seite (`/documents`) | ✅ Fertig | Liste, Vorschau, Löschen, Download |
| TailwindCSS v4-Setup | ✅ Fertig | PostCSS konfiguriert |
| `useIsMobile`-Hook | ✅ Fertig | SSR-sicher, 768px-Breakpoint |
| `cn()`-Utility (clsx + tailwind-merge) | ✅ Fertig | Standard-Helfer |
| Docker-Compose (5 Services) | ✅ Fertig | db, redis, api, openwebui, caddy – mit Volumes und Healthchecks |
| Caddy HTTPS Reverse Proxy | ✅ Fertig | `--profile prod` – automatisches TLS via Let's Encrypt |
| Backup-Skript (`backup.sh`) | ✅ Fertig | pg_dump + tar für uploads |
| Sync-Skript (`sync.sh`) | ✅ Fertig | Tablet-freundlicher Git-Push |
| Dev-Container (VSCode) | ✅ Fertig | Python 3.11, Extensions, psql-Client |
| Alembic-Konfiguration | ✅ Fertig | Verbindung zu PostgreSQL hinterlegt |
| **API-Key-Authentifizierung** | ✅ Fertig | Bearer Token; `verify_api_key`-Dependency; Auth deaktivierbar (Dev) |
| **Token-basiertes Rate-Limiting** | ✅ Fertig | `_get_user_id()` bevorzugt Token-Hash vor Client-IP; X-Forwarded-For-Support |
| **Erweiterte Prompt-Injection-Defense** | ✅ Fertig | 20 Patterns: Overrides, Jailbreaks, Role-Injection, Template-Injection |
| **SQLAlchemy ORM-Modelle** | ✅ Fertig | `UploadedFile`, `FileEmbedding` in `models.py` |
| **Alembic-Erstmigration** | ✅ Fertig | `0001_initial_schema.py` – pgvector Extension + Tabellen |
| **RAG-Pipeline** | ✅ Fertig | Chunking, `text-embedding-004`, pgvector-Insert und -Suche |
| **Document Management API** | ✅ Fertig | GET/DELETE/Download für hochgeladene Dateien |
| **Web-Search Tool** | ✅ Fertig | Serper API (primär) + DuckDuckGo (Fallback) |
| **Open WebUI** | ✅ Fertig | Chat-UI auf Port 3002, OpenAI-API-kompatibel |
| **REACTIVE_MAX_ITERATIONS** | ✅ Fertig | Aus `.env` gelesen, in Chat-Loop verwendet |
| **GOAL_MAX_ITERATIONS** | ✅ Fertig | Aus `.env` gelesen (für Phase-2 Goal-Engine vorbereitet) |
| **Metadaten/Titel** | ✅ Fertig | `layout.tsx` und `metadata.json` korrekt befüllt |

### 2.2 Unvollständig oder ausstehend ⚠️

| Komponente | Problem | Priorität |
|---|---|---|
| API-Authentifizierung (API-Key) | ✅ Implementiert (Bearer Token, M6) | 🟠 Hoch |
| ESLint im Build | `ignoreDuringBuilds: false` – ESLint aktiv (M6) | ✅ Behoben |
| Prompt-Injection-Pattern | Regex-Liste klein (5 Pattern); L33tspeak / Leerzeichen-Bypass möglich | 🟡 Mittel |
| Health-Endpoint `GET /health` | Nicht vorhanden – DB + Redis Verbindung nicht prüfbar | 🟡 Mittel |
| Alembic automatisch beim Start | `alembic upgrade head` muss manuell ausgeführt werden | 🟡 Mittel |
| Log-Rotation | JSONL-Datei wächst unbegrenzt | 🟡 Mittel |
| Tests | **Null** Test-Dateien vorhanden | 🟡 Mittel |
| CI/CD-Pipeline | Keine GitHub Actions, kein automatisches Deployment | 🔵 Phase 2 |
| JWT Rate-Limiting | Rate-Limiting nutzt Token-Hash statt roher IP (M6) | ✅ Behoben |
| LangGraph-Agenten | Für Phase 2 geplant (`GOAL_MAX_ITERATIONS`) | 🔵 Phase 2 |

### 2.3 Gesamtfortschritt

```
Infrastruktur      ██████████████████████  ~95%  (Caddy HTTPS, 5 Services)
Backend-Logik      █████████████████░░░░░  ~80%  (Gemini, RAG, HITL – kein JWT)
Frontend / UI      ███████████░░░░░░░░░░░  ~55%  (Dashboard + Dokumente-Seite)
RAG-Pipeline       ████████████████████░░  ~90%  (Upload, Embed, Retrieve, Inject)
Sicherheit         ████████████████░░░░░░  ~75%  (kein JWT, schwache Injection-Pattern)
Tests              ░░░░░░░░░░░░░░░░░░░░░░   ~0%
Dokumentation      █████████████████░░░░░  ~75%  (README, ROADMAP, Swagger)
─────────────────────────────────────────────────
Gesamt (MVP)       █████████████░░░░░░░░░  ~55%
```

---

## 3. Bugs & Architekturprobleme

### 3.1 Behobene Bugs ✅

#### BUG-01: Keine echte LLM-Anbindung – ✅ BEHOBEN
- **Fix:** `google-generativeai>=0.8.0` in `requirements.txt`; echter `generate_content`-Call
  in `sse_generator()` und non-Streaming-Pfad; Startup-Check für `GEMINI_API_KEY`.

#### BUG-02: Keine Frontend-Seiten – ✅ BEHOBEN
- **Fix:** `app/page.tsx` (Dashboard), `app/documents/page.tsx` (Dokumentenverwaltung)
  mit vollständigem UI, Service-Links und Feature-Übersicht.

#### BUG-03: `pdf.pages` nach `with`-Block referenziert – ✅ BEHOBEN
- **Fix:** `page_count = len(pdf.pages)` wird jetzt korrekt innerhalb des `with`-Blocks
  berechnet, danach erst im Return-Wert verwendet.

### 3.2 Behobene Architekturprobleme ✅

#### ARCH-02: Keine Datenbankmodelle – ✅ BEHOBEN
- `backend/models.py` enthält `UploadedFile` und `FileEmbedding` (SQLAlchemy ORM).
- Alembic-Erstmigration `0001_initial_schema.py` legt pgvector-Extension, Tabellen
  und IVFFlat-Index an.

#### ARCH-03: pgvector nicht integriert – ✅ BEHOBEN
- Vollständige RAG-Pipeline: PDF-Text in Chunks aufteilen → `text-embedding-004` Embedding
  → pgvector-Insert → Cosine-Ähnlichkeitssuche bei `chat/completions` mit `file_ids`.

#### ARCH-04: `approval_events`-Dict ohne TTL – ✅ BEHOBEN
- HITL-Freigaben erhalten einen 60-Sekunden-Timeout; danach wird automatisch abgelehnt.

#### ARCH-06: `google-generativeai` fehlte – ✅ BEHOBEN
- `google-generativeai>=0.8.0` ist in `backend/requirements.txt` enthalten.

#### ARCH-07: Datenbank-Passwort hartkodiert – ✅ BEHOBEN
- `docker-compose.yml` liest `POSTGRES_PASSWORD` aus `.env` mit Pflicht-Validierung.

#### ARCH-08: Iterations-Limits nicht verwendet – ✅ BEHOBEN
- `REACTIVE_MAX_ITERATIONS` steuert die Tool-Call-Schleife in `sse_generator()`.
- `GOAL_MAX_ITERATIONS` aus `.env` gelesen, für Phase-2-Goal-Engine vorbereitet.

#### ARCH-10: Falscher Titel in `layout.tsx` – ✅ BEHOBEN
- Titel: `"AI-Workhorse v8"`, Beschreibung: DSGVO-konforme Plattformbeschreibung.

#### ARCH-11: Leere `metadata.json` – ✅ BEHOBEN
- `name` und `description` korrekt befüllt.

### 3.3 Offene Architekturprobleme 🔴🟠🟡

#### ARCH-01: IP-basiertes Rate-Limiting statt JWT – ✅ BEHOBEN (M6)
- **Fix:** `verify_api_key`-Dependency (Bearer Token); `_get_user_id()` nutzt Token-Hash;
  `_get_client_ip()` wertet `X-Forwarded-For` korrekt aus (Caddy-Proxy-kompatibel).

#### ARCH-05: Schwache Prompt-Injection-Erkennung – ✅ BEHOBEN (M6)
- **Fix:** `_INJECTION_PATTERNS`-Liste mit 20 Patterns (direkte Overrides, Jailbreaks,
  Role-Injection, Template-Injection-Marker).

#### ARCH-09: ESLint im Build deaktiviert – ✅ BEHOBEN (M6)
- **Fix:** `ignoreDuringBuilds: false` in `next.config.ts`; alle ESLint-Fehler bereinigt.

#### ARCH-12: Keine Tests
- **Problem:** Weder für Backend (pytest) noch für Frontend (vitest) existieren Test-Dateien.
- **Fix:** Testsuite aufbauen (siehe Meilenstein 8).

#### ARCH-13: Kein Health-Endpoint
- **Problem:** `GET /health` existiert nicht – Infrastruktur-Monitoring und Container-Orchestrierung
  (z.B. Kubernetes) haben keine Möglichkeit den Applikationszustand zu prüfen.
- **Fix:** Endpoint implementieren, der DB- und Redis-Verbindung prüft.

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
- [ ] **ARCH-09:** ESLint im Build aktivieren (`ignoreDuringBuilds: false`)

---

### Meilenstein 1: Lokale Infrastruktur vollständig lauffähig ✅ ABGESCHLOSSEN
> **Ergebnis:** `docker compose up` startet alle Services fehlerfrei.

- [x] `docker-compose.yml`: Datenbankpasswort aus `.env` einlesen
- [x] `backend/requirements.txt`: `google-generativeai>=0.8.0` hinzugefügt
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
- [x] Alembic-Erstmigration (`0001_initial_schema.py`)
- [x] pgvector-Extension in Migration aktiviert
- [x] IVFFlat-Cosine-Index auf `file_embeddings.embedding`
- [x] Async-SQLAlchemy-Session via `lifespan` in FastAPI integriert
- [ ] Alembic-Migrationen beim Start automatisch ausführen (`alembic upgrade head` im `lifespan`-Hook)

**Abnahmekriterium:** ✅ Tabellen werden beim ersten Start automatisch erstellt.

---

### Meilenstein 3: Gemini-API-Integration ✅ ABGESCHLOSSEN
> **Ergebnis:** Echte KI-Antworten statt Mock-Strings.

- [x] `GEMINI_API_KEY` aus Umgebungsvariable einlesen
- [x] Startup-Warning: App loggt Warnung wenn `GEMINI_API_KEY` fehlt
- [x] `google-generativeai`-Client initialisieren (Singleton via `lifespan`)
- [x] Non-Streaming-Pfad: Echter `generate_content`-Call an `gemini-2.0-flash-exp`
- [x] Streaming-Pfad: `generate_content_stream` via Thread-Pool in `sse_generator()` integriert
- [x] OpenAI-Format → Gemini-Format Konvertierung (`_convert_messages_for_gemini`)
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

- [x] Embedding-Modell: `text-embedding-004` (Google, 768 Dim.) via `google-generativeai`
- [x] Nach PDF-Upload: Text in Chunks aufteilen (500 Wörter, 50 Wörter Overlap)
- [x] Für jeden Chunk: Embedding erstellen, in pgvector-Tabelle speichern
- [x] Chat-Completions: Wenn `file_ids` übergeben, Cosine-Ähnlichkeitssuche via pgvector
- [x] Top-5-Chunks als Kontext in System-Prompt eingefügt
- [x] Document-Management-API: `GET /v1/files`, `GET /v1/files/{id}`, `DELETE /v1/files/{id}`
- [x] Download-Endpoint: `GET /v1/files/{id}/download`
- [x] Web-Search-Tool: Serper API (primär) + DuckDuckGo (Fallback) – echte Implementierung

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
> **Ergebnis:** 39 Backend-Tests, alle grün (0 Fehler).

**Backend (pytest) – `backend/tests/` – 39/39 ✅:**
- [x] `requirements-dev.txt` + `pytest.ini` + `conftest.py` (Fixtures: Mock-Lifespan, Mock-Redis, Auth-Client)
- [x] `test_health.py`: `/readyz` (public), `/health` (auth), Redis-Down → 503
- [x] `test_security.py`: Auth-Guard (401), 17 Injection-Patterns (400), Unicode-Bypass, Rate-Limit (429)
- [x] `test_chat.py`: Gemini-Routing, Mistral-Routing, DeepSeek-Routing, RFC 7807 Error-Format
- [x] `test_models.py`: Format, Vollständigkeit aller Provider (Gemini, DeepSeek, Mistral)

**Frontend (vitest):**
- [ ] Verschoben auf M9 oder Post-v1.0 (Next.js App Router-Komponenten erfordern separaten Audit)

**Abnahmekriterium:** ✅ `python -m pytest tests/ -v` → `39 passed, 1 warning in 41.58s`

---

### Meilenstein 9: Dokumentation & Finale Qualitätssicherung (Dauer: ~1 Tag)
> **Ziel:** Ein Entwickler kann das Projekt ohne Vorkenntnisse lokal aufsetzen.

### Meilenstein 9: Dokumentation & Finale Qualitätssicherung ✅ ABGESCHLOSSEN
> **Ergebnis:** Onboarding-ready. Ein neuer Entwickler kann das Projekt in < 30 Minuten lokal starten.

- [x] `.env.example` auf Vollständigkeit geprüft: alle Variablen dokumentiert (MISTRAL_API_KEY, WEBUI_API_KEY, WEBUI_INTERNAL_URL, POSTGRES_*, REACTIVE_MAX_ITERATIONS, etc.)
- [x] Inline-Code-Kommentare überprüft und ergänzt (Rate-Limiter, RAG-Pipeline, Injection-Defense, Proxy-Routing)
- [x] ESLint-Konfiguration: `ignoreDuringBuilds: false` bestätigt aktiv in `next.config.ts`
- [x] Dead-Code aus `main.py` entfernt (M7-Vorbereitung)
- [x] End-to-End-Verifikation: Alle 39 Backend-Tests grün, API-Endpunkte live und erreichbar

**Abnahmekriterium:** ✅ Alle Tests grün. `.env.example` dokumentiert vollständig den Onboarding-Pfad.

---

## 5. Zusammenfassung der Roadmap

```
M0: Hotfixes & Cleanup                  [✅ Fertig]  → Saubere Codebasis
M1: Lokale Infrastruktur                [✅ Fertig]  → Docker läuft komplett (5 Services)
M2: Datenbank & Migrationen             [✅ Fertig]  → Persistenz vorhanden
M3: Gemini-API-Integration              [✅ Fertig]  → Echte KI-Antworten ✓
M4: Chat-Frontend                       [✅ Fertig]  → Open WebUI + Dashboard ✓
M5: RAG-Pipeline                        [✅ Fertig]  → PDF-Kontext in Antworten ✓
M5.5: HTTPS für Hetzner VPS             [✅ Fertig]  → Caddy + Let's Encrypt ✓
M6: Authentifizierung & Sicherheit      [✅ Fertig]  → API-Key-Auth, erweiterter Schutz ✓
M7: Fehlerbehandlung & Logging          [✅ Fertig]  → /health, /readyz, Stdout-Logging ✓
M8: Tests                               [✅ Fertig]  → 39 Backend-Tests, alle grün ✓
M9: Dokumentation & QA                  [✅ Fertig]  → Onboarding-Ready, .env.example ✓
─────────────────────────────────────────────────────────────────────────────
🎉  v1.0 STABIL – Bereit für Produktion!
```

> [!IMPORTANT]
> Mit Abschluss von **Meilenstein 9** ist die **stabile v1.0** erreicht.
> Das System ist produktionsreif mit: RAG, Multi-Provider-LLMs (Gemini/Mistral/DeepSeek),
> HTTPS, Auth, Rate Limiting, 39 Tests und vollständiger Dokumentation.

---

## 6. Was für Phase 2 geplant ist (nach v1.0)

Die folgenden Features sind bereits in der Architektur angedeutet (Alembic `checkpoints`-Tabellen, `GOAL_MAX_ITERATIONS`), aber explizit für nach der ersten stabilen Version vorgesehen:

- **LangGraph-Agenten:** Autonome, mehrstufige Goal-Engine (`GOAL_MAX_ITERATIONS=10`)
- **Redis-Caching für RAG:** Dokumenten-basiertes Caching (z.B. arXiv-Paper) zur Beschleunigung identischer Anfragen und Kostensenkung.
- **Nginx & Skalierung:** Reverse Proxy mit Lastverteilung (Load Balancing) bei steigender Nutzerzahl (>50).
- **Security-Härtung (Enterprise-Ready):**
  - **JWT/OAuth2:** Übergang von statischem API-Key zu dynamischen, ablaufenden Token.
  - **DB-Verschlüsselung:** TDE (Disk-at-rest) und optional `pgcrypto` für sensible PDF-Inhalte.
  - **PDF-Sandboxing:** Metadaten-Stripping (`exiftool`) und isoliertes Parsing (z. B. gVisor).
- **UX & Stabilität (Hoher Mehrwert):**
  - **Asynchrone Uploads:** Hintergrund-Verarbeitung (Redis + `arq`) zur Entlastung der UI.
  - **Idempotenz & Safety:** Idempotenz-Tokens für API-Calls und dediziertes Rate Limiting für Daemons.
  - **Sentry-Integration:** Fehler-Monitoring und Alerts in Echtzeit.
- **CI/CD-Pipeline:** GitHub Actions für automatische Tests und Cloud-Run/Hetzner-Deployment
- **Monitoring & Alerting:** APM-Integration (z.B. OpenTelemetry, Sentry)
- **Erweiterte Sicherheit:** NLP-basierte Prompt-Injection-Erkennung statt reiner Regex
- **Skalierung:** Kubernetes-Konfiguration, Horizontal Pod Autoscaler
- **Chat-Session-Persistenz im Backend:** `ChatSession` und `ChatMessage` ORM-Modelle (Open WebUI hat eigene Persistenz, aber Backend-seitiger Verlauf für Audit-Logs)
