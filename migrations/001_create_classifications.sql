CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS classifications (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message text NOT NULL,
    result jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version)
VALUES ('001_create_classifications')
ON CONFLICT (version) DO NOTHING;
