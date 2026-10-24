import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/comemos/",
  server: {
    proxy: { "/comemos/api/v1": { target: "http://localhost:8000", rewrite: (path) => path.replace(/^\/comemos/, "") } },
  },
  test: { environment: "node" },
});
