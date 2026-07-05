/**
 * Typed HTTP error for API failures (RFC 7807 body optional).
 * Kept separate from client.ts so pure helpers can use it without client-only.
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
