
<div align="center">

# 🤖 AI-Workhorse v8

**DSGVO-konforme KI-Assistenten-Plattform mit Human-in-the-Loop-Kontrolle**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com/)
[![License](https://img.shields.io/badge/Lizenz-MIT-green?style=flat-square)](LICENSE)

*Sicher. Souverän. DSGVO-konform.*

</div>

---

## 📖 Projektübersicht

**AI-Workhorse v8** ist eine selbst gehostete, DSGVO-konforme KI-Plattform, die leistungsstarke KI-Funktionen mit maximaler Datenschutzkontrolle verbindet. Das System verbindet die Gemini AI API mit einer robusten Sicherheitsarchitektur und einem Human-in-the-Loop-Freigabesystem – damit bleibt der Mensch immer in Kontrolle.

### 🎯 Kernfunktionen

| Feature | Beschreibung |
|---|---|
| 🛡️ **Prompt-Injection-Defense** | Dreistufige Schutzarchitektur: Unicode-Normalisierung, System-Anker und Regex-Filter |
| 👤 **Human-in-the-Loop (HITL)** | Freigabe-System für Tool-Ausführungen via Server-Sent Events (SSE) |
| 📄 **RAG-Pipeline** | PDF-Upload, Vektorisierung und semantische Suche via pgvector |
| ⚡ **Rate Limiting** | Token-Bucket-Algorithmus über Redis (10 Req/Min/IP) |
| 💬 **Chat UI** | Open WebUI – vollständig OpenAI-API-kompatibel |
| 🔒 **DSGVO-konform** | Alle Daten bleiben auf Ihrer eigenen Infrastruktur |

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    AI-Workhorse v8                      │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │  Open WebUI  │───▶│  FastAPI     │                  │
│  │  (Port 3000) │    │  (Port 8000) │                  │
│  │  Chat UI     │    │  Backend     │                  │
│  └──────────────┘    └──────┬───────┘                  │
│                             │                           │
│              ┌──────────────┼──────────────┐           │
│              ▼              ▼              ▼           │
│        ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│        │PostgreSQL│  │  Redis   │  │  Gemini  │      │
│        │+ pgvector│  │ (Cache / │  │   API    │      │
│        │(Port5432)│  │Rate Limit│  │          │      │
│        └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 🔧 Tech-Stack

| Schicht | Technologie |
|---|---|
| **Chat UI** | [Open WebUI](https://github.com/open-webui/open-webui) |
| **Dashboard** | Next.js 15 + React 19 + TypeScript + TailwindCSS v4 |
| **Backend** | FastAPI 0.110 + Python 3.11 + Uvicorn |
| **KI-Modell** | Google Gemini 2.0 Flash (via REST API) |
| **Datenbank** | PostgreSQL 16 mit pgvector-Extension |
| **Cache / Queue** | Redis 7 (Token-Bucket, SHA256-Caching) |
| **Containerisierung** | Docker Compose |

---

## 🚀 Schnellstart

### Voraussetzungen

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Google Gemini API-Key](https://aistudio.google.com/app/apikey)

### 1. Repository klonen

```bash
git clone https://github.com/Infinizius/Aiworkhorse-v8.git
cd Aiworkhorse-v8
```

### 2. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Öffne `.env` und trage deine Werte ein:

```env
GEMINI_API_KEY=dein-gemini-api-key-hier
POSTGRES_PASSWORD=sicheres-datenbankpasswort
WEBUI_SECRET_KEY=sicherer-session-schluessel
```

### 3. Starten

```bash
docker compose up -d
```

Das System startet automatisch alle Services:

| Service | URL | Beschreibung |
|---|---|---|
| 💬 **Chat UI** | http://localhost:3000 | Open WebUI – Hauptoberfläche |
| ⚙️ **API** | http://localhost:8000 | FastAPI Backend |
| 📊 **API Docs** | http://localhost:8000/docs | Swagger UI |

### 4. Logs verfolgen

```bash
# Alle Services
docker compose logs -f

# Nur das API-Backend
docker compose logs -f api
```

---

## ⚙️ Konfiguration

Alle Einstellungen erfolgen über die `.env`-Datei. Eine vollständige Vorlage findest du in [`.env.example`](.env.example).

| Variable | Beschreibung | Standard |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API-Schlüssel | *(erforderlich)* |
| `POSTGRES_PASSWORD` | Datenbankpasswort | *(erforderlich)* |
| `WEBUI_SECRET_KEY` | Session-Schlüssel für Open WebUI | `change-me-in-production` |
| `SERPER_API_KEY` | Serper API für Web-Suche *(optional)* | – |
| `REACTIVE_MAX_ITERATIONS` | Max. Iterationen im reaktiven Modus | `3` |
| `GOAL_MAX_ITERATIONS` | Max. Iterationen für die Goal-Engine | `10` |
| `CORS_ALLOW_ORIGINS` | Erlaubte CORS-Origins | `http://localhost:3000` |

---

## 🛡️ Sicherheitsarchitektur

AI-Workhorse v8 setzt auf mehrere Sicherheitsschichten:

```
Eingehende Anfrage
       │
       ▼
┌─────────────────────┐
│ 1. Rate Limiting    │  Token-Bucket via Redis (10 Req/Min/IP)
│    (IP-basiert)     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 2. Prompt-Defense   │  Unicode-Normalisierung + System-Anker + Regex
│    (Dreistufig)     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 3. HITL-Freigabe    │  Mensch genehmigt Tool-Ausführungen via SSE
│    (Tool-Calls)     │
└─────────┬───────────┘
          │
          ▼
     Gemini API
```

---

## 📁 Projektstruktur

```
Aiworkhorse-v8/
├── 📂 app/                  # Next.js Dashboard (Status-Seite)
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── 📂 backend/              # FastAPI-Backend
│   ├── main.py              # API-Endpunkte, RAG, HITL, Rate Limiting
│   ├── models.py            # SQLAlchemy-Modelle
│   ├── requirements.txt     # Python-Abhängigkeiten
│   └── alembic/             # Datenbank-Migrationen
├── 📂 hooks/                # React Hooks (z.B. useIsMobile)
├── 📂 lib/                  # Utilities (cn(), etc.)
├── docker-compose.yml       # Service-Orchestrierung
├── .env.example             # Konfigurationsvorlage
├── backup.sh                # Datenbank-Backup-Skript
├── sync.sh                  # Git-Sync für Tablet-Workflow
└── ROADMAP.md               # Entwicklungsfahrplan
```

---

## 🗺️ Roadmap

Einen detaillierten Überblick über den aktuellen Entwicklungsstand und die geplanten Features findest du in der [ROADMAP.md](ROADMAP.md).

**Aktueller Gesamtfortschritt (MVP):** *(Stand: März 2026 – Schätzwerte)*

```
Infrastruktur      ████████████████████░░  ~85%
Backend-Logik      ████████████░░░░░░░░░░  ~55%
Sicherheit         ███████████████░░░░░░░  ~70%
RAG-Pipeline       █████░░░░░░░░░░░░░░░░░  ~20%
Frontend / UI      ██░░░░░░░░░░░░░░░░░░░░  ~10%
Tests              ░░░░░░░░░░░░░░░░░░░░░░   ~0%
─────────────────────────────────────────────────
Gesamt (MVP)       █████████░░░░░░░░░░░░░  ~35%
```

---

## 🛠️ Entwicklung

### Lokale Entwicklungsumgebung (ohne Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend (Dashboard):**
```bash
npm install
npm run dev
```

### Dev-Container (VS Code)

Das Projekt enthält eine vollständige Dev-Container-Konfiguration für VS Code mit Python 3.11, allen Extensions und einem vorinstallierten PostgreSQL-Client.

### Backup

```bash
# Datenbank und Uploads sichern
./backup.sh
```

---

## 🤝 Beitragen

Beiträge sind willkommen! Bitte lies die [ROADMAP.md](ROADMAP.md) für offene Aufgaben und schau dir die bekannten Bugs an, bevor du einen Pull Request öffnest.

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

---

<div align="center">

**AI-Workhorse v8** – Gebaut mit ❤️ für DSGVO-konforme KI

</div>
