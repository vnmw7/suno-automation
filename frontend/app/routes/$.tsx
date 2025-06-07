// Catch-all route to handle browser extension requests and other 404s
import { LoaderFunctionArgs } from "@remix-run/node";

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);

  // If it's a .map file request (likely from browser extensions), return 404 without logging
  if (url.pathname.endsWith(".map")) {
    return new Response(null, { status: 404 });
  }

  // For other 404s, you can redirect to home or show a 404 page
  throw new Response("Not Found", { status: 404 });
}

export default function CatchAll() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">Page Not Found</h1>
      <p className="text-gray-600 mb-6">
        The page you&#39;re looking for doesn&#39;t exist.
      </p>
      <a
        href="/"
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
      >
        Go Home
      </a>
    </div>
  );
}
