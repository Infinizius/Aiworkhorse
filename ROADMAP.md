# AI-Workhorse v8 – Entwicklungsstatus & Roadmap zur stabilen v1.0

> **Stand:** März 2026 | **Branch:** `copilot/workhorse-development-status-report`

---

## 1. Projektüberblick

**AI-Workhorse** ist eine DSGVO-konforme KI-Assistenten-Plattform mit folgenden Kernfunktionen:

- **Sichere Chat-Completions** mit dreistufiger Prompt-Injection-Defense
- **Human-in-the-Loop (HITL)** Freigabe-System für Tool-Ausführungen via SSE
- **RAG (Retrieval-Augmented Generation)** mit PDF-Upload und pgvector
- **Rate Limiting** via Token-Bucket-Algorithmus (Redis)
- **Tablet-optimiertes "Vibe-Coding"-Workflow** (ARM64, HMR-steuerbar)

**Tech-Stack:**
| Schicht | Technologie |
|---|---|
| Frontend | Next.js 15 + React 19 + TypeScript + TailwindCSS v4 |
| Backend | FastAPI 0.110 + Python 3.11 + Uvicorn |
| Datenbank | PostgreSQL 16 mit pgvector-Extension |
| Cache / Queue | Redis 7 |
| Containerisierung | Docker Compose |
| Zielplattform | Google AI Studio / Cloud Run (ARM64) |

---

## 2. Aktueller Entwicklungsstand

### 2.1 Implementiert und funktionsfähig ✅

| Komponente | Status | Anmerkung |
|---|---|---|
| FastAPI-Backend-Grundstruktur | ✅ Fertig | Endpoints definiert, Pydantic-Modelle vorhanden |
| Strukturiertes JSON-Logging (JSONL) | ✅ Fertig | ISO-8601-Zeitstempel, Request-Kontext |
| Token-Bucket Rate Limiter | ✅ Fertig | 10 Req/Min/IP via Redis |
| Dreistufige Prompt-Injection-Defense | ✅ Fertig | Unicode-Normalisierung + System-Anker + Regex |
| HITL Freigabe-System + SSE-Heartbeat | ✅ Fertig | Memory-Leak-Schutz im finally-Block |
| PDF-Upload mit Path-Traversal-Schutz | ✅ Fertig | UUID-Dateinamen, pdfplumber-Parsing |
| SHA256-Prompt-Caching (Redis, 24h TTL) | ✅ Fertig | Nur für Non-RAG-Queries |
| Next.js-Frontend-Grundstruktur | ✅ Fertig | Layout, Global CSS, TypeScript-Config |
| TailwindCSS v4-Setup | ✅ Fertig | PostCSS konfiguriert |
| `useIsMobile`-Hook | ✅ Fertig | SSR-sicher, 768px-Breakpoint |
| `cn()`-Utility (clsx + tailwind-merge) | ✅ Fertig | Standard-Helfer |
| Docker-Compose (3 Services) | ✅ Fertig | db, redis, api – mit Volumes und Healthchecks |
| Backup-Skript (`backup.sh`) | ✅ Fertig | pg_dump + tar für uploads |
| Sync-Skript (`sync.sh`) | ✅ Fertig | Tablet-freundlicher Git-Push |
| Dev-Container (VSCode) | ✅ Fertig | Python 3.11, Extensions, psql-Client |
| Alembic-Konfiguration | ✅ Konfiguriert | Verbindung zu PostgreSQL hinterlegt |

### 2.2 Unvollständig oder Platzhalter ⚠️

| Komponente | Problem | Priorität |
|---|---|---|
| LLM-Integration (Gemini API) | Gibt hartkodierte Mock-Antwort zurück | 🔴 Kritisch |
| Frontend-Seiten / Chat-UI | Nur `layout.tsx` vorhanden – keine einzige Seite | 🔴 Kritisch |
| Vektor-Embedding + pgvector-Insert | TODO-Kommentar in `main.py:256` – nicht implementiert | 🔴 Kritisch |
| Web-Search-Tool | Dummy-Funktion, keine echte API (Serper/DDG) | 🟠 Hoch |
| Datenbank-Modelle (SQLAlchemy) | Keine ORM-Modelle, keine Datenbankabfragen | 🟠 Hoch |
| Alembic-Migrationsskripte | Konfiguriert, aber keine `versions/`-Dateien | 🟠 Hoch |
| API-Authentifizierung (JWT) | Nur IP-basiertes Rate-Limiting, kein Login | 🟠 Hoch |
| Iterations-Limits aus `.env` | `REACTIVE_MAX_ITERATIONS` / `GOAL_MAX_ITERATIONS` definiert, aber **nirgends verwendet** | 🟡 Mittel |
| Google GenAI SDK (`@google/genai`) | In `package.json` installiert, aber im Code nicht importiert | 🟡 Mittel |
| API-Dokumentation | Kein Swagger-UI / kein explizites OpenAPI-Schema | 🟡 Mittel |
| Tests | **Null** Test-Dateien vorhanden | 🟡 Mittel |
| CI/CD-Pipeline | Keine GitHub Actions, kein Cloud Build | 🟡 Mittel |
| README.md | Nur 8 Zeilen – kein Setup-Guide | 🟡 Mittel |
| LangGraph-Agenten | Alembic-Config nennt `checkpoints`-Tabellen, aber kein Code | 🔵 Phase 2 |

