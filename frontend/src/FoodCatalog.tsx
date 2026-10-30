import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import Cropper from "react-easy-crop";
import { ApiError } from "./api";
import AppIcon from "./AppIcon";
import { createFoodLabel, deleteFoodLabel, getFoodLabelImpact, getFoodLabels, importFoodImageUrl, prepareFoodImage, updateFoodLabel, type FoodLabel } from "./mealPlanningApi";

type Props = { csrfToken: string; onSessionExpired: () => void };

export function filterAndSortFoods(labels: FoodLabel[], query: string): FoodLabel[] {
  const search = query.toLocaleLowerCase("es");
  return labels
    .filter((label) => label.name.toLocaleLowerCase("es").includes(search))
    .sort((a, b) => a.name.localeCompare(b.name, "es", { sensitivity: "base" }));
}

export function FoodCard({ label, busy, onEdit, onRemove }: { label: FoodLabel; busy: boolean; onEdit: (label: FoodLabel, opener: HTMLElement) => void; onRemove: (label: FoodLabel) => void }) {
  return <article className="dish-card">{label.image_url ? <img src={`${import.meta.env.VITE_API_BASE_URL || "/comemos"}/api/v1${label.image_url}`} alt="" /> : <span className="dish-image"><AppIcon name="utensils" /></span>}<strong>{label.name}</strong><div className="food-card-actions"><button type="button" className="secondary" aria-label={`Editar ${label.name}`} title={`Editar ${label.name}`} disabled={busy} onClick={(e) => onEdit(label, e.currentTarget)}><AppIcon name="edit" /></button><button type="button" className="danger" aria-label={`Eliminar ${label.name}`} title={`Eliminar ${label.name}`} disabled={busy} onClick={() => onRemove(label)}><AppIcon name="trash" /></button><button type="button" className="secondary" aria-label={`Ver recetas de ${label.name}`} title="Recetas no disponibles" disabled><AppIcon name="eye" /></button></div></article>;
}


