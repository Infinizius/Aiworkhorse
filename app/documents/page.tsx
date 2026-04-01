'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, FileText, Trash2, RefreshCw, Calendar, Layers, Eye, EyeOff } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface DocumentFile {
  file_id: string;
  filename: string;
  page_count: number | null;
  chunks_embedded: number;
  uploaded_at: string | null;
  preview: string;
}

interface FilesResponse {
  files: DocumentFile[];
  total: number;
}

function formatDate(iso: string | null): string {
  if (!iso) return '–';
  return new Date(iso).toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function DocumentsPage() {
  const [files, setFiles] = useState<DocumentFile[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/v1/files`);
      if (!res.ok) throw new Error(`API Fehler: ${res.status} ${res.statusText}`);
      const data: FilesResponse = await res.json();
      setFiles(data.files);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleDelete = async (fileId: string, filename: string) => {
    if (!confirm(`Datei „${filename}" wirklich löschen? Alle Embeddings werden ebenfalls entfernt.`)) return;
    setDeleting(fileId);
    try {
      const res = await fetch(`${API_URL}/v1/files/${fileId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`Löschen fehlgeschlagen: ${res.status} ${res.statusText}`);
      setFiles((prev) => prev.filter((f) => f.file_id !== fileId));
      setTotal((prev) => prev - 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Löschen fehlgeschlagen');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Dashboard
            </Link>
            <span className="text-gray-700">|</span>
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-400" />
              <span className="font-semibold">Dokumente</span>
            </div>
          </div>
          <button
            onClick={fetchFiles}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:border-blue-500 hover:text-gray-100 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Aktualisieren
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-10 space-y-6">
        {/* Title & Stats */}
        <div>
          <h2 className="text-2xl font-bold text-gray-50">Hochgeladene Dokumente</h2>
          <p className="mt-1 text-sm text-gray-400">
            Alle in der Datenbank gespeicherten PDF-Dateien mit extrahiertem Text und Embeddings.
          </p>
        </div>

        {/* Stats bar */}
        <div className="flex gap-6 rounded-2xl border border-gray-800 bg-gray-900/50 px-6 py-4">
          <div>
            <p className="text-xs text-gray-500">Dokumente gesamt</p>
            <p className="text-2xl font-bold text-blue-400">{total}</p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-800 bg-red-900/30 px-5 py-4 text-sm text-red-300">
            <strong>Fehler:</strong> {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 rounded-2xl bg-gray-800/40 animate-pulse" />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && files.length === 0 && (
          <div className="rounded-2xl border border-dashed border-gray-700 bg-gray-800/20 px-6 py-16 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-600 mb-4" />
            <p className="text-gray-400">Noch keine Dokumente hochgeladen.</p>
            <p className="mt-1 text-sm text-gray-600">
              Lade über das Open WebUI Chat-Interface eine PDF-Datei hoch.
            </p>
          </div>
        )}

        {/* File list */}
        {!loading && files.length > 0 && (
          <ul className="space-y-3">
            {files.map((file) => (
              <li
                key={file.file_id}
                className="rounded-2xl border border-gray-700 bg-gray-800/40 p-5 transition-all hover:border-gray-600"
              >
                <div className="flex items-start justify-between gap-4">
                  {/* File info */}
                  <div className="flex items-start gap-3 min-w-0">
                    <FileText className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="font-semibold text-gray-100 truncate" title={file.filename}>
                        {file.filename}
                      </p>
                      <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(file.uploaded_at)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Layers className="h-3 w-3" />
                          {file.page_count ?? '?'} Seiten · {file.chunks_embedded} Chunks
                        </span>
                        <span className="font-mono text-gray-600 text-[10px]">{file.file_id}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => setExpandedId(expandedId === file.file_id ? null : file.file_id)}
                      className="flex items-center gap-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs text-gray-400 transition-colors hover:border-blue-600 hover:text-blue-300"
                      title={expandedId === file.file_id ? 'Vorschau einklappen' : 'Vorschau anzeigen'}
                    >
                      {expandedId === file.file_id ? (
                        <><EyeOff className="h-3.5 w-3.5" /> Einklappen</>
                      ) : (
                        <><Eye className="h-3.5 w-3.5" /> Vorschau</>
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(file.file_id, file.filename)}
                      disabled={deleting === file.file_id}
                      className="flex items-center gap-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs text-red-400 transition-colors hover:border-red-600 hover:bg-red-900/20 disabled:opacity-50"
                      title="Datei löschen"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      {deleting === file.file_id ? 'Lösche…' : 'Löschen'}
                    </button>
                  </div>
                </div>

                {/* Preview text */}
                {expandedId === file.file_id && file.preview && (
                  <div className="mt-4 rounded-xl bg-gray-900/70 px-4 py-3 text-xs text-gray-400 leading-relaxed font-mono whitespace-pre-wrap border border-gray-700/50">
                    {file.preview}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
