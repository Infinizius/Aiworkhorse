# 🛡️ Security Audit & Penetrationstest-Plan (v1.1.1)

Dieses Dokument beschreibt den aktuellen Sicherheitsstatus, identifizierte Risiken mit Bewertung, und einen priorisierten Penetrationstest-Plan für die AI-Workhorse Plattform.

---

## 1. Implementierte Sicherheitsmechanismen

| Mechanismus | Implementierung | Status |
|---|---|---|
| Bearer-Token-Authentifizierung | `verify_api_key`-Dependency; `API_KEY` aus `.env` | ✅ Aktiv |
| Nutzerspezifische API-Key-Verschlüsselung | AES-256 via Fernet + PBKDF2 (100.000 Iterationen) | ✅ Aktiv |
| Fail-Fast Startup-Validierung | Kein Start ohne `GEMINI_API_KEY` und `ENCRYPTION_KEY` | ✅ Aktiv |
| Dreistufige Prompt-Injection-Defense | NFKC-Normalisierung + 20 Regex-Patterns + System-Anker | ✅ Aktiv |
| HITL-Freigabe (User-gebunden) | `execution_id` an `user_id` in Redis gebunden (TTL 70s) | ✅ Aktiv |
| Token-Bucket Rate Limiting | 10 Req/Min/User über Token-Hash; `X-Forwarded-For`-Auswertung | ✅ Aktiv |
| SHA256-Prompt-Caching | 24h TTL, nur für Non-RAG-Queries | ✅ Aktiv |
| CORS-Konfiguration | Erlaubte Origins über `CORS_ALLOW_ORIGINS` in `.env` steuerbar | ✅ Aktiv |
| Strukturiertes Audit-Logging | JSON-Logs (JSONL) mit Request-IDs, tägl. Rotation, 7 Tage Retention | ✅ Aktiv |
| RFC 7807 Problem Details | Einheitliches Fehlerformat verhindert Information Leakage | ✅ Aktiv |

---

## 2. Risikobewertung (Audit-Findings)

### [HIGH] A. Trusted Header Authentication (X-User-Email)
- **Beschreibung**: Das System nutzt den `X-User-Email`-Header zur Nutzeridentifikation. Dieser Header wird von Open WebUI gesetzt und weitergeleitet. Ist Open WebUI korrekt konfiguriert, ist die Vertrauenskette intakt.
- **Risiko**: Wenn das Backend direkt (ohne Open WebUI als Proxy) erreichbar ist, kann ein Angreifer mit einem gültigen API-Key die Identität beliebiger Nutzer annehmen, indem er `X-User-Email` frei setzt.
- **Mitigations-Stand**: In Produktionsumgebungen ist das Backend hinter Caddy und Open WebUI und sollte nicht direkt öffentlich erreichbar sein. Für Multi-Tenant-Betrieb muss das Backend-Netzwerk auf interne Kommunikation beschränkt sein.
- **Empfohlene Maßnahme (Phase 2)**: Migration zu JWT/OAuth2 mit signierten Claims; Ablösung des Header-basierten Ansatzes.

### [MEDIUM] B. IDOR bei `/v1/user/config`
- **Beschreibung**: Der Endpunkt zum Speichern nutzerspezifischer API-Keys (`POST /v1/user/config`) identifiziert den Nutzer ausschließlich über den `X-User-Email`-Header.
- **Risiko**: Wenn Header Spoofing (Finding A) möglich ist, können fremde API-Keys überschrieben werden (IDOR).
- **Mitigations-Stand**: Gleiches Risikoprofil wie Finding A – durch korrekte Netzwerktopologie mitigiert.

