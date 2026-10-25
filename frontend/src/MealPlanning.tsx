import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { ApiError } from "./api";
import {
  addCalendarDays,
  annualMaximumEndDate,
  formatDateLabel,
  localToday,
  parseCalendarDate,
  shiftMonthClamped,
  visibleDateRange,
  type CalendarDate,
  type CalendarView,
} from "./mealPlanningDates";
import {
  applyMealPlanning,
  getFoodLabels,
  getMealPlanning,
  previewMealPlanning,
  type FoodLabel,
  type MealAssignment,
  type MealPlanningOperation,
  type MealPlanningPreview,
  type MealSlot,
} from "./mealPlanningApi";

type EditorDraft = {
  action: "assign" | "delete";
  labelId: string;
  repeat: boolean;
  intervalWeeks: string;
  endDate: string;
};

type Props = { csrfToken: string; onSessionExpired: () => void };

const SLOT_LABELS: Record<MealSlot, string> = { lunch: "Almuerzo", dinner: "Cena" };
const WEEKDAY_LABELS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

export default function MealPlanning({ csrfToken, onSessionExpired }: Props) {
  const [view, setView] = useState<CalendarView>("week");
  const [referenceDate, setReferenceDate] = useState<CalendarDate | null>(null);
  const queryDate = referenceDate ?? localToday();
  const range = useMemo(() => visibleDateRange(queryDate, view), [queryDate, view]);
  const [today, setToday] = useState<string | null>(null);
  const [labels, setLabels] = useState<FoodLabel[]>([]);
  const [assignments, setAssignments] = useState<MealAssignment[]>([]);
  const [calendarLoading, setCalendarLoading] = useState(true);
  const [editorDate, setEditorDate] = useState<CalendarDate | null>(null);
  const [editorSlot, setEditorSlot] = useState<MealSlot | null>(null);
  const [draft, setDraft] = useState<EditorDraft | null>(null);
  const [preview, setPreview] = useState<MealPlanningPreview | null>(null);
  const [forceReconfirmation, setForceReconfirmation] = useState(false);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let cancelled = false;
    void getFoodLabels()
      .then((result) => {
        if (!cancelled) setLabels(result.labels);
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
        else setError(errorMessage(cause));
      });
    return () => { cancelled = true; };
  }, [onSessionExpired]);

  useEffect(() => {
    let cancelled = false;
    setCalendarLoading(true);
    void getMealPlanning(range.start, range.end)
      .then((result) => {
        if (cancelled) return;
        setAssignments(result.assignments);
        setToday(result.today);
        if (referenceDate === null) setReferenceDate(result.today as CalendarDate);
        setError("");
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
        else setError(errorMessage(cause));
      })
      .finally(() => {
        if (!cancelled) setCalendarLoading(false);
      });
    return () => { cancelled = true; };
  }, [range.start, range.end, referenceDate, revision, onSessionExpired]);

  const assignmentMap = useMemo(() => {
    const result = new Map<string, MealAssignment>();
    for (const assignment of assignments) {
      result.set(`${assignment.date}:${assignment.slot}`, assignment);
    }
    return result;
  }, [assignments]);

  function moveRange(direction: -1 | 1) {
    setReferenceDate((current) => {
      const from = current ?? today ?? localToday();
      return view === "week"
        ? addCalendarDays(from, direction * 7)
        : shiftMonthClamped(from, direction);
    });
    closeEditor();
  }

  function openEditor(date: CalendarDate, slot: MealSlot) {
    const current = assignmentMap.get(`${date}:${slot}`);
    const labelId = current?.label.id ?? labels[0]?.id ?? "";
    setEditorDate(date);
    setEditorSlot(slot);
    setDraft({
      action: "assign",
      labelId,
      repeat: false,
      intervalWeeks: "1",
      endDate: annualMaximumEndDate(date),
    });
    setPreview(null);
    setForceReconfirmation(false);
    setError("");
    setNotice("");
  }

  function closeEditor() {
    setEditorDate(null);
    setEditorSlot(null);
    setDraft(null);
    setPreview(null);
    setForceReconfirmation(false);
  }

  function changeStartDate(value: string) {
    if (!draft || !value) return;
    const maximum = annualMaximumEndDate(value);
    let endDate = draft.endDate;
    try {
      if (parseCalendarDate(endDate) < parseCalendarDate(value)) endDate = value;
      if (parseCalendarDate(endDate) > parseCalendarDate(maximum)) endDate = maximum;
    } catch {
      endDate = maximum;
    }
    setEditorDate(value as CalendarDate);
    setDraft({ ...draft, endDate });
    setPreview(null);
  }

  function operationFromDraft(): MealPlanningOperation | null {
    if (!draft || !editorDate || !editorSlot || !draft.labelId) return null;
    return {
      action: draft.action,
      start_date: editorDate,
      slot: editorSlot,
      label_id: draft.labelId,
      repeat: draft.repeat
        ? { interval_weeks: Number(draft.intervalWeeks), end_date: draft.endDate }
        : null,
    };
  }

  async function runExclusive(action: () => Promise<void>) {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (cause: unknown) {
      if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
      else setError(errorMessage(cause));
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  function submitPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const operation = operationFromDraft();
    if (!operation) return;
    void runExclusive(async () => {
      const result = await previewMealPlanning(operation, csrfToken);
      setPreview(result);
      setForceReconfirmation(false);
    });
  }

  function saveOperation() {
    const operation = operationFromDraft();
    if (!operation || !preview) return;
    void runExclusive(async () => {
      try {
        const result = await applyMealPlanning(operation, preview.preview_token, csrfToken);
        closeEditor();
        setNotice(
          result.changed_count === 0
            ? "No había cambios que guardar."
            : `Se guardaron ${result.changed_count} cambio${result.changed_count === 1 ? "" : "s"}.`,
        );
        setRevision((value) => value + 1);
      } catch (cause: unknown) {
        if (!(cause instanceof ApiError) || cause.status !== 409) throw cause;
        const refreshed = await previewMealPlanning(operation, csrfToken);
        setPreview(refreshed);
        setForceReconfirmation(true);
        setError("La planificación cambió desde la vista previa. Revisa el estado actualizado antes de confirmar.");
      }
    });
  }

  const title = view === "week"
    ? `${formatDateLabel(range.start, { day: "numeric", month: "long" })} – ${formatDateLabel(range.end, { day: "numeric", month: "long", year: "numeric" })}`
    : formatDateLabel(queryDate, { month: "long", year: "numeric" });

  return (
    <section className="panel meal-planning" aria-labelledby="meal-planning-title">
      <div className="meal-heading">
        <div>
          <p className="eyebrow">Planificación familiar</p>
          <h2 id="meal-planning-title">Comidas</h2>
          <p className="meal-date-context">Hoy: {today ?? "…"} · Atlantic/Canary</p>
        </div>
        <div className="meal-view-switch" role="group" aria-label="Vista del calendario">
          <button type="button" className={view === "week" ? "" : "secondary"} aria-pressed={view === "week"} disabled={calendarLoading || busy} onClick={() => setView("week")}>Semana</button>
          <button type="button" className={view === "month" ? "" : "secondary"} aria-pressed={view === "month"} disabled={calendarLoading || busy} onClick={() => setView("month")}>Mes</button>
        </div>
      </div>

      <div className="calendar-navigation">
        <button type="button" className="secondary" aria-label={view === "week" ? "Semana anterior" : "Mes anterior"} disabled={calendarLoading || busy} onClick={() => moveRange(-1)}>←</button>
        <h3 aria-live="polite">{title}</h3>
        <button type="button" className="secondary" aria-label={view === "week" ? "Semana siguiente" : "Mes siguiente"} disabled={calendarLoading || busy} onClick={() => moveRange(1)}>→</button>
        <button type="button" className="secondary today-button" disabled={calendarLoading || busy} onClick={() => { setReferenceDate((today ?? localToday()) as CalendarDate); closeEditor(); }}>Hoy</button>
      </div>

      {error && <p className="message error" role="alert">{error}</p>}
      {notice && <p className="message success" role="status">{notice}</p>}
      {calendarLoading && <p role="status">Cargando planificación…</p>}

      {view === "week" ? (
        <div className="week-grid" aria-label="Planificación semanal">
          {range.dates.map((date, index) => (
            <CalendarDay
              key={date}
              date={date}
              weekday={WEEKDAY_LABELS[index]}
              today={date === today}
              assignments={assignmentMap}
              disabled={calendarLoading || busy}
              onEdit={openEditor}
            />
          ))}
        </div>
      ) : (
        <div
          className="month-calendar"
          role="region"
          aria-label="Planificación mensual"
          tabIndex={0}
          onFocus={(event) => {
            const target = event.target;
            if (!(target instanceof HTMLButtonElement)) return;
            requestAnimationFrame(() => {
              if (document.activeElement === target) {
                target.scrollIntoView({ block: "nearest", inline: "nearest" });
              }
            });
          }}
        >
          {WEEKDAY_LABELS.map((day) => (
            <div className="month-weekday" key={day}>
              <span aria-hidden="true">{day.slice(0, 2)}</span>
              <span className="visually-hidden">{day}</span>
            </div>
          ))}
          {range.dates.map((date) => (
            <CalendarDay
              key={date}
              date={date}
              weekday={formatDateLabel(date, { weekday: "long" })}
              today={date === today}
              outsideMonth={parseCalendarDate(date).getMonth() !== parseCalendarDate(queryDate).getMonth()}
              compact
              assignments={assignmentMap}
              disabled={calendarLoading || busy}
              onEdit={openEditor}
            />
          ))}
        </div>
      )}

      {editorDate && editorSlot && draft && (
        <form className="meal-editor" onSubmit={submitPreview} aria-labelledby="meal-editor-title">
          <div className="meal-editor-heading">
            <div>
              <h3 id="meal-editor-title">{SLOT_LABELS[editorSlot]} · {formatDateLabel(editorDate, { dateStyle: "full" })}</h3>
              <p>La repetición está desactivada inicialmente. Las fechas pasadas también se pueden modificar.</p>
            </div>
            <button type="button" className="secondary" onClick={closeEditor} disabled={busy}>Cerrar</button>
          </div>

          <label>Operación
            <select value={draft.action} onChange={(event) => { setDraft({ ...draft, action: event.target.value as EditorDraft["action"] }); setPreview(null); }}>
              <option value="assign">Asignar o sustituir</option>
              <option value="delete">Eliminar esta etiqueta</option>
            </select>
          </label>
          <label>Etiqueta
            <select value={draft.labelId} onChange={(event) => { setDraft({ ...draft, labelId: event.target.value }); setPreview(null); }} required>
              {labels.map((label) => <option key={label.id} value={label.id}>{label.name}</option>)}
            </select>
          </label>
          <label>Fecha inicial
            <input type="date" value={editorDate} onChange={(event) => changeStartDate(event.target.value)} required />
          </label>
          <label className="repeat-toggle">
            <input type="checkbox" checked={draft.repeat} onChange={(event) => { setDraft({ ...draft, repeat: event.target.checked }); setPreview(null); }} />
            Repetir cada cierto número de semanas
          </label>
          {draft.repeat && (
            <div className="repeat-fields">
              <label>Intervalo en semanas
                <input type="number" min={1} step={1} value={draft.intervalWeeks} onChange={(event) => { setDraft({ ...draft, intervalWeeks: event.target.value }); setPreview(null); }} required />
              </label>
              <label>Fecha final (incluida si coincide)
                <input type="date" min={editorDate} max={annualMaximumEndDate(editorDate)} value={draft.endDate} onChange={(event) => { setDraft({ ...draft, endDate: event.target.value }); setPreview(null); }} required />
              </label>
            </div>
          )}
          <div className="button-row">
            <button type="submit" disabled={busy || labels.length === 0}>{busy ? "Calculando…" : "Previsualizar cambios"}</button>
            <button type="button" className="secondary" onClick={closeEditor} disabled={busy}>Cancelar</button>
          </div>

          {preview && (
            <div className="meal-preview" aria-live="polite">
              <h4>Revisa los cambios</h4>
              {preview.requires_confirmation && <p className="confirmation-note">Esta operación sustituye o elimina asignaciones existentes y requiere tu confirmación.</p>}
              {forceReconfirmation && <p className="confirmation-note">El estado cambió desde la vista previa anterior. Esta es la versión actualizada; vuelve a confirmar si estás de acuerdo.</p>}
              {preview.dates.length === 0 ? <p>No hay fechas que modificar.</p> : (
                <ul>
                  {preview.dates.map((entry) => (
                    <li key={`${entry.date}:${entry.slot}`}>
                      <strong>{formatDateLabel(entry.date, { dateStyle: "medium" })} · {SLOT_LABELS[entry.slot]}</strong>
                      <span>{previewChangeLabel(entry.change, entry.current_label, entry.resulting_label)}</span>
                    </li>
                  ))}
                </ul>
              )}
              <p>{preview.changed_count} cambio{preview.changed_count === 1 ? "" : "s"} previsto{preview.changed_count === 1 ? "" : "s"}.</p>
              <div className="button-row">
                <button type="button" disabled={busy} onClick={saveOperation}>
                  {preview.requires_confirmation || forceReconfirmation ? "Confirmar y guardar" : "Guardar cambios"}
                </button>
                <button type="button" className="secondary" disabled={busy} onClick={closeEditor}>Cancelar sin guardar</button>
              </div>
            </div>
          )}
        </form>
      )}
    </section>
  );
}

