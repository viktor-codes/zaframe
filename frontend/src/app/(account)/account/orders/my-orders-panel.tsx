"use client";

import { useMemo } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { OrderCard } from "@entities/order";
import { fetchMyOrders, getUserFacingApiMessage } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { Button } from "@shared/ui";
import {
  OrdersEmptyState,
  OrdersErrorState,
  OrdersSkeleton,
} from "./my-orders-states";

const PAGE_SIZE = 20;
const LIST_PARAMS = { size: PAGE_SIZE } as const;

export function MyOrdersPanel() {
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: queryKeys.orders.my(LIST_PARAMS),
    queryFn: ({ pageParam }) =>
      fetchMyOrders({ ...LIST_PARAMS, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });

  const orders = useMemo(
    () => (data?.pages ?? []).flatMap((page) => page.items),
    [data?.pages],
  );
  const totalCount = data?.pages[0]?.total ?? 0;

  if (isLoading) {
    return <OrdersSkeleton />;
  }

  if (isError) {
    return (
      <OrdersErrorState
        message={getUserFacingApiMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  if (totalCount === 0) {
    return <OrdersEmptyState />;
  }

  return (
    <div className="space-y-6" data-testid="my-orders-panel">
      <div className="space-y-3">
        {orders.map((order) => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>

      {hasNextPage ? (
        <div className="flex justify-center">
          <Button
            type="button"
            variant="secondary"
            isLoading={isFetchingNextPage}
            onClick={() => void fetchNextPage()}
            data-testid="orders-load-more"
          >
            Load more
          </Button>
        </div>
      ) : null}
    </div>
  );
}