### [MEDIUM] C. Prompt Injection (Advanced)
- **Beschreibung**: Regex-basierte Filter schützen gegen bekannte Angriffsmuster.
- **Risiko**: Fortgeschrittene Techniken (Many-Shot-Jailbreaks, kontextuelle Role-Injection, semantische Umgehung) können Regex-Filter umgehen.
- **Mitigations-Stand**: NFKC-Normalisierung und 20 Patterns reduzieren die Angriffsfläche erheblich.
- **Empfohlene Maßnahme (Phase 3)**: LLM-basierter Guardrail (z.B. Llama Guard, Nvidia NeMo Guardrails).

### [LOW] D. RAG Indirect Prompt Injection (Poisoning)
- **Beschreibung**: Hochgeladene PDFs werden als Text extrahiert und später als Kontext in Prompts injiziert.
- **Risiko**: Ein präpariertes PDF könnte versteckte Instruktionen enthalten, die erst zum Zeitpunkt der Retrieval-Phase aktiv werden und das LLM-Verhalten manipulieren.
- **Mitigations-Stand**: PDFs werden mit `pdfplumber` extrahiert; Metadaten werden nicht direkt exponiert. Die Injection-Defense prüft nur User-Nachrichten, nicht den RAG-Kontext.
- **Empfohlene Maßnahme**: RAG-Kontext ebenfalls durch Injection-Filter leiten oder strukturiert als separaten Kontext-Block übergeben (kein direktes Einfügen in den System-Prompt).

### [LOW] E. Encryption Key: Statischer Salt
- **Beschreibung**: Der PBKDF2-Prozess zur Schlüsselableitung verwendet einen statischen Salt (`ai_workhorse_v8_salt`).
- **Risiko**: Bei Kompromittierung des `ENCRYPTION_KEY`-Werts ist kein Rainbow-Table-Angriff auf den Salt möglich (Salt ist nicht geheim), jedoch ist der Schutz schwächer als bei einem zufälligen Salt pro Nutzer.
- **Empfohlene Maßnahme**: Zufälligen Salt pro Nutzer/Datensatz generieren und in der DB speichern (z.B. in `user_configs.salt`).

---

## 3. Penetrationstest-Plan (Priorisiert)

Dieser Plan definiert konkrete Testszenarien, sortiert nach Priorität und logischem Ablauf.

### Stufe 1: Authentication & Authorization (Höchste Priorität)

**Ziel:** Verifizieren, dass keine Identitätsfälschung oder unerlaubter Zugriff möglich ist.

| # | Test | Erwartetes Ergebnis | Tool |
|---|---|---|---|
| 1.1 | Request ohne `Authorization`-Header an `/v1/chat/completions` | `HTTP 401` | curl |
| 1.2 | Request mit falschem Bearer Token | `HTTP 401` | curl |
| 1.3 | Request mit gültigem Token, aber manipuliertem `X-User-Email` Header an `/v1/user/config` | Keys von User A überschreiben (IDOR-Test) | curl |
| 1.4 | Direkter Zugriff auf FastAPI-Backend (Port 8000) aus dem Internet, wenn Caddy aktiv | Verbindung muss durch Firewall blockiert werden | nmap |
| 1.5 | HITL-Approve mit fremder `execution_id` durch anderen authentifizierten User | `HTTP 403 Forbidden` | curl |

### Stufe 2: AI-spezifische Angriffe

**Ziel:** Sicherstellen, dass die Injection-Defense und das HITL-System robust sind.

| # | Test | Erwartetes Ergebnis | Technik |
|---|---|---|---|
| 2.1 | Klassische Injections: "ignore all previous instructions", "jailbreak", "DAN" | `HTTP 400 Security Violation` | Parametrisierter Test |
| 2.2 | Unicode-Obfuskation: Fullwidth-Zeichen, homoglyph attacks | `HTTP 400` nach NFKC-Normalisierung | Python unicode manipulation |
| 2.3 | Many-Shot-Jailbreak: Viele harmlose Beispiele, dann schädliche Anfrage | Mögliche Umgehung – manuell bewerten | Manuell |
| 2.4 | Kontextuelle Role-Injection über RAG: Präpariertes PDF mit Instruktionen hochladen | LLM muss Kontext-Instruktionen ignorieren | Manuell mit präparierter PDF |
| 2.5 | Tool-Flooding: >10 Anfragen/Minute senden | `HTTP 429` nach Bucket-Leerung | Skript (e.g. `hey`, `vegeta`) |
| 2.6 | HITL-Bypass: Gleichzeitig HITL-Anfrage starten und sofort approven ohne Warten | Tool-Ausführung muss korrekt ablaufen (kein State-Leak) | Python async test |

