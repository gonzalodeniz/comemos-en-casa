-- Public recipe management: lifecycle state and normalized ordered content.
-- Draft and published recipes are both intentionally readable by every visitor.

ALTER TABLE recipes
    DROP CONSTRAINT recipes_image_url_check,
    DROP CONSTRAINT recipes_image_url_check1,
    DROP CONSTRAINT recipes_image_url_check2,
    ALTER COLUMN image_url SET DEFAULT '';

ALTER TABLE recipes
    ADD COLUMN status text NOT NULL DEFAULT 'draft',
    ADD CONSTRAINT recipes_status_check CHECK (status IN ('draft', 'published')),
    ADD CONSTRAINT recipes_image_url_local_or_legacy_check CHECK (
        char_length(image_url) <= 2048
        AND image_url = btrim(image_url)
        AND (image_url = '' OR image_url ~* '^https?://' OR image_url ~ '^/media/recipes/[0-9a-f-]+\.(jpg|png|webp)$')
    );

CREATE TABLE recipe_ingredients (
    recipe_id uuid NOT NULL REFERENCES recipes (id) ON DELETE CASCADE,
    position integer NOT NULL,
    name text NOT NULL,
    quantity text NULL,
    PRIMARY KEY (recipe_id, position),
    CHECK (position >= 1),
    CHECK (char_length(name) BETWEEN 1 AND 500),
    CHECK (name = btrim(name)),
    CHECK (quantity IS NULL OR (char_length(quantity) BETWEEN 1 AND 100 AND quantity = btrim(quantity)))
);

CREATE TABLE recipe_preparation_steps (
    recipe_id uuid NOT NULL REFERENCES recipes (id) ON DELETE CASCADE,
    position integer NOT NULL,
    instruction text NOT NULL,
    PRIMARY KEY (recipe_id, position),
    CHECK (position >= 1),
    CHECK (char_length(instruction) BETWEEN 1 AND 10000),
    CHECK (instruction = btrim(instruction)),
    CHECK (position(E'\r' in instruction) = 0)
);
