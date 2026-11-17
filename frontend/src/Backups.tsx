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

  return <main className="dashboard"><section className="panel"><h2>Copias de seguridad</h2><p>Crea una copia de la base de datos y las imágenes.</p><button type="button" disabled={loading} onClick={() => void createBackup()}>{loading ? "Creando copia…" : "Crear copia"}</button>{message && <p role="status">{message}</p>}{error && <p className="message error" role="alert">{error}</p>}<h3>Copias disponibles</h3>{backups.length ? <ul>{backups.map((backup) => <li key={backup.filename}>{backup.filename} ({backup.size} bytes) <a href={`/comemos/api/v1/backups/${encodeURIComponent(backup.filename)}`} download={backup.filename}>Descargar</a> <button type="button" onClick={() => setRestoreTarget(backup.filename)}>Restaurar copia</button></li>)}</ul> : <p>No hay copias disponibles.</p>}{restoreTarget && <div role="dialog" aria-modal="true" aria-labelledby="restore-title"><h3 id="restore-title">¿Restaurar esta copia?</h3><p>Se reemplazarán los datos actuales. Si la restauración falla, la recuperación deberá realizarse manualmente.</p><button type="button" disabled={restoring} onClick={() => setRestoreTarget("")}>Cancelar</button><button type="button" disabled={restoring} onClick={() => void restoreBackup()}>{restoring ? "Restaurando…" : "Confirmar restauración"}</button></div>}</section></main>;
}