### 2.3 Gesamtfortschritt

```
Infrastruktur      ████████████████████░░  ~85%
Backend-Logik      ████████████░░░░░░░░░░  ~55%  (Mock-Antworten!)
Frontend / UI      ██░░░░░░░░░░░░░░░░░░░░  ~10%
RAG-Pipeline       █████░░░░░░░░░░░░░░░░░  ~20%
Sicherheit         ███████████████░░░░░░░  ~70%  (kein JWT)
Tests              ░░░░░░░░░░░░░░░░░░░░░░   ~0%
Dokumentation      ████░░░░░░░░░░░░░░░░░░  ~15%
─────────────────────────────────────────────────
Gesamt (MVP)       █████████░░░░░░░░░░░░░  ~35%
```

---

## 3. Bugs & Architekturprobleme

### 3.1 Kritische Bugs 🔴

#### BUG-01: Keine echte LLM-Anbindung
- **Datei:** `backend/main.py`, Zeile 208 & 214
- **Problem:** Beide Endpunkte (Streaming & Non-Streaming) geben immer denselben hartkodieren String zurück:
  ```
  "Sichere Antwort aus dem EU-Backend. Prompt Injection Defense aktiv."
  ```
  Es wird **kein** API-Call an Gemini oder ein anderes Modell gemacht. `GEMINI_API_KEY` aus `.env` wird nie gelesen.
- **Impact:** Die Kernanwendung liefert keine KI-Antworten.
- **Fix:** `google-generativeai` (Python SDK) zu `requirements.txt` hinzufügen, `GEMINI_API_KEY` einlesen, echten API-Call in `sse_generator()` integrieren.

#### BUG-02: Keine Frontend-Seiten
- **Datei:** `app/` Verzeichnis
- **Problem:** Es existiert nur `app/layout.tsx` – keine `page.tsx`, keine Route, kein Chat-UI. Der Browser zeigt eine leere Seite.
- **Impact:** Die Anwendung ist für Endnutzer unbedienbar.
- **Fix:** Mindestens `app/page.tsx` mit Chat-Interface implementieren.

#### BUG-03: `pdf.pages` nach `with`-Block referenziert
- **Datei:** `backend/main.py`, Zeile 261
- **Problem:** Der Rückgabewert `len(pdf.pages)` befindet sich außerhalb des `with pdfplumber.open(...)` Blocks. Das `pdf`-Objekt ist an dieser Stelle bereits geschlossen – der Zugriff auf `.pages` ist ein Fehler, der in einigen pdfplumber-Versionen zu einem `AttributeError` oder `ValueError` führen kann.
  ```python
  # FALSCH:
  with pdfplumber.open(file_path) as pdf:
      for page in pdf.pages:
          ...
  return {"pages_extracted": len(pdf.pages), ...}  # ← pdf ist schon zu!
  ```
- **Fix:** `pages_extracted` innerhalb des `with`-Blocks berechnen:
  ```python
  page_count = 0
  with pdfplumber.open(file_path) as pdf:
      page_count = len(pdf.pages)
      for page in pdf.pages:
          ...
  return {"pages_extracted": page_count, ...}
  ```

### 3.2 Hochpriorisierte Architekturprobleme 🟠

