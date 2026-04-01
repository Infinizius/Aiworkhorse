# **AI-Workhorse: Master Blueprint v8.1 (The EU-Privacy Pivot)**

**Dokumententyp:** Vollständiges Projekthandbuch & Onboarding-Bibel **Status:** 🟢 PRODUCTION READY (Freigegeben für Sprint 0\) **Zielgruppe:** Lead Developer, DevOps, Backend Engineers **User-Base:** 1-5 Nutzer (Privatpersonen / Kleine Teams / Non-Profit) **Datum:** 30\. März 2026 | **Ort:** Bannewitz/Dresden, Sachsen

## **1\. Executive Summary: Das "MaxClaw-Killer" Paradigma**

KI-Plattformen von kommerziellen Anbietern (wie MaxClaw, ChatGPT Team oder Claude) bieten massiven Komfort, zwingen Nutzer jedoch in drei fatale Kompromisse:

1. **Intransparente Abo-Fallen** (20-100 € pro Nutzer/Monat).  
2. **Vendor-Lock-in** (Gefangen in einem geschlossenen Ökosystem).  
3. **Datenabfluss** (US-Server, Black-Box-Datennutzung für Modell-Training).

**AI-Workhorse 8.1 ist unsere souveräne Gegenantwort.** Wir bauen eine private Plattform, die den UX-Goldstandard von **Open WebUI** mit einem maßgeschneiderten, hochsicheren **FastAPI-Backend** kombiniert. Wir schlagen kommerzielle Anbieter gnadenlos im Preis und garantieren zeitgleich EU-Datenschutz auf Enterprise-Niveau.

### **Der Paradigmenwechsel: Vertragliche vs. Architektonische Garantie**

In frühen Entwürfen versuchten wir, absolute Datenhoheit durch lokale RAM-Monster-Modelle (Ollama) auf 32GB-Servern zu erzwingen. Das war teuer (\~30€/Monat) und extrem fehleranfällig (Out-of-Memory Crashes).  
**Der smarte Pivot:** Wir ersetzen teure Hardware durch vertragliche DSGVO-Sicherheit. Wir nutzen einen **europäischen Privacy-First API-Provider** (z.B. Requesty, Nordference, Exoscale). Diese Provider betreiben Server in der EU (z.B. Frankfurt), garantieren eine strikte *Zero Data Retention Policy* (kein Speichern oder Trainieren auf unseren Prompts) und unterzeichnen einen rechtsgültigen Auftragsverarbeitungsvertrag (AVV/DPA).

### **Die Kosten-Rechnung (Das 16-Euro-Wunder)**

Durch den Wegfall lokaler KI-Modelle sinken unsere Hardware-Anforderungen drastisch:

* **Server:** Hetzner CAX21 (ARM64, 8 GB RAM) \= **\~8,00 € / Monat**  
* **EU Privacy API (LLM \+ Embeddings):** Pay-per-Token für 1-5 User \= **\~8,00 € / Monat**  
* **Gesamtkosten:** **\~16,00 € / Monat für das gesamte Team\!**

*(Das Entwicklungsbudget von ca. 6.000 € für 12 Wochen MVP-Bauzeit – basierend auf dem regionalen Mindestlohn/Werkstudententarif in Sachsen – amortisiert sich im Vergleich zu Enterprise-Lizenzen in Rekordzeit).*

## **2\. Die Architektur: "Dumb Terminal" & Single Source of Truth**

Wir erfinden das Rad nicht neu. Wir bauen kein Frontend selbst, aber wir überlassen fremden Tools auch nicht unsere Geschäftslogik.

1. **Open WebUI (Das "Dumb Terminal"):** Liefert die mobile-optimierte Chat-Oberfläche. Sein internes RAG-System (ChromaDB) und seine SQLite-Datenbank werden **hart deaktiviert** (ENABLE\_RAG\_WEB\_SEARCH=false, ENABLE\_RAG\_LOCAL\_WEB\_FETCH=false, DOCS\_DIR=/dev/null).  
2. **FastAPI (Das Gehirn):** Fängt alle Anfragen ab (POST /v1/chat/completions). Hier liegen unsere Python-Tools, das PDF-Parsing und die API-Kommunikation zum EU-Provider.  
3. **PostgreSQL \+ pgvector (Single Source of Truth):** Die *einzige* persistente Datenbank im System. Speichert Chat-Historien, Agenten-Logs und alle RAG-Vektor-Embeddings.

