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
  /** URL бэкенда. Пустая строка = статичный лендинг без API. */
  apiUrl,
  /** Есть ли настроенный бэкенд (для условного отображения ссылок и т.п.). */
  hasBackend: apiUrl.length > 0,
} as const;