#### ARCH-01: IP-basiertes Rate-Limiting statt JWT
- **Datei:** `backend/main.py`, Zeile 76
- **Problem:** Die User-ID für das Token-Bucket ist die Client-IP. Hinter einem Reverse-Proxy (Nginx, Cloud Run Load Balancer) sehen alle Nutzer dieselbe IP, sodass das Rate-Limiting kollektiv für alle gilt. Außerdem lässt sich die IP-Adresse durch VPN trivial umgehen.
- **Kommentar im Code:** `"Für den MVP nutzen wir die Client-IP. Später: JWT/Auth-Token."` – Diese Entscheidung sollte vor dem ersten stabilen Release korrigiert werden.
- **Fix:** JWT-basierte Authentifizierung einführen. `X-Forwarded-For` / `X-Real-IP`-Header als Fallback, wenn kein Token vorhanden.

#### ARCH-02: Keine Datenbankmodelle
- **Datei:** `backend/main.py` – FEHLT
- **Problem:** Alembic ist konfiguriert, es gibt eine PostgreSQL-Instanz in Docker – aber es existieren weder SQLAlchemy-ORM-Modelle noch Migrationsskripte. Hochgeladene Dateien und Chat-Verläufe werden nicht persistiert.
- **Fix:** SQLAlchemy-Modelle für `files`, `chat_sessions`, `messages` anlegen; Alembic-Migration erstellen und ausführen.

#### ARCH-03: pgvector nicht integriert
- **Datei:** `backend/main.py`, Zeile 256: `# TODO: Vektorisierung & pgvector Insert`
- **Problem:** PDFs werden hochgeladen und geparst, aber nicht vektorisiert. Die RAG-Pipeline ist damit vollständig nicht funktionsfähig. Der `file_ids`-Parameter in `ChatCompletionRequest` wird nie tatsächlich genutzt.
- **Fix:** Embedding-Modell (z.B. `text-embedding-004` von Google) integrieren, pgvector-Tabelle mit Alembic anlegen, Ähnlichkeitssuche in `chat_completions_proxy` einhängen.

#### ARCH-04: `approval_events`-Dict ohne TTL
- **Datei:** `backend/main.py`, Zeile 43 / 137–201
- **Problem:** Obwohl der `finally`-Block einen sauberen Cleanup macht, gibt es kein Timeout für abgelehnte oder nie beantwortete Freigaben. Wenn das SSE-Event ewig wartet oder der Client die Verbindung abbricht, ohne den Approve-Endpoint aufzurufen, bleibt der Eintrag im Dict bis zum Serverneustart.
- **Aktueller Schutz:** `finally`-Block ist gut – aber nur, wenn die Exception korrekt hochkommt.
- **Fix:** Maximale Wartezeit (z.B. 60 Sekunden) für HITL-Freigaben; Danach automatisch ablehnen.

#### ARCH-05: Schwache Prompt-Injection-Erkennung
- **Datei:** `backend/main.py`, Zeilen 120–124
- **Problem:** Die Regex-Muster sind case-insensitive, aber können durch Tippfehler, Leerzeichen, L33tspeak oder Nicht-ASCII-Schrift umgangen werden. Beispiel: `ign0re previous`, `i g n o r e previous`.
- **Fix:** Erweiterte Pattern-Liste; alternativ semantische Erkennung über einen separaten Moderations-Endpoint (z.B. Gemini Safety-API).

### 3.3 Mittelprioritäre Probleme 🟡

| ID | Datei | Problem |
|---|---|---|
| ARCH-06 | `backend/requirements.txt` | `google-generativeai` fehlt komplett – Backend kann Gemini nicht aufrufen |
| ARCH-07 | `docker-compose.yml` | Datenbank-Passwort (`workhorse_secure_pw`) hartkodiert im Compose-File – sollte aus `.env` kommen |
| ARCH-08 | `.env.example` | `REACTIVE_MAX_ITERATIONS` und `GOAL_MAX_ITERATIONS` nirgendwo im Code verwendet |
| ARCH-09 | `next.config.ts:6` | `ignoreDuringBuilds: true` – ESLint-Fehler werden beim Build ignoriert und können versteckt werden |
| ARCH-10 | `app/layout.tsx` | Titel/Metadata ist `"My Google AI Studio App"` – Platzhalter, noch nicht angepasst |
| ARCH-11 | `metadata.json` | `description: ""` – leer |
| ARCH-12 | Gesamt | **Keine Tests** – weder für Backend (pytest) noch für Frontend (jest/vitest) |
| ARCH-13 | Gesamt | Keine CI/CD-Pipeline – kein automatisches Testen, kein automatisches Deployment |

---

## 4. Roadmap zur stabilen v1.0

Die folgende Roadmap ist in Meilensteine (M) gegliedert, die aufeinander aufbauen. Jeder Meilenstein endet mit einer testbaren, abnahmefähigen Version.

