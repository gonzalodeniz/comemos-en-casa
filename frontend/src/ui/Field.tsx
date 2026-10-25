import type { ReactNode } from "react";

export type FieldProps = {
  /** Visible label text. */
  label: string;
  /** Optional helper text shown under the control. */
  hint?: string;
  /** The form control (`input` or `select`) to label. */
  children: ReactNode;
};

export default function Field({ label, hint, children }: FieldProps) {
  return (
    <label className="ui-field">
      {label}
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}
