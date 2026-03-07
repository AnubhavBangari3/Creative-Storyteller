"use client";

import { useMemo, useState } from "react";
import ThemeToggle from "@/components/theme-toggle";

type StoryFormData = {
  topic: string;
  tone: string;
  language: string;
  duration: string;
  audience: string;
};

type Scene = {
  scene_number: number;
  title: string;
  narration: string;
  visual_prompt: string;
  text_overlay: string;
  audio_cue: string;
  image_url: string;
  audio_url: string;
  duration_seconds: number;
};

type StoryResponseData = {
  title: string;
  logline: string;
  overall_style: string;
  total_estimated_duration_seconds: number;
  scenes: Scene[];
};

type ApiResponse = {
  success: boolean;
  message: string;
  story_id?: number;
  data?: StoryResponseData;
  error?: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

function InfoTile({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div
      className="rounded-2xl border p-4"
      style={{
        background: "var(--card)",
        borderColor: "var(--card-border)",
      }}
    >
      <p className="text-sm" style={{ color: "var(--muted)" }}>
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function SceneCard({ scene }: { scene: Scene }) {
  return (
    <article
      className="rounded-3xl border p-5 md:p-6"
      style={{
        background: "var(--card)",
        borderColor: "var(--card-border)",
      }}
    >
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div
            className="inline-flex rounded-full border px-3 py-1 text-xs font-medium"
            style={{
              color: "var(--accent)",
              background: "var(--badge-bg)",
              borderColor: "var(--badge-border)",
            }}
          >
            Scene {scene.scene_number}
          </div>
          <h3 className="mt-3 text-2xl font-semibold">{scene.title}</h3>
        </div>

        <div
          className="rounded-2xl border px-3 py-2 text-sm"
          style={{
            background: "var(--input-bg)",
            borderColor: "var(--card-border)",
            color: "var(--muted)",
          }}
        >
          {scene.duration_seconds}s
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-5">
          <div
            className="flex min-h-[280px] items-center justify-center rounded-3xl border p-6 text-center"
            style={{
              background:
                "linear-gradient(135deg, var(--badge-bg), transparent 60%)",
              borderColor: "var(--card-border)",
            }}
          >
            {scene.image_url ? (
              <img
                src={
                  scene.image_url.startsWith("http")
                    ? scene.image_url
                    : `${API_BASE}${scene.image_url}`
                }
                alt={scene.title}
                className="h-full w-full rounded-2xl object-cover"
              />
            ) : (
              <div className="max-w-md">
                <p className="text-sm font-medium" style={{ color: "var(--accent)" }}>
                  Image Placeholder
                </p>
                <p className="mt-2 text-base font-semibold">{scene.text_overlay}</p>
                <p className="mt-3 text-sm leading-6" style={{ color: "var(--muted)" }}>
                  Scene image will appear here after T15 image generation.
                </p>
              </div>
            )}
          </div>

          <div
            className="rounded-2xl border p-4"
            style={{
              background: "var(--badge-bg)",
              borderColor: "var(--badge-border)",
            }}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em]" style={{ color: "var(--accent)" }}>
              Text Overlay
            </p>
            <p className="mt-2 text-lg font-medium">{scene.text_overlay}</p>
          </div>
        </div>

        <div className="space-y-4">
          <section
            className="rounded-2xl border p-4"
            style={{
              background: "var(--input-bg)",
              borderColor: "var(--card-border)",
            }}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em]" style={{ color: "var(--accent)" }}>
              Narration
            </p>
            <p className="mt-3 leading-7" style={{ color: "var(--foreground)" }}>
              {scene.narration}
            </p>
          </section>

          <section
            className="rounded-2xl border p-4"
            style={{
              background: "var(--input-bg)",
              borderColor: "var(--card-border)",
            }}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em]" style={{ color: "var(--accent)" }}>
              Visual Prompt
            </p>
            <p className="mt-3 text-sm leading-6" style={{ color: "var(--muted)" }}>
              {scene.visual_prompt}
            </p>
          </section>

          <section
            className="rounded-2xl border p-4"
            style={{
              background: "var(--input-bg)",
              borderColor: "var(--card-border)",
            }}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.2em]" style={{ color: "var(--accent)" }}>
              Audio Cue
            </p>
            <p className="mt-3 text-sm leading-6">{scene.audio_cue}</p>

            <div
              className="mt-4 rounded-2xl border p-3 text-sm"
              style={{
                background: "var(--card)",
                borderColor: "var(--card-border)",
                color: "var(--muted)",
              }}
            >
              {scene.audio_url ? (
                <audio controls className="w-full">
                  <source src={scene.audio_url} />
                  Your browser does not support audio playback.
                </audio>
              ) : (
                "Audio placeholder — narration playback will appear here after T17."
              )}
            </div>
          </section>
        </div>
      </div>
    </article>
  );
}

