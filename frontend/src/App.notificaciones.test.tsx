// Verifica que el perfil guarda la preferencia de correo de la cuenta autenticada.
// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";
import { apiRequest } from "./api";

const estado = vi.hoisted(() => ({ usuario: { id: "1", name: "Persona", email: "p@example.test", is_active: true, recordatorios_correo: true, recordatorios_push: false } }));
vi.mock("./api", () => ({
  ApiError: class extends Error {},
  apiRequest: vi.fn(async (ruta: string, opciones?: { body?: object }) => {
    if (ruta === "/auth/session") return { user: estado.usuario, csrf_token: "token", ultima_vista: "users" };
    if (ruta === "/users") return { users: [estado.usuario] };
    if (ruta === "/push/public-key") return { public_key: "BA" };
    if (ruta === "/push/subscriptions") return null;
    if (ruta === "/push/subscriptions/status") return { active: true };
    if (ruta === "/push/test") return null;
    if (ruta === "/users/1") { Object.assign(estado.usuario, opciones?.body); return { user: estado.usuario }; }
    throw new Error(`Petición inesperada: ${ruta}`);
  }),
}));
vi.mock("./AppWorkspace", () => ({ default: ({ userManagement }: { userManagement: React.ReactNode }) => <div>{userManagement}</div> }));
afterEach(() => { cleanup(); estado.usuario.recordatorios_correo = true; estado.usuario.recordatorios_push = false; vi.unstubAllGlobals(); Reflect.deleteProperty(navigator, "serviceWorker"); vi.clearAllMocks(); });

it("guarda y recupera la elección de correo del perfil", async () => {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  const correo = screen.getByRole("checkbox", { name: "Recordatorios por correo" });
  expect((correo as HTMLInputElement).checked).toBe(true);
  fireEvent.click(correo);
  fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
  await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/users/1", expect.objectContaining({ body: expect.objectContaining({ recordatorios_correo: false }) })));
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  expect((screen.getByRole("checkbox", { name: "Recordatorios por correo" }) as HTMLInputElement).checked).toBe(false);
});

// Comprueba que la campana envía una prueba solo cuando push está seleccionado.
it("muestra la campana y solicita una notificación de prueba", async () => {
  estado.usuario.recordatorios_push = true;
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("button", { name: "Probar notificación móvil" }));
  await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/push/test", { method: "POST", csrfToken: "token" }));
  expect(await screen.findByText("Notificación de prueba enviada." )).toBeTruthy();
  fireEvent.click(screen.getByRole("checkbox", { name: "Notificaciones móviles" }));
  expect(screen.queryByRole("button", { name: "Probar notificación móvil" })).toBeNull();
  estado.usuario.recordatorios_push = false;
});

// Comprueba que un fallo del servidor no se comunica como envío correcto.
it("informa si falla el envío de la notificación de prueba", async () => {
  estado.usuario.recordatorios_push = true;
  vi.mocked(apiRequest).mockImplementationOnce(async () => ({ user: estado.usuario, csrf_token: "token", ultima_vista: "users" }))
    .mockImplementationOnce(async () => ({ users: [estado.usuario] }))
    .mockRejectedValueOnce(new Error("notificación no disponible"));
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("button", { name: "Probar notificación móvil" }));
  expect(await screen.findByText(/No se pudo enviar la notificación de prueba/)).toBeTruthy();
});

// Comprueba que rechazar el permiso no altera la preferencia del correo.
it("informa si se rechaza el permiso de notificaciones móviles", async () => {
  vi.stubGlobal("Notification", { permission: "default", requestPermission: vi.fn().mockResolvedValue("denied") });
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: {} });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("checkbox", { name: "Notificaciones móviles" }));
  expect(await screen.findByText(/notificaciones móviles no están activas/i)).toBeTruthy();
  expect((screen.getByRole("checkbox", { name: "Recordatorios por correo" }) as HTMLInputElement).checked).toBe(true);
  expect((screen.getByRole("checkbox", { name: "Notificaciones móviles" }) as HTMLInputElement).checked).toBe(false);
  vi.unstubAllGlobals();
  Reflect.deleteProperty(navigator, "serviceWorker");
});

