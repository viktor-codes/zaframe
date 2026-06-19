# FR-11 — Future Backlog (P2+)

> These items are important product directions, but they should not block the first dashboard and
> user account iteration unless a specific screen needs them now.

## Rule for Promotion to Active Work

Do not add a new entity or endpoint until the agent can answer:

> On which screen will the user see this field or action?

If there is no immediate screen, keep the item here.

## Scheduling and Capacity

- [ ] Waitlist
  - promote customers when a spot opens
  - notify customers
  - define payment timing
- [ ] Room
  - room-level capacity
  - room assignment per occurrence
  - room conflicts
- [ ] Denormalized `Occurrence.booked_count`
  - faster dashboard/search counts
  - must stay transactionally correct
- [ ] Optimistic version
  - protect concurrent updates to occurrence/service/studio
  - useful with richer dashboard editing

## Monetization

- [ ] Subscriptions / credits
  - class packs
  - monthly memberships
  - credit balance
  - expiration policy
- [ ] Promo codes
  - fixed/percent discounts
  - redemption limits
  - owner/platform ownership

## Trust and Retention

- [ ] Reviews
  - studio reviews
  - service/class reviews
  - moderation
- [ ] Notifications log
  - email/SMS/push attempts
  - delivery status
  - user-visible notification history
- [ ] Online classes
  - meeting URL
  - access policy
  - link visibility after payment

## Media and Marketing

- [ ] Galleries
  - multiple images per studio/service
  - ordering
  - alt text
  - upload pipeline
- [ ] Booking sources
  - public page
  - dashboard/manual
  - referral
  - campaign
  - partner

## Operations and Governance

- [ ] AuditLog
  - member role changes
  - refunds
  - occurrence cancellations
  - schedule generation
  - sensitive account actions
- [ ] Payment history UI
  - can be promoted earlier if FR-04 lands and owners need money views.

## Promotion Criteria

Move an item from this backlog into a real `fr-*` task when:

- [ ] a planned frontend screen explicitly needs it
- [ ] there is a clear owner/customer story
- [ ] required data model and permissions are known
- [ ] tests can describe the behavior
- [ ] it does not create avoidable scope creep in Phase 1
