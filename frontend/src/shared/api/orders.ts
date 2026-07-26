/**
 * Orders API (customer account + studio owner lists).
 */

import type { PaginatedOrderList } from "@entities/order";
import { api } from "./client";

export interface MyOrdersParams {
  page?: number;
  size?: number;
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
