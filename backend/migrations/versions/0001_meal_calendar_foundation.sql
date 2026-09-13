-- Expand-only foundation for the shared meal calendar.
-- Do not add a recipes foreign key here: this repository has no recipes(id) migration.
-- A future catalogue-owned migration may add ON DELETE SET NULL after recipes exists.

CREATE TABLE meal_calendars (
    calendar_key text PRIMARY KEY CHECK (calendar_key = 'shared')
);

INSERT INTO meal_calendars (calendar_key) VALUES ('shared');

CREATE TABLE meal_assignments (
    id uuid PRIMARY KEY,
    calendar_key text NOT NULL REFERENCES meal_calendars (calendar_key),
    meal_date date NOT NULL,
    meal_slot text NOT NULL CHECK (meal_slot IN ('lunch', 'dinner')),
    assignment_kind text NOT NULL CHECK (assignment_kind IN ('recipe', 'free_text')),
    recipe_id uuid NULL,
    free_text text NULL,
    CHECK (
        (assignment_kind = 'recipe' AND free_text IS NULL)
        OR (
            assignment_kind = 'free_text'
            AND recipe_id IS NULL
            AND free_text IS NOT NULL
            AND free_text = btrim(free_text)
            AND char_length(free_text) BETWEEN 1 AND 100
        )
    )
);

CREATE INDEX meal_assignments_week_cell_idx
    ON meal_assignments (calendar_key, meal_date, meal_slot);
CREATE INDEX meal_assignments_recipe_idx
    ON meal_assignments (recipe_id) WHERE recipe_id IS NOT NULL;

CREATE TABLE meal_calendar_rate_limits (
    client_ip inet NOT NULL,
    window_start timestamptz NOT NULL,
    operation_class text NOT NULL CHECK (operation_class IN ('read', 'write')),
    request_count integer NOT NULL CHECK (request_count > 0),
    PRIMARY KEY (client_ip, window_start, operation_class)
);

CREATE INDEX meal_calendar_rate_limits_cleanup_idx
    ON meal_calendar_rate_limits (window_start);
