import { MyOrdersPanel } from "./my-orders-panel";

export default function AccountOrdersPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
        Course orders
      </h1>
      <p className="mb-8 text-neutral-600">
        Multi-session purchases and their payment status.
      </p>
      <MyOrdersPanel />
    </div>
  );
}
