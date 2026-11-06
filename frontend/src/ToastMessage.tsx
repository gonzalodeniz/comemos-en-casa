import { useEffect, useState } from "react";

type Props = { kind: "success" | "error"; children: string; onClose: () => void; duration?: number };

/** Muestra un aviso flotante que se puede cerrar o que desaparece automáticamente. */
export default function ToastMessage({ kind, children, onClose, duration = 5000 }: Props) {
  const [leaving, setLeaving] = useState(false);
  useEffect(() => {
    const salida = window.setTimeout(() => setLeaving(true), duration);
    return () => window.clearTimeout(salida);
  }, [duration]);
  useEffect(() => {
    if (!leaving) return;
    const cierre = window.setTimeout(onClose, 300);
    return () => window.clearTimeout(cierre);
  }, [leaving, onClose]);
  return <div className={`message ${kind} toast ${leaving ? "toast-leaving" : ""}`} role={kind === "error" ? "alert" : "status"}>
    <span>{children}</span>
    <button type="button" aria-label="Cerrar mensaje" onClick={onClose}>×</button>
  </div>;
}
