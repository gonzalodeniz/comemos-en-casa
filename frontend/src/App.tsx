import { FormEvent, useEffect, useReducer, useRef, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  addRecipeToCollection,
  ApiError,
  createAssignment,
  createCollection,
  createRecipe,
  deleteAssignment,
  deleteRecipe,
  deleteSeries,
  getCalendarContext,
  getCalendarWeek,
  getCollections,
  getCurrentUser,
  getFavorites,
  getPublicRecipe,
  getRecipeCatalogue,
  logout,
  setFavorite,
  setRecipeStatus,
  updateAssignment,
  updateRecipe,
  updateSeries,
  uploadRecipeImage,
} from "./api";
import { calendarReducer, initialCalendarState } from "./calendarReducer";
import type { AssignmentWritePayload, AuthenticatedUser, CalendarAssignment, MealSlot, RecipeCollection, RecipeDetail, RecipeIngredient, RecipeStatus, RecipeSummary, RecipeWritePayload } from "./types";

const mealRows: Array<{ slot: MealSlot; label: string; icon: string }> = [
  { slot: "lunch", label: "Comida", icon: "☀" },
  { slot: "dinner", label: "Cena", icon: "☾" },
];

type SessionState = { status: "loading" | "ready" | "error"; user: AuthenticatedUser | null };
type LoadState<T> = { status: "loading" | "ready" | "error"; data: T; error: string | null };
type RecipeEditorForm = RecipeWritePayload & { recipeId: string | null; image: File | null };

function useMediaQuery(query: string) {
  const getMatches = () => typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(query).matches;
  const [matches, setMatches] = useState(getMatches);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mediaQuery = window.matchMedia(query);
    const updateMatches = () => setMatches(mediaQuery.matches);
    updateMatches();
    mediaQuery.addEventListener("change", updateMatches);
    return () => mediaQuery.removeEventListener("change", updateMatches);
  }, [query]);

  return matches;
}

function emptyRecipeForm(): RecipeEditorForm {
  return { recipeId: null, title: "", detail: "", ingredients: [{ name: "", quantity: null }], steps: [{ instruction: "" }], image: null };
}

function recipeToForm(recipe: RecipeDetail): RecipeEditorForm {
  return { recipeId: recipe.id, title: recipe.title, detail: recipe.detail, ingredients: recipe.ingredients.length ? recipe.ingredients : [{ name: "", quantity: null }], steps: recipe.steps.length ? recipe.steps : [{ instruction: "" }], image: null };
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "No se pudo conectar con el servicio. Inténtalo de nuevo.";
}

function toDate(value: string): Date { return new Date(`${value}T12:00:00`); }
function toIsoDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
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
  return new Intl.DateTimeFormat("es", { weekday: "short", day: "numeric", month: "short" }).format(toDate(value));
}
function weekLabel(weekStart: string): string {
  const dates = weekDays(weekStart);
  const formatter = new Intl.DateTimeFormat("es", { month: "long", day: "numeric" });
  return `${formatter.format(toDate(dates[0]))} – ${formatter.format(toDate(dates[6]))}`;
}
function normalizeFreeText(value: string): string { return value.trim().replace(/\s+/g, " "); }

function generateAssignmentId(): string {
  const cryptoApi = typeof globalThis.crypto !== "undefined" ? globalThis.crypto : undefined;
  if (typeof cryptoApi?.randomUUID === "function") return cryptoApi.randomUUID();
  const bytes = new Uint8Array(16);
  if (typeof cryptoApi?.getRandomValues === "function") cryptoApi.getRandomValues(bytes);
  else for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("").replace(/^(........)(....)(....)(....)(............)$/, "$1-$2-$3-$4-$5");
}

function isCalendarRoute(pathname: string): boolean {
  return pathname === "/calendario" || /^\/(?:semanas|weeks)(?:\/|$)/.test(pathname);
}

function userInitials(label: string): string {
  const words = label.trim().split(/\s+/).filter(Boolean);
  return (words.length > 1 ? `${words[0][0]}${words[words.length - 1][0]}` : label.slice(0, 2)).toUpperCase();
}

function SiteHeader({ session, onLogout }: { session: SessionState; onLogout: () => void }) {
  const location = useLocation();
  const calendarRoute = isCalendarRoute(location.pathname);
  const userLabel = session.user?.displayName ?? session.user?.email;
  return (
    <header className="site-header">
      <Link className="brand" to="/calendario" aria-label="Como en casa, ir al calendario">
        <span className="brand-mark" aria-hidden="true">⌂</span>
        <span><strong>Como en casa</strong><small>Planifica. Cocina. Disfruta.</small></span>
      </Link>
      <form className="site-search" role="search" onSubmit={(event) => event.preventDefault()}>
        <label className="visually-hidden" htmlFor="site-search-input">Buscar recetas</label>
        <span aria-hidden="true">⌕</span>
        <input id="site-search-input" type="search" placeholder="Buscar recetas, ingredientes…" />
      </form>
      <nav className="primary-nav" aria-label="Navegación principal">
        {!calendarRoute ? <><Link to="/calendario">Calendario</Link><Link to="/recetas">Recetas</Link></> : null}
        {session.user ? <Link to="/mis-recetas">Mis recetas</Link> : null}
      </nav>
      <div className="session-entry">
        {session.status === "loading" ? <span className="session-status" role="status">Comprobando sesión…</span> : null}
        {userLabel && !calendarRoute ? <span className="user-name" title={session.user?.email}>{userLabel}</span> : null}
        {session.status === "ready" && !session.user ? calendarRoute
          ? <a className="login-avatar" href="/api/v1/auth/login" aria-label="Iniciar sesión" title="Iniciar sesión"><span aria-hidden="true">◯</span></a>
          : <a className="login-link" href="/api/v1/auth/login">Iniciar sesión</a> : null}
        {session.status === "ready" && session.user ? calendarRoute
          ? <button type="button" className="session-avatar" onClick={onLogout} aria-label={`Cerrar sesión de ${userLabel}`} title={`${userLabel} · Cerrar sesión`}><span aria-hidden="true">{userInitials(userLabel ?? "")}</span></button>
          : <button type="button" className="logout-button" onClick={onLogout}>Cerrar sesión</button> : null}
      </div>
    </header>
  );
}

