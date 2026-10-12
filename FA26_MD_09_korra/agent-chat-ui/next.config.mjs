/**
 * Filename: next.config.mjs
 * Author: Professor Denis O. Núñez
 * Email: donunez@programmingjourneys.com
 * Organization: Programming Journeys
 * Project: Project 09 - Korra: MCP Server and User Interface
 * Module: Module 09 - Interfacing and Communication
 * Layer: Deployment - Container
 * Date Created: October 4, 2026
 * Date Modified: October 4, 2026
 * Version: M09S04
 * License: Educational Use
 *
 * Requirements:
 *     Next.js, installed by pnpm with the Agent UI
 *
 * Description:
 *     Replaces the Agent UI's own next.config.mjs so the site can be
 *     containerized. One line matters: output "standalone".
 *
 *     Without it, pnpm build leaves a site that still needs the full
 *     node_modules tree to run, and .next/standalone is never created, so
 *     the frontend Dockerfile's COPY of that folder fails and the build
 *     stops. With it, Next.js writes a server.js and only the packages that
 *     are actually reached, which is what the runtime stage ships.
 *
 *     serverActions.bodySizeLimit is kept from the Agent UI's own config so
 *     this file does not quietly change the app's behavior.
 *
 * Usage Instructions:
 *     Copy into the agent-chat-ui folder, replacing the file already there,
 *     before building the image:
 *         docker compose up --build
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Produces .next/standalone, which the frontend Dockerfile copies
  output: "standalone",
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;
