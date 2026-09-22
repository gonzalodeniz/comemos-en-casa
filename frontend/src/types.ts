export type MealSlot = "lunch" | "dinner";
export type AssignmentKind = "recipe" | "free_text";
export type AssignmentEntryType = "assignment" | "recurring_occurrence";

export interface CalendarContext {
  timezone: string;
  currentWeekStart: string;
  guestMode: boolean;
}

export interface RecipeLabel {
  id: string;
  name: string;
  color: string;
}

export interface RecipeSummary {
  id: string;
  title: string;
  coverImageUrl: string;
  labels?: RecipeLabel[];
}

export interface RecipeIngredient {
  name: string;
  quantity: string | null;
}

export interface RecipeStep {
  instruction: string;
}

export interface RecipeDetail extends RecipeSummary {
  detail: string;
  ingredients: RecipeIngredient[];
  steps: RecipeStep[];
}

export interface RecipeWritePayload {
  title: string;
  detail: string;
  ingredients: RecipeIngredient[];
  steps: RecipeStep[];
  labels: string[];
}

export interface RecipeReference {
  id: string | null;
  available: boolean;
  title: string;
  coverImageUrl: string | null;
}

export interface CalendarAssignment {
  id: string;
  entryType?: AssignmentEntryType;
  date: string;
  slot: MealSlot;
  kind: AssignmentKind;
  recipe?: RecipeReference;
  text?: string;
  seriesId?: string;
  occurrenceDate?: string;
  initialDate?: string;
  recurrenceWeeks?: number;
}

export interface AssignmentWritePayload {
  id?: string;
  date: string;
  slot: MealSlot;
  kind: AssignmentKind;
  recipeId?: string;
  text?: string;
  recurrenceWeeks?: number;
}

export interface SeriesWritePayload {
  initialDate: string;
  text: string;
  recurrenceWeeks: number;
  confirmAnchorChange: boolean;
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

export interface AuthenticatedUser {
  id: string;
  email: string;
  displayName: string | null;
  pictureUrl: string | null;
}

export interface RecipeCollection {
  id: string;
  name: string;
  recipes: RecipeSummary[];
}

export interface ApiProblem {
  code: string;
  message: string;
  retryable: boolean;
}
