<div align="center">
  
# 🤖 AI-Workhorse v1.1 (Hardened)

**Die DSGVO-konforme KI-Assistenz-Plattform mit Multi-Model Support & absoluter Datenkontrolle**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)](https://docker.com/)
[![Redis](https://img.shields.io/badge/Redis-7-red?style=for-the-badge&logo=redis)](https://redis.io/)

*Sicher. Souverän. Multi-Modal. Gehärtet.*

---

![Open WebUI Chat Interface](assets/chat_ui.png)
*(v1.1 Hardened: Nutzerspezifische Keys, Asynchrones PDF-Processing & persistentes HITL sind aktiv!)*

</div>

<br>

> **AI-Workhorse v1.1** hebt die Plattform auf Enterprise-Niveau. Durch die Einführung von **nutzerspezifischen API-Keys (Fernet: AES-128-CBC + HMAC-SHA256)**, **asynchroner PDF-Verarbeitung (arq Worker)** und **persistenter Tool-Freigaben (Redis)** bietet v1.1 maximale Skalierbarkeit bei absoluter Datensouveränität.

---

## ✨ Premium Features (v1.1 Hardened)

Hier trifft ein ultra-kompatibles OpenAI-Interface auf ein eigens gehärtetes Backend.

| 🛡️ Security & Privacy | 🧠 AI & RAG Pipeline | ⚡ Performance & Resilience |
| :--- | :--- | :--- |
| **User-Specific API Keys**<br>Speicherung von Anbieter-Keys (Gemini/Mistral/DS) – Fernet-verschlüsselt (AES-128-CBC) in der DB. | **Asynchronous PDF Processing**<br>Hintergrund-Vektorisierung via `arq` Worker für verzögerungsfreie Uploads. | **Persistent HITL (Redis)**<br>Tool-Freigaben überleben Server-Restarts und skalieren über mehrere Instanzen. |
| **Dreistufige Injection-Defense**<br>Regex, Unicode-Normalisierung & System-Anker. | **google-genai SDK**<br>Neues Google SDK für maximale Performance und Zugriff auf neueste Modelle. | **RAG-Aware Caching**<br>SHA256 Prompt-Caching in Redis reduziert API-Kosten für identische Anfragen. |
| **Souveräne Identität**<br>Header-basierte Nutzer-Erkennung (X-User-Email) via Open WebUI Proxy. | **Multi-Model Routing**<br>Dynamisches Key-Routing pro User & Provider (Gemini/Mistral/DeepSeek). | **Automatisches HTTPS**<br>Caddy Reverse Proxy mit Let's Encrypt für VPS. |

---

## 🏗️ Systemarchitektur (v1.1)

Das Zusammenspiel von 7 isolierten Docker-Containern garantiert maximale Ausfallsicherheit:

```mermaid
flowchart TD
    User([Browser / User]) -- "HTTPS (443)" --> Caddy[Caddy Reverse Proxy\n TLS Let's Encrypt]
    
    subgraph Frontend [UI Layer]
        Caddy -- "HTTP" --> WebUI(Open WebUI\nPort 3002)
        User -- "HTTP (3001)" --> Dashboard(Next.js Dashboard\nPort 3001)
        Dashboard -- "Proxy /api" --> API
    end
    
    subgraph Backend [AI Engine Layer]
        WebUI -- "REST /v1\nBearer Token" --> API{FastAPI Backend\nPort 8000}
        API -- "Queue Jobs" --> Worker(arq Worker\nBackground Tasks)
    end
    
    subgraph Data [Storage & Cache]
        API -- "Rate Limiting / HITL / Cache" --> Redis[(Redis 7)]
        API -- "User Configs / RAG" --> Postgres[(PostgreSQL 16)]
        Worker -- "Vector Insert" --> Postgres
    end
    
    API -- "Dynamic User-Key Routing" -.-> LLMs((Gemini / Mistral / DeepSeek))
```

---

## 🚀 Schnellstart

### Voraussetzungen

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- Erforderlich: [Google Gemini API-Key](https://aistudio.google.com/app/apikey)
- Erforderlich: `ENCRYPTION_KEY` in deiner `.env` (für Fernet-Schlüsselableitung)

### 1. Klonen & Setup

```bash
git clone https://github.com/Infinizius/Aiworkhorse-v8.git
cd Aiworkhorse-v8
cp .env.example .env
```
*WICHTIG: Setze einen starken `ENCRYPTION_KEY` in der `.env`. Ohne diesen Schlüssel können nutzerspezifische Keys nicht verschlüsselt gespeichert werden.*

### 2. Services starten

```bash
docker compose up -d
```

- 💬 **Chat UI:** [http://localhost:3002](http://localhost:3002)
- 📊 **Dashboard:** [http://localhost:3001](http://localhost:3001)
- ⚙️ **API Docs (via Dashboard-Proxy):** [http://localhost:3001/docs](http://localhost:3001/docs)
- 🩺 **Health (via Dashboard-Proxy):** [http://localhost:3001/health](http://localhost:3001/health)

### 3. Nutzerspezifische Keys konfigurieren

Sende einen POST-Request an `/v1/user/config`, um deine eigenen API-Keys zu hinterlegen. Das System nutzt diese automatisch für deine Anfragen (identifiziert via `X-User-Email` Header).

> **Hinweis:** Die Keys werden mit Fernet (AES-128-CBC + HMAC-SHA256) verschlüsselt gespeichert. Der `ENCRYPTION_KEY` in der `.env` ist zwingend erforderlich.

### 4. Next.js-Dashboard (optional)

Das Dashboard läuft auf Port 3001 und zeigt Service-Status, verfügbare Modelle und hochgeladene Dokumente.  
Es spricht ausschließlich über einen serverseitigen Proxy mit dem FastAPI-Backend; Port 8000 wird nicht mehr auf dem Host veröffentlicht.

---

## 🛡️ Der v1.1 Request-Lifecycle

1. **Auth:** Verification via `API_KEY` (Bearer).
2. **Identity:** Extraktion der `user_id` via `X-User-Email`.
3. **Routing:** Auflösung des verschlüsselten API-Keys aus der Datenbank.
4. **Defense:** Prüfung auf Prompt-Injection.
5. **HITL:** Persistenten Redis-Check für Tool-Freigaben (SSE-Heartbeat).
6. **Execution:** Tokenisierter Aufruf an den Provider (Gemini/Mistral/DS).

---

## 🗺️ GESAMTSTATUS v1.1

```text
Infrastruktur (Docker/Worker)  ███████████████████████  100% ✅
Backend SDK (google-genai)     ███████████████████████  100% ✅
Encrypted Key Management       ███████████████████████  100% ✅
Persistent HITL (Redis)        ███████████████████████  100% ✅  (BUG-14 behoben: User-Binding)
Async PDF Pipeline (arq)       ███████████████████████  100% ✅
API/Frontend Kompatibilität    ███████████████████████  100% ✅  (BUG-04–07 behoben, Audit Apr 2026)
Sicherheit & Robustheit        ███████████████████████  100% ✅  (BUG-08–15 behoben, Audit Apr 2026)
─────────────────────────────────────────────────────────────────
GESAMTSTATUS v1.1              ███████████████████████  100% GEHÄRTET
```

## 🔎 Audit-Check (April 2026)

- Meilenstein 1–9 gegen Code, Docker-Setup, Migrationen und Tests geprüft: umgesetzt.
- v1.1-Kernfeatures verifiziert: User-Keys, arq-Worker, Redis-HITL, Multi-Provider-Routing und Open-WebUI-Kompatibilität sind vorhanden.
- Dokumentation korrigiert: Fernet-Wording vereinheitlicht; Web-Search ist korrekt als Serper-only mit DuckDuckGo in Phase 2 beschrieben.
- Runtime-Härtung ergänzt: Graceful Shutdown schließt Redis- und arq-Verbindungen jetzt explizit.
- Verifiziert mit `npm run lint`, `npm run build` und `python3 -m pytest tests -v` (40/40 Backend-Tests grün).

> **Bekannte Limitierungen (non-blocking):** DuckDuckGo-Fallback nicht implementiert (nur Serper), HITL-Trigger-Heuristik (`"search"`-Keyword) zu breit (False Positives; Re-Trigger nach Tool-Call mit BUG-08 behoben), SSE blockiert Event-Loop bei Streaming. Alle für Phase 2 vorgesehen.

---

<div align="center">
  <br>
  <b>AI-Workhorse v1.1</b> – Gebaut mit ❤️ für Enterprise KI-Souveränität
</div>