---

### Meilenstein 0: Hotfixes & Cleanup (Dauer: ~2 Tage)
> **Ziel:** Alle bekannten Bugs beheben, die lokales Testen derzeit verhindern.

- [ ] **BUG-03 fixen:** `len(pdf.pages)` innerhalb des `with`-Blocks berechnen (`backend/main.py`)
- [ ] **ARCH-10 fixen:** Titel/Metadata in `app/layout.tsx` und `metadata.json` aktualisieren
- [ ] **ARCH-09 entschärfen:** ESLint im Build aktivieren (oder zumindest auf `warn` setzen)
- [ ] **ARCH-07 fixen:** Datenbank-Passwort aus hartkodiertem Wert in `.env`-Variable auslagern
- [ ] **ARCH-08 bereinigen:** Nicht verwendete Env-Variablen entweder implementieren oder entfernen
- [ ] **ARCH-11 fixen:** `metadata.json` Description ausfüllen

**Ergebnis:** Saubere Codebasis ohne offensichtliche Bugs.

---

### Meilenstein 1: Lokale Infrastruktur vollständig lauffähig (Dauer: ~1 Tag)
> **Ziel:** `docker-compose up` startet alle Services fehlerfrei; Backend-Endpoints antworten korrekt.

- [ ] `docker-compose.yml`: Datenbankpasswort aus `.env` einlesen
- [ ] `backend/requirements.txt`: `google-generativeai>=0.8.0` hinzufügen
- [ ] `backend/requirements.txt`: `sqlalchemy>=2.0`, `asyncpg`, `pgvector` hinzufügen
- [ ] Backend-Startsequenz testen: `docker-compose up` – api, db, redis starten ohne Fehler
- [ ] Redis-Verbindungstest: Rate-Limiting prüfen
- [ ] PostgreSQL-Verbindungstest: DB erreichbar, pgvector-Extension aktivierbar

**Abnahmekriterium:** `docker-compose up && curl http://localhost:8000/docs` gibt Swagger-UI zurück.

---

### Meilenstein 2: Datenbankschema & Migrations (Dauer: ~2 Tage)
> **Ziel:** Persistente Datenhaltung für Dateien und Chat-Verläufe.

- [ ] SQLAlchemy-ORM-Modelle anlegen:
  - `UploadedFile` (id, filename, path, extracted_text, uploaded_at)
  - `ChatSession` (id, user_id, created_at)
  - `ChatMessage` (id, session_id, role, content, created_at)
  - `FileEmbedding` (id, file_id, chunk_text, embedding VECTOR(768))
- [ ] Alembic-Erstmigration (`alembic revision --autogenerate -m "initial_schema"`)
- [ ] Migration ausführen: `alembic upgrade head`
- [ ] pgvector-Extension in Migration aktivieren: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] Async-SQLAlchemy-Session in FastAPI integrieren (Dependency Injection)

**Abnahmekriterium:** `alembic upgrade head` läuft durch; Tabellen sind in PostgreSQL sichtbar.

---

### Meilenstein 3: Gemini-API-Integration (Dauer: ~3 Tage)
> **Ziel:** Echte KI-Antworten statt Mock-Strings.

- [ ] `GEMINI_API_KEY` aus Umgebungsvariable einlesen (`os.getenv("GEMINI_API_KEY")`)
- [ ] Startup-Check: App wirft Fehler beim Start, wenn `GEMINI_API_KEY` fehlt
- [ ] `google-generativeai`-Client initialisieren (Singleton via `lifespan`)
- [ ] Non-Streaming-Pfad: Echter `generate_content`-Call an `gemini-2.0-flash-exp`
- [ ] Streaming-Pfad: `generate_content_stream` in `sse_generator()` integrieren
- [ ] `REACTIVE_MAX_ITERATIONS` aus `.env` lesen und in Chat-Loop einbauen
- [ ] Error-Handling: Gemini-API-Fehler (Rate-Limit, Auth-Fehler) korrekt abfangen und als HTTP 502 weitergeben
- [ ] Cache-Invalidierung: Bei Gemini-Fehler keinen Fehler cachen

**Abnahmekriterium:** `POST /v1/chat/completions` gibt eine echte Gemini-Antwort zurück (prüfbar mit `curl`).

---

### Meilenstein 4: Minimales Chat-Frontend (Dauer: ~3 Tage)
> **Ziel:** Nutzbare Oberfläche im Browser – der erste End-to-End-Test des Systems.

