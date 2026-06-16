# TZ-09 — Move `booking` + `order` into `modules/booking`; fix cross-domain coupling

> Read [README.md](./README.md). Depends on tz-02 (payment), tz-07 (catalog/service).
> **High risk.** This is where the SOLID coupling problems are actually resolved.

## Goal & why
Bring booking and its order sub-domain home, and eliminate the private cross-domain imports:
- `payment` → `booking.is_own_booking` becomes a **published policy**.
- `catalog/service` → `booking._ensure_no_active_booking_for_guest`, `_persist_bookings`
  disappears because `create_course_booking` moves **into** `booking/order` (intra-domain).
- `auth` → `booking.attach_guest_bookings` switches to the published interface.

## Files
| From | To |
|------|----|
| `app/services/booking.py` | `app/modules/booking/service.py` (+ extract policies) |
| `app/repositories/booking_repo.py` | `app/modules/booking/repository.py` |
| `app/schemas/booking.py` | `app/modules/booking/schemas.py` |
| `app/repositories/order_repo.py` | `app/modules/booking/order/repository.py` |
| `app/schemas/order.py` | `app/modules/booking/order/schemas.py` |
| `create_course_booking` (temp in `catalog/service/service.py`) | `app/modules/booking/order/service.py` |
| `CourseBookingInput`, `CourseBookingResultDTO` (in `catalog/service/dto.py`) | `app/modules/booking/order/dto.py` |
| _(new)_ | `app/modules/booking/__init__.py`, `app/modules/booking/policies.py`, `app/modules/booking/order/__init__.py` |

> `CourseAvailabilityDTO` + `CourseBookingPreviewItemDTO` **stay** in `catalog/service/dto.py`
> (produced by availability logic). `booking/order` imports them from `app.modules.catalog.service`.

## Steps
1. `git mv` booking service/repo/schemas and order repo/schemas to the locations above.
2. **Extract policies** — create `app/modules/booking/policies.py` and move the pure
   functions `is_own_booking`, `can_access_booking` there (and keep `map_booking_*`,
   `get_*`, write paths in `service.py`). `service.py` imports them back:
   `from app.modules.booking.policies import can_access_booking, is_own_booking`.
3. Create `booking/order/` package; move `create_course_booking` from
   `catalog/service/service.py` into `booking/order/service.py`. Its imports:
   - `from app.modules.booking.service import _ensure_no_active_booking_for_guest, _persist_bookings` (intra-domain — allowed).
   - `from app.modules.catalog.service import check_course_availability_for_update`.
   - `from app.modules.booking.order.dto import CourseBookingInput, CourseBookingResultDTO`.
   - `from app.modules.catalog.service import CourseAvailabilityDTO`  # producer-owned
   - keep `app.core.*`, `app.models`.
   Remove the temporary `create_course_booking` re-export from `catalog/service/__init__.py`.
4. Move `CourseBookingInput`, `CourseBookingResultDTO` into `booking/order/dto.py`; update
   `catalog/service/dto.py` to drop them; update the `app/services/dto/__init__.py` facade.
5. In-file imports:
   - `booking/service.py`: schemas → `from app.modules.booking.schemas import ...`; keep `app.core.*`, `app.models`.
   - `order/schemas.py`: `from app.schemas.booking import BookingSelfResponse` → `from app.modules.booking.schemas import BookingSelfResponse`.
   - repos: keep `app.models`, `app.repositories.base`.
6. Published interfaces:
   - `app/modules/booking/__init__.py`:
     ```python
     from app.modules.booking.policies import can_access_booking, is_own_booking
     from app.modules.booking.repository import BookingRepository
     from app.modules.booking.schemas import (
         BookingCreate, BookingCreatedResponse, BookingOwnerResponse,
         BookingSelfListItem, BookingSelfResponse,
     )
     from app.modules.booking.service import (
         attach_guest_bookings, cancel_booking, create_booking,
         get_booking_for_user_or_raise, get_bookings, get_my_bookings,
         get_owner_bookings, get_owner_bookings_count,
         map_booking_created_response, map_booking_for_user,
         # + lifecycle fns used by scripts: expire_stale_pending, complete_past_confirmed
     )
     __all__ = [...]
     ```
   - `app/modules/booking/order/__init__.py`: export `OrderRepository`, `OrderResponse`,
     `CourseBookingCreate`, `CourseBookingResponse`, `create_course_booking`,
     `CourseBookingInput`, `CourseBookingResultDTO`.
   - **Note:** keep private `_ensure_no_active_booking_for_guest`, `_persist_bookings`
     OUT of `__all__` — they are intra-domain only.
7. Facades — `app/schemas/__init__.py`: re-export Booking + Order/course schemas from new
   locations. Keep all `model_rebuild()` calls for now.
8. Repo wiring — `core/uow.py` + `app/repositories/__init__.py`: import `BookingRepository`
   from `app.modules.booking`, `OrderRepository` from `app.modules.booking.order`.
   `uow.bookings`, `uow.orders` unchanged.
9. **Fix the coupling (the point of this step):**
   - `app/modules/payment/service.py`: `from app.services.booking import is_own_booking` → `from app.modules.booking import is_own_booking`.
   - `app/modules/auth/service.py`: `from app.services.booking import attach_guest_bookings` → `from app.modules.booking import attach_guest_bookings`.
   - `app/api/v1/occurrences.py`: `from app.services.booking import get_bookings` → `from app.modules.booking import get_bookings`.
   - `app/api/v1/bookings.py`: booking fns → `from app.modules.booking import ...`; `create_course_booking`, `CourseBookingInput` → `from app.modules.booking.order import ...`.
   - `scripts/run_booking_lifecycle.py` and any seed scripts importing `app.services.booking` → `app.modules.booking`.
10. Tests: repoint `app.services.booking` / `app.repositories.booking_repo` / `app.repositories.order_repo` patches and imports in `tests/` to the new module paths.

## Grep targets (MUST be zero, no facade allowed here)
```bash
rg -n "app\.services\.booking|app\.repositories\.(booking_repo|order_repo)|app\.schemas\.(booking|order)" backend
```

## Definition of Done
- `uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.
- No module imports a `_underscore` name from a **different** domain (manual check / tz-11
  will enforce).

## Commit
```
refactor(booking): move booking + order into modules/booking, add policies
```

## Out of scope
Router relocation (tz-10); deleting the legacy `app/services` & `app/schemas` facades (tz-10).
