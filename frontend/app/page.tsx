"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";

type HealthResponse = {
  status: string;
  message: string;
};

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const data = await fetchHealth();
        setHealth(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    loadHealth();
  }, []);

  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center px-6">
      <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl">
        <div className="space-y-4 text-center">
          <h1 className="text-4xl font-bold text-purple-400">
            Creative Storyteller
          </h1>
          <p className="text-gray-400">
            Frontend to Backend Connectivity Check
          </p>
        </div>

        <div className="mt-8 rounded-xl bg-black/40 p-6 border border-white/10">
          {loading && (
            <p className="text-yellow-400">Checking backend connection...</p>
          )}

          {!loading && error && (
            <div className="space-y-2">
              <p className="text-red-400 font-semibold">Connection Failed</p>
              <p className="text-sm text-gray-300">{error}</p>
            </div>
          )}

          {!loading && health && (
            <div className="space-y-3">
              <p className="text-green-400 font-semibold">
                Backend Connected Successfully
              </p>
              <div className="rounded-lg bg-white/5 p-4 text-left">
                <p>
                  <span className="font-semibold text-purple-300">Status:</span>{" "}
                  {health.status}
                </p>
                <p>
                  <span className="font-semibold text-purple-300">Message:</span>{" "}
                  {health.message}
                </p>
                <p>
                  <span className="font-semibold text-purple-300">API Base URL:</span>{" "}
                  {process.env.NEXT_PUBLIC_API_URL}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}