## **3\. Die RAG-Integration & Der Upload-Fix**

Da wir Open WebUIs internes RAG abschalten, haben wir den Datei-Upload neu und deterministisch definiert. Wir verlassen uns NICHT auf Filesystem-Polling (was zu Race-Conditions führt).

* **Der Dedizierte Upload-Endpoint:** FastAPI stellt einen Endpunkt /v1/files/upload bereit. Open WebUI (via modifiziertem Filter/Upload-Handler) schickt das PDF dorthin, erhält eine file\_id (UUID) zurück und hängt diese an jeden Chat-Request an.  
* **PDF-Parsing:** FastAPI nutzt pdfplumber (Reines Python). Es ist 100% ARM64-kompatibel und liefert für wissenschaftliche Paper (Dresdner Uni-Kontext) erheblich bessere Layout- und Tabellenerkennung als andere C++ basierte Parser.  
* **Embeddings:** Um den 8GB-Server komplett von ML-Lasten zu befreien, generiert FastAPI die Vektoren über die EU-API (z.B. Requesty nomic-embed-text) und speichert sie in pgvector.

## **4\. Die 8 Eisernen Überlebensregeln (Errata-Fixes)**

*Diese 8 Regeln sind das Destillat aus monatelanger Fehleranalyse. Sie verhindern Memory-Leaks, Timeouts und Hacker-Angriffe. Sie sind bindendes Gesetz für den Code.*

1. **Die 3-stufige Prompt Injection Defense:** Regex allein reicht nicht\!  
   * *Stufe 1:* Unicode-Normalisierung (unicodedata.normalize("NFKC", text)).  
   * *Stufe 2:* Harter System-Prompt-Anker im Backend (User-Nachrichten sind *niemals* Systembefehle).  
   * *Stufe 3:* Regex-Fallback für bekannte Pattern (z.B. ignore previous).  
2. **Der SSE-Heartbeat (Gegen 504 Timeouts):** Wenn der Agent auf den User wartet, muss FastAPI die HTTP-Verbindung am Leben erhalten. *Lösung:* Ein yield ': keep-alive\\n\\n' gepaart mit einem simplen await asyncio.sleep(5) (Kein wait\_for, um Race Conditions zu vermeiden\!).  
3. **HITL Memory Leak Prävention:** Das asyncio.Event für User-Freigaben muss zwingend in einem finally-Block aufgeräumt werden (app.state.approval\_events.pop(...)), sonst läuft der RAM auf Dauer voll.  
4. **UID/GID Sync für Uploads:** Damit FastAPI abgelegte Dateien lesen kann, müssen die relevanten Container in der docker-compose.yml unter demselben User (user: "1000:1000") laufen.  
5. **Deterministischer Backup-Pfad:** In der docker-compose.yml muss in Zeile 1 zwingend name: ai-workhorse stehen. Das backup.sh Skript sichert dann den pg\_dump und das Upload-Verzeichnis sicher ab.  
6. **RAG-Aware SHA256 Caching:** Prompt-Caching (via Redis) zur Kostensenkung wird bei RAG-Queries im Code **hart deaktiviert**. Dynamisch angehängte PDF-Chunks verändern den Hash bei jeder Anfrage, was den Cache nutzlos macht.  
7. **Getrennte Iterations-Limits:** REACTIVE\_MAX\_ITERATIONS \= 3 (Schutz vor Endlosschleifen im Chat). GOAL\_MAX\_ITERATIONS \= 10 (Für die spätere autonome Goal-Engine).  
8. **LangGraph vs. Alembic Konflikt:** In der alembic.ini muss exclude\_tables \= checkpoints,checkpoint\_blobs gesetzt werden. Sonst zerstören Datenbank-Migrationen später die State-Tabellen unserer autonomen Agenten.

