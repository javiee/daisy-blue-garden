import { NextRequest, NextResponse } from 'next/server'

export async function middleware(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:9000'
  let pathname = request.nextUrl.pathname
  if (!pathname.endsWith('/')) pathname += '/'
  const url = `${backendUrl}${pathname}${request.nextUrl.search}`

  const headers = new Headers(request.headers)
  headers.delete('host')

  const response = await fetch(url, {
    method: request.method,
    headers,
    body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
    // @ts-expect-error duplex is needed for streaming request bodies
    duplex: 'half',
  })

  const responseHeaders = new Headers(response.headers)
  responseHeaders.delete('transfer-encoding')

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  })
}

export const config = {
  matcher: '/api/:path*',
}
