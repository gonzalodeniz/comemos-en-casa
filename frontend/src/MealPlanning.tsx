import { useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
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
  intervalWeeks: string;
  endDate: string;
};

type Props = { csrfToken: string; onSessionExpired: () => void };

const SLOT_LABELS: Record<MealSlot, string> = { lunch: "Almuerzo", dinner: "Cena" };
const WEEKDAY_LABELS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const MAX_LOADED_WEEKS = 26;

export function adjacentWeek(starts: CalendarDate[], direction: -1 | 1): CalendarDate {
  return addCalendarDays(direction === -1 ? starts[0] : starts[starts.length - 1], direction * 7);
}

export function extendWeeks(starts: CalendarDate[], direction: -1 | 1): CalendarDate[] {
  const adjacent = adjacentWeek(starts, direction);
  return direction === -1
    ? [adjacent, ...starts].slice(0, MAX_LOADED_WEEKS)
    : [...starts, adjacent].slice(-MAX_LOADED_WEEKS);
}

export function weekLabel(start: CalendarDate): string {
  const end = addCalendarDays(start, 6);
  const sameMonth = start.slice(0, 7) === end.slice(0, 7);
  const sameYear = start.slice(0, 4) === end.slice(0, 4);
  return `Semana del ${formatDateLabel(start, { day: "numeric", ...(!sameMonth ? { month: "long" as const } : {}), ...(!sameYear ? { year: "numeric" as const } : {}) })} al ${formatDateLabel(end, { day: "numeric", month: "long", year: "numeric" })}`;
}

