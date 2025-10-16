/**
 * System: Suno Automation Frontend
 * Module: Health Route
 * File URL: frontend/app/routes/health.ts
 * Purpose: Provide a lightweight health probe endpoint for container readiness checks.
 */

import type { HeadersFunction, LoaderFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node";

export const loader = async (_args: LoaderFunctionArgs) => {
  return json(
    {
      status: "healthy",
      timestamp: new Date().toISOString(),
    },
    {
      headers: {
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
      },
    }
  );
};

export const headers: HeadersFunction = () => {
  return {
    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
  };
};
