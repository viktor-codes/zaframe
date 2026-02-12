/**
 * Конфигурация приложения из переменных окружения.
 * Если NEXT_PUBLIC_API_URL не задан — режим «только лендинг» (без бэкенда).
 */

function getEnv(key: string, fallback = ""): string {
  const value = process.env[key];
  if (value === undefined || value === "") return fallback;
  return value;
}

const apiUrl = getEnv("NEXT_PUBLIC_API_URL");

export const config = {
  /** URL бэкенда. Пустая строка = статичный лендинг без API. */
  apiUrl: apiUrl.trim(),
  /** Есть ли настроенный бэкенд (для условного отображения ссылок и т.п.). */
  hasBackend: apiUrl.trim().length > 0,
} as const;