// Comprueba que el navegador informa de la ausencia de soporte push.
it("informa cuando el dispositivo no admite notificaciones móviles", async () => {
  vi.stubGlobal("Notification", undefined);
  Reflect.deleteProperty(navigator, "serviceWorker");
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("checkbox", { name: "Notificaciones móviles" }));
  expect(await screen.findByText(/notificaciones móviles no están activas/i)).toBeTruthy();
  expect((screen.getByRole("checkbox", { name: "Recordatorios por correo" }) as HTMLInputElement).checked).toBe(true);
  vi.unstubAllGlobals();
});

// Comprueba los errores inesperados al solicitar permiso al sistema.
it("informa si falla la solicitud del permiso de notificaciones", async () => {
  vi.stubGlobal("Notification", { requestPermission: vi.fn().mockRejectedValue(new Error("permission unavailable")) });
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: {} });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("checkbox", { name: "Notificaciones móviles" }));
  expect(await screen.findByText(/notificaciones móviles no están activas/i)).toBeTruthy();
  vi.unstubAllGlobals();
  Reflect.deleteProperty(navigator, "serviceWorker");
});

// Comprueba el registro del dispositivo antes de activar la preferencia.
it("registra el dispositivo y guarda las notificaciones móviles", async () => {
  vi.stubGlobal("Notification", { permission: "default", requestPermission: vi.fn().mockResolvedValue("granted") });
  const suscripcion = { endpoint: "https://fcm.googleapis.com/fcm/send/example", keys: { p256dh: "clave", auth: "secreto" } };
  const dispositivo = { endpoint: suscripcion.endpoint, toJSON: () => suscripcion, unsubscribe: vi.fn().mockResolvedValue(true) };
  const registro = { active: { state: "activated" }, pushManager: { getSubscription: vi.fn().mockResolvedValue(null), subscribe: vi.fn().mockResolvedValue(dispositivo) } };
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: { register: vi.fn().mockResolvedValue(registro), ready: Promise.resolve(registro) } });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("checkbox", { name: "Notificaciones móviles" }));
  await waitFor(() => expect((screen.getByRole("checkbox", { name: "Notificaciones móviles" }) as HTMLInputElement).checked).toBe(true));
  expect(apiRequest).toHaveBeenCalledWith("/push/subscriptions", expect.objectContaining({ method: "POST", body: suscripcion }));
  fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
  await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/users/1", expect.objectContaining({ body: expect.objectContaining({ recordatorios_push: true }) })));
  vi.unstubAllGlobals();
  Reflect.deleteProperty(navigator, "serviceWorker");
});

// Comprueba que desactivar push retira la suscripción del dispositivo.
it("desactiva y retira la suscripción de este dispositivo", async () => {
  estado.usuario.recordatorios_push = true;
  const dispositivo = { endpoint: "https://fcm.googleapis.com/fcm/send/example", unsubscribe: vi.fn().mockResolvedValue(true) };
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: { getRegistration: vi.fn().mockResolvedValue({ pushManager: { getSubscription: vi.fn().mockResolvedValue(dispositivo) } }) } });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("checkbox", { name: "Notificaciones móviles" }));
  fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
  await waitFor(() => expect(dispositivo.unsubscribe).toHaveBeenCalled());
  expect(apiRequest).toHaveBeenCalledWith("/push/subscriptions", expect.objectContaining({ method: "DELETE", body: { endpoint: dispositivo.endpoint } }));
  estado.usuario.recordatorios_push = false;
  Reflect.deleteProperty(navigator, "serviceWorker");
});

// Comprueba que cancelar la edición no modifica la suscripción guardada.
it("conserva la suscripción al cancelar la desactivación", async () => {
  estado.usuario.recordatorios_push = true;
  const dispositivo = { endpoint: "https://fcm.googleapis.com/fcm/send/example", unsubscribe: vi.fn().mockResolvedValue(true) };
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: { getRegistration: vi.fn().mockResolvedValue({ pushManager: { getSubscription: vi.fn().mockResolvedValue(dispositivo) } }) } });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("checkbox", { name: "Notificaciones móviles" }));
  fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
  await waitFor(() => expect(apiRequest).not.toHaveBeenCalledWith("/push/subscriptions", expect.objectContaining({ method: "DELETE" })));
  expect(dispositivo.unsubscribe).not.toHaveBeenCalled();
  estado.usuario.recordatorios_push = false;
  Reflect.deleteProperty(navigator, "serviceWorker");
});

