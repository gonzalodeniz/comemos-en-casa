import type { ReactNode } from "react";

export type MessageTone = "error" | "success";

export type MessageProps = {
  /** `error` is announced as an alert, `success` as a status update. */
  tone: MessageTone;
  children: ReactNode;
};

export default function Message({ tone, children }: MessageProps) {
  return (
    <p className={`ui-message ${tone}`} role={tone === "error" ? "alert" : "status"}>
      {children}
    </p>
  );
}
