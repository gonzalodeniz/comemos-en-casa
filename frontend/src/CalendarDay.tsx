import AppIcon from "./AppIcon";
import { useEffect, useRef } from "react";
import { formatDateLabel, type CalendarDate } from "./mealPlanningDates";
import type { MealAssignment, MealSlot } from "./mealPlanningApi";

const SLOT_LABELS: Record<MealSlot, string> = { lunch: "Almuerzo", dinner: "Cena" };

function MealThumbnail({ name, imageUrl }: { name: string; imageUrl?: string | null }) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const image = ref.current;
    const slot = image?.parentElement;
    const text = slot?.querySelector(".meal-details strong");
    if (!image || !slot || !(text instanceof HTMLElement)) return;
    const media = window.matchMedia("(max-width: 600px)");
    let active = true;
    const update = () => {
      if (!active) return;
      if (!media.matches || !slot.closest(".week-grid")) { slot.classList.remove("hide-meal-image"); return; }
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      if (!context) return;
      const style = getComputedStyle(text);
      const slotStyle = getComputedStyle(slot);
      context.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
      const longest = Math.max(0, ...name.split(/\s+/).map((word) => context.measureText(word).width));
      const available = slot.clientWidth - parseFloat(slotStyle.paddingLeft) - parseFloat(slotStyle.paddingRight) - 44 - (parseFloat(slotStyle.columnGap) || 0);
      slot.classList.toggle("hide-meal-image", longest > available);
    };
    const observer = new ResizeObserver(update);
    observer.observe(slot);
    media.addEventListener("change", update);
    void document.fonts.ready.then(update);
    update();
    return () => { active = false; observer.disconnect(); media.removeEventListener("change", update); slot.classList.remove("hide-meal-image"); };
  }, [name]);

  return <span className="meal-thumbnail" ref={ref}>{imageUrl ? <img src={`${import.meta.env.VITE_API_BASE_URL || "/comemos"}/api/v1${imageUrl}`} alt="" /> : <AppIcon name="utensils" />}</span>;
}

export default function CalendarDay({ date, weekday, today, outsideMonth = false, compact = false, assignments, disabled, onEdit, onDelete }: {
  date: CalendarDate;
  weekday: string;
  today: boolean;
  outsideMonth?: boolean;
  compact?: boolean;
  assignments: Map<string, MealAssignment>;
  disabled: boolean;
  onEdit: (date: CalendarDate, slot: MealSlot) => void;
  onDelete: (date: CalendarDate, slot: MealSlot) => void;
}) {

  return (
    <article className={`calendar-day${today ? " is-today" : ""}${outsideMonth ? " outside-month" : ""}${compact ? " compact-day" : ""}`} aria-current={today ? "date" : undefined}>
      <h4><span>{compact ? weekday : weekday.slice(0, 3)}</span><time dateTime={date}>{formatDateLabel(date, { day: "numeric", month: compact ? undefined : "short" })}</time>{today && <span className="visually-hidden">Hoy</span>}</h4>
      <div className="day-meals">
        {(Object.keys(SLOT_LABELS) as MealSlot[]).map((slot) => {
          const assignment = assignments.get(`${date}:${slot}`);
          return (
            <div className={`meal-card${assignment ? " assigned" : ""}`} key={slot}>
            <div className={`meal-slot ${assignment ? "planned" : "unplanned"}`}>
              <MealThumbnail name={assignment?.label.name ?? "Sin planificar"} imageUrl={assignment?.label.image_url} />
              <span className="meal-details"><strong>{assignment?.label.name ?? "Sin planificar"}</strong>{compact && assignment && <span className={`meal-card-status ${slot}`}>{SLOT_LABELS[slot]}</span>}</span>
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