// Comprueba el alta de otro móvil cuando la cuenta ya tiene push activado.
it("permite activar otro dispositivo con push habilitado en la cuenta", async () => {
  estado.usuario.recordatorios_push = true;
  vi.stubGlobal("Notification", { permission: "default", requestPermission: vi.fn().mockResolvedValue("granted") });
  const suscripcion = { endpoint: "https://fcm.googleapis.com/fcm/send/otro", keys: { p256dh: "clave", auth: "secreto" } };
  const registro = { active: { state: "activated" }, pushManager: { getSubscription: vi.fn().mockResolvedValue(null), subscribe: vi.fn().mockResolvedValue({ toJSON: () => suscripcion }) } };
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: { register: vi.fn().mockResolvedValue(registro), ready: new Promise(() => {}) } });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(screen.getByRole("button", { name: "Activar en este dispositivo" }));
  await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/push/subscriptions", expect.objectContaining({ method: "POST", body: suscripcion })));
  expect(await screen.findByText("Notificaciones móviles activadas en este dispositivo.")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Desactivar en este dispositivo" })).toBeTruthy();
  estado.usuario.recordatorios_push = false;
  vi.unstubAllGlobals();
  Reflect.deleteProperty(navigator, "serviceWorker");
});

// Comprueba que el perfil sale del estado de espera si la instalación falla.
it("informa del fallo y permite reintentar si el worker queda descartado", async () => {
  estado.usuario.recordatorios_push = true;
  vi.stubGlobal("Notification", { requestPermission: vi.fn().mockResolvedValue("granted") });
  const worker = Object.assign(new EventTarget(), { state: "installing" });
  const register = vi.fn().mockResolvedValue({ installing: worker });
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: { register, ready: new Promise(() => {}) } });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  const boton = screen.getByRole<HTMLButtonElement>("button", { name: "Activar en este dispositivo" });
  fireEvent.click(boton);
  expect(boton.disabled).toBe(true);
  expect(screen.getByText("Activando notificaciones móviles…")).toBeTruthy();
  await waitFor(() => expect(register).toHaveBeenCalled());
  await act(async () => {
    worker.state = "redundant";
    worker.dispatchEvent(new Event("statechange"));
  });
  expect(await screen.findByText(/no están activas en este dispositivo/)).toBeTruthy();
  expect(boton.disabled).toBe(false);
  expect(apiRequest).not.toHaveBeenCalledWith("/push/subscriptions", expect.anything());
});

// Comprueba que retirar este navegador conserva la preferencia de la cuenta.
it("desactiva solo el dispositivo y vuelve a mostrar la opción de activarlo", async () => {
  estado.usuario.recordatorios_push = true;
  const suscripcion = { endpoint: "https://fcm.googleapis.com/fcm/send/uno", unsubscribe: vi.fn().mockResolvedValue(true) };
  const registro = { pushManager: { getSubscription: vi.fn().mockResolvedValue(suscripcion) } };
  Object.defineProperty(navigator, "serviceWorker", { configurable: true, value: { getRegistration: vi.fn().mockResolvedValue(registro) } });
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Editar perfil" }));
  fireEvent.click(await screen.findByRole("button", { name: "Desactivar en este dispositivo" }));
  expect(await screen.findByRole("button", { name: "Activar en este dispositivo" })).toBeTruthy();
  expect(apiRequest).toHaveBeenCalledWith("/push/subscriptions", { method: "DELETE", csrfToken: "token", body: { endpoint: suscripcion.endpoint } });
  expect(suscripcion.unsubscribe).toHaveBeenCalled();
  expect((screen.getByRole("checkbox", { name: "Notificaciones móviles" }) as HTMLInputElement).checked).toBe(true);
});
