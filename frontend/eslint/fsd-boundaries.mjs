import boundaries from "eslint-plugin-boundaries";

/**
 * FSD layer boundaries — see docs/ARCHITECTURE.md §1.
 *
 * Dependency direction: app → features → entities → shared
 * - Lower layers never import from higher layers.
 * - Features never import sibling features (only internal slice imports).
 * - Entities never import sibling entities.
 */
export const fsdBoundaryConfig = {
  files: ["src/**/*.{ts,tsx}"],
  plugins: { boundaries },
  settings: {
    "import/resolver": {
      typescript: {
        alwaysTryTypes: true,
        project: "./tsconfig.json",
      },
    },
    "boundaries/root-path": "src",
    "boundaries/elements": [
      { type: "feature", pattern: "features/*", capture: ["slice"] },
      { type: "entity", pattern: "entities/*", capture: ["name"] },
      { type: "shared", pattern: "shared/*" },
      { type: "app", pattern: "app/*" },
    ],
  },
  rules: {
    "boundaries/dependencies": [
      "error",
      {
        default: "disallow",
        policies: [
          {
            allow: {
              dependency: { relationship: { to: "internal" } },
            },
          },
          {
            from: { element: { types: "shared" } },
            allow: { to: { element: { types: "shared" } } },
          },
          {
            from: { element: { types: "shared" } },
            allow: {
              to: { element: { types: "entity" } },
              dependency: { kind: "type" },
            },
          },
          {
            from: { element: { types: "entity" } },
            allow: { to: { element: { types: "shared" } } },
          },
          {
            from: { element: { types: "feature" } },
            allow: {
              to: { element: { types: ["shared", "entity"] } },
            },
          },
          {
            from: { element: { types: "app" } },
            allow: {
              to: {
                element: {
                  types: ["shared", "entity", "feature", "app"],
                },
              },
            },
          },
        ],
      },
    ],
  },
};
