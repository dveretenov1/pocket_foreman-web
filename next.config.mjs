/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Optimizes for production deployment
  distDir: '.next',
  images: {
    domains: ['via.placeholder.com'],
  },
  experimental: {
    // Remove sharp from external packages to use Next.js built-in image optimization
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/:path*` : 'http://api:5000/:path*',
      },
    ];
  },
  // Production optimizations
  poweredByHeader: false,
  generateEtags: true,
  compress: true,
  productionBrowserSourceMaps: false,
  // Timeout configurations
  serverTimeout: 60000, // 60 seconds
  staticPageGenerationTimeout: 120,
};

export default nextConfig;
