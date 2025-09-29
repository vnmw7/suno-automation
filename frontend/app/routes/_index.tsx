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
  // Use backend service name for server-side requests in Docker
  const API_URL = process.env.BACKEND_URL || "http://backend:8000";
  try {
    const response = await fetch(`${API_URL}/`);
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

  const login_with_google = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/login");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const responseData = await response.json();
      console.log("Login response received:", responseData);
      console.log("Response type:", typeof responseData);
      console.log("Is array:", Array.isArray(responseData));

      // Check for various successful response formats
      let loginSuccessful = false;

      if (
        Array.isArray(responseData) &&
        responseData.length > 0 &&
        responseData[0] === true
      ) {
        loginSuccessful = true;
      } else if (responseData === true) {
        loginSuccessful = true;
      } else if (responseData && responseData.success === true) {
        loginSuccessful = true;
      } else if (responseData && responseData.status === "success") {
        loginSuccessful = true;
      }

      if (loginSuccessful) {
        console.log("Login successful, navigating to /main");
        navigate("/main");
      } else {
        console.log("Login failed, unexpected response format:", responseData);
        alert(
          `Login failed. Unexpected response from backend: ${JSON.stringify(
            responseData
          )}`
        );
      }
    } catch (error) {
      console.error("Login failed:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      alert(`Login failed. Error: ${errorMessage}`);
    } finally {
      console.log("Setting loading to false");
      setIsLoading(false);
    }
  };

    const login_with_microsoft = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/login/microsoft");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const responseData = await response.json();
      console.log("Login response received:", responseData);
      console.log("Response type:", typeof responseData);
      console.log("Is array:", Array.isArray(responseData));

      // Check for various successful response formats
      let loginSuccessful = false;

      if (
        Array.isArray(responseData) &&
        responseData.length > 0 &&
        responseData[0] === true
      ) {
        loginSuccessful = true;
      } else if (responseData === true) {
        loginSuccessful = true;
      } else if (responseData && responseData.success === true) {
        loginSuccessful = true;
      } else if (responseData && responseData.status === "success") {
        loginSuccessful = true;
      }

      if (loginSuccessful) {
        console.log("Login successful, navigating to /main");
        navigate("/main");
      } else {
        console.log("Login failed, unexpected response format:", responseData);
        alert(
          `Login failed. Unexpected response from backend: ${JSON.stringify(
            responseData
          )}`
        );
      }
    } catch (error) {
      console.error("Login failed:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      alert(`Login failed. Error: ${errorMessage}`);
    } finally {
      console.log("Setting loading to false");
      setIsLoading(false);
    }
  };

  const triggerManualLogin = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/manual-login", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const responseData = await response.json();
      console.log("Manual login response:", responseData);

      if (responseData.success) {
        console.log("Manual login successful, navigating to /main");
        navigate("/main");
      } else {
        alert("Manual login failed or was cancelled");
      }
    } catch (error) {
      console.error("Manual login failed:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      alert(`Manual login failed. Error: ${errorMessage}`);
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

        <div className="space-y-4">
          <button
            className={`w-full flex items-center justify-center font-bold py-3 px-6 rounded-lg transition-all duration-200 ${
              isLoading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-white border border-gray-300 hover:bg-gray-100 active:bg-gray-200 text-gray-700"
            }`}
            onClick={login_with_google}
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-700"
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
              <>
                <svg
                  className="w-5 h-5 mr-2"
                  viewBox="0 0 48 48"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z"
                    fill="#FFC107"
                  />
                  <path
                    d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z"
                    fill="url(#paint0_linear)"
                  />
                  <path
                    d="M24 46c5.9 0 11.2-2.2 15.1-5.9L32.7 34C30.1 35.8 27.2 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22z"
                    fill="#4CAF50"
                  />
                  <path
                    d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z"
                    fill="#1976D2"
                  />
                  <path
                    d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z"
                    fill="#FF3D00"
                  />
                  <defs>
                    <linearGradient
                      id="paint0_linear"
                      x1="24"
                      y1="2"
                      x2="24"
                      y2="46"
                      gradientUnits="userSpaceOnUse"
                    >
                      <stop stopColor="#FFC107" />
                      <stop offset="1" stopColor="#FF9800" />
                    </linearGradient>
                  </defs>
                </svg>
                Login with Google
              </>
            )}
          </button>

          <button
            className={`w-full flex items-center justify-center font-bold py-3 px-6 rounded-lg transition-all duration-200 ${
              isLoading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white"
            }`}
            onClick={login_with_microsoft}
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
              <>
                <svg
                  className="w-5 h-5 mr-2"
                  viewBox="0 0 21 21"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M1 1H10V10H1V1Z" fill="#F25022" />
                  <path d="M11 1H20V10H11V1Z" fill="#7FBA00" />
                  <path d="M1 11H10V20H1V11Z" fill="#00A4EF" />
                  <path d="M11 11H20V20H11V11Z" fill="#FFB900" />
                </svg>
                Login with Microsoft
              </>
            )}
          </button>

          {/* Manual Login Button */}
          <div className="relative mt-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or</span>
            </div>
          </div>

          <button
            className={`w-full mt-4 flex items-center justify-center font-bold py-3 px-6 rounded-lg transition-all duration-200 ${
              isLoading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-gray-600 hover:bg-gray-700 active:bg-gray-800 text-white"
            }`}
            onClick={triggerManualLogin}
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
              <>
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                  />
                </svg>
                Manual Login (Choose Provider)
              </>
            )}
          </button>
        </div>

        {isLoading && (
          <p className="text-center text-gray-600 text-sm mt-3">
            Please wait while we connect...
          </p>
        )}
      </div>
    </div>
  );
}
