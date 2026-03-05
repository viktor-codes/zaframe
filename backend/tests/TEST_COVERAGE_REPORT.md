# Отчёт о покрытии тестами

## Что уже покрыто

### 1. **test_api_auth.py** — API аутентификации
- Health endpoint
- Запрос magic link (200)
- Верификация с неверным токеном (400)
- Полный флоу: request → verify → refresh → me → logout → старый refresh не работает
- /me без Bearer → 401
- refresh с невалидным токеном → 401
- logout без Bearer → 401

### 2. **test_auth_service.py** — сервис auth (юниты)
- get_current_user_from_token: валидный токен → user; невалидный → None; пользователь не найден → None
- logout_current_session: невалидный токен — no op; токен другого пользователя — no op

### 3. **test_security.py** — core.security
- create_access_token, decode_token (sub, email, type, exp, iat)
- get_user_id_from_access_token (валидный, wrong type, invalid)
- create_refresh_token, parse_refresh_token (валидный, access вместо refresh, invalid)
- get_user_id_from_refresh_token
- decode_token (access, refresh, invalid)
- hash_magic_link_token (детерминированность, разные хеши)
- get_magic_link_expires_at (future, utc-aware)

### 4. **test_api_studios_slots_bookings.py** — интеграции
- CRUD студии (create, update, delete, 404 после удаления)
- Слот + бронирование: создание студии → слот → гостевое бронирование → отмена → удаление слота

### 5. **test_service_helpers.py** — Service.get_capacity_status
- Базовые лимиты (soft, hard)
- Дробные коэффициенты

---

## Что не покрыто (изменённые модули)

### 1. **app/api/webhooks.py** — Stripe webhook
| Сценарий | Покрытие |
|----------|----------|
| STRIPE_WEBHOOK_SECRET не задан → 500 | ❌ |
| Невалидный payload (ValueError) → 400 | ❌ |
| Невалидная подпись (SignatureVerificationError) → 400 | ❌ |
| Тип события ≠ checkout.session.completed → 200 | ❌ |
| metadata.order_id есть → confirm_order_after_payment, commit, 200 | ❌ |
| order_id не int (ValueError) → 200 | ❌ |
| metadata.booking_id есть → confirm_booking_after_payment, commit, 200 | ❌ |
| booking_id не int (ValueError) → 200 | ❌ |
| Нет ни booking_id, ни order_id → 200 (warning) | ❌ |
| _parse_checkout_session_metadata (dict / object) | ❌ |
| _parse_payment_intent_id | ❌ |
| Исключение в блоке try → rollback, re-raise | ❌ |

### 2. **app/services/payment.py** — платёжный сервис
| Сценарий | Покрытие |
|----------|----------|
| create_checkout_session: бронирование не найдено → NotFoundError | ❌ |
| create_checkout_session: статус не PENDING → ValidationError | ❌ |
| create_checkout_session: уже есть checkout_session_id → ValidationError | ❌ |
| create_checkout_session: slot.price_cents <= 0 → ValidationError | ❌ |
| create_checkout_session: успех → url + session_id | ❌ |
| create_checkout_session: STRIPE_SECRET_KEY не задан → AppError 503 | ❌ |
| create_order_checkout_session: заказ не найден → NotFoundError | ❌ |
| create_order_checkout_session: статус не PENDING → ValidationError | ❌ |
| create_order_checkout_session: total_amount_cents <= 0 → ValidationError | ❌ |
| create_order_checkout_session: успех | ❌ |
| confirm_booking_after_payment: бронирование не найдено → False | ❌ |
| confirm_booking_after_payment: уже CONFIRMED → True (идемпотентность) | ❌ |
| confirm_booking_after_payment: успех + payment_intent_id | ❌ |
| confirm_order_after_payment: заказ не найден → False | ❌ |
| confirm_order_after_payment: уже PAID → True (идемпотентность) | ❌ |
| confirm_order_after_payment: успех + подтверждение связанных бронирований | ❌ |

### 3. **app/core/repositories/booking_repo.py**
| Сценарий | Покрытие |
|----------|----------|
| get_by_id, get_by_id_with_slot | Косвенно через интеграции |
| list_ с фильтрами (slot_id, user_id, guest_email, status, order_id) | ❌ юнит-тестов нет |
| count, count_confirmed_by_slot, count_pending_by_slot | ❌ |
| get_confirmed_pending_counts_by_slot_ids (в т.ч. пустой список) | ❌ |

### 4. **API payments** (app/api/v1/payments.py)
- Эндпоинты POST /checkout-session и POST /order-checkout-session не покрыты интеграционными тестами (нужен мок Stripe).

---

## Рекомендации

1. Добавить **test_webhooks.py** — мок stripe.Webhook.construct_event и payload; проверка всех веток webhook (500, 400, 200, order/booking).
2. Добавить **test_payment_service.py** — юнит-тесты с моком UoW и Stripe для create_checkout_session, create_order_checkout_session, confirm_booking_after_payment, confirm_order_after_payment.
3. При необходимости — юнит-тесты для BookingRepository с тестовой БД или моками (можно оставить только интеграционное покрытие через test_api_studios_slots_bookings).

После добавления test_webhooks.py и test_payment_service.py критические сценарии платежей и webhook будут покрыты.
