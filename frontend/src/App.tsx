import { FormEvent, useEffect, useReducer, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  ApiError,
  createAssignment,
  deleteAssignment,
  getCalendarContext,
  getCalendarWeek,
  getPublicRecipe,
  searchPublicRecipes,
  updateAssignment,
} from "./api";
import { calendarReducer, initialCalendarState } from "./calendarReducer";
import type { AssignmentWritePayload, CalendarAssignment, MealSlot, RecipeDetail } from "./types";

const mealRows: Array<{ slot: MealSlot; label: string }> = [
  { slot: "lunch", label: "Lunch" },
  { slot: "dinner", label: "Dinner" },
];

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Unable to reach the calendar. Please try again.";
}

function toDate(value: string): Date {
  return new Date(`${value}T12:00:00`);
}

function toIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function shiftWeek(weekStart: string, amount: number): string {
  const date = toDate(weekStart);
  date.setDate(date.getDate() + amount * 7);
  return toIsoDate(date);
}

function weekDays(weekStart: string): string[] {
  return Array.from({ length: 7 }, (_, offset) => {
    const date = toDate(weekStart);
    date.setDate(date.getDate() + offset);
    return toIsoDate(date);
  });
}

function dayLabel(value: string): string {
  return new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric", month: "short" }).format(toDate(value));
}

function weekLabel(weekStart: string): string {
  const dates = weekDays(weekStart);
  const formatter = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
  return `${formatter.format(toDate(dates[0]))} – ${formatter.format(toDate(dates[6]))}`;
}

