-- Calendar-owned integration after 0002_recipe_catalogue_foundation.sql.
-- Keep recipes schema ownership with the catalogue migrations.
ALTER TABLE meal_assignments
    ADD CONSTRAINT meal_assignments_recipe_id_fkey
    FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE SET NULL;