### Stufe 3: Infrastruktur & Storage

**Ziel:** Verifizieren, dass Datenhaltung und Konfiguration sicher sind.

| # | Test | Erwartetes Ergebnis | Tool |
|---|---|---|---|
| 3.1 | Direkter Zugriff auf PostgreSQL-Port (5432) von außen | Port nicht erreichbar (Firewall) | nmap |
| 3.2 | Direkter Zugriff auf Redis-Port (6379) von außen | Port nicht erreichbar (Firewall) | nmap |
| 3.3 | Path-Traversal beim PDF-Upload: Dateiname `../../etc/passwd` | UUID-basierter Dateiname verhindert Traversal | curl |
| 3.4 | Prüfung der Logs auf sensitive Daten (API-Keys, Passwörter) | Keine sensitiven Werte in JSONL-Logs | grep auf `logs/workhorse.jsonl` |
| 3.5 | `ENCRYPTION_KEY` aus laufendem Container extrahieren | Key nur als Env-Variable vorhanden; nicht auf Disk | `docker inspect` / `docker exec env` |
| 3.6 | Download einer fremden Datei über `/v1/files/{id}/download` mit eigenem API-Key | Aktuell erlaubt (kein File-Owner-Check) – dokumentiertes Risiko | curl |

---

## 4. Bekannte Risiken und Akzeptanzentscheidungen

| Finding | Entscheidung | Begründung |
|---|---|---|
| A (Header Spoofing) | **Akzeptiert für v1.1** | Netzwerktopologie (Backend nicht direkt öffentlich) mitigiert Risiko. Für Phase 2 JWT geplant. |
| D (RAG Poisoning) | **Akzeptiert für v1.1** | Zugriff auf Upload-Endpoint erfordert API-Key; vertrauenswürdige Nutzer. Für Phase 3 Guardrails. |
| E (Statischer Salt) | **Akzeptiert für v1.1** | Schlüssel ist geheim gehalten; Salt-Angriff praktisch nicht relevant. Für Phase 2 verbesserbar. |
| 3.6 (File-Owner-Check) | **Bekanntes Gap** | Alle Dateien sind für alle API-Key-Nutzer sichtbar. Akzeptiert für Single-Tenant-Betrieb. |

---

## 5. Erledigte Security-Fixes (Changelog)

| Version | Fix |
|---|---|
| v1.0 | API-Key-Authentifizierung (Bearer Token) |
| v1.0 | Rate Limiting (Token-Bucket, Redis) |
| v1.0 | Prompt-Injection-Defense (20 Patterns + NFKC) |
| v1.1 | AES-256 Verschlüsselung für nutzerspezifische API-Keys |
| v1.1 | Fail-Fast Startup bei unsicherem `ENCRYPTION_KEY` |
| v1.1 | Persistentes HITL via Redis (Restart-sicher) |
| v1.1.1 | **HITL-Hardening**: `execution_id` wird an `user_id` gebunden; `/v1/tools/approve` gibt `HTTP 403` bei User-Mismatch |
| v1.1.1 | Strukturiertes Audit-Logging mit Request-IDs und Log-Rotation |
| v1.1.1 | RFC 7807 Problem Details für alle Fehler-Responses |

---

*Erstellt: 02.04.2026 – AI-Workhorse Security Team | Zuletzt aktualisiert: 02.04.2026 (v1.1.1 Fixes)*