- [ ] `app/page.tsx` anlegen mit grundlegendem Chat-UI:
  - Nachrichtenverlauf (Messages-Liste)
  - Eingabefeld + Senden-Button
  - Streaming-Anzeige (SSE-Consumer)
  - Lade-Spinner während API-Call
- [ ] API-Client-Funktion in `lib/api.ts` (Fetch + SSE-Handling)
- [ ] HITL-Freigabe-UI: Banner/Modal erscheint, wenn Backend HITL-Request sendet
  - "Freigeben"- und "Ablehnen"-Button, die `POST /v1/tools/approve/{execution_id}` aufrufen
- [ ] `app/layout.tsx`: Titel und Favicon aktualisieren
- [ ] Grundlegendes Error-State-Handling: Fehlermeldungen anzeigen, wenn API nicht erreichbar

**Abnahmekriterium:** Chat-Seite öffnet sich im Browser, User kann Nachricht eingeben und erhält echte Gemini-Antwort.

---

### Meilenstein 5: RAG-Pipeline vervollständigen (Dauer: ~4 Tage)
> **Ziel:** Hochgeladene PDFs werden vektorisiert und bei relevanten Queries genutzt.

- [ ] Embedding-Modell wählen: `text-embedding-004` (Google, 768 Dim.) via `google-generativeai`
- [ ] Nach PDF-Upload: Text in Chunks aufteilen (z.B. 500 Tokens, 50 Token Overlap)
- [ ] Für jeden Chunk: Embedding erstellen, in pgvector-Tabelle speichern
- [ ] Chat-Completions: Wenn `file_ids` übergeben, Ähnlichkeitssuche via pgvector (`<->` Operator)
- [ ] Top-K-Chunks (z.B. K=5) als Kontext in System-Prompt einfügen
- [ ] Frontend: PDF-Upload-Komponente mit Drag-and-Drop
- [ ] Frontend: Hochgeladene Dateien anzeigen und dem Chat zuweisen (`file_ids`-Parameter)

**Abnahmekriterium:** PDF hochladen, Frage dazu stellen, Antwort enthält Inhalte aus dem PDF.

---

### Meilenstein 6: Authentifizierung & Sicherheit (Dauer: ~3 Tage)
> **Ziel:** Sicherer Mehrnutzer-Betrieb ohne IP-basiertes Rate-Limiting.

- [ ] Einfache API-Key-Authentifizierung implementieren (Bearer Token in Header)
  - Alternativ: Passwort-basierter Login mit JWT (simpler Flow für V1)
- [ ] Rate-Limiting auf Basis des User-Tokens statt IP
- [ ] `X-Forwarded-For`-Header korrekt auswerten (für Proxy-Betrieb)
- [ ] CORS-Konfiguration in FastAPI: Nur erlaubte Origins zulassen
- [ ] HITL-Timeout: Freigaben nach 60 Sekunden automatisch ablehnen
- [ ] Prompt-Injection-Muster erweitern (mindestens 15–20 bekannte Bypass-Patterns)
- [ ] Secrets aus Docker-Compose in `.env`-Datei auslagern (kein Hardcoding)

**Abnahmekriterium:** Anfragen ohne gültigen API-Key werden mit HTTP 401 abgelehnt.

---

### Meilenstein 7: Fehlerbehandlung, Logging & Monitoring (Dauer: ~2 Tage)
> **Ziel:** Produktionsreifes Logging und nachvollziehbare Fehler.

- [ ] Konsistente HTTP-Fehlerstruktur für alle Endpoints (Problem-Details RFC 7807)
- [ ] Request-ID in alle Log-Einträge einbauen (UUIDv4 per Request, via Middleware)
- [ ] Startup-Validation: Alle erforderlichen Env-Variablen beim Start prüfen
- [ ] Structured Logging für alle Endpoints (aktuell nur Chat und Upload)
- [ ] Health-Check-Endpoint `GET /health` (DB + Redis Verbindung prüfen)
- [ ] Alembic-Migrationen beim Start automatisch ausführen (`alembic upgrade head` in Startup-Hook)
- [ ] Log-Rotation konfigurieren (JSONL-Datei wächst sonst unbegrenzt)

**Abnahmekriterium:** `GET /health` gibt `{"status": "ok", "db": "connected", "redis": "connected"}` zurück.

---

### Meilenstein 8: Tests (Dauer: ~3 Tage)
> **Ziel:** Grundlegende Testsuite, die Regressionen verhindert.

