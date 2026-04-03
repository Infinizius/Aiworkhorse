import { proxyToBackend } from '@/lib/backend-proxy';

export const dynamic = 'force-dynamic';

function getBackendPath(path: string[] | undefined): string {
  return `/${(path ?? []).join('/')}`;
}

async function handle(request: Request, context: { params: Promise<{ path?: string[] }> }) {
  const { path } = await context.params;
  return proxyToBackend(request, getBackendPath(path));
}

export { handle as GET, handle as POST, handle as PUT, handle as PATCH, handle as DELETE, handle as OPTIONS, handle as HEAD };