export default function MealPlanning({ csrfToken, onSessionExpired }: Props) {
  const [view, setView] = useState<CalendarView>("week");
  const [referenceDate, setReferenceDate] = useState<CalendarDate | null>(null);
  const queryDate = referenceDate ?? localToday();
  const range = useMemo(() => visibleDateRange(queryDate, view), [queryDate, view]);
  const [today, setToday] = useState<string | null>(null);
  const [labels, setLabels] = useState<FoodLabel[]>([]);
  const [assignments, setAssignments] = useState<MealAssignment[]>([]);
  const [calendarLoading, setCalendarLoading] = useState(true);
  const [mainLoadError, setMainLoadError] = useState(false);
  const [weekStarts, setWeekStarts] = useState<CalendarDate[]>(() => [visibleDateRange(localToday(), "week").start]);
  const weekStartsRef = useRef(weekStarts);
  const [edgeLoading, setEdgeLoading] = useState(false);
  const [edgeError, setEdgeError] = useState<"previous" | "next" | null>(null);
  const [observerAvailable, setObserverAvailable] = useState(true);
  const edgeBusyRef = useRef(false);
  const generationRef = useRef(0);
  const weekListRef = useRef<HTMLDivElement>(null);
  const topSentinelRef = useRef<HTMLDivElement>(null);
  const bottomSentinelRef = useRef<HTMLDivElement>(null);
  const scrollAnchorRef = useRef<{ start: CalendarDate; top: number } | null>(null);
  const todayScrollRef = useRef<CalendarDate | null>(null);
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
  const [search, setSearch] = useState("");
  const editorOpen = editorDate !== null && editorSlot !== null && draft !== null;
  const filteredLabels = filterFoodLabels(labels, search);

  useEffect(() => { setObserverAvailable(typeof IntersectionObserver !== "undefined"); }, []);

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
    const generation = ++generationRef.current;
    let cancelled = false;
    edgeBusyRef.current = false;
    setEdgeLoading(false);
    setEdgeError(null);
    setCalendarLoading(true);
    const start = view === "week" ? weekStartsRef.current[0] : range.start;
    const end = view === "week" ? addCalendarDays(weekStartsRef.current[weekStartsRef.current.length - 1], 6) : range.end;
    void getMealPlanning(start, end)
      .then((result) => {
        if (cancelled || generation !== generationRef.current) return;
        setAssignments(result.assignments);
        setToday(result.today);
        if (referenceDate === null) {
          const serverToday = result.today as CalendarDate;
          const serverWeek = visibleDateRange(serverToday, "week").start;
          if (view === "week" && serverWeek !== weekStartsRef.current[0]) {
            weekStartsRef.current = [serverWeek];
            setWeekStarts([serverWeek]);
          }
          setReferenceDate(serverToday);
        }
        setMainLoadError(false);
        setError("");
      })
      .catch((cause: unknown) => {
        if (cancelled || generation !== generationRef.current) return;
        if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
        else { setMainLoadError(true); setError(errorMessage(cause)); }
      })
      .finally(() => {
        if (!cancelled && generation === generationRef.current) setCalendarLoading(false);
      });
    return () => { cancelled = true; if (generationRef.current === generation) generationRef.current += 1; };
  }, [view, range.start, range.end, referenceDate, revision, onSessionExpired]);

  useLayoutEffect(() => {
    const anchor = scrollAnchorRef.current;
    if (anchor) {
      const element = weekListRef.current?.querySelector<HTMLElement>(`[data-week-start="${anchor.start}"]`);
      if (element) weekListRef.current?.closest<HTMLElement>(".workspace-content")?.scrollBy(0, element.getBoundingClientRect().top - anchor.top);
      scrollAnchorRef.current = null;
    }
    if (todayScrollRef.current && view === "week") {
      const date = todayScrollRef.current;
      todayScrollRef.current = null;
      window.requestAnimationFrame(() => {
        const row = weekListRef.current?.querySelector<HTMLTimeElement>(`time[datetime="${date}"]`)?.closest<HTMLElement>(".calendar-day");
        const scrollRoot = weekListRef.current?.closest<HTMLElement>(".workspace-content");
        const header = scrollRoot?.querySelector<HTMLElement>(".planning-sticky-header");
        if (row && scrollRoot && header) {
          const rowRect = row.getBoundingClientRect();
          const visibleCenter = (header.getBoundingClientRect().bottom + scrollRoot.getBoundingClientRect().bottom) / 2;
          scrollRoot.scrollBy(0, rowRect.top + rowRect.height / 2 - visibleCenter);
        }
      });
    }
  }, [weekStarts, view]);

  async function loadAdjacentWeek(direction: -1 | 1) {
    if (view !== "week" || calendarLoading || mainLoadError || edgeBusyRef.current || editorOpen || busyRef.current) return;
    const generation = generationRef.current;
    const start = adjacentWeek(weekStartsRef.current, direction);
    edgeBusyRef.current = true;
    setEdgeLoading(true);
    setEdgeError(null);
    setError("");
    try {
      const result = await getMealPlanning(start, addCalendarDays(start, 6));
      if (generation !== generationRef.current) return;
      const currentWeeks = weekStartsRef.current;
      const next = extendWeeks(currentWeeks, direction);
      if (direction === -1 || next[0] !== currentWeeks[0]) {
        const anchor = direction === -1 ? currentWeeks[0] : next[0];
        const element = weekListRef.current?.querySelector<HTMLElement>(`[data-week-start="${anchor}"]`);
        if (element) scrollAnchorRef.current = { start: anchor, top: element.getBoundingClientRect().top };
      }
      weekStartsRef.current = next;
      const lastDate = addCalendarDays(next[next.length - 1], 6);
      setAssignments((current) => [...current, ...result.assignments].filter((assignment) => assignment.date >= next[0] && assignment.date <= lastDate));
      setWeekStarts(next);
      setToday(result.today);
    } catch (cause: unknown) {
      if (generation !== generationRef.current) return;
      if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
      else { setEdgeError(direction === -1 ? "previous" : "next"); setError(errorMessage(cause)); }
    } finally {
      if (generation === generationRef.current) { edgeBusyRef.current = false; setEdgeLoading(false); }
    }
  }

  useEffect(() => {
    if (view !== "week" || calendarLoading || mainLoadError || edgeLoading || editorOpen || edgeError || typeof IntersectionObserver === "undefined") return;
    const scrollRoot = weekListRef.current?.closest<HTMLElement>(".workspace-content");
    if (!scrollRoot) return;
    let lastY = scrollRoot.scrollTop;
    let movingUp = false;
    let touchY = 0;
    const nearTop = () => {
      const rect = topSentinelRef.current?.getBoundingClientRect();
      const rootRect = scrollRoot.getBoundingClientRect();
      return !!rect && rect.top <= rootRect.bottom + 200 && rect.bottom >= rootRect.top - 200;
    };
    const handleScroll = () => { movingUp = scrollRoot.scrollTop < lastY; lastY = scrollRoot.scrollTop; };
    const handleWheel = (event: WheelEvent) => { if (event.deltaY < 0 && nearTop()) void loadAdjacentWeek(-1); };
    const handleTouchStart = (event: TouchEvent) => { touchY = event.touches[0]?.clientY ?? 0; };
    const handleTouchMove = (event: TouchEvent) => {
      const nextY = event.touches[0]?.clientY ?? touchY;
      if (nextY > touchY && nearTop()) void loadAdjacentWeek(-1);
      touchY = nextY;
    };
    const handleKey = (event: globalThis.KeyboardEvent) => {
      if (["ArrowUp", "PageUp", "Home"].includes(event.key) && nearTop()) void loadAdjacentWeek(-1);
    };
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        if (entry.target === topSentinelRef.current && movingUp) void loadAdjacentWeek(-1);
        else if (entry.target === bottomSentinelRef.current) void loadAdjacentWeek(1);
      }
    }, { root: scrollRoot, rootMargin: "200px 0px" });
    if (topSentinelRef.current) observer.observe(topSentinelRef.current);
    if (bottomSentinelRef.current) observer.observe(bottomSentinelRef.current);
    scrollRoot.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("wheel", handleWheel, { passive: true });
    window.addEventListener("touchstart", handleTouchStart, { passive: true });
    window.addEventListener("touchmove", handleTouchMove, { passive: true });
    window.addEventListener("keydown", handleKey);
    return () => {
      observer.disconnect();
      scrollRoot.removeEventListener("scroll", handleScroll);
      window.removeEventListener("wheel", handleWheel);
      window.removeEventListener("touchstart", handleTouchStart);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("keydown", handleKey);
    };
  });

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
      return shiftMonthClamped(from, direction);
    });
    closeEditor();
  }

  function changeView(next: CalendarView) {
    if (next === view) return;
    generationRef.current += 1;
    edgeBusyRef.current = false;
    scrollAnchorRef.current = null;
    if (next === "week") {
      const current = (today ?? localToday()) as CalendarDate;
      const start = visibleDateRange(current, "week").start;
      weekStartsRef.current = [start];
      setWeekStarts([start]);
      setReferenceDate(current);
      todayScrollRef.current = current;
    } else {
      const visibleDay = Array.from(weekListRef.current?.querySelectorAll<HTMLElement>(".calendar-day") ?? [])
        .find((day) => { const rect = day.getBoundingClientRect(); return rect.bottom > 0 && rect.top < window.innerHeight; });
      const date = visibleDay?.querySelector<HTMLTimeElement>("time")?.dateTime;
      if (date) setReferenceDate(date as CalendarDate);
    }
    setView(next);
    closeEditor();
  }

  function returnToToday() {
    const current = (today ?? localToday()) as CalendarDate;
    if (view === "week") {
      generationRef.current += 1;
      edgeBusyRef.current = false;
      scrollAnchorRef.current = null;
      const start = visibleDateRange(current, "week").start;
      weekStartsRef.current = [start];
      setWeekStarts([start]);
      todayScrollRef.current = current;
      setRevision((value) => value + 1);
    }
    setReferenceDate(current);
    closeEditor();
  }

  function openEditor(date: CalendarDate, slot: MealSlot) {
    const current = assignmentMap.get(`${date}:${slot}`);
    const labelId = current?.label.id ?? labels[0]?.id ?? "";
    const nextDraft: EditorDraft = {
      action: "assign", labelId, intervalWeeks: "0",
      endDate: annualMaximumEndDate(date),
    };
    const active = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const closedDetails = active?.closest("details:not([open])");
    openerRef.current = closedDetails?.querySelector<HTMLElement>("summary") ?? active;
    setSearch("");
    setEditorDate(date);
    setEditorSlot(slot);
    setDraft(nextDraft);
    setPreview(null);
    setForceReconfirmation(false);
    setError("");
    setNotice("");
  }

  function openDeletePreview(date: CalendarDate, slot: MealSlot) {
    const current = assignmentMap.get(`${date}:${slot}`);
    if (!current || busyRef.current) return;
    const nextDraft: EditorDraft = {
      action: "delete", labelId: current.label.id, intervalWeeks: "0",
      endDate: annualMaximumEndDate(date),
    };
    const operation: MealPlanningOperation = {
      action: "delete", start_date: date, slot, label_id: current.label.id, repeat: null,
    };
    const active = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    openerRef.current = active;
    setSearch("");
    setEditorDate(date);
    setEditorSlot(slot);
    setDraft(nextDraft);
    setPreview(null);
    previewOperationRef.current = null;
    setForceReconfirmation(false);
    setError("");
    setNotice("");
    const snapshot = snapshotOperation(operation);
    void runExclusive(async () => {
      const result = await previewMealPlanning(snapshot, csrfToken);
      previewOperationRef.current = snapshot;
      setPreview(result);
    });
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

  function operationFromDraft(): MealPlanningOperation | null {
    if (!draft || !editorDate || !editorSlot || !draft.labelId) return null;
    return {
      action: draft.action,
      start_date: editorDate,
      slot: editorSlot,
      label_id: draft.labelId,
      repeat: repeatFromInterval(draft.intervalWeeks, draft.endDate),
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
      if (!result.requires_confirmation) {
        const saved = await applyMealPlanning(snapshot, result.preview_token, csrfToken);
        closeEditor();
        setNotice(saved.changed_count === 0 ? "No había cambios que guardar." : `Se guardaron ${saved.changed_count} cambio${saved.changed_count === 1 ? "" : "s"}.`);
        setRevision((value) => value + 1);
        return;
      }
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

  const title = formatDateLabel(queryDate, { month: "long", year: "numeric" });

  return (
    <section className="meal-planning" aria-labelledby="meal-planning-title">
      <div className={view === "week" ? "planning-sticky-header" : undefined}>
      <div className="meal-heading">
        <div className="meal-title">
          <h2 id="meal-planning-title">Planificación de comidas</h2>
          {view === "month" && <p className="meal-subtitle">Vista mensual</p>}
        </div>
        <div className="calendar-toolbar">
          {view === "month" && <div className="calendar-navigation">
            <button type="button" className="secondary" aria-label="Mes anterior" disabled={calendarLoading || busy} onClick={() => moveRange(-1)}><AppIcon name="chevron-left" /></button>
            <h3 aria-live="polite">{title}</h3>
            <button type="button" className="secondary" aria-label="Mes siguiente" disabled={calendarLoading || busy} onClick={() => moveRange(1)}><AppIcon name="chevron-right" /></button>
          </div>}
          <div className="meal-view-switch" role="group" aria-label="Vista del calendario">
            <button type="button" aria-pressed={view === "week"} disabled={calendarLoading || busy} onClick={() => changeView("week")}>Semana</button>
            <button type="button" aria-pressed={view === "month"} disabled={calendarLoading || busy} onClick={() => changeView("month")}>Mes</button>
          </div>
        </div>
      </div>
      <div className="calendar-context">
        <p className="meal-date-context">Tu menú, día a día <span aria-hidden="true">·</span> <span>Atlantic/Canary</span></p>
        <button type="button" className={`secondary today-button${view === "week" ? " today-button-fixed" : ""}`} disabled={calendarLoading || busy} onClick={returnToToday}>Volver a hoy</button>
      </div>
      {view === "week" && <div className="week-meal-headings">
        <span className="week-heading-spacer" aria-hidden="true" />
        <div className="week-heading-meals">
          <span><span aria-hidden="true">☀️</span><span className="week-heading-label" aria-hidden="true">Almuerzo</span><span className="visually-hidden">Almuerzo</span></span>
          <span><span aria-hidden="true">🌙</span><span className="week-heading-label" aria-hidden="true">Cena</span><span className="visually-hidden">Cena</span></span>
        </div>
      </div>}
      </div>

      {error && !editorOpen && <p className="message error" role="alert">{error}</p>}
      {mainLoadError && !editorOpen && <button type="button" className="secondary" disabled={calendarLoading} onClick={() => setRevision((value) => value + 1)}>Reintentar cargar planificación</button>}
      {notice && <p className="message success toast" role="status">{notice}</p>}
      {calendarLoading && <p role="status">Cargando planificación…</p>}

      {view === "week" ? (
        <div className="week-scroll-content" ref={weekListRef} aria-label="Planificación semanal">
          <div ref={topSentinelRef} className="week-sentinel" aria-hidden="true" />
          {(edgeError === "previous" || !observerAvailable) && <button type="button" className="secondary week-retry" disabled={calendarLoading || edgeLoading || busy} onClick={() => void loadAdjacentWeek(-1)}>{edgeError === "previous" ? "Reintentar semanas anteriores" : "Cargar semana anterior"}</button>}
          {weekStarts.map((start) => (
            <section className="week-grid week-section" data-week-start={start} key={start} aria-label={weekLabel(start)}>
              <h3 className="week-separator">{weekLabel(start)}</h3>
              {visibleDateRange(start, "week").dates.map((date, index) => (
                <CalendarDay key={date} date={date} weekday={WEEKDAY_LABELS[index]} today={date === today}
                  assignments={assignmentMap} disabled={calendarLoading || mainLoadError || busy} onEdit={openEditor} onDelete={openDeletePreview} />
              ))}
            </section>
          ))}
          {(edgeError === "next" || !observerAvailable) && <button type="button" className="secondary week-retry" disabled={calendarLoading || edgeLoading || busy} onClick={() => void loadAdjacentWeek(1)}>{edgeError === "next" ? "Reintentar semanas siguientes" : "Cargar semana siguiente"}</button>}
          {edgeLoading && <p role="status" className="week-loading">Cargando semana…</p>}
          <div ref={bottomSentinelRef} className="week-sentinel" aria-hidden="true" />
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
              disabled={calendarLoading || mainLoadError || busy}
              onEdit={openEditor}
              onDelete={openDeletePreview}
            />
          ))}
        </div>
      )}

      {editorDate && editorSlot && draft && (
        <div className="drawer-overlay">
          <form className="meal-editor" ref={editorRef} tabIndex={-1} onSubmit={submitPreview}
            onKeyDown={handleDrawerKeyDown} role="dialog" aria-modal="true" aria-labelledby="meal-editor-title" aria-describedby="meal-editor-subtitle">
            <div className="meal-editor-heading">
              <div>
                <h3 id="meal-editor-title">Asignar comida</h3>
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
                <div className="repeat-panel">
                  <label className="repeat-toggle"><AppIcon name="repeat" /><strong>Repetir</strong><input type="checkbox" role="switch" checked={Number(draft.intervalWeeks) > 0} onChange={(event) => { setDraft({ ...draft, intervalWeeks: event.target.checked ? "1" : "0" }); setPreview(null); }} /></label>
                  <div className="repeat-fields">
                    <label>Cada<input type="number" min={1} step={1} aria-label="Intervalo en semanas" value={Number(draft.intervalWeeks) > 0 ? draft.intervalWeeks : ""} disabled={Number(draft.intervalWeeks) <= 0} onChange={(event) => { setDraft({ ...draft, intervalWeeks: Number(event.target.value) > 0 ? event.target.value : "1" }); setPreview(null); }} required={Number(draft.intervalWeeks) > 0} /><span>semanas</span></label>
                    <label>Hasta<input type="date" aria-label="Fecha final" min={editorDate} max={annualMaximumEndDate(editorDate)} value={draft.endDate} disabled={Number(draft.intervalWeeks) <= 0} onChange={(event) => { setDraft({ ...draft, endDate: event.target.value }); setPreview(null); }} required={Number(draft.intervalWeeks) > 0} /></label>
                  </div>
                  <p className="repeat-summary">{Number(draft.intervalWeeks) > 0 ? `Se repetirá cada ${draft.intervalWeeks} semana${Number(draft.intervalWeeks) === 1 ? "" : "s"}${draft.endDate ? ` hasta el ${formatDateLabel(draft.endDate, { dateStyle: "long" })}` : ""}.` : "No se repetirá esta comida."}</p>
                </div>
                <label className="dish-search">
                  <span className="visually-hidden">Buscar plato</span>
                  <span><input type="search" placeholder="Buscar plato..." value={search} onChange={(event) => setSearch(event.target.value)} /></span>
                </label>
                <fieldset className="dish-selector">
                  <legend>Plato</legend>
                  {filteredLabels.length === 0 ? <p>No se encontraron platos.</p> : <div className="dish-grid">
                    {filteredLabels.map((label) => (
                      <button type="button" key={label.id} className={`dish-card${draft.labelId === label.id ? " selected" : ""}`}
                        aria-pressed={draft.labelId === label.id} onClick={() => { setDraft({ ...draft, labelId: label.id }); setPreview(null); }}>
                        <span className="dish-image" aria-hidden="true">{label.image_url ? <img src={`${import.meta.env.VITE_API_BASE_URL || "/comemos"}/api/v1${label.image_url}`} alt="" /> : <AppIcon name="utensils" />}</span>
                        <strong>{label.name}</strong>
                        {draft.labelId === label.id && <span className="dish-check" aria-hidden="true">✓</span>}
                      </button>
                    ))}
                  </div>}
                </fieldset>
              </fieldset>}
            </div>
            <div className="drawer-actions">
              {preview ? <>
                <button type="button" className="secondary" disabled={busy} onClick={() => setPreview(null)}>Volver a editar</button>
                <button type="button" disabled={busy} onClick={saveOperation}>{busy ? "Guardando…" : "Confirmar y guardar"}</button>
              </> : <>
                <button type="button" className="secondary" onClick={requestClose} disabled={busy}>Cancelar</button>
                <button type="submit" disabled={busy || labels.length === 0}>{busy ? "Guardando…" : "Guardar"}</button>
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

export function repeatFromInterval(intervalWeeks: string, endDate: string): MealPlanningOperation["repeat"] {
  const interval = Number(intervalWeeks);
  return interval > 0 ? { interval_weeks: interval, end_date: endDate } : null;
}
