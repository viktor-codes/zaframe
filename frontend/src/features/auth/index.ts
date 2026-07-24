/** Auth feature — public API: OTP login form.
 * Route guards live in `@shared/auth` (`RequireAuth`, `RequireStudioRole`).
 */
export { LoginForm } from "./ui";
/** @deprecated Prefer `RequireAuth` from `@shared/auth`. */
export { RequireAuth } from "./ui";
