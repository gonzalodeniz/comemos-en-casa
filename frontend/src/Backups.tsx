// Permite iniciar una copia manual y comunica el resultado de la operación.
import { useEffect, useState } from "react";
import { apiRequest, ApiError } from "./api";

type Props = { csrfToken: string; onSessionExpired: () => void };

export default function Backups({ csrfToken, onSessionExpired }: Props) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [backups, setBackups] = useState<{ filename: string; size: number }[]>([]);
  const [restoreTarget, setRestoreTarget] = useState("");
  const [restoring, setRestoring] = useState(false);
  const [frequency, setFrequency] = useState<"daily" | "weekly">("daily");
  const [maximum, setMaximum] = useState("3");
  const [savingSchedule, setSavingSchedule] = useState(false);

  useEffect(() => {
    void apiRequest<{ backups: { filename: string; size: number }[] }>("/backups").then((result) => setBackups(result.backups)).catch((cause) => {
      if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
      setError("No se pudieron cargar las copias de seguridad.");
    });
  }, [onSessionExpired]);

  async function createBackup() {
    setLoading(true);
    setMessage("");
    setError("");
    try {
      const result = await apiRequest<{ filename: string }>("/backups", { method: "POST", csrfToken, body: {} });
      setMessage(`Copia creada: ${result.filename}`);
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
      setError("No se pudo crear la copia de seguridad.");
    } finally {
      setLoading(false);
    }
  }

  async function restoreBackup() {
    setRestoring(true);
    setError("");
    setMessage("");
    try {
      await apiRequest(`/backups/${encodeURIComponent(restoreTarget)}/restore`, { method: "POST", csrfToken, body: {} });
      setMessage(`Copia restaurada: ${restoreTarget}`);
      setRestoreTarget("");
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
      setError(cause instanceof ApiError ? cause.message : "La restauración falló; la recuperación debe realizarse manualmente.");
    } finally {
      setRestoring(false);
    }
  }

  // Guarda la frecuencia y el máximo global de copias conservadas.
  async function saveSchedule() {
    setSavingSchedule(true);
    setError("");
    setMessage("");
    try {
      await apiRequest("/backups/schedule", { method: "POST", csrfToken, body: { frequency, maximum: Number(maximum) } });
      setMessage("Configuración guardada.");
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) onSessionExpired();
      setError(cause instanceof Error ? cause.message : "No se pudo guardar la configuración.");
    } finally {
      setSavingSchedule(false);
    }
  }

  return <main className="dashboard"><section className="panel"><h2>Copias de seguridad</h2><p>Crea una copia de la base de datos y las imágenes.</p><button type="button" disabled={loading} onClick={() => void createBackup()}>{loading ? "Creando copia…" : "Crear copia"}</button>{message && <p role="status">{message}</p>}{error && <p className="message error" role="alert">{error}</p>}<h3>Automatización</h3><label>Frecuencia<select aria-label="Frecuencia" value={frequency} onChange={(event) => setFrequency(event.target.value as "daily" | "weekly")}><option value="daily">Diaria</option><option value="weekly">Semanal</option></select></label><label>Máximo de copias<input aria-label="Máximo de copias" type="number" min="1" step="1" value={maximum} onChange={(event) => setMaximum(event.target.value)} /></label><button type="button" disabled={savingSchedule || !/^\d+$/.test(maximum) || Number(maximum) < 1} onClick={() => void saveSchedule()}>{savingSchedule ? "Guardando…" : "Guardar automatización"}</button><h3>Copias disponibles</h3>{backups.length ? <ul>{backups.map((backup) => <li key={backup.filename}>{backup.filename} ({backup.size} bytes) <a href={`/comemos/api/v1/backups/${encodeURIComponent(backup.filename)}`} download={backup.filename}>Descargar</a> <button type="button" onClick={() => setRestoreTarget(backup.filename)}>Restaurar copia</button></li>)}</ul> : <p>No hay copias disponibles.</p>}{restoreTarget && <div role="dialog" aria-modal="true" aria-labelledby="restore-title"><h3 id="restore-title">¿Restaurar esta copia?</h3><p>Se reemplazarán los datos actuales. Si la restauración falla, la recuperación deberá realizarse manualmente.</p><button type="button" disabled={restoring} onClick={() => setRestoreTarget("")}>Cancelar</button><button type="button" disabled={restoring} onClick={() => void restoreBackup()}>{restoring ? "Restaurando…" : "Confirmar restauración"}</button></div>}</section></main>;
}
