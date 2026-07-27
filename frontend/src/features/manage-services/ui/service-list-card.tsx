import Link from "next/link";

import { VisibilityBadge, type ServiceResponse } from "@entities/service";
import { formatMoneyFromCents, ServiceVisibility } from "@shared/lib";
import { Card } from "@shared/ui";

export interface ServiceListCardProps {
  studioId: number;
  service: ServiceResponse;
}

export function ServiceListCard({ studioId, service }: ServiceListCardProps) {
  return (
    <Link href={`/dashboard/studios/${studioId}/services/${service.id}`}>
      <Card variant="interactive" data-testid="service-list-card">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="font-semibold text-neutral-900">{service.name}</h2>
            <p className="mt-1 text-sm text-neutral-600">
              {service.duration_minutes} min · {service.max_capacity} seats ·{" "}
              {formatMoneyFromCents(service.price_single_cents)}
            </p>
            <div className="mt-2">
              <VisibilityBadge
                visibility={service.visibility}
                showStorefrontHint={
                  service.visibility !== ServiceVisibility.PUBLISHED
                }
              />
            </div>
          </div>
          <span className="shrink-0 text-sm font-medium text-primary">
            Edit →
          </span>
        </div>
      </Card>
    </Link>
  );
}
