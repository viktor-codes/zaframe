/**
 * FSD shared layer — zero domain knowledge.
 *
 * Import from subpaths (`@shared/api`, `@shared/lib`) to avoid pulling client-only
 * modules through a barrel. Only safe, isomorphic exports belong here.
 */
export * from "./lib";
