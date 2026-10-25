import type { HTMLAttributes } from "react";

export type PanelProps = Omit<HTMLAttributes<HTMLElement>, "className"> & {
  /** Constrains the panel to a centered, narrow column (used by auth forms). */
  narrow?: boolean;
};

export default function Panel({ narrow = false, ...props }: PanelProps) {
  return <section className={`ui-panel${narrow ? " narrow" : ""}`} {...props} />;
}
