import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  basePath: '',
  assetPrefix: '/',
  // allowedDevOrigins: ['*'],
  // crossOrigin: 'anonymous',
  /* config options here */
  transpilePackages: ['tdesign-react'],
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // 客户端构建时，忽略 node: 协议的模块
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        url: false,
        zlib: false,
        http: false,
        https: false,
        assert: false,
        os: false,
        path: false,
      };
    }
    return config;
  },
};

export default nextConfig;