**Backend (pytest):**
- [ ] pytest + httpx (AsyncClient) als Dev-Dependency hinzufügen
- [ ] Tests für Prompt-Injection-Defense (Positivfälle + Bypass-Versuche)
- [ ] Tests für Rate-Limiting (Mock-Redis)
- [ ] Tests für PDF-Upload (korrektes PDF + ungültige Datei + Path-Traversal-Versuch)
- [ ] Tests für Chat-Completions (Mock-Gemini-API)
- [ ] Test für HITL-Flow (Approve + Reject)

**Frontend (vitest + testing-library):**
- [ ] Vitest + React Testing Library als Dev-Dependency hinzufügen
- [ ] Smoke-Test: Chat-Seite rendert korrekt
- [ ] Test: Nachricht absenden ruft API auf
- [ ] Test: HITL-Banner erscheint bei Tool-Request

**Abnahmekriterium:** `pytest` und `npm test` laufen durch, alle Tests grün.

---

### Meilenstein 9: Dokumentation & Finale Qualitätssicherung (Dauer: ~2 Tage)
> **Ziel:** Ein Entwickler kann das Projekt ohne Vorkenntnisse lokal aufsetzen.

- [ ] `README.md` vollständig neu schreiben:
  - Voraussetzungen (Docker, Node.js, Python, API-Keys)
  - Lokales Setup Schritt für Schritt
  - Architekturübersicht
  - API-Referenz (Kurzform)
- [ ] `.env.example` vervollständigen (alle verwendeten Variablen mit Beschreibung)
- [ ] Inline-Code-Kommentare für komplexe Stellen überprüfen/ergänzen
- [ ] ESLint-Warnungen im Frontend auf null reduzieren
- [ ] `next.config.ts`: `ignoreDuringBuilds` auf `false` setzen
- [ ] Finaler End-to-End-Test: Frisch aufgesetztes System, Neuer-User-Flow durchspielen

**Abnahmekriterium:** Interner Review bestätigt: Ein neuer Entwickler kann das Projekt in < 30 Minuten lokal zum Laufen bringen.

---

## 5. Zusammenfassung der Roadmap

```
M0: Hotfixes & Cleanup                  [~2 Tage]  → Stabile Codebasis
M1: Lokale Infrastruktur                [~1 Tag]   → Docker läuft komplett
M2: Datenbank & Migrationen             [~2 Tage]  → Persistenz vorhanden
M3: Gemini-API-Integration              [~3 Tage]  → Echte KI-Antworten ✓
M4: Minimales Chat-Frontend             [~3 Tage]  → Nutzbare Oberfläche ✓
M5: RAG-Pipeline                        [~4 Tage]  → PDF-Kontext in Antworten ✓
M6: Authentifizierung & Sicherheit      [~3 Tage]  → Sicherer Mehrnutzer-Betrieb
M7: Fehlerbehandlung & Logging          [~2 Tage]  → Produktionsreifes Backend ✓
M8: Tests                               [~3 Tage]  → Testsuite vorhanden
M9: Dokumentation & QA                  [~2 Tage]  → Onboarding-Ready
─────────────────────────────────────────────────────────────────────────────
Gesamt geschätzter Aufwand:              ~25 Entwicklertage (~5 Wochen solo)
```

Nach Abschluss von **Meilenstein 4** ist eine erste minimal funktionsfähige Version (MVP) lokal nutzbar.
Nach Abschluss von **Meilenstein 7** ist eine produktionsreife v1.0 verfügbar.
**Meilensteine 8 und 9** erhöhen die Langzeitstabilität und Wartbarkeit.

---

## 6. Was für Phase 2 geplant ist (nach v1.0)

Die folgenden Features sind bereits in der Architektur angedeutet (Alembic `checkpoints`-Tabellen, `GOAL_MAX_ITERATIONS`), aber explizit für nach der ersten stabilen Version vorgesehen:

- **LangGraph-Agenten:** Autonome, mehrstufige Goal-Engine (`GOAL_MAX_ITERATIONS=10`)
- **CI/CD-Pipeline:** GitHub Actions für automatische Tests und Cloud-Run-Deployment
- **Monitoring & Alerting:** APM-Integration (z.B. OpenTelemetry, Sentry)
- **Erweiterte Sicherheit:** NLP-basierte Prompt-Injection-Erkennung statt reiner Regex
- **Skalierung:** Kubernetes-Konfiguration, Horizontal Pod Autoscaler
- **Weitere Tools:** Serper/DuckDuckGo Web-Search (echte Implementierung)
