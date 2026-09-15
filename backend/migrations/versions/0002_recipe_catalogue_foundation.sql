CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE recipes (
    id uuid PRIMARY KEY,
    title text NOT NULL,
    image_url text NOT NULL,
    detail text NOT NULL,
    title_search_key text NOT NULL,
    CHECK (char_length(title) BETWEEN 1 AND 200),
    CHECK (title = btrim(title)),
    CHECK (char_length(image_url) BETWEEN 1 AND 2048),
    CHECK (image_url = btrim(image_url)),
    CHECK (image_url ~* '^https?://'),
    CHECK (char_length(detail) BETWEEN 1 AND 10000),
    CHECK (detail = btrim(detail)),
    CHECK (position(E'\r' in detail) = 0),
    CHECK (char_length(title_search_key) > 0)
);

CREATE INDEX recipes_title_search_idx
    ON recipes USING gin (title_search_key gin_trgm_ops);
