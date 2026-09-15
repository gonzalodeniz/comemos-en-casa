-- Private user-owned favorites and recipe collections.
-- Recipes remain public; deleting a recipe cleans every saved reference.

CREATE TABLE recipe_favorites (
    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    recipe_id uuid NOT NULL REFERENCES recipes (id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, recipe_id)
);

CREATE INDEX recipe_favorites_user_created_idx
    ON recipe_favorites (user_id, created_at DESC, recipe_id);

CREATE TABLE recipe_collections (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (char_length(name) BETWEEN 1 AND 200),
    CHECK (name = btrim(name))
);

CREATE INDEX recipe_collections_user_created_idx
    ON recipe_collections (user_id, created_at DESC, id);

CREATE TABLE collection_recipes (
    collection_id uuid NOT NULL REFERENCES recipe_collections (id) ON DELETE CASCADE,
    recipe_id uuid NOT NULL REFERENCES recipes (id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (collection_id, recipe_id)
);

CREATE INDEX collection_recipes_collection_created_idx
    ON collection_recipes (collection_id, created_at, recipe_id);