function CalendarSidebar() {
  return <aside className="calendar-sidebar">
    <nav aria-label="Secciones del espacio de planificación">
      <p className="calendar-sidebar-label">Organización</p>
      <ul className="calendar-sidebar-nav">
        <li><Link className="is-active" to="/calendario" aria-current="page"><span className="sidebar-icon" aria-hidden="true">▦</span> Calendario</Link></li>
        <li><Link to="/recetas"><span className="sidebar-icon" aria-hidden="true">♜</span> Recetas</Link></li>
        <li><span><span className="sidebar-icon" aria-hidden="true">☷</span> Lista de la compra</span></li>
        <li><span><span className="sidebar-icon" aria-hidden="true">♧</span> Trucos</span></li>
        <li><span><span className="sidebar-icon" aria-hidden="true">♧</span> Mi familia</span></li>
        <li><span><span className="sidebar-icon" aria-hidden="true">♙</span> Perfil</span></li>
      </ul>
    </nav>
    <aside className="calendar-sidebar-note" aria-label="Consejo de planificación">
      <span className="calendar-sidebar-pot" aria-hidden="true">🍲</span>
      <p>Buena comida, mejores momentos <span aria-hidden="true">❤️</span></p>
    </aside>
  </aside>;
}

function CalendarDayHeader({ day }: { day: string }) {
  const date = toDate(day);
  const weekday = new Intl.DateTimeFormat("es", { weekday: "long" }).format(date);
  const dayNumber = new Intl.DateTimeFormat("es", { day: "numeric" }).format(date);
  return <><span className="calendar-day-name">{weekday}</span><span className="calendar-day-number">{dayNumber}</span></>;
}

function AssignmentCard({ assignment, deleting, onEdit }: { assignment: CalendarAssignment; deleting: boolean; onEdit: () => void }) {
  const title = assignment.kind === "recipe" ? assignment.recipe?.title : assignment.text;
  const imageUrl = assignment.kind === "recipe" ? assignment.recipe?.coverImageUrl : null;
  const recipeId = assignment.kind === "recipe" && assignment.recipe?.available ? assignment.recipe.id : null;
  const accessibleTitle = title ?? "Comida no disponible";
  const slotLabel = assignment.slot === "lunch" ? "comida" : "cena";
  const assignmentLabel = `${accessibleTitle}, ${slotLabel} del ${dayLabel(assignment.date)}`;
  const editLabel = `Editar ${accessibleTitle}`;
  return (
    <article className="assignment-card" aria-label={assignmentLabel}>
      <button type="button" className="assignment-card-open" onClick={onEdit} disabled={deleting} aria-label={editLabel}>
        {imageUrl
          ? <img className="assignment-image" src={imageUrl} alt={`Portada de ${accessibleTitle}`} />
          : <span className="assignment-image-placeholder" aria-hidden="true">🍲</span>}
      </button>
      <h3><button type="button" className="assignment-card-title" onClick={onEdit} disabled={deleting}>{accessibleTitle}</button></h3>
      {assignment.kind === "recipe" && !assignment.recipe?.available ? <small>Receta no disponible</small> : null}
      {assignment.entryType === "recurring_occurrence" && assignment.recurrenceWeeks ? <small className="recurrence-label">Repite cada {assignment.recurrenceWeeks === 1 ? "semana" : `${assignment.recurrenceWeeks} semanas`}</small> : null}
      <div className="assignment-actions">
        {recipeId ? <Link to={`/recetas/${recipeId}`}>Ver receta</Link> : null}
      </div>
    </article>
  );
}

function AssignmentModal({ heading, children, onClose, closeDisabled = false }: { heading: string; children: React.ReactNode; onClose: () => void; closeDisabled?: boolean }) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previousActiveElement = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      previousActiveElement?.focus();
    };
  }, []);
  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape" && !closeDisabled) {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab" || !dialogRef.current) return;
    const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>("button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href]"));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !closeDisabled) onClose(); }}>
    <div ref={dialogRef} className="assignment-modal" role="dialog" aria-modal="true" aria-labelledby="assignment-dialog-title" tabIndex={-1} onKeyDown={handleKeyDown}>
      <div className="assignment-modal-heading">
        <h2 id="assignment-dialog-title">{heading}</h2>
        <button ref={closeButtonRef} type="button" className="assignment-modal-close" onClick={onClose} disabled={closeDisabled} aria-label="Cerrar">×</button>
      </div>
      {children}
    </div>
  </div>;
}

function RecipeCard({ recipe, action }: { recipe: RecipeSummary; action?: React.ReactNode }) {
  return <article className="recipe-card">
    {recipe.coverImageUrl ? <img src={recipe.coverImageUrl} alt="" /> : <div className="recipe-image-placeholder" aria-hidden="true">🍲</div>}
    <div className="recipe-card-content">
      {recipe.status === "draft" ? <span className="status-pill">Borrador público</span> : null}
      <h3><Link to={`/recetas/${recipe.id}`}>{recipe.title}</Link></h3>
      <div className="recipe-card-actions"><Link to={`/recetas/${recipe.id}`}>Ver receta</Link>{action}</div>
    </div>
  </article>;
}

function RecipeCataloguePage() {
  const [query, setQuery] = useState("");
  const [load, setLoad] = useState<LoadState<RecipeSummary[]>>({ status: "loading", data: [], error: null });
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoad((current) => ({ ...current, status: "loading", error: null }));
    getRecipeCatalogue(query, controller.signal)
      .then((recipes) => setLoad({ status: "ready", data: recipes, error: null }))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) setLoad((current) => ({ ...current, status: "error", error: errorMessage(error) }));
      });
    return () => controller.abort();
  }, [query, reload]);

  return <main className="app-shell">
    <section className="page-hero" aria-labelledby="catalogue-title">
      <div><p className="eyebrow">Recetario público</p><h1 id="catalogue-title">Recetas para cada día</h1><p>Explora recetas públicas, incluidos los borradores, y guárdalas en tus listas al iniciar sesión.</p></div>
      <Link className="primary-link" to="/calendario">Ver calendario</Link>
    </section>
    <form className="catalogue-search" role="search" onSubmit={(event) => event.preventDefault()}>
      <label htmlFor="catalogue-query">Buscar recetas</label>
      <input id="catalogue-query" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nombre de receta o ingrediente" />
    </form>
    {load.status === "loading" ? <p className="loading-state" role="status">Cargando recetas…</p> : null}
    {load.status === "error" ? <div className="notice error-notice" role="alert"><p>{load.error}</p><button type="button" onClick={() => setReload((value) => value + 1)}>Reintentar</button></div> : null}
    {load.status === "ready" && load.data.length === 0 ? <p className="empty-state">No hay recetas que coincidan con la búsqueda.</p> : null}
    {load.data.length > 0 ? <section className="recipe-catalogue" aria-label="Resultados de recetas">{load.data.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} />)}</section> : null}
  </main>;
}

