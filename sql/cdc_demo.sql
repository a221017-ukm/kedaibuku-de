-- Lab 3, Step 6: change data capture (CDC) with PostgreSQL's own change log.
-- Run the whole file:  docker compose exec -T postgres psql -U de_student -d kedaibuku < sql/cdc_demo.sql

-- 1. The "operational" orders table the KedaiBuku web shop writes to
CREATE SCHEMA IF NOT EXISTS app;
DROP TABLE IF EXISTS app.orders_live;
CREATE TABLE app.orders_live (
    order_id    text PRIMARY KEY,
    customer_id text NOT NULL,
    status      text NOT NULL,
    updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE app.orders_live REPLICA IDENTITY FULL;   -- log the old row values too

-- 2. Start capturing: a replication slot keeps every change until it is read
SELECT 'slot created' AS step, slot_name
FROM pg_create_logical_replication_slot('kedai_cdc', 'test_decoding');

-- 3. The shop does its normal work: two orders, two status changes, one cancellation
INSERT INTO app.orders_live (order_id, customer_id, status) VALUES
    ('O90001', 'C0001', 'placed'), ('O90002', 'C0002', 'placed');
UPDATE app.orders_live SET status = 'paid',    updated_at = now() WHERE order_id = 'O90001';
UPDATE app.orders_live SET status = 'shipped', updated_at = now() WHERE order_id = 'O90001';
DELETE FROM app.orders_live WHERE order_id = 'O90002';

-- 4. What CDC sees: every change, in order
SELECT data AS cdc_change_log FROM pg_logical_slot_peek_changes('kedai_cdc', NULL, NULL);

-- 5. What a timestamp query sees: only the latest state
SELECT order_id, status, updated_at AS timestamp_query_sees
FROM app.orders_live
WHERE updated_at > now() - interval '1 hour';

-- 6. Clean up: an unread slot makes PostgreSQL keep its change log forever
SELECT COUNT(*) AS changes_consumed FROM pg_logical_slot_get_changes('kedai_cdc', NULL, NULL);
SELECT pg_drop_replication_slot('kedai_cdc');
