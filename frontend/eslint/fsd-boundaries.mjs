import boundaries from "eslint-plugin-boundaries";

/**
 * FSD layer boundaries — see docs/ARCHITECTURE.md §1.
 *
 * Dependency direction: app → features → entities → shared
 * - Lower layers never import from higher layers.
 * - Features never import sibling features (only internal slice imports).
 * - Entities never import sibling entities.
 *
 * `legacy` covers pre-FSD folders (lib, components, types, context, store).
 * Remove the legacy element and policy in ROADMAP step 9.
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
      { type: "legacy", pattern: "lib/*" },
      { type: "legacy", pattern: "components/*" },
      { type: "legacy", pattern: "types/*" },
      { type: "legacy", pattern: "context/*" },
      { type: "legacy", pattern: "store/*" },
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
            from: { element: { types: "entity" } },
            allow: { to: { element: { types: "shared" } } },
          },
          {
            from: { element: { types: "feature" } },
            allow: {
              to: { element: { types: ["shared", "entity", "legacy"] } },
            },
          },
          {
            from: { element: { types: "app" } },
            allow: {
              to: {
                element: {
                  types: ["shared", "entity", "feature", "legacy", "app"],
                },
              },
            },
          },
          {
            from: { element: { types: "legacy" } },
            allow: {
              to: {
                element: {
                  types: ["shared", "entity", "feature", "app", "legacy"],
                },
              },
            },
          },
        ],
      },
    ],
  },
};