function RecipeDetailPage({ session }: { session: SessionState }) {
  const { recipeId } = useParams();
  const [detail, setDetail] = useState<LoadState<RecipeDetail | null>>({ status: "loading", data: null, error: null });
  const [saved, setSaved] = useState<LoadState<{ favorites: RecipeSummary[]; collections: RecipeCollection[] }>>({ status: "ready", data: { favorites: [], collections: [] }, error: null });
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [selectedCollection, setSelectedCollection] = useState("");

  useEffect(() => {
    if (!recipeId) return;
    const controller = new AbortController();
    setDetail({ status: "loading", data: null, error: null });
    getPublicRecipe(recipeId, controller.signal)
      .then((recipe) => setDetail({ status: "ready", data: recipe, error: null }))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) setDetail({ status: "error", data: null, error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [recipeId]);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    setSaved((current) => ({ ...current, status: "loading", error: null }));
    Promise.all([getFavorites(controller.signal), getCollections(controller.signal)])
      .then(([favorites, collections]) => setSaved({ status: "ready", data: { favorites, collections }, error: null }))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) setSaved((current) => ({ ...current, status: "error", error: errorMessage(error) }));
      });
    return () => controller.abort();
  }, [session.user]);

  const isFavorite = Boolean(detail.data && saved.data.favorites.some((recipe) => recipe.id === detail.data?.id));
  async function toggleFavorite() {
    if (!detail.data) return;
    setSaveMessage(null);
    try {
      await setFavorite(detail.data.id, !isFavorite);
      setSaved((current) => ({ ...current, data: { ...current.data, favorites: isFavorite ? current.data.favorites.filter((recipe) => recipe.id !== detail.data?.id) : [...current.data.favorites, detail.data!] } }));
      setSaveMessage(isFavorite ? "Se eliminó de tus favoritos." : "Se guardó en tus favoritos.");
    } catch (error) { setSaveMessage(errorMessage(error)); }
  }
  async function saveToCollection() {
    if (!detail.data || !selectedCollection) return;
    setSaveMessage(null);
    try {
      await addRecipeToCollection(selectedCollection, detail.data.id);
      setSaveMessage("La receta se añadió a la colección.");
    } catch (error) { setSaveMessage(errorMessage(error)); }
  }

  return <main className="app-shell detail-page">
    <Link className="back-link" to="/recetas">← Volver a recetas</Link>
    {detail.status === "loading" ? <p className="loading-state" role="status">Cargando receta…</p> : null}
    {detail.status === "error" ? <p className="notice error-notice" role="alert">{detail.error}</p> : null}
    {detail.data ? <article className="recipe-detail">
      <div className="recipe-detail-image">{detail.data.coverImageUrl ? <img src={detail.data.coverImageUrl} alt="" /> : <div className="recipe-image-placeholder" aria-hidden="true">🍲</div>}</div>
      <div className="recipe-detail-content">
        <p className="eyebrow">{detail.data.status === "draft" ? "Borrador público" : "Receta pública"}</p>
        <h1>{detail.data.title}</h1>
        <p className="recipe-description">{detail.data.detail}</p>
        {session.user ? <section className="recipe-saved-actions" aria-labelledby="save-recipe-title">
          <h2 id="save-recipe-title">Guardar receta</h2>
          {saved.status === "loading" ? <p role="status">Cargando tus listas…</p> : null}
          {saved.status === "error" ? <p className="inline-error" role="alert">{saved.error}</p> : null}
          {saved.status === "ready" ? <div className="saved-controls"><button type="button" className={isFavorite ? "secondary-button is-favorite" : "secondary-button"} onClick={() => void toggleFavorite()}>{isFavorite ? "♥ En favoritos" : "♡ Añadir a favoritos"}</button>
            <label>Guardar en una colección<select value={selectedCollection} onChange={(event) => setSelectedCollection(event.target.value)}><option value="">Selecciona una colección</option>{saved.data.collections.map((collection) => <option key={collection.id} value={collection.id}>{collection.name}</option>)}</select></label>
            <button type="button" onClick={() => void saveToCollection()} disabled={!selectedCollection}>Guardar</button>
            <Link to="/mis-recetas">Gestionar mis recetas</Link></div> : null}
          {saveMessage ? <p className="save-message" role="status">{saveMessage}</p> : null}
        </section> : <p className="login-callout">Inicia sesión para guardar esta receta en favoritos o colecciones. <a href="/api/v1/auth/login">Iniciar sesión</a></p>}
        <section className="recipe-content-section" aria-labelledby="ingredients-title"><h2 id="ingredients-title">Ingredientes</h2>{detail.data.ingredients.length ? <ul className="ingredient-list">{detail.data.ingredients.map((ingredient, index) => <li key={`${ingredient.name}-${index}`}><span>{ingredient.name}</span>{ingredient.quantity ? <span>{ingredient.quantity}</span> : null}</li>)}</ul> : <p>No se han añadido ingredientes.</p>}</section>
        <section className="recipe-content-section" aria-labelledby="steps-title"><h2 id="steps-title">Preparación</h2>{detail.data.steps.length ? <ol className="step-list">{detail.data.steps.map((step, index) => <li key={`${step.instruction}-${index}`}>{step.instruction}</li>)}</ol> : <p>No se han añadido pasos de preparación.</p>}</section>
      </div>
    </article> : null}
  </main>;
}

function CollectionsPage({ session }: { session: SessionState }) {
  const [load, setLoad] = useState<LoadState<{ favorites: RecipeSummary[]; collections: RecipeCollection[] }>>({ status: "loading", data: { favorites: [], collections: [] }, error: null });
  const [name, setName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    setLoad((current) => ({ ...current, status: "loading", error: null }));
    Promise.all([getFavorites(controller.signal), getCollections(controller.signal)])
      .then(([favorites, collections]) => setLoad({ status: "ready", data: { favorites, collections }, error: null }))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) setLoad((current) => ({ ...current, status: "error", error: errorMessage(error) }));
      });
    return () => controller.abort();
  }, [session.user, reload]);
  async function submitCollection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedName = normalizeFreeText(name);
    if (!normalizedName) { setMessage("Escribe un nombre para la colección."); return; }
    try {
      const collection = await createCollection(normalizedName);
      setLoad((current) => ({ ...current, data: { ...current.data, collections: [collection, ...current.data.collections] } }));
      setName(""); setMessage("La colección se creó correctamente.");
    } catch (error) { setMessage(errorMessage(error)); }
  }
  if (!session.user && session.status === "ready") return <main className="app-shell"><section className="empty-state"><h1>Mis recetas</h1><p>Inicia sesión para ver tus favoritos y colecciones privadas.</p><a className="primary-link" href="/api/v1/auth/login">Iniciar sesión</a></section></main>;
  return <main className="app-shell"><section className="page-hero" aria-labelledby="my-recipes-title"><div><p className="eyebrow">Espacio privado</p><h1 id="my-recipes-title">Mis recetas</h1><p>Organiza las recetas públicas que quieres conservar.</p></div></section>
    {load.status === "loading" ? <p className="loading-state" role="status">Cargando tus recetas…</p> : null}
    {load.status === "error" ? <div className="notice error-notice" role="alert"><p>{load.error}</p><button type="button" onClick={() => setReload((value) => value + 1)}>Reintentar</button></div> : null}
    {load.status === "ready" ? <><section className="private-section" aria-labelledby="favorites-title"><h2 id="favorites-title">Favoritos</h2>{load.data.favorites.length ? <div className="recipe-catalogue compact-catalogue">{load.data.favorites.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} />)}</div> : <p>Aún no tienes recetas favoritas.</p>}</section>
      <section className="private-section" aria-labelledby="collections-title"><div className="section-heading"><div><h2 id="collections-title">Colecciones</h2><p>Estas colecciones solo son visibles para ti.</p></div></div><form className="create-collection" onSubmit={submitCollection}><label htmlFor="collection-name">Nueva colección</label><input id="collection-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Por ejemplo, Cenas rápidas" /><button type="submit">Crear colección</button></form>{message ? <p className="save-message" role="status">{message}</p> : null}
        {load.data.collections.length ? <div className="collection-grid">{load.data.collections.map((collection) => <article className="collection-card" key={collection.id}><h3>{collection.name}</h3><p>{collection.recipes.length} {collection.recipes.length === 1 ? "receta" : "recetas"}</p>{collection.recipes.length ? <ul>{collection.recipes.slice(0, 4).map((recipe) => <li key={recipe.id}><Link to={`/recetas/${recipe.id}`}>{recipe.title}</Link></li>)}</ul> : <p className="muted">Todavía no hay recetas en esta colección.</p>}</article>)}</div> : <p>Aún no tienes colecciones.</p>}</section></> : null}
  </main>;
}

