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

> **AI-Workhorse v1.1** hebt die Plattform auf Enterprise-Niveau. Durch die Einführung von **nutzerspezifischen API-Keys (AES-256 verschlüsselt)**, **asynchroner PDF-Verarbeitung (arq Worker)** und **persistenter Tool-Freigaben (Redis)** bietet v1.1 maximale Skalierbarkeit bei absoluter Datensouveränität.

---

## ✨ Premium Features (v1.1 Hardened)

Hier trifft ein ultra-kompatibles OpenAI-Interface auf ein eigens gehärtetes Backend.

| 🛡️ Security & Privacy | 🧠 AI & RAG Pipeline | ⚡ Performance & Resilience |
| :--- | :--- | :--- |
| **User-Specific API Keys**<br>Speicherung von Anbieter-Keys (Gemini/Mistral/DS) – AES-256 verschlüsselt in der DB. | **Asynchronous PDF Processing**<br>Hintergrund-Vektorisierung via `arq` Worker für verzögerungsfreie Uploads. | **Persistent HITL (Redis)**<br>Tool-Freigaben überleben Server-Restarts und skalieren über mehrere Instanzen. |
| **Dreistufige Injection-Defense**<br>Regex, Unicode-Normalisierung & System-Anker. | **google-genai Migration**<br>Migration auf das modernste Google SDK für maximale Performance. | **RAG-Aware Caching**<br>SHA256 Prompt-Caching in Redis reduziert API-Kosten für identische Anfragen. |
| **Souveräne Identität**<br>Header-basierte Nutzer-Erkennung (X-User-Email) via Open WebUI Proxy. | **Multi-Model Routing**<br>Dynamisches Key-Routing pro User & Provider (Gemini/Mistral/DeepSeek). | **Automatisches HTTPS**<br>Caddy Reverse Proxy mit Let's Encrypt für VPS. |

---

## 🏗️ Systemarchitektur (v1.1)

Das Zusammenspiel von 6 isolierten Docker-Containern garantiert maximale Ausfallsicherheit:

```mermaid
flowchart TD
    User([Browser / User]) -- "HTTPS (443)" --> Caddy[Caddy Reverse Proxy\n TLS Let's Encrypt]
    
    subgraph Frontend [UI Layer]
        Caddy -- "HTTP" --> WebUI(Open WebUI\nPort 3002)
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
- Erforderlich: `ENCRYPTION_KEY` in deiner `.env` (für AES-256)

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
- ⚙️ **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Health:** [http://localhost:8000/health](http://localhost:8000/health)

### 3. Nutzerspezifische Keys konfigurieren

Sende einen POST-Request an `/v1/user/config`, um deine eigenen API-Keys zu hinterlegen. Das System nutzt diese automatisch für deine Anfragen (identifiziert via `X-User-Email` Header).

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
Persistent HITL (Redis)        ███████████████████████  100% ✅
Async PDF Pipeline             ███████████████████████  100% ✅
─────────────────────────────────────────────────────────────────
GESAMTSTATUS v1.1              ███████████████████████  100% GEHÄRTET
```

---

<div align="center">
  <br>
  <b>AI-Workhorse v1.1</b> – Gebaut mit ❤️ für Enterprise KI-Souveränität
</div>
