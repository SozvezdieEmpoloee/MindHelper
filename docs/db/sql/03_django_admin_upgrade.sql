-- Upgrade existing database for Django backend compatibility.
-- Run this after 01_schema.sql / 02_seed.sql if your DB was created earlier.

BEGIN;

ALTER TABLE user_account
    ADD COLUMN IF NOT EXISTS is_staff boolean NOT NULL DEFAULT false;

ALTER TABLE user_account
    ADD COLUMN IF NOT EXISTS is_superuser boolean NOT NULL DEFAULT false;

ALTER TABLE site_content
    ADD COLUMN IF NOT EXISTS slug varchar(255);

UPDATE user_account
SET is_staff = true,
    is_superuser = true
WHERE email = 'admin@mindhelper.local';

UPDATE site_content
SET slug = lower(
    trim(
        both '-'
        FROM regexp_replace(title, '[^a-zA-Z0-9]+', '-', 'g')
    )
)
WHERE slug IS NULL;

ALTER TABLE site_content
    ALTER COLUMN slug SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_site_content_slug
    ON site_content(slug);

COMMIT;