export default function Home() {
  const [formData, setFormData] = useState<StoryFormData>({
    topic: "",
    tone: "cinematic",
    language: "English",
    duration: "1-2 min",
    audience: "",
  });

  const [story, setStory] = useState<StoryResponseData | null>(null);
  const [storyId, setStoryId] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");

  const totalSceneDuration = useMemo(() => {
    if (!story?.scenes?.length) return 0;
    return story.scenes.reduce((sum, scene) => sum + scene.duration_seconds, 0);
  }, [story]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  setIsGenerating(true);
  setError("");
  setStory(null);
  setStoryId(null);

  try {
    // Step 1: Generate story structure
    const storyResponse = await fetch(`${API_BASE}/api/story/generate/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic: formData.topic,
        tone: formData.tone,
        language: formData.language,
        duration: formData.duration,
        audience: formData.audience,
        number_of_scenes: 5,
        style_notes: "epic, mysterious, emotional",
      }),
    });

    const storyResult: ApiResponse = await storyResponse.json();

    if (!storyResponse.ok || !storyResult.success || !storyResult.data) {
      throw new Error(
        storyResult.message || storyResult.error || "Failed to generate story"
      );
    }

    // Step 2: Generate images for scenes
    const imageResponse = await fetch(`${API_BASE}/api/story/generate-images/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        scenes: storyResult.data.scenes,
      }),
    });

    const imageResult = await imageResponse.json();

    if (!imageResponse.ok || !imageResult.success || !imageResult.scenes) {
      throw new Error(
        imageResult.message || imageResult.error || "Failed to generate images"
      );
    }

    // Step 3: Merge updated scenes with image URLs
    const updatedStory: StoryResponseData = {
      ...storyResult.data,
      scenes: imageResult.scenes,
    };

    setStory(updatedStory);
    setStoryId(storyResult.story_id ?? null);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Something went wrong.";
    setError(message);
  } finally {
    setIsGenerating(false);
  }
};

  return (
    <main
      className="min-h-screen transition-colors"
      style={{ background: "var(--background)", color: "var(--foreground)" }}
    >
      <section className="mx-auto w-full max-w-7xl px-6 py-12">
        <div className="fixed left-6 top-6 z-50">
          <ThemeToggle />
        </div>

        <div className="grid min-h-screen items-center gap-10 lg:grid-cols-2">
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
              <InfoTile label="Narration" value="AI Story" />
              <InfoTile label="Visuals" value="Scene Prompts" />
              <InfoTile label="Audio" value="Voice-ready" />
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
                disabled={isGenerating}
                className="w-full rounded-2xl px-6 py-3 text-base font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-70"
                style={{ background: "var(--accent)" }}
              >
                {isGenerating ? "Generating Story..." : "Generate Story"}
              </button>
            </form>

            {error ? (
              <div
                className="mt-5 rounded-2xl border p-4 text-sm"
                style={{
                  background: "rgba(239, 68, 68, 0.08)",
                  borderColor: "rgba(239, 68, 68, 0.25)",
                  color: "#dc2626",
                }}
              >
                {error}
              </div>
            ) : null}

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

        {story ? (
          <section className="mt-14 space-y-8">
            <div
              className="rounded-3xl border p-6 md:p-8"
              style={{
                background: "var(--card)",
                borderColor: "var(--card-border)",
              }}
            >
              <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                <div className="max-w-3xl">
                  <div
                    className="inline-flex rounded-full border px-4 py-1 text-sm"
                    style={{
                      color: "var(--accent)",
                      background: "var(--badge-bg)",
                      borderColor: "var(--badge-border)",
                    }}
                  >
                    Story Playback
                  </div>

                  <h2 className="mt-4 text-3xl font-bold md:text-4xl">
                    {story.title}
                  </h2>

                  <p
                    className="mt-3 max-w-2xl text-base leading-7 md:text-lg"
                    style={{ color: "var(--muted)" }}
                  >
                    {story.logline}
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-3 md:grid-cols-1 lg:grid-cols-3">
                  <InfoTile
                    label="Story ID"
                    value={storyId ? `#${storyId}` : "N/A"}
                  />
                  <InfoTile
                    label="Scenes"
                    value={`${story.scenes.length}`}
                  />
                  <InfoTile
                    label="Duration"
                    value={`${totalSceneDuration}s`}
                  />
                </div>
              </div>

              <div
                className="mt-6 rounded-2xl border p-4"
                style={{
                  background: "var(--input-bg)",
                  borderColor: "var(--card-border)",
                }}
              >
                <p className="text-xs font-semibold uppercase tracking-[0.2em]" style={{ color: "var(--accent)" }}>
                  Overall Style
                </p>
                <p className="mt-3 leading-7">{story.overall_style}</p>
              </div>
            </div>

            <div className="space-y-6">
              {story.scenes.map((scene) => (
                <SceneCard key={scene.scene_number} scene={scene} />
              ))}
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}