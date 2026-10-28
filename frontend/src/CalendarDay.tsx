import AppIcon from "./AppIcon";
import { formatDateLabel, type CalendarDate } from "./mealPlanningDates";
import type { MealAssignment, MealSlot } from "./mealPlanningApi";

const SLOT_LABELS: Record<MealSlot, string> = { lunch: "Almuerzo", dinner: "Cena" };

export default function CalendarDay({ date, weekday, today, outsideMonth = false, compact = false, assignments, disabled, onEdit }: {
  date: CalendarDate;
  weekday: string;
  today: boolean;
  outsideMonth?: boolean;
  compact?: boolean;
  assignments: Map<string, MealAssignment>;
  disabled: boolean;
  onEdit: (date: CalendarDate, slot: MealSlot) => void;
}) {

  return (
    <article className={`calendar-day${today ? " is-today" : ""}${outsideMonth ? " outside-month" : ""}${compact ? " compact-day" : ""}`} aria-current={today ? "date" : undefined}>
      <h4><span>{compact ? weekday : weekday.slice(0, 3)}</span><time dateTime={date}>{formatDateLabel(date, { day: "numeric", month: compact ? undefined : "short" })}</time>{today && <span className="visually-hidden">Hoy</span>}</h4>
      <div className="day-meals">
        {(Object.keys(SLOT_LABELS) as MealSlot[]).map((slot) => {
          const assignment = assignments.get(`${date}:${slot}`);
          const action = assignment ? "Editar" : "Planificar";
          return (
            <button
              key={slot}
              type="button"
              className={`meal-slot ${assignment ? "planned" : "unplanned"}`}
              aria-label={`${action} ${SLOT_LABELS[slot].toLowerCase()} del ${formatDateLabel(date, { dateStyle: "full" })}${assignment ? `: ${assignment.label.name}` : ""}`}
              disabled={disabled}
              onClick={() => onEdit(date, slot)}
            >
              <span className="meal-thumbnail"><AppIcon name="utensils" /></span>
              <span className="meal-details"><strong>{assignment?.label.name ?? "Sin planificar"}</strong>{compact && assignment && <span className={`meal-card-status ${slot}`}>{SLOT_LABELS[slot]}</span>}</span>
            </button>
          );
        })}
      </div>
      {!compact && <details className="day-actions">
        <summary aria-label={`Acciones del ${formatDateLabel(date, { dateStyle: "full" })}`}>⋮</summary>
        <div className="day-actions-menu">
          {(Object.keys(SLOT_LABELS) as MealSlot[]).map((slot) => (
            <button key={slot} type="button" disabled={disabled} onClick={(event) => {
              event.currentTarget.closest("details")?.removeAttribute("open");
              onEdit(date, slot);
            }}>{assignments.has(`${date}:${slot}`) ? "Editar" : "Planificar"} {SLOT_LABELS[slot].toLowerCase()}</button>
          ))}
        </div>
      </details>}
    </article>
  );
}