function RecipeWorkspacePage({ session }: { session: SessionState }) {
  const [saved, setSaved] = useState<LoadState<{ favorites: RecipeSummary[]; collections: RecipeCollection[] }>>({ status: "loading", data: { favorites: [], collections: [] }, error: null });
  const [recipes, setRecipes] = useState<LoadState<RecipeSummary[]>>({ status: "loading", data: [], error: null });
  const [collectionName, setCollectionName] = useState("");
  const [collectionMessage, setCollectionMessage] = useState<string | null>(null);
  const [editor, setEditor] = useState<RecipeEditorForm | null>(null);
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [isSavingRecipe, setIsSavingRecipe] = useState(false);
  const [recipeMessage, setRecipeMessage] = useState<{ kind: "error" | "success"; text: string } | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    setSaved((current) => ({ ...current, status: "loading", error: null }));
    Promise.all([getFavorites(controller.signal), getCollections(controller.signal)])
      .then(([favorites, collections]) => setSaved({ status: "ready", data: { favorites, collections }, error: null }))
      .catch((error: unknown) => { if (!(error instanceof DOMException && error.name === "AbortError")) setSaved((current) => ({ ...current, status: "error", error: errorMessage(error) })); });
    return () => controller.abort();
  }, [session.user, reload]);

  useEffect(() => {
    if (!session.user) return;
    const controller = new AbortController();
    setRecipes((current) => ({ ...current, status: "loading", error: null }));
    getRecipeCatalogue("", controller.signal)
      .then((data) => setRecipes({ status: "ready", data, error: null }))
      .catch((error: unknown) => { if (!(error instanceof DOMException && error.name === "AbortError")) setRecipes((current) => ({ ...current, status: "error", error: errorMessage(error) })); });
    return () => controller.abort();
  }, [session.user, reload]);

  async function submitCollection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedName = normalizeFreeText(collectionName);
    if (!normalizedName) { setCollectionMessage("Escribe un nombre para la colección."); return; }
    try {
      const collection = await createCollection(normalizedName);
      setSaved((current) => ({ ...current, data: { ...current.data, collections: [collection, ...current.data.collections] } }));
      setCollectionName(""); setCollectionMessage("La colección se creó correctamente.");
    } catch (error) { setCollectionMessage(errorMessage(error)); }
  }

  async function openRecipeEditor(recipeId: string) {
    setOpeningId(recipeId); setRecipeMessage(null);
    try { setEditor(recipeToForm(await getPublicRecipe(recipeId))); }
    catch (error) { setRecipeMessage({ kind: "error", text: errorMessage(error) }); }
    finally { setOpeningId(null); }
  }

  function updateIngredient(index: number, field: keyof RecipeIngredient, value: string) {
    setEditor((current) => current ? { ...current, ingredients: current.ingredients.map((ingredient, itemIndex) => itemIndex === index ? { ...ingredient, [field]: field === "quantity" ? value || null : value } : ingredient) } : current);
  }
  function updateStep(index: number, value: string) {
    setEditor((current) => current ? { ...current, steps: current.steps.map((step, itemIndex) => itemIndex === index ? { instruction: value } : step) } : current);
  }
  function removeIngredient(index: number) { setEditor((current) => current ? { ...current, ingredients: current.ingredients.filter((_, itemIndex) => itemIndex !== index) } : current); }
  function removeStep(index: number) { setEditor((current) => current ? { ...current, steps: current.steps.filter((_, itemIndex) => itemIndex !== index) } : current); }

  async function saveRecipe(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || isSavingRecipe) return;
    const payload: RecipeWritePayload = {
      title: normalizeFreeText(editor.title),
      detail: editor.detail.trim(),
      ingredients: editor.ingredients.map((ingredient) => ({ name: normalizeFreeText(ingredient.name), quantity: normalizeFreeText(ingredient.quantity ?? "") || null })).filter((ingredient) => ingredient.name),
      steps: editor.steps.map((step) => ({ instruction: step.instruction.trim() })).filter((step) => step.instruction),
    };
    if (!payload.title || !payload.detail) { setRecipeMessage({ kind: "error", text: "El título y la descripción son obligatorios." }); return; }
    if (editor.image && editor.image.size > 10 * 1024 * 1024) { setRecipeMessage({ kind: "error", text: "La imagen no puede superar 10 MB." }); return; }
    setIsSavingRecipe(true); setRecipeMessage(null);
    try {
      let result = editor.recipeId ? await updateRecipe(editor.recipeId, payload) : await createRecipe(payload);
      if (editor.image) result = await uploadRecipeImage(result.id, editor.image);
      setEditor(recipeToForm(result));
      setRecipes((current) => ({ ...current, data: current.data.some((recipe) => recipe.id === result.id) ? current.data.map((recipe) => recipe.id === result.id ? result : recipe) : [result, ...current.data] }));
      setRecipeMessage({ kind: "success", text: editor.recipeId ? "Los cambios se guardaron correctamente." : "La receta se creó como borrador." });
    } catch (error) { setRecipeMessage({ kind: "error", text: errorMessage(error) }); }
    finally { setIsSavingRecipe(false); }
  }

  async function changeStatus(status: RecipeStatus) {
    if (!editor?.recipeId || isSavingRecipe) return;
    setIsSavingRecipe(true); setRecipeMessage(null);
    try {
      const result = await setRecipeStatus(editor.recipeId, status);
      setEditor(recipeToForm(result));
      setRecipes((current) => ({ ...current, data: current.data.map((recipe) => recipe.id === result.id ? result : recipe) }));
      setRecipeMessage({ kind: "success", text: status === "published" ? "La receta se publicó." : "La receta volvió a borrador." });
    } catch (error) { setRecipeMessage({ kind: "error", text: errorMessage(error) }); }
    finally { setIsSavingRecipe(false); }
  }

  async function removeRecipe() {
    if (!editor?.recipeId || isSavingRecipe || !window.confirm(`¿Eliminar la receta “${editor.title}”? Esta acción no se puede deshacer.`)) return;
    setIsSavingRecipe(true); setRecipeMessage(null);
    try {
      await deleteRecipe(editor.recipeId);
      setRecipes((current) => ({ ...current, data: current.data.filter((recipe) => recipe.id !== editor.recipeId) }));
      setEditor(null); setRecipeMessage({ kind: "success", text: "La receta se eliminó." });
    } catch (error) { setRecipeMessage({ kind: "error", text: errorMessage(error) }); }
    finally { setIsSavingRecipe(false); }
  }

  if (session.status === "loading") return <main className="app-shell"><p className="loading-state" role="status">Comprobando tu sesión…</p></main>;
  if (!session.user) return <main className="app-shell"><section className="empty-state"><h1>Mis recetas</h1><p>Inicia sesión para gestionar recetas, favoritos y colecciones.</p><a className="primary-link" href="/api/v1/auth/login">Iniciar sesión</a></section></main>;
  const recipeStatus = editor?.recipeId ? recipes.data.find((recipe) => recipe.id === editor.recipeId)?.status : undefined;
  return <main className="app-shell"><section className="page-hero" aria-labelledby="my-recipes-title"><div><p className="eyebrow">Espacio privado</p><h1 id="my-recipes-title">Mis recetas</h1><p>Crea, edita y publica recetas; conserva también tus favoritos y colecciones.</p></div><button type="button" onClick={() => { setEditor(emptyRecipeForm()); setRecipeMessage(null); }}>Nueva receta</button></section>
    <section className="private-section recipe-management" aria-labelledby="recipe-management-title"><div className="section-heading"><div><h2 id="recipe-management-title">Gestionar recetas</h2><p>Las recetas se crean como borradores públicos. Guarda los cambios antes de publicar.</p></div></div>
      {recipeMessage ? <p className={recipeMessage.kind === "error" ? "notice error-notice" : "notice success-notice"} role={recipeMessage.kind === "error" ? "alert" : "status"}>{recipeMessage.text}</p> : null}
      {editor ? <form className="recipe-editor" onSubmit={saveRecipe} aria-labelledby="recipe-editor-title"><div className="editor-heading"><div><p className="eyebrow">{editor.recipeId ? "Editar receta" : "Nueva receta"}</p><h3 id="recipe-editor-title">{editor.recipeId ? "Contenido de la receta" : "Completa los datos iniciales"}</h3></div>{recipeStatus ? <span className="status-pill">{recipeStatus === "published" ? "Publicada" : "Borrador público"}</span> : null}</div>
        <label>Título<input required maxLength={200} value={editor.title} onChange={(event) => setEditor({ ...editor, title: event.target.value })} /></label><label>Descripción<textarea required maxLength={10000} value={editor.detail} onChange={(event) => setEditor({ ...editor, detail: event.target.value })} /></label>
        <fieldset><legend>Ingredientes</legend>{editor.ingredients.map((ingredient, index) => <div className="recipe-row" key={`ingredient-${index}`}><label>Ingrediente<input value={ingredient.name} maxLength={500} onChange={(event) => updateIngredient(index, "name", event.target.value)} /></label><label>Cantidad<input value={ingredient.quantity ?? ""} maxLength={100} onChange={(event) => updateIngredient(index, "quantity", event.target.value)} /></label><button type="button" className="text-button" onClick={() => removeIngredient(index)} aria-label={`Eliminar ingrediente ${index + 1}`}>Eliminar</button></div>)}<button type="button" className="secondary-button" onClick={() => setEditor({ ...editor, ingredients: [...editor.ingredients, { name: "", quantity: null }] })}>Añadir ingrediente</button></fieldset>
        <fieldset><legend>Preparación</legend>{editor.steps.map((step, index) => <div className="recipe-row step-row" key={`step-${index}`}><label>Paso {index + 1}<textarea value={step.instruction} onChange={(event) => updateStep(index, event.target.value)} /></label><button type="button" className="text-button" onClick={() => removeStep(index)} aria-label={`Eliminar paso ${index + 1}`}>Eliminar</button></div>)}<button type="button" className="secondary-button" onClick={() => setEditor({ ...editor, steps: [...editor.steps, { instruction: "" }] })}>Añadir paso</button></fieldset>
        <label>Imagen de la receta <span className="field-hint">JPEG, PNG o WebP; máximo 10 MB.</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setEditor({ ...editor, image: event.target.files?.[0] ?? null })} /></label>{editor.image ? <p className="field-hint">Imagen seleccionada: {editor.image.name}</p> : null}
        <div className="editor-actions"><button type="submit" disabled={isSavingRecipe}>{isSavingRecipe ? "Guardando…" : "Guardar receta"}</button>{editor.recipeId ? <><button type="button" className="secondary-button" onClick={() => void changeStatus(recipeStatus === "published" ? "draft" : "published")} disabled={isSavingRecipe}>{recipeStatus === "published" ? "Pasar a borrador" : "Publicar receta"}</button><button type="button" className="danger-button" onClick={() => void removeRecipe()} disabled={isSavingRecipe}>Eliminar receta</button></> : null}<button type="button" className="text-button" onClick={() => setEditor(null)} disabled={isSavingRecipe}>Cerrar</button></div>
      </form> : null}
      {recipes.status === "loading" ? <p className="loading-state" role="status">Cargando recetas…</p> : null}{recipes.status === "error" ? <div className="notice error-notice" role="alert"><p>{recipes.error}</p><button type="button" onClick={() => setReload((value) => value + 1)}>Reintentar</button></div> : null}{recipes.status === "ready" && !recipes.data.length ? <p>Aún no hay recetas para gestionar.</p> : null}{recipes.data.length ? <div className="recipe-catalogue compact-catalogue" aria-label="Recetas disponibles">{recipes.data.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} action={<button type="button" className="secondary-button" onClick={() => void openRecipeEditor(recipe.id)} disabled={openingId === recipe.id}>{openingId === recipe.id ? "Abriendo…" : "Editar"}</button>} />)}</div> : null}
    </section>
    {saved.status === "loading" ? <p className="loading-state" role="status">Cargando favoritos y colecciones…</p> : null}{saved.status === "error" ? <div className="notice error-notice" role="alert"><p>{saved.error}</p><button type="button" onClick={() => setReload((value) => value + 1)}>Reintentar</button></div> : null}{saved.status === "ready" ? <><section className="private-section" aria-labelledby="favorites-title"><h2 id="favorites-title">Favoritos</h2>{saved.data.favorites.length ? <div className="recipe-catalogue compact-catalogue">{saved.data.favorites.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} />)}</div> : <p>Aún no tienes recetas favoritas.</p>}</section><section className="private-section" aria-labelledby="collections-title"><div className="section-heading"><div><h2 id="collections-title">Colecciones</h2><p>Estas colecciones solo son visibles para ti.</p></div></div><form className="create-collection" onSubmit={submitCollection}><label htmlFor="workspace-collection-name">Nueva colección</label><input id="workspace-collection-name" value={collectionName} onChange={(event) => setCollectionName(event.target.value)} placeholder="Por ejemplo, Cenas rápidas" /><button type="submit">Crear colección</button></form>{collectionMessage ? <p className="save-message" role="status">{collectionMessage}</p> : null}{saved.data.collections.length ? <div className="collection-grid">{saved.data.collections.map((collection) => <article className="collection-card" key={collection.id}><h3>{collection.name}</h3><p>{collection.recipes.length} {collection.recipes.length === 1 ? "receta" : "recetas"}</p>{collection.recipes.length ? <ul>{collection.recipes.slice(0, 4).map((recipe) => <li key={recipe.id}><Link to={`/recetas/${recipe.id}`}>{recipe.title}</Link></li>)}</ul> : <p className="muted">Todavía no hay recetas en esta colección.</p>}</article>)}</div> : <p>Aún no tienes colecciones.</p>}</section></> : null}
  </main>;
}

