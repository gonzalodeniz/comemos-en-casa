export type MealSlot = "lunch" | "dinner";
export type AssignmentKind = "recipe" | "free_text";

export interface CalendarContext {
  timezone: string;
  currentWeekStart: string;
  guestMode: boolean;
}

export interface RecipeSummary {
  id: string;
  title: string;
  coverImageUrl: string;
}

export interface RecipeDetail extends RecipeSummary {
  detail: string;
}

export interface RecipeReference {
  id: string | null;
  available: boolean;
  title: string;
  coverImageUrl: string | null;
}

export interface CalendarAssignment {
  id: string;
  date: string;
  slot: MealSlot;
  kind: AssignmentKind;
  recipe?: RecipeReference;
  text?: string;
}

export interface AssignmentWritePayload {
  id?: string;
  date: string;
  slot: MealSlot;
  kind: AssignmentKind;
  recipeId?: string;
  text?: string;
}

export interface CalendarWeek {
  weekStart: string;
  weekEnd: string;
  timezone: string;
  assignments: CalendarAssignment[];
}

export interface RecipeSearchResult {
  recipes: RecipeSummary[];
  nextCursor: string | null;
}

export interface ApiProblem {
  code: string;
  message: string;
  retryable: boolean;
}
