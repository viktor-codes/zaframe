-- OTP codes retention cleanup (production).
-- Requires pg_cron extension on PostgreSQL.
--
-- Apply once on production DB:
--   psql $DATABASE_URL -f backend/scripts/pg_cron_otp_cleanup.sql

CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule(
    'otp_codes_cleanup_daily',
    '0 3 * * *',
    $$DELETE FROM otp_codes WHERE expires_at < now() - interval '7 days'$$
);
