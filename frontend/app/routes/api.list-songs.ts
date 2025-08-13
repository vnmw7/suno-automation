import { json, type LoaderFunctionArgs } from "@remix-run/node";

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const bookName = url.searchParams.get("bookName");
  const chapterParam = url.searchParams.get("chapter");
  const range = url.searchParams.get("range"); // e.g., "1-11"

  const backendUrl = new URL("http://127.0.0.1:8000/song/list");
  if (bookName) backendUrl.searchParams.append("bookName", bookName);
  if (chapterParam) backendUrl.searchParams.append("chapter", chapterParam);
  if (range) backendUrl.searchParams.append("range", range);

  try {
    const response = await fetch(backendUrl.toString());
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Network response was not ok" }));
      return json({ success: false, error: errorData.error || `HTTP error! status: ${response.statusText} (${response.status})` }, { status: response.status });
    }
    const data = await response.json();
    return json(data);
  } catch (error: unknown) {
    console.error(`Error fetching song files from backend:`, error);
    return json(
      { success: false, error: "Failed to fetch song files from backend." },
      { status: 500 }
    );
  }
}