function normalizeFreeText(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function AssignmentCard({
  assignment,
  deleting,
  onEdit,
  onDelete,
}: {
  assignment: CalendarAssignment;
  deleting: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const title = assignment.kind === "recipe" ? assignment.recipe?.title : assignment.text;
  const imageUrl = assignment.kind === "recipe" ? assignment.recipe?.coverImageUrl : null;
  const recipeId = assignment.kind === "recipe" && assignment.recipe?.available ? assignment.recipe.id : null;

  return (
    <article className="assignment-card">
      {imageUrl ? <img className="assignment-image" src={imageUrl} alt="" /> : null}
      <span>{title ?? "Meal unavailable"}</span>
      {assignment.kind === "recipe" && !assignment.recipe?.available ? <small>Recipe unavailable</small> : null}
      <div className="assignment-actions">
        {recipeId ? <Link to={`/recipes/${recipeId}`}>View recipe</Link> : null}
        <button type="button" className="text-button" onClick={onEdit} disabled={deleting}>Edit</button>
        <button type="button" className="danger-button" onClick={onDelete} disabled={deleting}>
          {deleting ? "Deleting…" : "Delete"}
        </button>
      </div>
    </article>
  );
}

function RecipeDetailPage() {
  const { recipeId } = useParams();
  const [detail, setDetail] = useState<{ status: "loading" | "ready" | "error"; data: RecipeDetail | null; error: string | null }>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    if (!recipeId) return;
    const controller = new AbortController();
    setDetail({ status: "loading", data: null, error: null });
    getPublicRecipe(recipeId, controller.signal)
      .then((recipe) => setDetail({ status: "ready", data: recipe, error: null }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDetail({ status: "error", data: null, error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [recipeId]);

  return (
    <main className="app-shell detail-page">
      <Link className="back-link" to="/">← Back to calendar</Link>
      {detail.status === "loading" ? <p className="loading-state" role="status">Loading recipe…</p> : null}
      {detail.status === "error" ? <p className="notice error-notice" role="alert">{detail.error}</p> : null}
      {detail.data ? (
        <article className="recipe-detail">
          <img src={detail.data.coverImageUrl} alt="" />
          <div>
            <p className="eyebrow">Public recipe</p>
            <h1>{detail.data.title}</h1>
            <p>{detail.data.detail}</p>
          </div>
        </article>
      ) : null}
    </main>
  );
}

function CalendarPage() {
  const { weekStart: weekStartFromPath } = useParams();
  const navigate = useNavigate();
  const [state, dispatch] = useReducer(calendarReducer, initialCalendarState);
  const [reloadVersion, setReloadVersion] = useState(0);
  const activeWeekStart = weekStartFromPath ?? state.context.data?.currentWeekStart;

  useEffect(() => {
    const controller = new AbortController();
    dispatch({ type: "context/loading" });
    getCalendarContext(controller.signal)
      .then((context) => dispatch({ type: "context/success", payload: context }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        dispatch({ type: "context/error", payload: errorMessage(error) });
      });
    return () => controller.abort();
  }, [reloadVersion]);

  useEffect(() => {
    if (!activeWeekStart) return;
    const controller = new AbortController();
    dispatch({ type: "week/loading" });
    getCalendarWeek(activeWeekStart, controller.signal)
      .then((week) => dispatch({ type: "week/success", payload: week }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        dispatch({ type: "week/error", payload: errorMessage(error) });
      });
    return () => controller.abort();
  }, [activeWeekStart, reloadVersion]);

  function retryCalendar() {
    setReloadVersion((version) => version + 1);
  }

  function navigateWeek(amount: number) {
    if (activeWeekStart) navigate(`/weeks/${shiftWeek(activeWeekStart, amount)}`);
  }

  function openCurrentWeek() {
    if (state.context.data) navigate(`/weeks/${state.context.data.currentWeekStart}`);
  }

  async function submitRecipeSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    dispatch({ type: "recipes/loading" });
    try {
      const results = await searchPublicRecipes(state.recipeQuery);
      dispatch({ type: "recipes/success", payload: results });
    } catch (error: unknown) {
      dispatch({ type: "recipes/error", payload: errorMessage(error) });
    }
  }

  async function saveAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const editor = state.editor;
    if (!editor || state.mutation.status === "loading") return;

    let payload: AssignmentWritePayload;
    if (editor.kind === "recipe") {
      if (!state.selectedRecipe) {
        dispatch({ type: "mutation/error", payload: "Choose a public recipe from the search results before saving." });
        return;
      }
      payload = { date: editor.date, slot: editor.slot, kind: "recipe", recipeId: state.selectedRecipe.id };
    } else {
      const text = normalizeFreeText(editor.freeText);
      if (!text) {
        dispatch({ type: "mutation/error", payload: "Enter a meal description before saving." });
        return;
      }
      dispatch({ type: "editor/freeTextChanged", payload: text });
      payload = { date: editor.date, slot: editor.slot, kind: "free_text", text };
    }

    const assignmentId = editor.assignmentId;
    const isEditing = assignmentId !== null;
    dispatch({ type: "mutation/loading", payload: { type: isEditing ? "update" : "create", assignmentId } });
    try {
      const assignment = assignmentId
        ? await updateAssignment(assignmentId, payload)
        : await createAssignment({ ...payload, id: crypto.randomUUID() });
      dispatch({ type: "week/assignmentSaved", payload: assignment });
      dispatch({ type: "mutation/success", payload: isEditing ? "Meal assignment updated." : "Meal assignment saved." });
      dispatch({ type: "editor/close" });
    } catch (error: unknown) {
      dispatch({ type: "mutation/error", payload: errorMessage(error) });
    }
  }

  async function removeAssignment(assignment: CalendarAssignment) {
    if (state.mutation.status === "loading") return;
    if (!window.confirm(`Delete ${assignment.kind === "recipe" ? assignment.recipe?.title : assignment.text ?? "this meal"}?`)) return;

    dispatch({ type: "mutation/loading", payload: { type: "delete", assignmentId: assignment.id } });
    try {
      await deleteAssignment(assignment.id);
      dispatch({ type: "week/assignmentDeleted", payload: assignment.id });
      dispatch({ type: "mutation/success", payload: "Meal assignment deleted." });
      if (state.editor?.assignmentId === assignment.id) dispatch({ type: "editor/close" });
    } catch (error: unknown) {
      dispatch({ type: "mutation/error", payload: errorMessage(error) });
    }
  }

  const assignments = state.week.data?.assignments ?? [];
  const days = activeWeekStart ? weekDays(activeWeekStart) : [];
  const editor = state.editor;
  const isSaving = state.mutation.status === "loading" && (state.mutation.type === "create" || state.mutation.type === "update");
  const canChooseRecipe = !editor || editor.kind === "recipe";

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Shared meal planning</p>
          <h1>Comemos en casa</h1>
          <p className="intro">See the week at a glance and browse recipes that are public to everyone.</p>
        </div>
        {state.context.data?.guestMode ? <p className="guest-banner" role="status">Guest mode is on: this calendar is shared with every visitor.</p> : null}
      </header>

      <section className="calendar-section" aria-labelledby="calendar-title">
        <div className="section-heading">
          <div>
            <h2 id="calendar-title">Weekly calendar</h2>
            <p>{activeWeekStart ? weekLabel(activeWeekStart) : "Loading current week…"}</p>
          </div>
          <div className="week-controls" aria-label="Week navigation">
            <button type="button" onClick={() => navigateWeek(-1)} disabled={!activeWeekStart}>Previous week</button>
            <button type="button" onClick={openCurrentWeek} disabled={!state.context.data}>Current week</button>
            <button type="button" onClick={() => navigateWeek(1)} disabled={!activeWeekStart}>Next week</button>
          </div>
        </div>

        {state.context.status === "error" ? <div className="notice error-notice" role="alert"><p>{state.context.error}</p><button type="button" onClick={retryCalendar}>Retry</button></div> : null}
        {state.week.status === "error" ? <div className="notice error-notice" role="alert"><p>{state.week.error}</p><button type="button" onClick={retryCalendar}>Retry</button></div> : null}
        {state.context.status === "loading" || state.week.status === "loading" ? <p className="loading-state" role="status">Loading calendar…</p> : null}

        {activeWeekStart && state.week.status === "ready" ? (
          <div className="calendar-scroll">
            <table className="calendar-grid">
              <thead><tr><th scope="col">Meal</th>{days.map((day) => <th scope="col" key={day}>{dayLabel(day)}</th>)}</tr></thead>
              <tbody>
                {mealRows.map(({ slot, label }) => (
                  <tr key={slot}>
                    <th scope="row">{label}</th>
                    {days.map((day) => {
                      const cellAssignments = assignments.filter((assignment) => assignment.date === day && assignment.slot === slot);
                      const selected = editor?.date === day && editor.slot === slot;
                      return (
                        <td className={selected ? "selected-calendar-cell" : undefined} key={`${day}-${slot}`}>
                          {cellAssignments.length > 0 ? cellAssignments.map((assignment) => (
                            <AssignmentCard
                              key={assignment.id}
                              assignment={assignment}
                              deleting={state.mutation.status === "loading" && state.mutation.type === "delete" && state.mutation.assignmentId === assignment.id}
                              onEdit={() => dispatch({ type: "editor/openEdit", payload: assignment })}
                              onDelete={() => void removeAssignment(assignment)}
                            />
                          )) : <span className="empty-cell">No plan</span>}
                          <button type="button" className="add-assignment" onClick={() => dispatch({ type: "editor/openCreate", payload: { date: day, slot } })}>
                            Add meal
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {state.mutation.status === "success" ? <p className="notice success-notice" role="status">{state.mutation.message}</p> : null}
        {state.mutation.status === "error" ? <p className="notice error-notice" role="alert">{state.mutation.message}</p> : null}

        {editor ? (
          <form className="assignment-editor" onSubmit={saveAssignment} aria-labelledby="assignment-editor-title">
            <div>
              <p className="eyebrow">{editor.assignmentId ? "Edit meal" : "New meal"}</p>
              <h3 id="assignment-editor-title">{dayLabel(editor.date)} · {editor.slot === "lunch" ? "Lunch" : "Dinner"}</h3>
            </div>
            {!editor.assignmentId ? (
              <fieldset className="assignment-kind">
                <legend>Meal type</legend>
                <label><input type="radio" checked={editor.kind === "recipe"} onChange={() => dispatch({ type: "editor/kindChanged", payload: "recipe" })} /> Public recipe</label>
                <label><input type="radio" checked={editor.kind === "free_text"} onChange={() => dispatch({ type: "editor/kindChanged", payload: "free_text" })} /> Free text</label>
              </fieldset>
            ) : null}
            {editor.kind === "recipe" ? (
              <div className="recipe-choice">
                <p>{state.selectedRecipe ? <>Selected recipe: <strong>{state.selectedRecipe.title}</strong></> : "Search below, then choose a public recipe."}</p>
                <p className="field-hint">{editor.assignmentId ? "You can replace this recipe with another public recipe." : "Choose from the public search results below."}</p>
              </div>
            ) : (
              <label className="free-text-field" htmlFor="meal-text">
                Meal description
                <input
                  id="meal-text"
                  value={editor.freeText}
                  onChange={(event) => dispatch({ type: "editor/freeTextChanged", payload: event.target.value })}
                  onBlur={(event) => dispatch({ type: "editor/freeTextChanged", payload: normalizeFreeText(event.target.value) })}
                  placeholder="e.g. vegetable soup"
                />
              </label>
            )}
            <div className="editor-actions">
              <button type="submit" disabled={isSaving}>{isSaving ? "Saving…" : editor.assignmentId ? "Save changes" : "Save meal"}</button>
              <button type="button" className="secondary-button" onClick={() => dispatch({ type: "editor/close" })} disabled={isSaving}>Cancel</button>
            </div>
          </form>
        ) : null}
      </section>

      <section className="recipe-panel" aria-labelledby="recipe-search-title">
        <div>
          <p className="eyebrow">Public catalogue</p>
          <h2 id="recipe-search-title">Find a recipe</h2>
          <p>Search public recipes, view their details, and choose one for the selected calendar cell.</p>
        </div>
        <form className="recipe-search" onSubmit={submitRecipeSearch}>
          <label htmlFor="recipe-query">Recipe name</label>
          <div className="search-controls">
            <input id="recipe-query" type="search" value={state.recipeQuery} onChange={(event) => dispatch({ type: "recipes/queryChanged", payload: event.target.value })} placeholder="e.g. vegetable soup" />
            <button type="submit" disabled={state.recipes.status === "loading"}>Search</button>
          </div>
        </form>

        {state.recipes.status === "loading" ? <p className="loading-state" role="status">Searching recipes…</p> : null}
        {state.recipes.status === "error" ? <p className="notice error-notice" role="alert">{state.recipes.error}</p> : null}
        {state.recipes.status === "ready" && state.recipes.data?.recipes.length === 0 ? <p>No public recipes matched that search.</p> : null}
        {state.recipes.data?.recipes.length ? (
          <ul className="recipe-results" aria-label="Public recipe results">
            {state.recipes.data.recipes.map((recipe) => (
              <li key={recipe.id} className="recipe-result">
                <img src={recipe.coverImageUrl} alt="" />
                <span>{recipe.title}</span>
                <div className="recipe-result-actions">
                  <button type="button" onClick={() => dispatch({ type: "recipes/selected", payload: recipe })} disabled={!canChooseRecipe}>Choose</button>
                  <Link to={`/recipes/${recipe.id}`}>View details</Link>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
        {state.selectedRecipe ? <p className="selected-recipe" role="status">Selected public recipe: <strong>{state.selectedRecipe.title}</strong></p> : null}
      </section>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<CalendarPage />} />
      <Route path="/weeks/:weekStart" element={<CalendarPage />} />
      <Route path="/recipes/:recipeId" element={<RecipeDetailPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
