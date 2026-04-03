const INTERNAL_API_URL = process.env.INTERNAL_API_URL ?? 'http://ai-workhorse-api:8000';
const SERVER_API_KEY = process.env.API_KEY ?? '';
const NORMALIZED_INTERNAL_API_URL = INTERNAL_API_URL.endsWith('/')
  ? INTERNAL_API_URL
  : `${INTERNAL_API_URL}/`;

const FORWARDED_REQUEST_HEADERS = [
  'accept',
  'content-type',
  'range',
  'x-request-id',
] as const;

function getCookieValue(cookieHeader: string | null, name: string): string | null {
  if (!cookieHeader) {
    return null;
  }

  for (const cookie of cookieHeader.split(';')) {
    const [rawName, ...rawValue] = cookie.trim().split('=');
    if (rawName === name) {
      return decodeURIComponent(rawValue.join('='));
    }
  }

  return null;
}

function buildTargetUrl(pathname: string, requestUrl: string): URL {
  const targetUrl = new URL(pathname, NORMALIZED_INTERNAL_API_URL);
  targetUrl.search = new URL(requestUrl).search;
  return targetUrl;
}

function buildForwardHeaders(request: Request): Headers {
  const headers = new Headers();

  for (const headerName of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(headerName);
    if (value) {
      headers.set(headerName, value);
    }
  }

  const forwardedUserEmail =
    request.headers.get('x-user-email') ??
    getCookieValue(request.headers.get('cookie'), 'workhorse_user_email');
  if (forwardedUserEmail) {
    headers.set('x-user-email', forwardedUserEmail);
  }

  if (SERVER_API_KEY) {
    headers.set('authorization', `Bearer ${SERVER_API_KEY}`);
  }

  return headers;
}

function buildResponseHeaders(upstreamHeaders: Headers): Headers {
  const headers = new Headers();
  for (const [key, value] of upstreamHeaders.entries()) {
    const lowerKey = key.toLowerCase();
    if (lowerKey === 'content-encoding' || lowerKey === 'transfer-encoding') {
      continue;
    }
    headers.set(key, value);
  }
  return headers;
}

export async function proxyToBackend(request: Request, pathname: string): Promise<Response> {
  const targetUrl = buildTargetUrl(pathname, request.url);
  const method = request.method.toUpperCase();
  const hasBody = !['GET', 'HEAD'].includes(method);

  const upstreamResponse = await fetch(targetUrl, {
    method,
    headers: buildForwardHeaders(request),
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: 'no-store',
  });

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: buildResponseHeaders(upstreamResponse.headers),
  });
}
