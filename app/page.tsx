import Link from 'next/link';
import { ExternalLink, Shield, Database, Cpu, Radio, FileText, ArrowRight } from 'lucide-react';

const OPEN_WEBUI_URL = process.env.NEXT_PUBLIC_OPEN_WEBUI_URL ?? 'http://localhost:3002';
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface ServiceCardProps {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  internal?: boolean;
}

function ServiceCard({ title, description, href, icon, badge, internal }: ServiceCardProps) {
  const inner = (
    <>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-blue-400">{icon}</div>
          <span className="font-semibold text-gray-100">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          {badge && (
            <span className="rounded-full bg-blue-900/60 px-2 py-0.5 text-xs text-blue-300">
              {badge}
            </span>
          )}
          {internal ? (
            <ArrowRight className="h-4 w-4 text-gray-500 transition-colors group-hover:text-blue-400" />
          ) : (
            <ExternalLink className="h-4 w-4 text-gray-500 transition-colors group-hover:text-blue-400" />
          )}
        </div>
      </div>
      <p className="text-sm text-gray-400">{description}</p>
      <span className="text-xs text-gray-500 font-mono">{href}</span>
    </>
  );

  const className =
    'group flex flex-col gap-3 rounded-2xl border border-gray-700 bg-gray-800/50 p-6 transition-all hover:border-blue-500 hover:bg-gray-800';

  if (internal) {
    return (
      <Link href={href} className={className}>
        {inner}
      </Link>
    );
  }

  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
      {inner}
    </a>
  );
}

interface FeatureItemProps {
  label: string;
  status: 'done' | 'partial' | 'planned';
}

function FeatureItem({ label, status }: FeatureItemProps) {
  const colors = {
    done: 'text-green-400',
    partial: 'text-yellow-400',
    planned: 'text-gray-500',
  };
  const icons = { done: '✓', partial: '◑', planned: '○' };
  return (
    <li className={`flex items-center gap-2 text-sm ${colors[status]}`}>
      <span>{icons[status]}</span>
      <span className={status === 'planned' ? 'text-gray-500' : 'text-gray-300'}>{label}</span>
    </li>
  );
}

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Shield className="h-7 w-7 text-blue-400" />
            <div>
              <h1 className="text-xl font-bold">AI-Workhorse v8</h1>
              <p className="text-xs text-gray-400">DSGVO-konform · EU-Backend · Gemini powered</p>
            </div>
          </div>
          <a
            href={OPEN_WEBUI_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-500"
          >
            Chat öffnen
            <ExternalLink className="h-4 w-4" />
          </a>
          <Link
            href="/documents"
            className="flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-800 px-4 py-2 text-sm font-semibold text-gray-300 transition-colors hover:border-blue-500 hover:text-gray-100"
          >
            <FileText className="h-4 w-4" />
            Dokumente
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-12 space-y-12">
        {/* Hero */}
        <section className="text-center space-y-4">
          <h2 className="text-3xl font-bold text-gray-50">
            KI-Assistent mit DSGVO-Compliance
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-lg">
            AI-Workhorse kombiniert Gemini Flash, RAG-Pipeline (PDF + pgvector) und ein
            Human-in-the-Loop-Freigabesystem in einem sicheren, EU-gehosteten Backend.
          </p>
          <a
            href={OPEN_WEBUI_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-2xl bg-blue-600 px-8 py-3 font-semibold text-white transition-colors hover:bg-blue-500 text-lg mt-4"
          >
            <Radio className="h-5 w-5" />
            Jetzt chatten (Open WebUI · Port 3002)
          </a>
        </section>

        {/* Services */}
        <section>
          <h3 className="mb-4 text-lg font-semibold text-gray-300">Services</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <ServiceCard
              title="Open WebUI"
              description="Chat-Interface mit Streaming, PDF-Upload und Verlaufsspeicherung."
              href={OPEN_WEBUI_URL}
              icon={<Radio className="h-5 w-5" />}
              badge="UI"
            />
            <ServiceCard
              title="FastAPI Backend"
              description="REST-API mit Gemini-Integration, HITL-Freigaben und Rate Limiting."
              href={`${API_URL}/docs`}
              icon={<Cpu className="h-5 w-5" />}
              badge="API"
            />
            <ServiceCard
              title="API Docs (Swagger)"
              description="Vollständige OpenAPI-Dokumentation aller Endpunkte."
              href={`${API_URL}/redoc`}
              icon={<Database className="h-5 w-5" />}
              badge="Docs"
            />
            <ServiceCard
              title="Dokumente"
              description="Alle hochgeladenen PDF-Dateien mit Vorschau und Verwaltung."
              href="/documents"
              icon={<FileText className="h-5 w-5" />}
              badge="DB"
              internal
            />
          </div>
        </section>

        {/* Feature list */}
        <section className="grid gap-6 sm:grid-cols-2">
          <div className="rounded-2xl border border-gray-700 bg-gray-800/40 p-6">
            <h3 className="mb-4 font-semibold text-gray-200">Backend-Features</h3>
            <ul className="space-y-2">
              <FeatureItem label="Gemini 2.0 Flash – Streaming & Non-Streaming" status="done" />
              <FeatureItem label="Dreistufige Prompt-Injection-Defense" status="done" />
              <FeatureItem label="Token-Bucket Rate Limiter (Redis)" status="done" />
              <FeatureItem label="HITL Tool-Freigabe (60s Timeout)" status="done" />
              <FeatureItem label="SHA256-Prompt-Caching (24h TTL)" status="done" />
              <FeatureItem label="PDF-Upload + pdfplumber-Parsing" status="done" />
              <FeatureItem label="pgvector Embedding (text-embedding-004)" status="done" />
              <FeatureItem label="RAG – Ähnlichkeitssuche mit file_ids" status="done" />
              <FeatureItem label="Web-Search (Serper / DuckDuckGo)" status="done" />
              <FeatureItem label="JWT-Authentifizierung" status="planned" />
            </ul>
          </div>
          <div className="rounded-2xl border border-gray-700 bg-gray-800/40 p-6">
            <h3 className="mb-4 font-semibold text-gray-200">Infrastruktur</h3>
            <ul className="space-y-2">
              <FeatureItem label="Docker Compose (API, DB, Redis, Open WebUI)" status="done" />
              <FeatureItem label="PostgreSQL 16 mit pgvector-Extension" status="done" />
              <FeatureItem label="Redis 7 (Caching & Rate Limiting)" status="done" />
              <FeatureItem label="Strukturiertes JSON-Logging (JSONL)" status="done" />
              <FeatureItem label="ARM64-kompatibel (Hetzner CAX21)" status="done" />
              <FeatureItem label="Alembic-Migrationen" status="partial" />
              <FeatureItem label="CI/CD Pipeline" status="planned" />
              <FeatureItem label="Tests (pytest / vitest)" status="planned" />
            </ul>
          </div>
        </section>
      </div>
    </main>
  );
}
