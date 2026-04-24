import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // prodステージでの最小Dockerイメージ構成に必要（ECS Fargateデプロイ用）
  output: "standalone",
  devIndicators: false,
};

export default nextConfig;