function CalendarDay({
  date,
  weekday,
  today,
  outsideMonth = false,
  compact = false,
  assignments,
  disabled,
  onEdit,
}: {
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
    <article className={`calendar-day${today ? " is-today" : ""}${outsideMonth ? " outside-month" : ""}${compact ? " compact-day" : ""}`}>
      <h4><span>{weekday}</span><time dateTime={date}>{formatDateLabel(date, { day: "numeric", month: compact ? undefined : "short" })}</time></h4>
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
            <span>{SLOT_LABELS[slot]}</span>
            <strong>{assignment?.label.name ?? "Sin planificar"}</strong>
          </button>
        );
      })}
    </article>
  );
}

function previewChangeLabel(
  change: string,
  current: FoodLabel | null,
  resulting: FoodLabel | null,
): string {
  if (change === "assign") return `Asignar ${resulting?.name ?? "etiqueta"}`;
  if (change === "replace") return `Sustituir ${current?.name ?? "etiqueta"} por ${resulting?.name ?? "etiqueta"}`;
  if (change === "delete") return `Eliminar ${current?.name ?? "etiqueta"}`;
  if (change === "unchanged") return `Ya tiene ${current?.name ?? "esta etiqueta"}`;
  return "Sin cambios: la etiqueta exacta no coincide";
}

function errorMessage(cause: unknown): string {
  if (cause instanceof Error) return cause.message;
  return "No se pudo completar la operación. Inténtalo de nuevo.";
}
