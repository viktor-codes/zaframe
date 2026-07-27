/**
 * Export OpenAPI from the FastAPI backend and generate TypeScript types.
 *
 * Requires: backend uv env (`cd backend && uv sync`), Node deps in frontend.
 */

import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "..");
const backendRoot = path.resolve(frontendRoot, "..", "backend");
const snapshotPath = path.join(frontendRoot, "openapi.snapshot.json");
const outputPath = path.join(
  frontendRoot,
  "src",
  "shared",
  "api",
  "types.generated.ts",
);

const exportOpenApiCmd = `uv run python -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))"`;

console.log("Exporting OpenAPI schema from backend…");
const openapiJson = execSync(exportOpenApiCmd, {
  cwd: backendRoot,
  encoding: "utf8",
  stdio: ["ignore", "pipe", "inherit"],
});

writeFileSync(snapshotPath, openapiJson, "utf8");
console.log(`Wrote ${path.relative(frontendRoot, snapshotPath)}`);

console.log("Generating TypeScript types…");
execSync(`npx openapi-typescript "${snapshotPath}" -o "${outputPath}"`, {
  cwd: frontendRoot,
  stdio: "inherit",
});

console.log(`Done → ${path.relative(frontendRoot, outputPath)}`);
