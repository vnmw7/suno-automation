import type { MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData, useNavigate } from "@remix-run/react";

export const meta: MetaFunction = () => {
  return [
    { title: "Suno Automation" },
    { name: "description", content: "automation" },
  ];
};

export async function loader() {
  try {
    const response = await fetch("http://127.0.0.1:8000/");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return json(data);
  } catch (error) {
    console.error("Failed to fetch from backend:", error);
    return json({ error: "Failed to load data from backend" }, { status: 500 });
  }
}

export default function Index() {
  const data = useLoaderData<typeof loader>();
  const navigate = useNavigate();

  const login_suno = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/login");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const responseData = await response.json();
      console.log("Login successful:", responseData);

      if (
        Array.isArray(responseData) &&
        responseData.length > 0 &&
        responseData[0] === true
      ) {
        navigate("/main-page");
      } else {
        alert("Login failed. Someting happened in the backend.");
      }
    } catch (error) {
      console.error("Login failed:", error);
      alert("Login failed. Please try again.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1>Suno Automation Frontend</h1>
      {data && !data.error && (
        <p>Message from backend: {JSON.stringify(data)}</p>
      )}
      {data && data.error && (
        <p style={{ color: "red" }}>Error: {data.error}</p>
      )}
      <button
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
        onClick={login_suno}
      >
        Start
      </button>
    </div>
  );
}
