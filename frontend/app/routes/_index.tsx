import type { MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData, useNavigate } from "@remix-run/react";
import { useState } from "react";

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
  const [isLoading, setIsLoading] = useState(false);

  const login_suno = async () => {
    setIsLoading(true);
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
        navigate("/main");
      } else {
        alert("Login failed. Someting happened in the backend.");
      }
    } catch (error) {
      console.error("Login failed:", error);
      alert("Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full mx-4">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">
          Hello, click start.
        </h1>

        {data && !data.error && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded">
            <p className="text-sm text-green-700">
              Backend connected: {JSON.stringify(data)}
            </p>
          </div>
        )}

        {data && data.error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-sm text-red-700">Error: {data.error}</p>
          </div>
        )}

        <button
          className={`w-full font-bold py-3 px-6 rounded-lg transition-all duration-200 ${
            isLoading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-500 hover:bg-blue-700 active:bg-blue-800"
          } text-white`}
          onClick={login_suno}
          disabled={isLoading}
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Connecting...
            </div>
          ) : (
            "Start"
          )}
        </button>

        {isLoading && (
          <p className="text-center text-gray-600 text-sm mt-3">
            Please wait while we connect to Suno...
          </p>
        )}
      </div>
    </div>
  );
}
