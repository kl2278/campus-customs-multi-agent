import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server must be on 5173: the backend only allows that origin (plus 3000).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  preview: { port: 5173, strictPort: true },
});
