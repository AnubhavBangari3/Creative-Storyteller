"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

export default function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button className="rounded-full border px-4 py-2 text-sm">
        Theme
      </button>
    );
  }

  const activeTheme = theme === "system" ? resolvedTheme : theme;

  return (
    <button
      onClick={() => setTheme(activeTheme === "dark" ? "light" : "dark")}
      className="rounded-full border px-4 py-2 text-sm font-medium transition cursor-pointer"
      style={{
        borderColor: "var(--card-border)",
        background: "var(--card)",
        color: "var(--foreground)",
      }}
    >
      {activeTheme === "dark" ? "Light Mode" : "Dark Mode"}
    </button>
  );
}