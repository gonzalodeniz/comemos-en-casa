// Presenta el catálogo consultable de trucos de cocina.
import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "./api";

type Truco = { id: string; title: string; content: string };
type Props = { onSessionExpired: () => void };

export default function KitchenTips({ onSessionExpired }: Props) {
  const [trucos, setTrucos] = useState<Truco[]>([]);
  const [seleccionado, setSeleccionado] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelado = false;
    void apiRequest<{ trucos: Truco[] }>("/kitchen-tips").then((resultado) => {
      if (!cancelado) {
        setTrucos(resultado.trucos);
        setSeleccionado(resultado.trucos[0]?.id ?? null);
      }
    }).catch((causa: unknown) => {
      if (cancelado) return;
      if (causa instanceof ApiError && causa.status === 401) onSessionExpired();
      else setError("No se pudieron cargar los trucos.");
    });
    return () => { cancelado = true; };
  }, [onSessionExpired]);

  const trucoActual = trucos.find((truco) => truco.id === seleccionado);
  return <main className="dashboard">
    <section className="panel">
      <p className="eyebrow">Consejos prácticos</p>
      <h2>Trucos de cocina</h2>
      {error && <p className="message error" role="alert">{error}</p>}
      {!error && trucos.length === 0 && <p role="status">Cargando trucos…</p>}
      {trucos.length > 0 && <div className="kitchen-tips">
        <nav aria-label="Trucos disponibles">
          {trucos.map((truco) => <button key={truco.id} type="button" aria-current={seleccionado === truco.id ? "true" : undefined} onClick={() => setSeleccionado(truco.id)}>{truco.title}</button>)}
        </nav>
        {trucoActual && <article aria-live="polite"><h3>{trucoActual.title}</h3><p>{trucoActual.content}</p></article>}
      </div>}
    </section>
  </main>;
}
