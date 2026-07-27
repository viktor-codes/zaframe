import type { StudioConnectOnboardingInput } from "@entities/studio";
import { roleHasPermission, StudioPermission } from "@shared/lib";

type StudioRoleInput = {
  id: number;
  role: string;
};

type QueryLike = {
  isLoading: boolean;
  isPending: boolean;
  isError: boolean;
  data?: unknown;
  error?: unknown;
  refetch: () => unknown;
};

type ServiceQueryLike = QueryLike & {
  data?: { items?: ReadonlyArray<{ visibility: string }> };
};

type ConnectQueryLike = QueryLike & {
  data?: {
    stripe_account_id?: string | null;
    stripe_charges_enabled?: boolean;
    stripe_payouts_enabled?: boolean;
  };
};

export function buildServicesByStudioId(
  studios: ReadonlyArray<StudioRoleInput>,
  serviceQueries: ReadonlyArray<ServiceQueryLike>,
): Map<number, ReadonlyArray<{ visibility: string }> | undefined> {
  const map = new Map<
    number,
    ReadonlyArray<{ visibility: string }> | undefined
  >();

  studios.forEach((studio, index) => {
    const canManageServices = roleHasPermission(
      studio.role,
      StudioPermission.MANAGE_SERVICES,
    );

    if (!canManageServices) {
      map.set(studio.id, undefined);
      return;
    }

    const query = serviceQueries[index];
    if (!query || query.isLoading || query.isPending || query.isError) {
      // WHY: leave undefined on error — panel surfaces isError, never fake empty.
      map.set(studio.id, undefined);
      return;
    }

    map.set(studio.id, query.data?.items ?? []);
  });

  return map;
}

export function buildConnectByStudioId(
  studios: ReadonlyArray<StudioRoleInput>,
  connectQueries: ReadonlyArray<ConnectQueryLike>,
): Map<number, StudioConnectOnboardingInput> {
  const map = new Map<number, StudioConnectOnboardingInput>();

  studios.forEach((studio, index) => {
    const canManagePayouts = roleHasPermission(
      studio.role,
      StudioPermission.MANAGE_PAYOUTS,
    );

    if (!canManagePayouts) {
      return;
    }

    const query = connectQueries[index];
    if (!query || query.isLoading || query.isPending || query.isError) {
      map.set(studio.id, undefined);
      return;
    }

    map.set(studio.id, {
      stripe_account_id: query.data?.stripe_account_id,
      stripe_charges_enabled: query.data?.stripe_charges_enabled ?? false,
      stripe_payouts_enabled: query.data?.stripe_payouts_enabled ?? false,
    });
  });

  return map;
}

export function findRoleScopedQueryIssue(
  studios: ReadonlyArray<StudioRoleInput>,
  queries: ReadonlyArray<QueryLike>,
  permission: StudioPermission,
): { isLoading: boolean; failed: QueryLike | undefined } {
  const isLoading = queries.some(
    (query, index) =>
      roleHasPermission(studios[index]?.role, permission) &&
      (query.isLoading || query.isPending),
  );

  const failed = queries.find(
    (query, index) =>
      roleHasPermission(studios[index]?.role, permission) && query.isError,
  );

  return { isLoading, failed };
}
