// Presenta el catálogo consultable de trucos de cocina.
import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "./api";

type Truco = { id: string; title: string; content: string };
type Props = { onSessionExpired: () => void };

export default function KitchenTips({ onSessionExpired }: Props) {
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

  const trucoActual = trucos.find((truco) => truco.id === seleccionado);
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
      setEditando(null);
      setTitulo("");
      setContenido("");
      setErrorFormulario("");
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
  return <main className="dashboard">
    <section className="panel">
      <p className="eyebrow">Consejos prácticos</p>
      <h2>Trucos de cocina</h2>
      {error && <p className="message error" role="alert">{error}</p>}
      {!error && cargando && trucos.length === 0 && <p role="status">Cargando trucos…</p>}
      {!error && !cargando && trucos.length === 0 && <p role="status">No hay trucos de cocina todavía.</p>}
      {trucos.length > 0 && <div className="kitchen-tips">
        <nav aria-label="Trucos disponibles">
          {trucos.map((truco) => <button key={truco.id} type="button" aria-current={seleccionado === truco.id ? "true" : undefined} onClick={() => setSeleccionado(truco.id)}>{truco.title}</button>)}
        </nav>
        {trucoActual && <article aria-live="polite"><h3>{trucoActual.title}</h3><p>{trucoActual.content}</p><button type="button" onClick={() => { setEditando(trucoActual.id); setTitulo(trucoActual.title); setContenido(trucoActual.content); setErrorFormulario(""); }}>Editar truco</button><button type="button" onClick={() => void eliminarTruco()}>Eliminar truco</button></article>}
      </div>}
      <form onSubmit={guardarTruco}>
        <label>Título<input value={titulo} onChange={(evento) => setTitulo(evento.target.value)} /></label>
        <label>Contenido<textarea value={contenido} onChange={(evento) => setContenido(evento.target.value)} /></label>
        {errorFormulario && <p role="alert">{errorFormulario}</p>}
        <button type="submit">{editando ? "Guardar cambios" : "Guardar truco"}</button>
      </form>
    </section>
  </main>;
}
