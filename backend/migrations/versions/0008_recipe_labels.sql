-- Global public recipe labels and the public-only recipe contract.
-- This migration is applied after 0001 through 0007.

ALTER TABLE recipes
    DROP CONSTRAINT IF EXISTS recipes_status_check,
    DROP COLUMN IF EXISTS status;

CREATE TABLE recipe_labels (
    id uuid PRIMARY KEY,
    name text NOT NULL UNIQUE,
    color text NOT NULL
);

CREATE INDEX recipe_labels_name_idx
    ON recipe_labels (name);

CREATE TABLE recipe_label_assignments (
    recipe_id uuid NOT NULL REFERENCES recipes (id) ON DELETE CASCADE,
    label_id uuid NOT NULL REFERENCES recipe_labels (id) ON DELETE CASCADE,
    PRIMARY KEY (recipe_id, label_id)
);

CREATE INDEX recipe_label_assignments_label_recipe_idx
    ON recipe_label_assignments (label_id, recipe_id);