function CalendarPage() {
  const { weekStart: weekStartFromPath } = useParams();
  const navigate = useNavigate();
  const [state, dispatch] = useReducer(calendarReducer, initialCalendarState);
  const [reloadVersion, setReloadVersion] = useState(0);
  const [assignmentModal, setAssignmentModal] = useState<{ type: "edit"; assignment: CalendarAssignment } | null>(null);
  const isMobile = useMediaQuery("(max-width: 760px)");
  const activeWeekStart = weekStartFromPath ?? state.context.data?.currentWeekStart;
  useEffect(() => { const controller = new AbortController(); dispatch({ type: "context/loading" }); getCalendarContext(controller.signal).then((context) => dispatch({ type: "context/success", payload: context })).catch((error: unknown) => { if (!(error instanceof DOMException && error.name === "AbortError")) dispatch({ type: "context/error", payload: errorMessage(error) }); }); return () => controller.abort(); }, [reloadVersion]);
  useEffect(() => { if (!activeWeekStart) return; const controller = new AbortController(); dispatch({ type: "week/loading" }); getCalendarWeek(activeWeekStart, controller.signal).then((week) => dispatch({ type: "week/success", payload: week })).catch((error: unknown) => { if (!(error instanceof DOMException && error.name === "AbortError")) dispatch({ type: "week/error", payload: errorMessage(error) }); }); return () => controller.abort(); }, [activeWeekStart, reloadVersion]);
  function retryCalendar() { setReloadVersion((version) => version + 1); }
  function navigateWeek(amount: number) { if (activeWeekStart) navigate(`/semanas/${shiftWeek(activeWeekStart, amount)}`); }
  function openCurrentWeek() { if (state.context.data) navigate(`/semanas/${state.context.data.currentWeekStart}`); }
  function openCreateEditor(date: string, slot: MealSlot) {
    dispatch({ type: "editor/openCreate", payload: { date, slot, createId: generateAssignmentId() } });
  }
  function openNewMeal() {
    if (activeWeekStart) openCreateEditor(activeWeekStart, "lunch");
  }
  async function saveSeries(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const editor = state.editor;
    if (!editor?.seriesId || state.mutation.status === "loading") return;
    const text = normalizeFreeText(editor.freeText);
    if (!text) { dispatch({ type: "mutation/error", payload: "Escribe una descripción para la comida." }); return; }
    const anchorChanged = editor.date !== (editor.initialDate ?? editor.date);
    if (editor.recurrenceWeeks === 0) {
      if (!window.confirm(`¿Dejar de repetir ${text}?`)) return;
      dispatch({ type: "mutation/loading", payload: { type: "delete", assignmentId: editor.seriesId } });
      try {
        await deleteSeries(editor.seriesId, true);
        dispatch({ type: "mutation/success", payload: "La serie se eliminó." });
        dispatch({ type: "editor/close" });
        setAssignmentModal(null);
        setReloadVersion((version) => version + 1);
      } catch (error) { dispatch({ type: "mutation/error", payload: errorMessage(error) }); }
      return;
    }
    if (anchorChanged && !window.confirm(`¿Cambiar la fecha inicial de la serie a ${dayLabel(editor.date)}?`)) return;
    dispatch({ type: "mutation/loading", payload: { type: "update", assignmentId: editor.seriesId } });
    try {
      await updateSeries(editor.seriesId, { initialDate: editor.date, text, recurrenceWeeks: editor.recurrenceWeeks, confirmAnchorChange: anchorChanged });
      dispatch({ type: "mutation/success", payload: "La serie se actualizó." });
      dispatch({ type: "editor/close" });
      setAssignmentModal(null);
      setReloadVersion((version) => version + 1);
    } catch (error) { dispatch({ type: "mutation/error", payload: errorMessage(error) }); }
  }
  async function saveAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const editor = state.editor; if (!editor || editor.seriesId || state.mutation.status === "loading") return;
    let payload: AssignmentWritePayload;
    if (editor.kind === "recipe") { if (!state.selectedRecipe) { dispatch({ type: "mutation/error", payload: "Elige una receta pública antes de guardar." }); return; } payload = { date: editor.date, slot: editor.slot, kind: "recipe", recipeId: state.selectedRecipe.id }; }
    else { const text = normalizeFreeText(editor.freeText); if (!text) { dispatch({ type: "mutation/error", payload: "Escribe una descripción para la comida." }); return; } dispatch({ type: "editor/freeTextChanged", payload: text }); payload = { date: editor.date, slot: editor.slot, kind: "free_text", text, ...(editor.recurrenceWeeks > 0 ? { recurrenceWeeks: editor.recurrenceWeeks } : {}) }; }
    const assignmentId = editor.assignmentId; const isEditing = assignmentId !== null; const isRecurringMutation = editor.kind === "free_text" && editor.recurrenceWeeks > 0; dispatch({ type: "mutation/loading", payload: { type: isEditing ? "update" : "create", assignmentId } });
    try {
      const assignment = assignmentId ? await updateAssignment(assignmentId, payload) : await createAssignment({ ...payload, id: editor.createId ?? generateAssignmentId() });
      if (isRecurringMutation) {
        dispatch({ type: "mutation/success", payload: isEditing ? "La serie se creó." : "La comida se guardó." });
        dispatch({ type: "editor/close" });
        setAssignmentModal(null);
        setReloadVersion((version) => version + 1);
      } else {
        dispatch({ type: "week/assignmentSaved", payload: assignment }); dispatch({ type: "mutation/success", payload: isEditing ? "La comida se actualizó." : "La comida se guardó." }); dispatch({ type: "editor/close" }); if (isEditing) setAssignmentModal(null);
      }
    } catch (error) { dispatch({ type: "mutation/error", payload: errorMessage(error) }); }
  }
  async function removeSeries(seriesId: string, text: string) {
    if (state.mutation.status === "loading" || !window.confirm(`¿Eliminar la serie ${text}?`)) return;
    dispatch({ type: "mutation/loading", payload: { type: "delete", assignmentId: seriesId } });
    try {
      await deleteSeries(seriesId, true);
      dispatch({ type: "mutation/success", payload: "La serie se eliminó." });
      dispatch({ type: "editor/close" });
      setAssignmentModal(null);
      setReloadVersion((version) => version + 1);
    } catch (error) { dispatch({ type: "mutation/error", payload: errorMessage(error) }); }
  }
  async function removeAssignment(assignment: CalendarAssignment) {
    const title = assignment.kind === "recipe" ? assignment.recipe?.title : assignment.text ?? "esta comida";
    if (state.mutation.status === "loading" || !window.confirm(`¿Eliminar ${title}?`)) return;
    dispatch({ type: "mutation/loading", payload: { type: "delete", assignmentId: assignment.id } });
    try {
      await deleteAssignment(assignment.id);
      dispatch({ type: "week/assignmentDeleted", payload: assignment.id });
      dispatch({ type: "mutation/success", payload: "La comida se eliminó." });
      setAssignmentModal(null);
      if (state.editor?.assignmentId === assignment.id) dispatch({ type: "editor/close" });
    } catch (error) { dispatch({ type: "mutation/error", payload: errorMessage(error) }); }
  }
  function openEditAssignment(assignment: CalendarAssignment) {
    dispatch({ type: "editor/openEdit", payload: assignment });
    setAssignmentModal({ type: "edit", assignment });
  }
  function closeAssignmentModal() {
    if (state.mutation.status === "loading") return;
    if (assignmentModal?.type === "edit") dispatch({ type: "editor/close" });
    setAssignmentModal(null);
  }
  const assignments = state.week.data?.assignments ?? []; const days = activeWeekStart ? weekDays(activeWeekStart) : []; const editor = state.editor; const isSaving = state.mutation.status === "loading" && (state.mutation.type === "create" || state.mutation.type === "update");
  const isDeleting = state.mutation.status === "loading" && state.mutation.type === "delete";
  const editingAssignment = editor?.assignmentId ? assignments.find((assignment) => assignment.id === editor.assignmentId) : null;
  const assignmentEditor = editor ? <form className="assignment-editor" onSubmit={editor.seriesId ? saveSeries : saveAssignment} aria-labelledby="assignment-editor-title"><div><p className="eyebrow">{editor.seriesId ? "Editar serie" : editor.assignmentId ? "Editar comida" : "Nueva comida"}</p><h3 id="assignment-editor-title">{editor.seriesId ? "Serie de comidas" : `${dayLabel(editor.date)} · ${editor.slot === "lunch" ? "Comida" : "Cena"}`}</h3></div>{editor.seriesId ? <><label className="free-text-field" htmlFor="series-initial-date">Fecha inicial<input id="series-initial-date" type="date" value={editor.date} onChange={(event) => dispatch({ type: "editor/dateChanged", payload: event.target.value })} /></label><label className="free-text-field" htmlFor="series-meal-slot">Comida/Cena<select id="series-meal-slot" value={editor.slot} disabled><option value="lunch">Comida</option><option value="dinner">Cena</option></select></label></> : null}{!editor.assignmentId && !editor.seriesId ? <fieldset className="assignment-kind"><legend>Tipo de comida</legend><label><input type="radio" checked={editor.kind === "recipe"} onChange={() => dispatch({ type: "editor/kindChanged", payload: "recipe" })} />Receta pública</label><label><input type="radio" checked={editor.kind === "free_text"} onChange={() => dispatch({ type: "editor/kindChanged", payload: "free_text" })} />Texto libre</label></fieldset> : null}{editor.kind === "recipe" ? <div className="recipe-choice"><p>{state.selectedRecipe ? <>Receta seleccionada: <strong>{state.selectedRecipe.title}</strong></> : "Busca y elige una receta pública."}</p><p className="field-hint">Puedes elegir otra receta desde los resultados de abajo.</p></div> : <><label className="free-text-field" htmlFor="meal-text">Descripción de la comida<input id="meal-text" value={editor.freeText} onChange={(event) => dispatch({ type: "editor/freeTextChanged", payload: event.target.value })} onBlur={(event) => dispatch({ type: "editor/freeTextChanged", payload: normalizeFreeText(event.target.value) })} placeholder="Por ejemplo, crema de verduras" /></label><label className="free-text-field" htmlFor="recurrence-weeks">Repetición<select id="recurrence-weeks" value={editor.recurrenceWeeks} onChange={(event) => dispatch({ type: "editor/recurrenceChanged", payload: Number(event.target.value) })}><option value="0">No repetir</option><option value="1">Cada semana</option><option value="2">Cada 2 semanas</option><option value="3">Cada 3 semanas</option><option value="4">Cada 4 semanas</option></select></label></>}{<div className="editor-actions"><button type="submit" disabled={isSaving || isDeleting}>{isSaving ? "Guardando…" : editor.seriesId ? "Guardar serie" : editor.assignmentId ? "Guardar cambios" : "Guardar comida"}</button>{editor.seriesId ? <button type="button" className="danger-button" onClick={() => void removeSeries(editor.seriesId!, editor.freeText)} disabled={isSaving || isDeleting}>{isDeleting ? "Eliminando…" : "Eliminar serie"}</button> : editingAssignment ? <button type="button" className="danger-button" onClick={() => void removeAssignment(editingAssignment)} disabled={isSaving || isDeleting}>{isDeleting ? "Eliminando…" : "Eliminar"}</button> : null}<button type="button" className="secondary-button" onClick={editor.assignmentId || editor.seriesId ? closeAssignmentModal : () => dispatch({ type: "editor/close" })} disabled={isSaving || isDeleting}>Cancelar</button></div>}</form> : null;
  const calendarCellContent = (day: string, slot: MealSlot, label: string) => {
    const cellAssignments = assignments.filter((assignment) => assignment.date === day && assignment.slot === slot);
    const dayDescription = dayLabel(day);
    const slotLabel = label.toLowerCase();
    const addActionText = `Añadir ${slotLabel}`;

    return <>{cellAssignments.length ? cellAssignments.map((assignment) => <AssignmentCard key={assignment.id} assignment={assignment} deleting={state.mutation.status === "loading" && state.mutation.type === "delete" && state.mutation.assignmentId === assignment.id} onEdit={() => openEditAssignment(assignment)} />) : <span className="empty-cell">Sin plan</span>}<button type="button" className="add-assignment" onClick={() => openCreateEditor(day, slot)} aria-label={`${addActionText} el ${dayDescription}`}>+ {addActionText}</button></>;
  };
  return <main className="app-shell calendar-workspace">
    <div className="calendar-frame"><CalendarSidebar /><div className="calendar-content">
    <section className="calendar-section" aria-labelledby="calendar-title" aria-busy={state.context.status === "loading" || state.week.status === "loading"}><div className="section-heading"><div className="calendar-heading-copy"><p className="eyebrow">Vista semanal</p><h2 id="calendar-title">Semana del {activeWeekStart ? weekLabel(activeWeekStart) : "…"}</h2><p>Elige una casilla para añadir o editar una comida.</p></div><div className="week-controls" aria-label="Navegación por semanas"><button type="button" onClick={() => navigateWeek(-1)} disabled={!activeWeekStart} aria-label="Semana anterior">←</button><button type="button" onClick={() => navigateWeek(1)} disabled={!activeWeekStart} aria-label="Semana siguiente">→</button><button type="button" onClick={openCurrentWeek} disabled={!state.context.data}>Hoy</button><button type="button" className="calendar-primary-action" onClick={openNewMeal} disabled={!activeWeekStart}>+ Añadir comida</button></div></div>
      {state.context.status === "error" ? <div className="notice error-notice" role="alert"><p>{state.context.error}</p><button type="button" onClick={retryCalendar}>Reintentar</button></div> : null}{state.week.status === "error" ? <div className="notice error-notice" role="alert"><p>{state.week.error}</p><button type="button" onClick={retryCalendar}>Reintentar</button></div> : null}{state.context.status === "loading" || state.week.status === "loading" ? <p className="loading-state" role="status">Cargando calendario…</p> : null}
      {activeWeekStart && state.week.status === "ready" ? isMobile ? <div className="calendar-mobile-list" aria-label="Calendario semanal por día">
        {days.map((day) => <section className="calendar-mobile-day" key={day} aria-labelledby={`calendar-mobile-day-${day}`}>
          <h3 id={`calendar-mobile-day-${day}`}><CalendarDayHeader day={day} /></h3>
          {mealRows.map(({ slot, label, icon }) => <section className={`calendar-mobile-slot${editor?.date === day && editor.slot === slot ? " selected-calendar-cell" : ""}`} key={slot} aria-labelledby={`calendar-mobile-${day}-${slot}`}>
            <h4 id={`calendar-mobile-${day}-${slot}`}><span aria-hidden="true">{icon}</span> {label}</h4>
            {calendarCellContent(day, slot, label)}
          </section>)}
        </section>)}
      </div> : <><p id="calendar-scroll-instructions" className="visually-hidden">La tabla contiene los siete días de la semana. Desplázate horizontalmente para consultar todos los días y usa los encabezados para mantener el contexto.</p><div id="tabla_calendario" className="calendar-scroll" tabIndex={0} role="region" aria-label="Calendario semanal desplazable horizontalmente" aria-describedby="calendar-scroll-instructions">
        <table className="calendar-grid">
          <thead><tr><th scope="col">Momento</th>{days.map((day) => <th id={`calendar-day-${day}`} scope="col" key={day}><CalendarDayHeader day={day} /></th>)}</tr></thead>
          <tbody>{mealRows.map(({ slot, label, icon }) => <tr key={slot}><th id={`calendar-slot-${slot}`} scope="row"><span aria-hidden="true">{icon}</span> {label}</th>{days.map((day) => <td className={editor?.date === day && editor.slot === slot ? "selected-calendar-cell" : undefined} headers={`calendar-slot-${slot} calendar-day-${day}`} key={`${day}-${slot}`}>{calendarCellContent(day, slot, label)}</td>)}</tr>)}</tbody>
        </table>
      </div></> : null}
      {state.mutation.status === "success" ? <p className="notice success-notice" role="status">{state.mutation.message}</p> : null}{state.mutation.status === "error" && !assignmentModal ? <p className="notice error-notice" role="alert">{state.mutation.message}</p> : null}
      {editor && !editor.assignmentId && !editor.seriesId ? assignmentEditor : null}
      {assignmentModal?.type === "edit" && (editor?.assignmentId || editor?.seriesId) ? <AssignmentModal heading={editor.seriesId ? "Editar serie" : "Editar comida"} onClose={closeAssignmentModal} closeDisabled={isSaving || isDeleting}>{state.mutation.status === "error" ? <p className="notice error-notice" role="alert">{state.mutation.message}</p> : null}{assignmentEditor}</AssignmentModal> : null}
    </section>
    <footer className="calendar-planning-footer"><span aria-hidden="true">🌿</span><p>“La planificación de hoy es el sabor de un mañana más tranquilo.”</p><strong>Planifica · Cocina · Disfruta. <span aria-hidden="true">❤️</span></strong></footer>
    </div></div>
  </main>;
}

export default function App() {
  const [session, setSession] = useState<SessionState>({ status: "loading", user: null });
  useEffect(() => { const controller = new AbortController(); getCurrentUser(controller.signal).then((user) => setSession({ status: "ready", user })).catch(() => setSession({ status: "error", user: null })); return () => controller.abort(); }, []);
  async function handleLogout() {
    try { await logout(); setSession({ status: "ready", user: null }); }
    catch { setSession({ status: "error", user: null }); }
  }
  return <><SiteHeader session={session} onLogout={() => void handleLogout()} /><Routes><Route path="/" element={<Navigate to="/calendario" replace />} /><Route path="/calendario" element={<CalendarPage />} /><Route path="/semanas/:weekStart" element={<CalendarPage />} /><Route path="/recetas" element={<RecipeCataloguePage />} /><Route path="/recetas/:recipeId" element={<RecipeDetailPage session={session} />} /><Route path="/mis-recetas" element={<RecipeWorkspacePage session={session} />} /><Route path="/weeks/:weekStart" element={<CalendarPage />} /><Route path="/recipes/:recipeId" element={<Navigate to="/recetas" replace />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></>;
}
