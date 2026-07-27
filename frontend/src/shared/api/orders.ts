/**
 * Orders API (customer account + studio owner lists + success-page poll).
 */

import type { OrderListItem, PaginatedOrderList } from "@entities/order";
import { api, type RequestConfig } from "./client";

export interface MyOrdersParams {
  page?: number;
  size?: number;
}

export interface OrderAccessOptions {
  /**
   * Guest opaque token from course POST /bookings (`CourseBookingResponse`).
   * When set, sent as Bearer and session refresh is skipped.
   */
  accessToken?: string | null;
  signal?: AbortSignal;
}

function orderAuthConfig(options?: OrderAccessOptions): RequestConfig {
  const config: RequestConfig = {};
  if (options?.signal) {
    config.signal = options.signal;
  }
  const accessToken = options?.accessToken;
  if (accessToken) {
    return {
      ...config,
      skipAuth: true,
      skipRefresh: true,
      headers: { Authorization: `Bearer ${accessToken}` },
    };
  }
  return config;
}

const DEFAULT_PAGE = 1;
const DEFAULT_SIZE = 20;

/** GET /orders/my — paginated course orders for the current customer. */
export async function fetchMyOrders(
  params: MyOrdersParams = {},
): Promise<PaginatedOrderList> {
  return api.get<PaginatedOrderList>("api/v1/orders/my", {
    params: {
      page: params.page ?? DEFAULT_PAGE,
      size: params.size ?? DEFAULT_SIZE,
    },
  });
}

/**
 * GET /orders/{id} — success-page poll after course Stripe checkout.
 * Guest: opaque order access_token as Bearer; session: own order JWT.
 */
export async function fetchOrder(
  orderId: number,
  options?: OrderAccessOptions,
): Promise<OrderListItem> {
  return api.get<OrderListItem>(
    `api/v1/orders/${orderId}`,
    orderAuthConfig(options),
  );
}
