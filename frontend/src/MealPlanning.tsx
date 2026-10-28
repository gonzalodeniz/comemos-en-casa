import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ApiError } from "./api";
import AppIcon from "./AppIcon";
import CalendarDay from "./CalendarDay";
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
  const previewOperationRef = useRef<MealPlanningOperation | null>(null);
  const [forceReconfirmation, setForceReconfirmation] = useState(false);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const editorRef = useRef<HTMLFormElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);
  const initialDraftRef = useRef("");
  const [search, setSearch] = useState("");
  const [hadAssignment, setHadAssignment] = useState(false);
  const editorOpen = editorDate !== null && editorSlot !== null && draft !== null;
  const dirty = draft !== null && JSON.stringify({ date: editorDate, draft }) !== initialDraftRef.current;
  const filteredLabels = filterFoodLabels(labels, search);

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(""), 4000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    if (!editorOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    editorRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      openerRef.current?.focus();
    };
  }, [editorOpen]);

  useEffect(() => {
    if (editorOpen && (preview || busy)) editorRef.current?.focus();
  }, [editorOpen, preview, busy]);

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
    const nextDraft: EditorDraft = {
      action: "assign", labelId, repeat: false, intervalWeeks: "1",
      endDate: annualMaximumEndDate(date),
    };
    const active = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const closedDetails = active?.closest("details:not([open])");
    openerRef.current = closedDetails?.querySelector<HTMLElement>("summary") ?? active;
    initialDraftRef.current = JSON.stringify({ date, draft: nextDraft });
    setHadAssignment(Boolean(current));
    setSearch("");
    setEditorDate(date);
    setEditorSlot(slot);
    setDraft(nextDraft);
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

  function requestClose() {
    if (busyRef.current) return;
    if (dirty && !window.confirm("¿Descartar los cambios sin guardar?")) return;
    setError("");
    closeEditor();
  }

  function handleDrawerKeyDown(event: KeyboardEvent<HTMLFormElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      requestClose();
      return;
    }
    if (event.key !== "Tab") return;
    const items = Array.from(editorRef.current?.querySelectorAll<HTMLElement>(
      'button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex="-1"]):not(:disabled)',
    ) ?? []);
    if (!items.length) { event.preventDefault(); editorRef.current?.focus(); return; }
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && (document.activeElement === first || document.activeElement === editorRef.current)) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); first.focus();
    }
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
    const snapshot = snapshotOperation(operation);
    void runExclusive(async () => {
      const result = await previewMealPlanning(snapshot, csrfToken);
      previewOperationRef.current = snapshot;
      setPreview(result);
      setForceReconfirmation(false);
    });
  }

  function saveOperation() {
    const operation = previewOperationRef.current;
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
    ? `${formatDateLabel(range.start, { day: "numeric", month: "short", ...(range.start.slice(0, 4) !== range.end.slice(0, 4) ? { year: "numeric" } : {}) })} – ${formatDateLabel(range.end, { day: "numeric", month: "short", year: "numeric" })}`
    : formatDateLabel(queryDate, { month: "long", year: "numeric" });

  return (
    <section className="meal-planning" aria-labelledby="meal-planning-title">
      <div className="meal-heading">
        <div className="meal-title">
          <h2 id="meal-planning-title">Planificación de comidas</h2>
          <p className="meal-subtitle">{view === "week" ? `Semana del ${title}` : "Vista mensual"}</p>
        </div>
        <div className="calendar-toolbar">
          <div className="calendar-navigation">
            <button type="button" className="secondary" aria-label={view === "week" ? "Semana anterior" : "Mes anterior"} disabled={calendarLoading || busy} onClick={() => moveRange(-1)}><AppIcon name="chevron-left" /></button>
            <h3 aria-live="polite">{title}</h3>
            <button type="button" className="secondary" aria-label={view === "week" ? "Semana siguiente" : "Mes siguiente"} disabled={calendarLoading || busy} onClick={() => moveRange(1)}><AppIcon name="chevron-right" /></button>
          </div>
          <div className="meal-view-switch" role="group" aria-label="Vista del calendario">
            <button type="button" aria-pressed={view === "week"} disabled={calendarLoading || busy} onClick={() => setView("week")}>Semana</button>
            <button type="button" aria-pressed={view === "month"} disabled={calendarLoading || busy} onClick={() => setView("month")}>Mes</button>
          </div>
        </div>
      </div>
      <div className="calendar-context">
        <p className="meal-date-context">Tu menú, día a día <span aria-hidden="true">·</span> <span>Atlantic/Canary</span></p>
        <button type="button" className="secondary today-button" disabled={calendarLoading || busy} onClick={() => { setReferenceDate((today ?? localToday()) as CalendarDate); closeEditor(); }}>Volver a hoy</button>
      </div>

      {error && !editorOpen && <p className="message error" role="alert">{error}</p>}
      {notice && <p className="message success toast" role="status">{notice}</p>}
      {calendarLoading && <p role="status">Cargando planificación…</p>}

      {view === "week" ? (
        <div className="week-grid" aria-label="Planificación semanal">
          <div className="week-meal-headings">
            <span className="week-heading-spacer" aria-hidden="true" />
            <div className="week-heading-meals">
              <span><span aria-hidden="true">☀️</span><span className="week-heading-label" aria-hidden="true">Almuerzo</span><span className="visually-hidden">Almuerzo</span></span>
              <span><span aria-hidden="true">🌙</span><span className="week-heading-label" aria-hidden="true">Cena</span><span className="visually-hidden">Cena</span></span>
            </div>
            <span className="week-heading-spacer" aria-hidden="true" />
          </div>
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
        <div className="drawer-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) requestClose(); }}>
          <form className="meal-editor" ref={editorRef} tabIndex={-1} onSubmit={submitPreview}
            onKeyDown={handleDrawerKeyDown} role="dialog" aria-modal="true" aria-labelledby="meal-editor-title" aria-describedby="meal-editor-subtitle">
            <div className="meal-editor-heading">
              <div>
                <h3 id="meal-editor-title">{hadAssignment ? "Editar comida" : "Añadir comida"}</h3>
                <p id="meal-editor-subtitle">{formatDateLabel(editorDate, { dateStyle: "full" })} · {SLOT_LABELS[editorSlot]}</p>
              </div>
              <button type="button" className="drawer-close secondary" onClick={requestClose} disabled={busy} aria-label="Cerrar editor">×</button>
            </div>
            <div className="drawer-content">
              {error && <p className="message error" role="alert">{error}</p>}
              {preview ? (
                <div className="meal-preview" aria-live="polite">
                  <h4>Revisa los cambios</h4>
                  {preview.requires_confirmation && <p className="confirmation-note">Esta operación sustituye o elimina asignaciones existentes y requiere tu confirmación.</p>}
                  {forceReconfirmation && <p className="confirmation-note">El estado cambió desde la vista previa anterior. Esta es la versión actualizada; vuelve a confirmar si estás de acuerdo.</p>}
                  {preview.dates.length === 0 ? <p>No hay fechas que modificar.</p> : (
                    <ul>{preview.dates.map((entry) => (
                      <li key={`${entry.date}:${entry.slot}`}>
                        <strong>{formatDateLabel(entry.date, { dateStyle: "medium" })} · {SLOT_LABELS[entry.slot]}</strong>
                        <span>{previewChangeLabel(entry.change, entry.current_label, entry.resulting_label)}</span>
                      </li>
                    ))}</ul>
                  )}
                  <p>{preview.changed_count} cambio{preview.changed_count === 1 ? "" : "s"} previsto{preview.changed_count === 1 ? "" : "s"}.</p>
                </div>
              ) : <fieldset className="drawer-edit-fields" disabled={busy}>
                <label>Operación
                  <select value={draft.action} onChange={(event) => { setDraft({ ...draft, action: event.target.value as EditorDraft["action"] }); setPreview(null); }}>
                    <option value="assign">Asignar o sustituir</option>
                    <option value="delete">Eliminar esta etiqueta</option>
                  </select>
                </label>
                <label className="dish-search">Buscar plato
                  <span><span aria-hidden="true">⌕</span><input type="search" placeholder="Buscar plato..." value={search} onChange={(event) => setSearch(event.target.value)} /></span>
                </label>
                <fieldset className="dish-selector">
                  <legend>Plato</legend>
                  {filteredLabels.length === 0 ? <p>No se encontraron platos.</p> : <div className="dish-grid">
                    {filteredLabels.map((label) => (
                      <button type="button" key={label.id} className={`dish-card${draft.labelId === label.id ? " selected" : ""}`}
                        aria-pressed={draft.labelId === label.id} onClick={() => { setDraft({ ...draft, labelId: label.id }); setPreview(null); }}>
                        <span className="dish-image" aria-hidden="true"><AppIcon name="utensils" /></span>
                        <strong>{label.name}</strong>
                        {draft.labelId === label.id && <span className="dish-check" aria-hidden="true">✓</span>}
                      </button>
                    ))}
                  </div>}
                </fieldset>
                <label>Fecha
                  <input type="date" value={editorDate} onChange={(event) => changeStartDate(event.target.value)} required />
                </label>
                <label className="repeat-toggle">
                  <input type="checkbox" role="switch" checked={draft.repeat} onChange={(event) => { setDraft({ ...draft, repeat: event.target.checked }); setPreview(null); }} />
                  <span>Repetir cada cierto número de semanas</span>
                </label>
                {draft.repeat && <div className="repeat-fields">
                  <label>Intervalo en semanas
                    <input type="number" min={1} step={1} value={draft.intervalWeeks} onChange={(event) => { setDraft({ ...draft, intervalWeeks: event.target.value }); setPreview(null); }} required />
                  </label>
                  <label>Fecha final (incluida si coincide)
                    <input type="date" min={editorDate} max={annualMaximumEndDate(editorDate)} value={draft.endDate} onChange={(event) => { setDraft({ ...draft, endDate: event.target.value }); setPreview(null); }} required />
                  </label>
                </div>}
              </fieldset>}
            </div>
            <div className="drawer-actions">
              {preview ? <>
                <button type="button" className="secondary" disabled={busy} onClick={() => setPreview(null)}>Volver a editar</button>
                <button type="button" disabled={busy} onClick={saveOperation}>{busy ? "Guardando…" : "Confirmar y guardar"}</button>
              </> : <>
                <button type="button" className="secondary" onClick={requestClose} disabled={busy}>Cancelar</button>
                <button type="submit" disabled={busy || labels.length === 0}>{busy ? "Calculando…" : "Previsualizar cambios"}</button>
              </>}
            </div>
          </form>
        </div>
      )}
    </section>
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

export function filterFoodLabels(labels: FoodLabel[], search: string): FoodLabel[] {
  const query = search.trim().toLocaleLowerCase("es");
  return labels.filter((label) => label.name.toLocaleLowerCase("es").includes(query));
}

export function snapshotOperation(operation: MealPlanningOperation): MealPlanningOperation {
  return { ...operation, repeat: operation.repeat ? { ...operation.repeat } : null };
}
