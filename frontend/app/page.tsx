"use client";

import { useState } from "react";
import ThemeToggle from "@/components/theme-toggle";

type StoryFormData = {
  topic: string;
  tone: string;
  language: string;
  duration: string;
  audience: string;
};

export default function Home() {
  const [formData, setFormData] = useState<StoryFormData>({
    topic: "",
    tone: "cinematic",
    language: "English",
    duration: "1-2 min",
    audience: "",
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    console.log("Story Input Data:", formData);
    alert("Story input captured successfully. Next step: connect generate API.");
  };

  return (
    <main
      className="min-h-screen transition-colors"
      style={{ background: "var(--background)", color: "var(--foreground)" }}
    >
      <section className="mx-auto flex min-h-screen w-full max-w-7xl items-center justify-center px-6 py-12">
        <div className="fixed left-6 top-6 z-50">
  <ThemeToggle />
</div>

        <div className="grid w-full gap-10 lg:grid-cols-2">
          <div className="flex flex-col justify-center space-y-6">
            <div
              className="inline-flex w-fit rounded-full border px-4 py-1 text-sm"
              style={{
                color: "var(--accent)",
                background: "var(--badge-bg)",
                borderColor: "var(--badge-border)",
              }}
            >
              AI Creative Director
            </div>

            <div className="space-y-4">
              <h1 className="text-4xl font-bold leading-tight md:text-6xl">
                Creative
                <span className="block" style={{ color: "var(--accent)" }}>
                  Storyteller
                </span>
              </h1>

              <p
                className="max-w-xl text-base leading-7 md:text-lg"
                style={{ color: "var(--muted)" }}
              >
                Transform a simple idea into a cinematic, multi-scene story with
                narration, visuals, and immersive storytelling flow.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              {[
                { label: "Narration", value: "AI Story" },
                { label: "Visuals", value: "Scene Prompts" },
                { label: "Audio", value: "Voice-ready" },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-2xl border p-4"
                  style={{
                    background: "var(--card)",
                    borderColor: "var(--card-border)",
                  }}
                >
                  <p className="text-sm" style={{ color: "var(--muted)" }}>
                    {item.label}
                  </p>
                  <p className="mt-1 text-lg font-semibold">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div
            className="rounded-3xl border p-6 shadow-2xl backdrop-blur md:p-8"
            style={{
              background: "var(--card)",
              borderColor: "var(--card-border)",
            }}
          >
            <div className="mb-6">
              <h2 className="text-2xl font-semibold">Generate Your Story</h2>
              <p className="mt-2 text-sm" style={{ color: "var(--muted)" }}>
                Enter your story details below to create a cinematic storytelling
                experience.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <label htmlFor="topic" className="text-sm font-medium">
                  Topic
                </label>
                <input
                  id="topic"
                  name="topic"
                  type="text"
                  placeholder="e.g. The lost city in the Himalayas"
                  value={formData.topic}
                  onChange={handleChange}
                  className="w-full rounded-2xl border px-4 py-3 outline-none transition"
                  style={{
                    background: "var(--input-bg)",
                    color: "var(--foreground)",
                    borderColor: "var(--card-border)",
                  }}
                  required
                />
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="tone" className="text-sm font-medium">
                    Tone
                  </label>
                  <select
                    id="tone"
                    name="tone"
                    value={formData.tone}
                    onChange={handleChange}
                    className="w-full rounded-2xl border px-4 py-3 outline-none transition"
                    style={{
                      background: "var(--input-bg)",
                      color: "var(--foreground)",
                      borderColor: "var(--card-border)",
                    }}
                  >
                    <option value="cinematic">Cinematic</option>
                    <option value="emotional">Emotional</option>
                    <option value="dark">Dark</option>
                    <option value="mythical">Mythical</option>
                    <option value="adventurous">Adventurous</option>
                    <option value="inspirational">Inspirational</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="language" className="text-sm font-medium">
                    Language
                  </label>
                  <select
                    id="language"
                    name="language"
                    value={formData.language}
                    onChange={handleChange}
                    className="w-full rounded-2xl border px-4 py-3 outline-none transition"
                    style={{
                      background: "var(--input-bg)",
                      color: "var(--foreground)",
                      borderColor: "var(--card-border)",
                    }}
                  >
                    <option value="English">English</option>
                    <option value="Hindi">Hindi</option>
                    <option value="Hinglish">Hinglish</option>
                  </select>
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="duration" className="text-sm font-medium">
                    Duration
                  </label>
                  <select
                    id="duration"
                    name="duration"
                    value={formData.duration}
                    onChange={handleChange}
                    className="w-full rounded-2xl border px-4 py-3 outline-none transition"
                    style={{
                      background: "var(--input-bg)",
                      color: "var(--foreground)",
                      borderColor: "var(--card-border)",
                    }}
                  >
                    <option value="30-60 sec">30-60 sec</option>
                    <option value="1-2 min">1-2 min</option>
                    <option value="2-3 min">2-3 min</option>
                    <option value="3-5 min">3-5 min</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="audience" className="text-sm font-medium">
                    Audience
                  </label>
                  <input
                    id="audience"
                    name="audience"
                    type="text"
                    placeholder="e.g. Kids, General, Mythology lovers"
                    value={formData.audience}
                    onChange={handleChange}
                    className="w-full rounded-2xl border px-4 py-3 outline-none transition"
                    style={{
                      background: "var(--input-bg)",
                      color: "var(--foreground)",
                      borderColor: "var(--card-border)",
                    }}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full rounded-2xl px-6 py-3 text-base font-semibold text-white transition"
                style={{ background: "var(--accent)" }}
              >
                Generate Story
              </button>
            </form>

            <div
              className="mt-6 rounded-2xl border p-4"
              style={{
                background: "var(--badge-bg)",
                borderColor: "var(--badge-border)",
              }}
            >
              <p className="text-sm">
                Example:
                <span className="ml-2">
                  Topic: Hidden kingdom under the ocean | Tone: Cinematic |
                  Language: English
                </span>
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}