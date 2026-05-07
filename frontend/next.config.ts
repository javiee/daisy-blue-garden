import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  skipTrailingSlashRedirect: true,
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: '**',
        pathname: '/media/**',
      },
    ],
  },
}

export default nextConfig
