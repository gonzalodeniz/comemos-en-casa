import { resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Builds the presentational UI components in src/ui as an ES module library.
export default defineConfig({
  root: __dirname,
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "dist"),
    emptyOutDir: true,
    lib: { entry: resolve(__dirname, "entry.ts"), formats: ["es"], fileName: () => "index.js" },
    rollupOptions: { external: ["react", "react-dom", "react/jsx-runtime"] },
  },
});
