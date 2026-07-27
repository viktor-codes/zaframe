import {
  getServiceVisibilityPresentation,
  type ServiceVisibilityTone,
} from "../model/service-visibility";

export interface VisibilityBadgeProps {
  visibility: string;
  /** Show "Not on storefront" for draft/archived. Default true. */
  showStorefrontHint?: boolean;
  className?: string;
}

const toneClasses: Record<ServiceVisibilityTone, string> = {
  neutral: "border-neutral-200 bg-neutral-100 text-neutral-700",
  amber: "border-amber-200 bg-amber-50 text-amber-900",
  green: "border-emerald-200 bg-emerald-50 text-emerald-900",
  teal: "border-teal-200 bg-teal-50 text-teal-800",
};

export function VisibilityBadge({
  visibility,
  showStorefrontHint = true,
  className = "",
}: VisibilityBadgeProps) {
  const { label, tone, storefrontHint } =
    getServiceVisibilityPresentation(visibility);

  return (
    <span
      className={`inline-flex flex-wrap items-center gap-1.5 ${className}`}
      data-testid="visibility-badge"
      data-visibility={visibility}
    >
      <span
        className={`inline-flex items-center rounded-lg border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}
      >
        {label}
      </span>
      {showStorefrontHint && storefrontHint ? (
        <span className="text-xs text-neutral-500">{storefrontHint}</span>
      ) : null}
    </span>
  );
}