## **5\. Die 12-Wochen-Roadmap (MVP)**

*Dieser Plan verzichtet auf Over-Engineering (wie Prometheus, Celery, Kubernetes) und fokussiert sich kompromisslos auf Kernstabilität.*

* **Woche 1-2 (Sprint 0 & Base):** \* *Go/No-Go:* ARM64-Spike (Lassen sich pgvector und asyncpg als C-Extensions fehlerfrei auf dem Hetzner ARM-Server kompilieren? Wenn nein \-\> Fallback auf x86 CPX21).  
  * Server-Provisionierung (CAX21, 8GB RAM).  
  * EU-Privacy Provider Setup (Account anlegen, **AVV/DPA digital unterzeichnen\!**).  
* **Woche 3-4 (Gateway & Uploads):** \* FastAPI "Fake OpenAI" Endpunkt (/v1/chat/completions) und dedizierten Upload-Endpunkt (/v1/files/upload) implementieren.  
  * **Path-Traversal-Schutz:** os.path.abspath Checks beim Speichern/Lesen der PDFs zwingend einbauen\!  
  * pdfplumber Extraktion und pgvector-Integration (Exact Sequential Scan reicht für \<10k Dokumente, kein RAM-fressender HNSW-Index\!).  
* **Woche 5-6 (Tools & Caching):** \* System-Tools (Web-Search) in FastAPI schreiben.  
  * Token-Bucket Rate Limiter in Redis (10 Req/Min/User) gegen Abuse.  
  * RAG-aware SHA256 Prompt-Caching einbauen (nur für non-RAG Queries).  
* **Woche 7-8 (HITL \- Human in the Loop):** \* asyncio.Event Mechanismus für Tool-Freigaben implementieren (inkl. Leak-freiem Cleanup\!).  
  * Einbau des **SSE-Heartbeat-Generators** zur Überbrückung von Wartezeiten in der UI.  
* **Woche 9-10 (Security & Logs):** \* Die 3-stufige Prompt Injection Defense einbauen (Unicode-Normalisierung \+ Anker \+ Regex).  
  * Strukturiertes JSON-Logging in FastAPI (in eine simple Datei).  
* **Woche 11-12 (Testing & Go-Live):** \* RTO-Restore-Test (\< 1 Stunde) über das deterministische Backup-Skript.  
  * Soft-Launch für das Team.

## **6\. Ausblick: Phase 2 (Autonome Goal-Engine)**

Dieses System ist zukunftssicher. Nach einem erfolgreichen MVP wird das System um einen "LangGraph-Daemon" (als isolierter Container) erweitert.

* **Funktion:** Autonome Langzeitaufgaben (z.B. "Prüfe jeden Morgen arXiv auf neue RAG-Paper, fasse sie zusammen").  
* **Integration:** Teilt sich die Postgres-DB (PostgresSaver) mit FastAPI. Er ruft Tools nicht selbst auf (keine Code-Duplizierung\!), sondern nutzt FastAPI als "Tool-Server" (POST /internal/tools/execute).  
* **Re-Entrancy Guard:** Pusht die Engine Ergebnisse via API in den Chat, muss der Header X-Source: goal-engine gesetzt sein. FastAPI ignoriert diese Nachrichten am Haupteingang.

**Abschließendes Wort an das Entwicklerteam:** Wir haben die perfekte Balance gefunden. Durch den Wechsel auf Privacy-APIs sparen wir uns Hardware-Schlachten und OOM-Crashes, bleiben aber dank EU-Recht zu 100% DSGVO-konform. Durch die rigorosen Fixes für Uploads, Timeouts, PDFs und Prompt-Injections haben wir jede architektonische Zeitbombe entschärft.  
Das System ist robust, spottbillig im Betrieb (\~16€/Monat) und skalierbar. Das ist der Blueprint, mit dem wir den Markt für uns selbst disruptieren.  
**Bereit. Execute.**