export default function FoodCatalog({ csrfToken, onSessionExpired }: Props) {
  const [labels, setLabels] = useState<FoodLabel[]>([]);
  const [query, setQuery] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<FoodLabel | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState("");
  const [readingImage, setReadingImage] = useState(false);
  const [imageRevision, setImageRevision] = useState(0);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [cropArea, setCropArea] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [removeImage, setRemoveImage] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const drawerRef = useRef<HTMLFormElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageReadRef = useRef(0);
  const openerRef = useRef<HTMLElement | null>(null);
  const createButtonRef = useRef<HTMLButtonElement>(null);

  async function reload() { const data = await getFoodLabels(); setLabels(data.labels); }
  useEffect(() => { void reload().catch((e: unknown) => { if (e instanceof ApiError && e.status === 401) onSessionExpired(); else setError("No se pudo cargar el catálogo."); }).finally(() => setLoading(false)); }, [onSessionExpired]);
  const filtered = useMemo(() => filterAndSortFoods(labels, query), [labels, query]);

  function open(label?: FoodLabel, opener?: HTMLElement) {
    imageReadRef.current += 1; setReadingImage(false);
    openerRef.current = opener ?? (document.activeElement instanceof HTMLElement ? document.activeElement : null);
    setEditing(label ?? null); setName(label?.name ?? ""); setSource(""); setCropArea(null); setRemoveImage(false); setError(""); setNotice(""); setImageUrl(""); setDrawerOpen(true);
  }
  function close() {
    if (busy) return;
    imageReadRef.current += 1; setReadingImage(false);
    setDrawerOpen(false); setEditing(null); setSource(""); setError(""); setNotice("");
    requestAnimationFrame(() => (openerRef.current?.isConnected ? openerRef.current : createButtonRef.current)?.focus());
  }
  useEffect(() => {
    if (!drawerOpen) return;
    const first = drawerRef.current?.querySelector<HTMLElement>('input:not([type="checkbox"]), button:not(:disabled)');
    first?.focus();
  }, [drawerOpen]);

  function handleDrawerKeyDown(event: KeyboardEvent<HTMLFormElement>) {
    if (event.key === "Escape") { event.preventDefault(); close(); return; }
    if (event.key !== "Tab") return;
    const items = Array.from(drawerRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), summary[tabindex], [tabindex]:not([tabindex="-1"]):not(:disabled)') ?? []).filter((item) => item.offsetParent !== null);
    if (!items.length) { event.preventDefault(); drawerRef.current?.focus(); return; }
    if (event.shiftKey && (document.activeElement === items[0] || document.activeElement === drawerRef.current)) { event.preventDefault(); items.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === items.at(-1)) { event.preventDefault(); items[0].focus(); }
  }
  function readFile(file?: File) {
    if (!file) return;
    if (file.size > 2 * 1024 * 1024 || !["image/jpeg", "image/png", "image/webp"].includes(file.type)) { setError("Usa una imagen JPG, PNG o WebP de hasta 2 MiB."); return; }
    const readId = ++imageReadRef.current;
    setReadingImage(true);
    const reader = new FileReader(); reader.onload = () => { if (readId !== imageReadRef.current) return; setReadingImage(false); setCropArea(null); setImageRevision((revision) => revision + 1); setSource(String(reader.result ?? "")); setRemoveImage(false); setError(""); setCrop({ x: 0, y: 0 }); setZoom(1); }; reader.onerror = () => { if (readId !== imageReadRef.current) return; setReadingImage(false); setError("No se pudo leer la imagen."); }; reader.readAsDataURL(file);
  }
  async function importUrl() {
    imageReadRef.current += 1; setReadingImage(false);
    setBusy(true); setError("");
    try { const result = await importFoodImageUrl(imageUrl, csrfToken); setCropArea(null); setImageRevision((revision) => revision + 1); setSource(result.data_url); setRemoveImage(false); setCrop({ x: 0, y: 0 }); setZoom(1); }
    catch (e) { if (e instanceof ApiError && e.status === 401) onSessionExpired(); setError(e instanceof ApiError && e.status === 401 ? "La sesión ha caducado." : "No se pudo importar la imagen desde esa URL."); }
    finally { setBusy(false); }
  }
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      let imageToken: string | undefined;
      if (readingImage || (source && !cropArea)) { setError("Espera a que la imagen esté lista antes de guardar."); return; }
      let imageError = false;
      if (source && cropArea) { try { imageToken = (await prepareFoodImage(source, cropArea, csrfToken)).image_token; } catch { imageError = true; } }
      if (editing) await updateFoodLabel(editing.id, name, csrfToken, imageToken, source ? false : removeImage);
      else await createFoodLabel(name, csrfToken, imageToken);
      await reload(); setDrawerOpen(false); setEditing(null); setSource(""); setNotice(imageError ? "La comida se guardó, pero no se pudo cargar la imagen; la imagen anterior se conservó." : editing ? "Cambios guardados." : "Comida añadida.");
      requestAnimationFrame(() => (openerRef.current?.isConnected ? openerRef.current : createButtonRef.current)?.focus());
    } catch (e) { if (e instanceof ApiError && e.status === 401) onSessionExpired(); else setError(e instanceof ApiError && e.status === 409 ? "La comida ya existe." : "No se pudo guardar la comida."); }
    finally { setBusy(false); }
  }
  async function remove(label: FoodLabel) {
    try {
      const impact = await getFoodLabelImpact(label.id);
      if (!window.confirm(`¿Eliminar ${label.name}?\n\n▦ ${impact.assignment_count} asignaciones en la planificación\n🍽 ${impact.recipe_count} recetas`)) return;
      setBusy(true); await deleteFoodLabel(label.id, csrfToken); await reload(); setNotice(`${label.name} eliminada.`);
    } catch (e) { if (e instanceof ApiError && e.status === 401) onSessionExpired(); else setError("No se pudo eliminar la comida."); } finally { setBusy(false); }
  }
  return <main className="food-catalog"><section className="panel food-catalog-panel">
    <header className="food-catalog-heading"><div><p className="eyebrow">Catálogo compartido</p><h1>Comidas</h1><p>Organiza las comidas disponibles para tu planificación.</p></div><button ref={createButtonRef} type="button" className="food-create-trigger" onClick={(e) => open(undefined, e.currentTarget)}><AppIcon name="plus" /> Nueva comida</button></header>
    {error && !editing && <p className="message error" role="alert">{error}</p>}{notice && <p className="message success" role="status">{notice}</p>}
    <div className="food-catalog-search-row"><div className="dish-search"><input id="food-search" type="search" aria-label="Buscar comida" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar comida" /></div>{query && <button type="button" className="secondary food-clear-search" onClick={() => setQuery("")}>Limpiar búsqueda</button>}</div>
    {loading ? <p className="food-empty-state" role="status">Cargando comidas…</p> : !filtered.length ? <p className="food-empty-state" role="status">{query ? "No se encontraron comidas con esa búsqueda." : "Todavía no hay comidas. Añade la primera."}</p> : <div className="dish-grid">{filtered.map((label) => <FoodCard key={label.id} label={label} busy={busy} onEdit={open} onRemove={(item) => void remove(item)} />)}</div>}
  </section>
  {drawerOpen && <div className="drawer-overlay food-drawer-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}>
    <form className="meal-editor food-editor" ref={drawerRef} tabIndex={-1} onSubmit={save} onKeyDown={handleDrawerKeyDown} role="dialog" aria-modal="true" aria-labelledby="food-editor-title">
      <header className="meal-editor-heading food-editor-heading"><div><h2 id="food-editor-title">{editing ? "Editar comida" : "Nueva comida"}</h2><p>{editing ? "Actualiza el nombre o la imagen de esta comida." : "Añade una comida al catálogo compartido."}</p></div><button className="drawer-close secondary" type="button" aria-label="Cerrar" onClick={close}>×</button></header>
      <div className="drawer-content food-editor-content">
        {error && <p className="message error" role="alert">{error}</p>}
        <label className="food-name-field">Nombre<input value={name} onChange={(e) => setName(e.target.value)} maxLength={100} required placeholder="Ej. Pasta con verduras" /></label>
        <div className="food-image-options">
          <label className="image-drop" tabIndex={0} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); readFile(e.dataTransfer.files[0]); }} onPaste={(e) => readFile(Array.from(e.clipboardData.files).find((f) => f.type.startsWith("image/")))}>
            Arrastra o pega una imagen, o selecciónala <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => { readFile(e.target.files?.[0]); e.target.value = ""; }} />
          </label>
          <div className="image-url-import"><label htmlFor="food-image-url">Importar desde URL</label><input id="food-image-url" type="url" value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} placeholder="https://…" /><button type="button" className="secondary" disabled={busy || !imageUrl} onClick={() => void importUrl()}>Cargar URL</button></div>
          {editing?.image_url && <label className="food-remove-image"><input type="checkbox" checked={removeImage} disabled={!!source || readingImage} onChange={(e) => setRemoveImage(e.target.checked)} /> Quitar imagen y mostrar cubiertos</label>}
        </div>
        {source && <section className="food-crop" aria-label="Recortar imagen"><div className="crop-area"><Cropper key={imageRevision} image={source} crop={crop} zoom={zoom} aspect={1} onCropChange={setCrop} onZoomChange={setZoom} onCropComplete={(_area, pixels) => setCropArea(pixels)} /><button type="button" className="food-crop-discard" aria-label="Descartar imagen seleccionada" title="Descartar imagen seleccionada" disabled={busy} onClick={() => { imageReadRef.current += 1; setReadingImage(false); setSource(""); setCropArea(null); setError(""); fileInputRef.current?.focus(); }}>×</button></div><label>Zoom<input type="range" min={1} max={3} step={0.05} value={zoom} onChange={(e) => setZoom(Number(e.target.value))} /></label></section>}
      </div>
      <footer className="drawer-actions"><button className="secondary" type="button" disabled={busy} onClick={close}>Cancelar</button><button className="food-save-button" disabled={busy || readingImage}>{busy ? "Guardando…" : editing ? "Guardar cambios" : "Añadir comida"}</button></footer>
    </form>
  </div>}
  </main>;
}
