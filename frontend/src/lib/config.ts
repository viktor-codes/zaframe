/**
 * Конфигурация приложения из переменных окружения.
 *
 * ВАЖНО: для клиентского кода в Next.js переменные должны быть
 * доступны как process.env.NEXT_PUBLIC_*, и обращаться к ним
 * нужно статически, а не через dynamic key, иначе на клиенте
 * объект process.env будет пустым.
 */

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
const apiUrl = rawApiUrl.trim();

export const config = {
  /** API base URL (trimmed). Empty means misconfiguration — the app needs a backend. */
  apiUrl,
  /** True when NEXT_PUBLIC_API_URL is set — API calls are possible. */
  hasBackend: apiUrl.length > 0,
} as const;
