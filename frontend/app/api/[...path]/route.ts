import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:9000'

async function proxy(request: NextRequest) {
  let path = request.nextUrl.pathname
  if (!path.endsWith('/')) path += '/'
  const search = request.nextUrl.search
  const url = `${BACKEND_URL}${path}${search}`

  const headers = new Headers(request.headers)
  headers.delete('host')

  const init: RequestInit = {
    method: request.method,
    headers,
  }

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.arrayBuffer()
  }

  const response = await fetch(url, init)

  const responseHeaders = new Headers(response.headers)
  responseHeaders.delete('transfer-encoding')

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  })
}

export const GET = proxy
export const POST = proxy
export const PUT = proxy
export const PATCH = proxy
export const DELETE = proxy
