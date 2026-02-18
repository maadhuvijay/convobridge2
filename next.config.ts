import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Note: Removed turbopack.root as it was causing module resolution issues
  // The warning about multiple lockfiles is harmless and can be ignored
};

export default nextConfig;
