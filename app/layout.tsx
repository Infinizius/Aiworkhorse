import type {Metadata} from 'next';
import './globals.css'; // Global styles

export const metadata: Metadata = {
  title: 'AI-Workhorse v8',
  description: 'DSGVO-konforme KI-Assistenten-Plattform mit Gemini API, RAG-Pipeline und Human-in-the-Loop-Freigabesystem.',
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
