// Presenta un día y sus comidas dentro del calendario.
import AppIcon from "./AppIcon";
import { formatDateLabel, type CalendarDate } from "./mealPlanningDates";
import type { MealAssignment, MealSlot } from "./mealPlanningApi";

const SLOT_LABELS: Record<MealSlot, string> = { lunch: "Almuerzo", dinner: "Cena" };

function MealThumbnail({ name, imageUrl, onOpen }: { name: string; imageUrl?: string | null; onOpen?: () => void }) {
  return <span className="meal-thumbnail" role={onOpen ? "button" : undefined} tabIndex={onOpen ? 0 : undefined} onClick={onOpen} onKeyDown={onOpen ? (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onOpen(); } } : undefined} aria-label={onOpen ? `Ver recetas de ${name}` : undefined}>{imageUrl ? <img src={`${import.meta.env.VITE_API_BASE_URL || "/comemos"}/api/v1${imageUrl}`} alt="" /> : <AppIcon name="utensils" />}</span>;
}

export default function CalendarDay({ date, weekday, today, outsideMonth = false, compact = false, visibleSlot = "both", assignments, disabled, onEdit, onDelete, onOpenRecipes = () => {} }: {
  date: CalendarDate;
  weekday: string;
  today: boolean;
  outsideMonth?: boolean;
  compact?: boolean;
  visibleSlot?: MealSlot | "both";
  assignments: Map<string, MealAssignment>;
  disabled: boolean;
  onEdit: (date: CalendarDate, slot: MealSlot) => void;
  onDelete: (date: CalendarDate, slot: MealSlot) => void;
  onOpenRecipes?: (foodId: string) => void;
}) {

  return (
    <article className={`calendar-day${today ? " is-today" : ""}${outsideMonth ? " outside-month" : ""}${compact ? " compact-day" : ""}`} aria-current={today ? "date" : undefined}>
      <h4><span>{compact ? weekday : weekday.slice(0, 3)}</span><time dateTime={date}>{formatDateLabel(date, { day: "numeric", month: compact ? undefined : "short" })}</time>{today && <span className="visually-hidden">Hoy</span>}</h4>
      <div className="day-meals">
        {(Object.keys(SLOT_LABELS) as MealSlot[]).filter((slot) => visibleSlot === "both" || visibleSlot === slot).map((slot) => {
          const assignment = assignments.get(`${date}:${slot}`);
          return (
            <div className={`meal-card${assignment ? " assigned" : ""}`} key={slot}>
            <div className={`meal-slot ${assignment ? "planned" : "unplanned"}`}>
              <MealThumbnail name={assignment?.label.name ?? "Sin planificar"} imageUrl={assignment?.label.image_url} onOpen={assignment ? () => onOpenRecipes(assignment.label.id) : undefined} />
              <span className="meal-details">{!compact && visibleSlot === "both" && <span className="etiqueta-comida-movil">{SLOT_LABELS[slot]}</span>}<strong>{assignment ? <button type="button" className="link-button meal-recipe-link" onClick={() => onOpenRecipes(assignment.label.id)}>{assignment.label.name}</button> : "Sin planificar"}</strong>{compact && assignment && <span className={`meal-card-status ${slot}`}>{SLOT_LABELS[slot]}</span>}</span>
              {assignment?.reminder && <span className="meal-reminder" role="img" aria-label="Recordatorio activado" title="Recordatorio activado"><AppIcon name="bell" /></span>}
              <button type="button" className="meal-edit" disabled={disabled}
                aria-label={`${assignment ? "Editar" : "Añadir"} ${SLOT_LABELS[slot].toLowerCase()} del ${formatDateLabel(date, { dateStyle: "full" })}`}
                title={assignment ? "Editar comida" : "Añadir comida"} onClick={() => onEdit(date, slot)}><AppIcon name={assignment ? "edit" : "plus"} /></button>
            </div>
            {assignment && <button type="button" className="meal-delete" disabled={disabled}
              aria-label={`Eliminar ${SLOT_LABELS[slot].toLowerCase()} del ${formatDateLabel(date, { dateStyle: "full" })}: ${assignment.label.name}`}
              title="Eliminar comida" onClick={() => onDelete(date, slot)}><AppIcon name="trash" /></button>}
            </div>
          );
        })}
      </div>
    </article>
  );
}
