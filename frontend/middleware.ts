import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:9000'
  const url = new URL(request.nextUrl.pathname + request.nextUrl.search, backendUrl)
  return NextResponse.rewrite(url)
}

export const config = {
  matcher: '/api/:path*',
}
