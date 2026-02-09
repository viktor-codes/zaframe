import {
  Alert,
  Badge,
  Button,
  Card,
  Input,
  Skeleton,
  Textarea,
} from "@/components/ui";

export const metadata = {
  title: "ZaFrame UI Kit",
  description: "Design System v1.0 - Mobile First",
};

export default function UIKitPage() {
  return (
    <div className="bg-neutral-50 min-h-screen p-8">
      <div className="max-w-6xl mx-auto space-y-16">
        {/* Header */}
        <header>
          <div className="flex items-center gap-4 mb-4">
            <Card className="p-3">
              <div className="bg-secondary w-12 h-12 rounded flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            </Card>
            <div>
              <h1 className="font-display font-bold text-4xl text-secondary">
                ZaFrame UI Kit
              </h1>
              <p className="text-neutral-500 text-sm">
                Design System v1.0 • Mobile First
              </p>
            </div>
          </div>
        </header>

        {/* 1. Colour Palette */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            01. Colour Palette
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <h3 className="font-semibold text-sm text-neutral-700 mb-4">
                Primary (Mint)
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-4 bg-primary rounded">
                  <span className="text-white font-mono text-xs">Default</span>
                  <span className="text-white font-mono text-xs">#45D1B8</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-primary-dark rounded">
                  <span className="text-white font-mono text-xs">Dark</span>
                  <span className="text-white font-mono text-xs">#3AB89F</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-primary-light rounded">
                  <span className="text-white font-mono text-xs">Light</span>
                  <span className="text-white font-mono text-xs">#6FDDC7</span>
                </div>
              </div>
            </Card>
            <Card>
              <h3 className="font-semibold text-sm text-neutral-700 mb-4">
                Secondary (Navy)
              </h3>
              <div className="flex items-center justify-between p-4 bg-secondary rounded">
                <span className="text-white font-mono text-xs">Default</span>
                <span className="text-white font-mono text-xs">#2C3E50</span>
              </div>
            </Card>
            <Card>
              <h3 className="font-semibold text-sm text-neutral-700 mb-4">
                Neutral (Gray Scale)
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-neutral-100 rounded">
                  <span className="text-neutral-700 font-mono text-xs">100</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-neutral-300 rounded">
                  <span className="text-neutral-700 font-mono text-xs">300</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-neutral-500 rounded">
                  <span className="text-white font-mono text-xs">500</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-neutral-700 rounded">
                  <span className="text-white font-mono text-xs">700</span>
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* 2. Typography */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            02. Typography
          </h2>
          <Card>
            <div className="space-y-8">
              <div>
                <p className="text-xs text-neutral-500 mb-2">
                  Display / Montserrat Bold
                </p>
                <h1 className="font-display font-bold text-5xl text-secondary">
                  Book Your Session
                </h1>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-2">
                  Heading 1 / Montserrat Bold
                </p>
                <h2 className="font-display font-bold text-4xl text-secondary">
                  Welcome to ZaFrame
                </h2>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-2">
                  Heading 2 / Montserrat SemiBold
                </p>
                <h3 className="font-display font-semibold text-2xl text-secondary">
                  Available Services
                </h3>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-2">
                  Heading 3 / Inter SemiBold
                </p>
                <h4 className="font-sans font-semibold text-xl text-secondary">
                  Select Your Time
                </h4>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-2">
                  Body / Inter Regular
                </p>
                <p className="font-sans text-base text-neutral-700">
                  Professional photography services with instant booking. Choose
                  your preferred date and time, and we&apos;ll capture your
                  perfect moment.
                </p>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-2">
                  Small / Inter Regular
                </p>
                <p className="font-sans text-sm text-neutral-600">
                  Duration: 60 minutes • Price: €120
                </p>
              </div>
            </div>
          </Card>
        </section>

        {/* 3. Buttons */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            03. Buttons
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <h3 className="font-semibold text-sm text-neutral-700 mb-4">
                Primary Buttons
              </h3>
              <div className="space-y-3">
                <Button fullWidth>Book Now</Button>
                <Button fullWidth disabled>
                  Button Disabled
                </Button>
                <Button fullWidth isLoading>
                  Loading...
                </Button>
              </div>
            </Card>
            <Card>
              <h3 className="font-semibold text-sm text-neutral-700 mb-4">
                Secondary Buttons
              </h3>
              <div className="space-y-3">
                <Button variant="outline" fullWidth>
                  View All Services
                </Button>
                <Button variant="secondary" fullWidth>
                  Cancel
                </Button>
                <Button variant="ghost" fullWidth>
                  Skip for now
                </Button>
              </div>
            </Card>
          </div>
        </section>

        {/* 4. Polaroid Cards */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            04. Polaroid Cards
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card variant="interactive">
              <div className="bg-gradient-to-br from-primary-light to-primary h-48 rounded mb-3 flex items-center justify-center">
                <svg
                  className="w-20 h-20 text-white opacity-50"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
              <div className="text-center">
                <h3 className="font-display font-bold text-lg text-secondary mb-1">
                  Portrait Session
                </h3>
                <p className="text-sm text-neutral-600 mb-2">
                  Professional headshots
                </p>
                <div className="flex items-center justify-center gap-4 text-xs text-neutral-500">
                  <span className="flex items-center gap-1">
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    60 min
                  </span>
                  <span className="font-semibold text-primary text-base">
                    €120
                  </span>
                </div>
              </div>
            </Card>
            <Card variant="interactive" className="hover:border-2 hover:border-primary">
              <div className="text-center py-6">
                <div className="text-3xl font-display font-bold text-secondary mb-1">
                  09:00
                </div>
                <div className="text-sm text-neutral-500">Morning slot</div>
                <Badge variant="available" className="mt-3">
                  Available
                </Badge>
              </div>
            </Card>
            <Card variant="disabled">
              <div className="text-center py-6">
                <div className="text-3xl font-display font-bold text-neutral-400 mb-1">
                  14:00
                </div>
                <div className="text-sm text-neutral-400">Afternoon</div>
                <Badge variant="booked" className="mt-3">
                  Booked
                </Badge>
              </div>
            </Card>
          </div>
        </section>

        {/* 5. Form Inputs */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            05. Form Inputs
          </h2>
          <Card className="max-w-2xl">
            <div className="space-y-4">
              <Input label="Full Name" placeholder="John Doe" />
              <Input label="Email Address" placeholder="john@example.com" />
              <Input
                label="Phone Number"
                placeholder="+353 12 345 6789"
                type="tel"
              />
              <Textarea
                label="Additional Notes (Optional)"
                placeholder="Any special requests or requirements..."
                rows={3}
              />
              <Input
                label="Email (Error State)"
                defaultValue="invalid-email"
                error="Please enter a valid email address"
              />
            </div>
          </Card>
        </section>

        {/* 6. Badges */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            06. Badges &amp; Tags
          </h2>
          <Card>
            <div className="flex flex-wrap gap-3">
              <Badge variant="available">Available</Badge>
              <Badge variant="booked">Booked</Badge>
              <Badge variant="pending">Pending</Badge>
              <Badge variant="new">NEW</Badge>
              <Badge variant="popular">POPULAR</Badge>
            </div>
          </Card>
        </section>

        {/* 7. Loading States */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            07. Loading States
          </h2>
          <Card>
            <div className="space-y-4">
              <div>
                <Skeleton className="h-48 w-full mb-3" />
                <Skeleton className="h-4 w-3/4 mb-2" />
                <Skeleton className="h-3 w-1/2" />
              </div>
              <div className="flex items-center justify-center py-8">
                <svg
                  className="animate-spin h-12 w-12 text-primary"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </div>
              <div className="flex items-center justify-center gap-2 py-4">
                <div
                  className="w-3 h-3 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <div
                  className="w-3 h-3 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <div
                  className="w-3 h-3 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </Card>
        </section>

        {/* 8. Alerts */}
        <section>
          <h2 className="font-display font-bold text-2xl text-secondary mb-6">
            08. Alerts &amp; Notifications
          </h2>
          <div className="space-y-4 max-w-2xl">
            <Alert variant="success" title="Booking Confirmed!">
              Your session has been successfully booked for March 15, 2024 at 2:00
              PM
            </Alert>
            <Alert variant="error" title="Time Slot No Longer Available">
              This slot was just booked. Please select another time.
            </Alert>
            <Alert variant="info" title="Session Details">
              Please arrive 10 minutes early. Studio is located on the 2nd floor.
            </Alert>
          </div>
        </section>

        <footer className="text-center py-12 text-neutral-500 text-sm">
          <p>ZaFrame UI Kit v1.0 • Next.js + Tailwind CSS</p>
          <p className="mt-2">Ready to integrate with FastAPI backend</p>
        </footer>
      </div>
    </div>
  );
}
