import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    // Media is served directly by Django (possibly from a changing LAN IP),
    // so skip next/image optimization and hostname allow-listing.
    unoptimized: true,
  },
}

export default nextConfig
