// Permite iniciar una copia manual y comunica el resultado de la operación.
import { useState } from "react";
import { apiRequest, ApiError } from "./api";

type Props = { csrfToken: string; onSessionExpired: () => void };

export default function Backups({ csrfToken, onSessionExpired }: Props) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

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

  return <main className="dashboard"><section className="panel"><h2>Copias de seguridad</h2><p>Crea una copia de la base de datos y las imágenes.</p><button type="button" disabled={loading} onClick={() => void createBackup()}>{loading ? "Creando copia…" : "Crear copia"}</button>{message && <p role="status">{message}</p>}{error && <p className="message error" role="alert">{error}</p>}</section></main>;
}
