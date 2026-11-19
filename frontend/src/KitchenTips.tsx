// Presenta el catálogo consultable de trucos de cocina.
import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "./api";
import AppIcon from "./AppIcon";

type Truco = { id: string; title: string; content: string };
type Props = { onSessionExpired: () => void };

export default function KitchenTips({ onSessionExpired }: Props) {
  const [busqueda, setBusqueda] = useState("");
  const [trucos, setTrucos] = useState<Truco[]>([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [titulo, setTitulo] = useState("");
  const [contenido, setContenido] = useState("");
  const [errorFormulario, setErrorFormulario] = useState("");
  const [editando, setEditando] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    void apiRequest<{ trucos: Truco[] }>("/kitchen-tips").then((resultado) => {
      if (!cancelado) {
        setTrucos(resultado.trucos);
        setSeleccionado(resultado.trucos[0]?.id ?? null);
        setCargando(false);
      }
    }).catch((causa: unknown) => {
      if (cancelado) return;
      if (causa instanceof ApiError && causa.status === 401) onSessionExpired();
      else { setError("No se pudieron cargar los trucos."); setCargando(false); }
    });
    return () => { cancelado = true; };
  }, [onSessionExpired]);

  // Filtra únicamente la presentación, sin cambiar la selección ni los datos guardados.
  const consulta = normalizarBusqueda(busqueda.trim());
  const visibles = trucos.filter((truco) => normalizarBusqueda(`${truco.title} ${truco.content}`).includes(consulta));
  const trucoActual = trucos.find((truco) => truco.id === seleccionado);
  // Descarta el borrador y devuelve el formulario al modo de creación.
  function limpiarFormulario() {
    setEditando(null);
    setTitulo("");
    setContenido("");
    setErrorFormulario("");
  }

  async function guardarTruco(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const tituloLimpio = titulo.trim();
    const contenidoLimpio = contenido.trim();
    if (!tituloLimpio || !contenidoLimpio) {
      setErrorFormulario(!tituloLimpio ? "El título es obligatorio." : "El contenido es obligatorio.");
      return;
    }
    try {
      const nuevo = await apiRequest<Truco>(editando ? `/kitchen-tips/${editando}` : "/kitchen-tips", {
        method: editando ? "PATCH" : "POST", body: { title: tituloLimpio, content: contenidoLimpio },
      });
      setTrucos((actuales) => [...actuales.filter((truco) => truco.id !== nuevo.id), nuevo].sort((a, b) => a.title.localeCompare(b.title)));
      setSeleccionado(nuevo.id);
      limpiarFormulario();
    } catch (causa) {
      if (causa instanceof ApiError && causa.status === 401) onSessionExpired();
      else setErrorFormulario("No se pudo guardar el truco.");
    }
  }
  /** Confirma y elimina el truco seleccionado del catálogo compartido. */
  async function eliminarTruco() {
    if (!trucoActual || !window.confirm(`¿Eliminar definitivamente «${trucoActual.title}»?`)) return;
    try {
      await apiRequest(`/kitchen-tips/${trucoActual.id}`, { method: "DELETE" });
      const restantes = trucos.filter((truco) => truco.id !== trucoActual.id);
      setTrucos(restantes);
      setSeleccionado(restantes[0]?.id ?? null);
    } catch (causa) {
      if (causa instanceof ApiError && causa.status === 401) onSessionExpired();
      else setError("No se pudo eliminar el truco.");
    }
  }
  return <main className="kitchen-tips-page">
    <section className="panel kitchen-tips-panel" aria-labelledby="trucos-titulo">
      <header>
        <p className="eyebrow">Consejos prácticos</p>
        <h2 id="trucos-titulo">Trucos de cocina</h2>
        <p>Pequeños consejos para hacerte más fácil el día a día en la cocina.</p>
      </header>
      <div className="kitchen-tips-search">
        <AppIcon name="search" />
        <input type="search" aria-label="Buscar trucos" placeholder="Buscar truco…" value={busqueda}
          onChange={(evento) => setBusqueda(evento.target.value)} />
      </div>
      {error && <p className="message error" role="alert">{error}</p>}
      {!error && cargando && <p role="status">Cargando trucos…</p>}
      {!error && !cargando && trucos.length === 0 && <p role="status">No hay trucos de cocina todavía.</p>}
      {trucos.length > 0 && visibles.length === 0 && <p role="status">No se encontraron trucos con esa búsqueda.</p>}
      {visibles.length > 0 && <nav className="kitchen-tips-list" aria-label="Trucos disponibles">
        {visibles.map((truco) => <button key={truco.id} type="button" aria-label={truco.title}
          aria-current={seleccionado === truco.id ? "true" : undefined} onClick={() => setSeleccionado(truco.id)}>
          <span className="kitchen-tips-mark"><AppIcon name="utensils" /></span>
          <span><strong>{truco.title}</strong><small>{truco.content}</small></span>
          {seleccionado === truco.id && <AppIcon name="check" className="kitchen-tips-selected" />}
        </button>)}
      </nav>}
      {trucoActual && <article className="kitchen-tip-detail" aria-live="polite">
        <header>
          <div>
            <span className="kitchen-tip-badge"><AppIcon name="utensils" /> Consejo de cocina</span>
            <h3>{trucoActual.title}</h3>
          </div>
          <div className="kitchen-tip-actions">
            <button type="button" aria-label={`Editar truco ${trucoActual.title}`} title="Editar truco"
              onClick={() => { setEditando(trucoActual.id); setTitulo(trucoActual.title); setContenido(trucoActual.content); setErrorFormulario(""); }}>
              <AppIcon name="edit" />
            </button>
            <button type="button" aria-label={`Eliminar truco ${trucoActual.title}`} title="Eliminar truco"
              onClick={() => void eliminarTruco()}><AppIcon name="trash" /></button>
          </div>
        </header>
        <p>{trucoActual.content}</p>
      </article>}
    </section>
    <section className="panel kitchen-tip-form-panel" aria-label={editando ? "Editar truco" : "Añadir truco"}>
      <header>
        <div className="kitchen-tip-illustration" aria-hidden="true">
          <svg viewBox="0 0 220 104" fill="none" focusable="false">
            <ellipse cx="110" cy="52" rx="108" ry="50" fill="#eaf6ef" />
            <path d="M66 49H148L144 74Q143 84 132 84H82Q71 84 70 74Z" fill="#9ed3ad" stroke="#378750" strokeWidth="2" />
            <path d="M62 49H152M69 48Q77 35 107 35T145 48M100 35V31Q100 25 107 25T114 31V35M65 57H54M149 57H160M79 57L81 70" stroke="#378750" strokeWidth="3" strokeLinecap="round" />
            <path d="M166 36L172 24M175 42L188 36M177 51L191 51" stroke="#4f9a5d" strokeWidth="3" strokeLinecap="round" />
          </svg>
        </div>
        <h2>{editando ? "Editar truco" : "Añadir un truco"}</h2>
        <p>{editando ? "Actualiza los pasos o el título de tu consejo." : "Comparte un consejo práctico que te ayude en la cocina."}</p>
      </header>
      <form onSubmit={guardarTruco}>
        <label>Título<input placeholder="Ej. Conservar el aguacate" value={titulo} onChange={(evento) => setTitulo(evento.target.value)} /></label>
        <label>Contenido<textarea rows={6} placeholder="Explica el truco paso a paso…" value={contenido} onChange={(evento) => setContenido(evento.target.value)} /></label>
        <aside className="kitchen-tip-help">
          <AppIcon name="bulb" />
          <div><strong>Consejo</strong><p>Sé claro y breve e incluye los pasos necesarios para que sea fácil de seguir.</p></div>
        </aside>
        {errorFormulario && <p className="message error" role="alert">{errorFormulario}</p>}
        <div className="kitchen-tip-form-actions">
          <button type="submit" aria-label={editando ? "Guardar cambios" : "Guardar truco"} title={editando ? "Guardar cambios" : "Guardar truco"}>
            <AppIcon name="check" />
          </button>
          {editando && <button type="button" className="secondary kitchen-tip-cancel" aria-label="Cancelar edición" title="Cancelar edición" onClick={limpiarFormulario}><AppIcon name="close" /></button>}
        </div>
      </form>
    </section>
  </main>;
}

// Permite encontrar palabras aunque la búsqueda no incluya tildes.
function normalizarBusqueda(texto: string) {
  return texto.toLocaleLowerCase("es").normalize("NFD").replace(/\p{Diacritic}/gu, "");
}
