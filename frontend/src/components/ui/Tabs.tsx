"use client";

export interface TabItem {
  id: string;
  label: string;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className = "" }: TabsProps) {
  return (
    <div className={`flex gap-2 border-b border-zinc-200 ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`relative px-4 py-3 text-sm font-semibold transition ${
            activeTab === tab.id
              ? "text-zinc-900"
              : "text-zinc-500 hover:text-zinc-700"
          }`}
        >
          {tab.label}
          {activeTab === tab.id && (
            <div
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-sky-400 via-teal-400 to-lime-300"
              aria-hidden
            />
          )}
        </button>
      ))}
    </div>
  );
}
