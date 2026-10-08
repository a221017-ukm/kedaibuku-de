-- Governance as code: roles, least-privilege grants and row-level security.
-- Run after every gold rebuild, because dropped tables lose their grants and policies.

-- 1. Group roles (no login) - created only if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kedai_analyst')   THEN CREATE ROLE kedai_analyst;   END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kedai_engineer')  THEN CREATE ROLE kedai_engineer;  END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kedai_marketing') THEN CREATE ROLE kedai_marketing; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kedai_johor')     THEN CREATE ROLE kedai_johor;     END IF;
    -- 2. People (login roles) who inherit a group role. Lab passwords only.
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'alice') THEN CREATE ROLE alice LOGIN PASSWORD 'alice123' IN ROLE kedai_analyst;   END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ben')   THEN CREATE ROLE ben   LOGIN PASSWORD 'ben123'   IN ROLE kedai_engineer;  END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mei')   THEN CREATE ROLE mei   LOGIN PASSWORD 'mei123'   IN ROLE kedai_marketing; END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'zul')   THEN CREATE ROLE zul   LOGIN PASSWORD 'zul123'   IN ROLE kedai_johor;     END IF;
END $$;

-- 3. Analysts and the Johor manager: read gold only
GRANT USAGE ON SCHEMA gold TO kedai_analyst, kedai_johor;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO kedai_analyst, kedai_johor;

-- 4. Engineers: read and write silver and gold
GRANT USAGE, CREATE ON SCHEMA silver, gold TO kedai_engineer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA silver, gold TO kedai_engineer;

-- 5. Marketing: three columns of one silver table, nothing else (column-level privilege)
GRANT USAGE ON SCHEMA silver TO kedai_marketing;
GRANT SELECT (customer_id, state, email_masked) ON silver.customers TO kedai_marketing;

-- 6. Row-level security: the Johor manager sees only Johor customers
ALTER TABLE gold.dim_customer ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS johor_only ON gold.dim_customer;
DROP POLICY IF EXISTS analysts_all ON gold.dim_customer;
DROP POLICY IF EXISTS engineers_all ON gold.dim_customer;
CREATE POLICY johor_only    ON gold.dim_customer FOR SELECT TO kedai_johor    USING (state = 'Johor');
CREATE POLICY analysts_all  ON gold.dim_customer FOR SELECT TO kedai_analyst  USING (true);
CREATE POLICY engineers_all ON gold.dim_customer FOR ALL    TO kedai_engineer USING (true);
