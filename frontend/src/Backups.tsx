// Gestiona las copias existentes sin alterar el procedimiento del servidor.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { apiRequest, ApiError } from "./api";
import AppIcon from "./AppIcon";
import { Button, Message } from "./ui";
import ToastMessage from "./ToastMessage";

// Describe los únicos metadatos publicados por el servidor.
type Copia = { filename: string; size: number };
// Representa la configuración persistida, incluida su ausencia inicial.
type Automatizacion = { enabled: boolean; frequency: "daily" | "weekly" | null; maximum: number | null };
// Define las credenciales y el tratamiento compartido de sesiones caducadas.
type Props = { csrfToken: string; onSessionExpired: () => void };
// Obtiene la fecha UTC del nombre generado, sin inventar metadatos.
function fecha(copia: Copia) {
  const partes = /^backup-(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z\.zip$/.exec(copia.filename);
  return partes ? new Date(`${partes[1]}-${partes[2]}-${partes[3]}T${partes[4]}:${partes[5]}:${partes[6]}Z`).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "Fecha no disponible";
}
// Expresa el espacio real en unidades legibles.
function tamano(bytes: number) {
  const indice = bytes >= 1024 ** 3 ? 3 : bytes >= 1024 ** 2 ? 2 : 1;
  return `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(bytes / 1024 ** indice)} ${["B", "KB", "MB", "GB"][indice]}`;
}
// Reutiliza el patrón de diálogo nativo y devuelve el foco al control de origen.
function Dialogo({ titulo, ocupado, cerrar, children }: { titulo: string; ocupado: boolean; cerrar: () => void; children: ReactNode }) {
  const referencia = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const origen = document.activeElement as HTMLElement | null;
    const ventana = referencia.current;
    ventana?.showModal();
    return () => { ventana?.close(); origen?.focus(); };
  }, []);
  return <dialog className="copias-dialogo" ref={referencia} aria-labelledby="copias-dialogo-titulo" aria-busy={ocupado} onCancel={(evento) => { evento.preventDefault(); if (!ocupado) cerrar(); }}><h2 id="copias-dialogo-titulo">{titulo}</h2>{children}</dialog>;
}
// Presenta el resumen, las acciones y las confirmaciones de operaciones críticas.
export default function Backups({ csrfToken, onSessionExpired }: Props) {
  const [copias, setCopias] = useState<Copia[]>([]);
  const [configuracion, setConfiguracion] = useState<Automatizacion | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorLista, setErrorLista] = useState("");
  const [errorConfiguracion, setErrorConfiguracion] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [ocupacion, setOcupacion] = useState("");
  const bloqueo = useRef(false);
  const [dialogo, setDialogo] = useState<"automatizacion" | "restaurar" | "eliminar" | null>(null);
  const [seleccionada, setSeleccionada] = useState<Copia | null>(null);
  const [frecuencia, setFrecuencia] = useState<"daily" | "weekly">("daily");
  const [maximo, setMaximo] = useState("3");
  // Mantiene el comportamiento de sesión ya utilizado por la aplicación.
  const comprobarSesion = useCallback((causa: unknown) => { if (causa instanceof ApiError && causa.status === 401) onSessionExpired(); }, [onSessionExpired]);
  // Actualiza los datos reales y distingue errores de consulta de un listado vacío.
  const cargarCopias = useCallback(async () => {
    try { const resultado = await apiRequest<{ backups: Copia[] }>("/backups"); setCopias([...resultado.backups].sort((a, b) => b.filename.localeCompare(a.filename))); setErrorLista(""); }
    catch (causa) { comprobarSesion(causa); setErrorLista("No se pudieron cargar las copias de seguridad. Vuelve a intentarlo."); }
    finally { setCargando(false); }
  }, [comprobarSesion]);
  // Consulta la automatización sin reemplazarla por valores locales de demostración.
  const cargarConfiguracion = useCallback(async () => {
    try { setConfiguracion(await apiRequest<Automatizacion>("/backups/schedule")); setErrorConfiguracion(""); }
    catch (causa) { comprobarSesion(causa); setErrorConfiguracion("No se pudo consultar la automatización."); }
  }, [comprobarSesion]);
  useEffect(() => { void cargarCopias(); void cargarConfiguracion(); }, [cargarCopias, cargarConfiguracion]);
  // Limpia mensajes antiguos y prepara una edición a partir de los datos confirmados.
  function abrir(tipo: typeof dialogo, copia: Copia | null = null) {
    setError(""); setMensaje(""); setSeleccionada(copia);
    setFrecuencia(configuracion?.frequency ?? "daily"); setMaximo(String(configuracion?.maximum ?? 3)); setDialogo(tipo);
  }
  // Serializa acciones y solo anuncia resultados confirmados por el backend.
  async function ejecutar(accion: "crear" | "automatizacion" | "restaurar" | "eliminar") {
    if (bloqueo.current) return;
    bloqueo.current = true; setOcupacion(accion); setError(""); setMensaje("");
    try {
      if (accion === "crear") {
        const resultado = await apiRequest<{ filename: string }>("/backups", { method: "POST", csrfToken, body: {} });
        setMensaje(`Copia creada: ${resultado.filename}`); await cargarCopias();
      } else if (accion === "automatizacion") {
        const resultado = await apiRequest<Automatizacion>("/backups/schedule", { method: "POST", csrfToken, body: { frequency: frecuencia, maximum: Number(maximo) } });
        setConfiguracion(resultado); setMensaje("Automatización guardada correctamente."); setDialogo(null);
      } else if (seleccionada) {
        await apiRequest(`/backups/${encodeURIComponent(seleccionada.filename)}${accion === "restaurar" ? "/restore" : ""}`, { method: accion === "restaurar" ? "POST" : "DELETE", csrfToken, ...(accion === "restaurar" ? { body: {} } : {}) });
        setDialogo(null); setMensaje(accion === "restaurar" ? "Copia restaurada correctamente." : "Copia eliminada correctamente.");
        await cargarCopias(); if (accion === "restaurar") await cargarConfiguracion();
      }
    } catch (causa) {
      comprobarSesion(causa);
      setError(accion === "restaurar" ? "La restauración no se ha completado. Puede ser necesaria una recuperación manual; no continúes modificando datos hasta comprobar su estado." : accion === "crear" ? "No se pudo crear la copia de seguridad." : accion === "eliminar" ? "No se pudo eliminar la copia de seguridad." : "No se pudo guardar la automatización.");
    } finally { bloqueo.current = false; setOcupacion(""); }
  }
  const ocupado = !!ocupacion;
  const valido = /^\d+$/.test(maximo) && Number.isSafeInteger(Number(maximo)) && Number(maximo) >= 1 && Number(maximo) <= 2147483647;
  const cambios = !configuracion?.enabled || frecuencia !== configuracion.frequency || Number(maximo) !== configuracion.maximum;
  return <main className="dashboard copias-pagina"><section className="panel">
    <header><h2>Copias de seguridad</h2><p>Crea y gestiona copias de la base de datos y las imágenes de tu aplicación.</p></header>
    <div className="copias-resumen">
      <article><AppIcon name="calendar" /><div><span>Última copia</span><strong>{cargando ? "Cargando…" : errorLista ? "No disponible" : copias[0] ? fecha(copias[0]) : "Sin copias todavía"}</strong></div></article>
      <article><AppIcon name="repeat" /><div><span>Automatización</span><strong>{errorConfiguracion ? "No disponible" : !configuracion ? "Cargando…" : configuracion.enabled ? `${configuracion.frequency === "daily" ? "Diaria" : "Semanal"} · Máx. ${configuracion.maximum} copias` : "Desactivada"}</strong></div></article>
      <article><AppIcon name="database" /><div><span>Almacenamiento</span><strong>{cargando ? "Cargando…" : errorLista ? "No disponible" : `${tamano(copias.reduce((total, copia) => total + copia.size, 0))} (${copias.length} copias)`}</strong></div></article>
    </div>
    <h3>Acciones rápidas</h3><div className="copias-acciones"><Button disabled={ocupado} onClick={() => void ejecutar("crear")}><AppIcon name="plus" />{ocupacion === "crear" ? "Creando copia…" : "Crear copia ahora"}</Button><Button variant="secondary" disabled={ocupado || !configuracion} onClick={() => abrir("automatizacion")}><AppIcon name="settings" />Configurar automatización</Button></div>
    {errorConfiguracion && <Message tone="error">{errorConfiguracion} <button className="link-button" onClick={() => void cargarConfiguracion()}>Reintentar</button></Message>}
    {mensaje && <ToastMessage key={mensaje} kind="success" onClose={() => setMensaje("")}>{mensaje}</ToastMessage>}
    {error && !dialogo && <Message tone="error">{error}</Message>}
    <h3>Copias disponibles</h3>
    {errorLista ? <Message tone="error">{errorLista} <button className="link-button" onClick={() => void cargarCopias()}>Reintentar</button></Message> : cargando ? <p role="status">Cargando copias…</p> : !copias.length ? <div className="copias-vacio"><p>Todavía no hay copias de seguridad</p><small>Crea una copia para conservar la base de datos y las imágenes de recetas, comidas y productos.</small><Button variant="secondary" disabled={ocupado} onClick={() => void ejecutar("crear")}>Crear primera copia</Button></div> : <table className="copias-tabla"><thead><tr><th>Copia</th><th>Fecha de creación</th><th>Tamaño</th><th>Acciones</th></tr></thead><tbody>{copias.map((copia) => <tr key={copia.filename}><td className="copias-archivo">{copia.filename}</td><td data-label="Fecha de creación">{fecha(copia)}</td><td data-label="Tamaño">{tamano(copia.size)}</td><td><div className="copias-controles"><a className="copias-descargar" href={`/comemos/api/v1/backups/${encodeURIComponent(copia.filename)}`} download={copia.filename} aria-label={`Descargar ${copia.filename}`}><AppIcon name="download" /></a><Button variant="secondary" disabled={ocupado} onClick={() => abrir("restaurar", copia)}><AppIcon name="undo" />Restaurar</Button><details><summary aria-label={`Más acciones para ${copia.filename}`}>⋯</summary><button type="button" disabled={ocupado} onClick={() => abrir("eliminar", copia)}>Eliminar copia</button></details></div></td></tr>)}</tbody></table>}
    {dialogo && <Dialogo titulo={dialogo === "automatizacion" ? "Automatización de copias" : dialogo === "restaurar" ? "Restaurar copia" : "Eliminar copia"} ocupado={ocupado} cerrar={() => setDialogo(null)}>
      {dialogo === "automatizacion" ? <><p>Configura la creación automática de copias de seguridad.</p><div className="copias-campos"><label>Frecuencia<select value={frecuencia} onChange={(evento) => setFrecuencia(evento.target.value as "daily" | "weekly")} disabled={ocupado}><option value="daily">Diaria</option><option value="weekly">Semanal</option></select><small>Cada cuánto tiempo se creará una copia automática.</small></label><label>Máximo de copias<input type="number" min="1" max="2147483647" step="1" value={maximo} disabled={ocupado} onChange={(evento) => setMaximo(evento.target.value)} /><small>Se conservarán únicamente las copias más recientes.</small></label></div><p>Las copias incluyen siempre la base de datos y las imágenes de recetas, comidas y productos. La retención se aplica al conjunto de copias cuando se ejecuta la automatización.</p>{!valido && <Message tone="error">Introduce un número entero entre 1 y 2147483647.</Message>}</> : <><p>{dialogo === "restaurar" ? "Se reemplazarán los datos actuales por el contenido de esta copia de seguridad." : "Se eliminará definitivamente esta copia de seguridad."}</p>{seleccionada && <dl className="copias-detalle"><dt>Copia</dt><dd>{seleccionada.filename}</dd><dt>Fecha de creación</dt><dd>{fecha(seleccionada)}</dd><dt>Tamaño</dt><dd>{tamano(seleccionada.size)}</dd></dl>}{dialogo === "restaurar" && <><p className="copias-advertencia">⚠ Te recomendamos crear una copia de seguridad actual antes de continuar.</p><small>Si falla la restauración de la base de datos o las imágenes, la recuperación deberá realizarse manualmente.</small></>}</>}
      {error && <Message tone="error">{error}</Message>}
      <div className="copias-acciones copias-dialogo-pie"><Button variant="secondary" disabled={ocupado} onClick={() => setDialogo(null)}>Cancelar</Button><Button variant={dialogo === "eliminar" ? "danger" : "primary"} disabled={ocupado || (dialogo === "automatizacion" && (!valido || !cambios))} onClick={() => void ejecutar(dialogo)}>{ocupado ? "Procesando…" : dialogo === "automatizacion" ? "Guardar automatización" : dialogo === "restaurar" ? "Confirmar restauración" : "Confirmar eliminación"}</Button></div>{ocupado && <p role="status">Operación en curso. Espera a que termine.</p>}
    </Dialogo>}
  </section></main>;
}
