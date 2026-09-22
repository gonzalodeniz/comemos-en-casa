import type {
  AssignmentKind,
  CalendarAssignment,
  CalendarContext,
  CalendarWeek,
  MealSlot,
  RecipeSearchResult,
  RecipeSummary,
} from "./types";

export type RequestState<T> = {
  status: "idle" | "loading" | "ready" | "error";
  data: T | null;
  error: string | null;
};

export type AssignmentEditor = {
  date: string;
  initialDate: string;
  slot: MealSlot;
  kind: AssignmentKind;
  assignmentId: string | null;
  seriesId: string | null;
  createId: string | null;
  freeText: string;
  recurrenceWeeks: number;
};

export type MutationState = {
  status: "idle" | "loading" | "success" | "error";
  type: "create" | "update" | "delete" | null;
  assignmentId: string | null;
  message: string | null;
};

export type CalendarState = {
  context: RequestState<CalendarContext>;
  week: RequestState<CalendarWeek>;
  recipes: RequestState<RecipeSearchResult>;
  recipeQuery: string;
  selectedRecipe: RecipeSummary | null;
  editor: AssignmentEditor | null;
  mutation: MutationState;
};

export const initialCalendarState: CalendarState = {
  context: { status: "idle", data: null, error: null },
  week: { status: "idle", data: null, error: null },
  recipes: { status: "idle", data: null, error: null },
  recipeQuery: "",
  selectedRecipe: null,
  editor: null,
  mutation: { status: "idle", type: null, assignmentId: null, message: null },
};

export type CalendarAction =
  | { type: "context/loading" }
  | { type: "context/success"; payload: CalendarContext }
  | { type: "context/error"; payload: string }
  | { type: "week/loading" }
  | { type: "week/success"; payload: CalendarWeek }
  | { type: "week/error"; payload: string }
  | { type: "week/assignmentSaved"; payload: CalendarAssignment }
  | { type: "week/assignmentDeleted"; payload: string }
  | { type: "recipes/queryChanged"; payload: string }
  | { type: "recipes/loading" }
  | { type: "recipes/success"; payload: RecipeSearchResult }
  | { type: "recipes/error"; payload: string }
  | { type: "recipes/selected"; payload: RecipeSummary | null }
  | { type: "editor/openCreate"; payload: { date: string; slot: MealSlot; createId: string } }
  | { type: "editor/openEdit"; payload: CalendarAssignment }
  | { type: "editor/close" }
  | { type: "editor/freeTextChanged"; payload: string }
  | { type: "editor/dateChanged"; payload: string }
  | { type: "editor/recurrenceChanged"; payload: number }
  | { type: "editor/kindChanged"; payload: AssignmentKind }
  | { type: "mutation/loading"; payload: { type: "create" | "update" | "delete"; assignmentId: string | null } }
  | { type: "mutation/success"; payload: string }
  | { type: "mutation/error"; payload: string };

function loading<T>(current: RequestState<T>): RequestState<T> {
  return { ...current, status: "loading", error: null };
}

function failed<T>(current: RequestState<T>, error: string): RequestState<T> {
  return { ...current, status: "error", error };
}

function sortAssignments(assignments: CalendarAssignment[]): CalendarAssignment[] {
  return [...assignments].sort((left, right) =>
    `${left.date}-${left.slot}-${left.id}`.localeCompare(`${right.date}-${right.slot}-${right.id}`),
  );
}

export function calendarReducer(state: CalendarState, action: CalendarAction): CalendarState {
  switch (action.type) {
    case "context/loading":
      return { ...state, context: loading(state.context) };
    case "context/success":
      return { ...state, context: { status: "ready", data: action.payload, error: null } };
    case "context/error":
      return { ...state, context: failed(state.context, action.payload) };
    case "week/loading":
      return { ...state, week: loading(state.week) };
    case "week/success":
      return { ...state, week: { status: "ready", data: action.payload, error: null } };
    case "week/error":
      return { ...state, week: failed(state.week, action.payload) };
    case "week/assignmentSaved": {
      if (!state.week.data) return state;
      const hasAssignment = state.week.data.assignments.some((assignment) => assignment.id === action.payload.id);
      const assignments = hasAssignment
        ? state.week.data.assignments.map((assignment) => assignment.id === action.payload.id ? action.payload : assignment)
        : [...state.week.data.assignments, action.payload];
      return { ...state, week: { ...state.week, data: { ...state.week.data, assignments: sortAssignments(assignments) } } };
    }
    case "week/assignmentDeleted":
      if (!state.week.data) return state;
      return {
        ...state,
        week: {
          ...state.week,
          data: { ...state.week.data, assignments: state.week.data.assignments.filter((assignment) => assignment.id !== action.payload) },
        },
      };
    case "recipes/queryChanged":
      return { ...state, recipeQuery: action.payload };
    case "recipes/loading":
      return { ...state, recipes: loading(state.recipes) };
    case "recipes/success":
      return { ...state, recipes: { status: "ready", data: action.payload, error: null } };
    case "recipes/error":
      return { ...state, recipes: failed(state.recipes, action.payload) };
    case "recipes/selected":
      return { ...state, selectedRecipe: action.payload };
    case "editor/openCreate":
      return {
        ...state,
        editor: {
          date: action.payload.date,
          initialDate: action.payload.date,
          slot: action.payload.slot,
          assignmentId: null,
          seriesId: null,
          createId: action.payload.createId,
          kind: state.selectedRecipe ? "recipe" : "free_text",
          freeText: "",
          recurrenceWeeks: 0,
        },
        mutation: { status: "idle", type: null, assignmentId: null, message: null },
      };
    case "editor/openEdit": {
      const recipe = action.payload.recipe;
      return {
        ...state,
        editor: {
          date: action.payload.initialDate ?? action.payload.date,
          initialDate: action.payload.initialDate ?? action.payload.date,
          slot: action.payload.slot,
          kind: action.payload.kind,
          assignmentId: action.payload.entryType === "recurring_occurrence" ? null : action.payload.id,
          seriesId: action.payload.seriesId ?? null,
          createId: null,
          freeText: action.payload.text ?? "",
          recurrenceWeeks: action.payload.recurrenceWeeks ?? 0,
        },
        selectedRecipe: recipe?.available && recipe.id
          ? { id: recipe.id, title: recipe.title, coverImageUrl: recipe.coverImageUrl ?? "" }
          : null,
        mutation: { status: "idle", type: null, assignmentId: null, message: null },
      };
    }
    case "editor/close":
      return { ...state, editor: null };
    case "editor/freeTextChanged":
      return state.editor ? { ...state, editor: { ...state.editor, freeText: action.payload } } : state;
    case "editor/dateChanged":
      return state.editor ? { ...state, editor: { ...state.editor, date: action.payload } } : state;
    case "editor/recurrenceChanged":
      return state.editor && state.editor.kind === "free_text"
        ? { ...state, editor: { ...state.editor, recurrenceWeeks: action.payload } }
        : state;
    case "editor/kindChanged":
      return state.editor && !state.editor.assignmentId && !state.editor.seriesId
        ? { ...state, editor: { ...state.editor, kind: action.payload, recurrenceWeeks: action.payload === "free_text" ? state.editor.recurrenceWeeks : 0 } }
        : state;
    case "mutation/loading":
      return { ...state, mutation: { status: "loading", ...action.payload, message: null } };
    case "mutation/success":
      return { ...state, mutation: { status: "success", type: null, assignmentId: null, message: action.payload } };
    case "mutation/error":
      return { ...state, mutation: { ...state.mutation, status: "error", message: action.payload } };
  }
}
