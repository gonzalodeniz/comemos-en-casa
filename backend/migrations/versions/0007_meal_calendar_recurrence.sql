-- Add one indefinite, shared-calendar rule per recurring free-text meal.
-- Generated dates are derived at read time; no date rows are stored.

CREATE TABLE meal_recurrence_rules (
    id uuid PRIMARY KEY,
    calendar_key text NOT NULL REFERENCES meal_calendars (calendar_key),
    initial_date date NOT NULL,
    meal_slot text NOT NULL CHECK (meal_slot IN ('lunch', 'dinner')),
    free_text text NOT NULL,
    interval_weeks smallint NOT NULL CHECK (interval_weeks IN (1, 2, 3, 4)),
    CHECK (free_text = btrim(free_text)),
    CHECK (char_length(free_text) BETWEEN 1 AND 100)
);

CREATE INDEX meal_recurrence_rules_calendar_initial_idx
    ON meal_recurrence_rules (calendar_key, initial_date);
