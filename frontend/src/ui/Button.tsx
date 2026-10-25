import type { ButtonHTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "danger" | "link";

export type ButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> & {
  /** Visual emphasis of the button. Defaults to `primary`. */
  variant?: ButtonVariant;
};

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: "",
  secondary: " secondary",
  danger: " danger",
  link: " link-button",
};

export default function Button({ variant = "primary", type = "button", ...props }: ButtonProps) {
  return <button type={type} className={`ui-button${VARIANT_CLASS[variant]}`} {...props} />;
}
