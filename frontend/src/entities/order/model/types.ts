import type { Schema } from "@shared/api/schema";

export type OrderResponse = Schema<"OrderResponse">;
export type OrderListItem = Schema<"OrderListItem">;
export type OrderBookingSummary = Schema<"OrderBookingSummary">;
export type OrderCheckoutSessionCreate = Schema<"OrderCheckoutSessionCreate">;
export type PaginatedOrderList = Schema<"PaginatedResponse_OrderListItem_">;

export type OrderLike = OrderResponse | OrderListItem;
