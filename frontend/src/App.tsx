// Presenta los flujos de acceso y administración de cuentas.
// Coordina la sesión, formularios, recuperación de contraseña y operaciones de usuario con la API, manteniendo los estados de carga y error.

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { apiRequest, ApiError, type User, type UserResponse } from "./api";
import MealPlanning from "./MealPlanning";
import AppWorkspace, { type AppView } from "./AppWorkspace";
import AppBrand from "./AppBrand";
import AppIcon from "./AppIcon";
import "./App.css";

type Screen = "loading" | "register" | "login" | "reset-request" | "reset-confirm" | "app";
type SessionResponse = { user: Omit<User, "is_active">; csrf_token: string };

function field(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value : "";
}

export default function App() {
  const [screen, setScreen] = useState<Screen>("loading");
  const [view, setView] = useState<AppView>("meal-planning");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [csrfToken, setCsrfToken] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [resetToken, setResetToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const mealSessionExpired = useCallback(() => {
    setCurrentUser(null);
    setCsrfToken("");
    setUsers([]);
    setScreen("login");
    setError("La sesión ha caducado. Inicia sesión de nuevo.");
    setNotice("");
  }, []);

  const loadUsers = useCallback(async () => {
    const result = await apiRequest<{ users: User[] }>("/users");
    setUsers(result.users);
  }, []);

  const refreshSession = useCallback(async () => {
    // Recupera también el token CSRF de la sesión antes de cargar recursos autenticados.
    const session = await apiRequest<SessionResponse>("/auth/session");
    setCurrentUser({ ...session.user, is_active: true });
    setCsrfToken(session.csrf_token);
    setView("meal-planning");
    setScreen("app");
    await loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    // Un enlace de restablecimiento prevalece sobre la consulta inicial de sesión.
    let cancelled = false;
    const token = new URLSearchParams(window.location.search).get("reset_token") ?? "";
    setResetToken(token);
    if (token) {
      setScreen("reset-confirm");
      return () => {
        cancelled = true;
      };
    }

    void (async () => {
      try {
        await refreshSession();
      } catch {
        try {
          const bootstrap = await apiRequest<{ initial_account_required: boolean }>(
            "/auth/bootstrap",
          );
          if (!cancelled) setScreen(bootstrap.initial_account_required ? "register" : "login");
        } catch {
          if (!cancelled) {
            setError("No se pudo conectar con el servicio. Comprueba la conexión e inténtalo de nuevo.");
            setScreen("login");
          }
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshSession]);

  async function perform(action: () => Promise<void>) {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        setCurrentUser(null);
        setCsrfToken("");
        setUsers([]);
        setScreen("login");
      }
      setError(cause instanceof Error ? cause.message : "No se pudo completar la operación.");
    } finally {
      setLoading(false);
    }
  }

  function submitForm(event: FormEvent<HTMLFormElement>, action: (form: FormData) => Promise<void>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    void perform(() => action(form));
  }

  async function createInitialAccount(form: FormData) {
    await apiRequest<UserResponse>("/auth/register-initial", {
      method: "POST",
      body: {
        name: field(form, "name"),
        email: field(form, "email"),
        password: field(form, "password"),
      },
    });
    setScreen("login");
    setNotice("La cuenta está creada. Inicia sesión para continuar.");
  }

  async function signIn(form: FormData) {
    await apiRequest<UserResponse>("/auth/login", {
      method: "POST",
      body: { email: field(form, "email"), password: field(form, "password") },
    });
    await refreshSession();
    setNotice("");
  }

  async function signOut() {
    await apiRequest<null>("/auth/logout", {
      method: "POST",
      csrfToken,
    });
    setCurrentUser(null);
    setCsrfToken("");
    setUsers([]);
    setScreen("login");
    setNotice("Has cerrado la sesión.");
  }

  async function requestReset(form: FormData) {
    const result = await apiRequest<{ message: string }>("/password-resets", {
      method: "POST",
      body: { email: field(form, "email") },
    });
    setNotice(result.message);
  }

  async function confirmReset(form: FormData) {
    await apiRequest<null>("/password-resets/confirm", {
      method: "POST",
      body: { token: resetToken, new_password: field(form, "password") },
    });
    window.history.replaceState({}, "", window.location.pathname);
    setResetToken("");
    setScreen("login");
    setNotice("Contraseña actualizada. Inicia sesión con la nueva contraseña.");
  }

  async function createUser(form: FormData) {
    await apiRequest<UserResponse>("/users", {
      method: "POST",
      csrfToken,
      body: {
        name: field(form, "name"),
        email: field(form, "email"),
        password: field(form, "password"),
      },
    });
    await loadUsers();
    setNotice("Usuario creado.");
  }

  async function updateUser(userId: string, form: FormData) {
    await apiRequest<UserResponse>(`/users/${userId}`, {
      method: "PATCH",
      csrfToken,
      body: { name: field(form, "name"), email: field(form, "email") },
    });
    await loadUsers();
    if (userId === currentUser?.id) {
      const updated = users.find((user) => user.id === userId);
      if (updated) setCurrentUser({ ...updated, name: field(form, "name"), email: field(form, "email") });
    }
    setNotice("Perfil actualizado.");
  }

  async function changeActivation(user: User) {
    await apiRequest<UserResponse>(`/users/${user.id}`, {
      method: "PATCH",
      csrfToken,
      body: { is_active: !user.is_active },
    });
    await loadUsers();
    setNotice(user.is_active ? "Cuenta desactivada; sus sesiones quedaron revocadas." : "Cuenta activada.");
  }

  async function deleteUser(user: User) {
    if (!window.confirm(`¿Eliminar definitivamente la cuenta de ${user.name}?`)) return;
    await apiRequest<null>(`/users/${user.id}`, { method: "DELETE", csrfToken });
    await loadUsers();
    setNotice("Cuenta eliminada.");
  }

  async function updatePassword(userId: string, form: FormData) {
    const body: { new_password: string; current_password?: string } = {
      new_password: field(form, "new_password"),
    };
    if (userId === currentUser?.id) body.current_password = field(form, "current_password");
    await apiRequest<null>(`/users/${userId}/password`, {
      method: "POST",
      csrfToken,
      body,
    });
    if (userId === currentUser?.id) {
      setCurrentUser(null);
      setCsrfToken("");
      setScreen("login");
      setNotice("Contraseña actualizada. Inicia sesión de nuevo.");
    } else {
      setNotice("Contraseña del usuario actualizada; sus sesiones anteriores se revocaron.");
    }
  }

  async function mutateUser(
    user: User,
    operation: (user: User) => Promise<void>,
  ) {
    await perform(() => operation(user));
  }

  return (
    <main className={`app-shell ${screen === "app" ? "authenticated" : "auth-shell"}`}>
      {screen !== "app" && <header className="app-header"><AppBrand /><p>Organiza tu semana. Disfruta en familia.</p></header>}

      {screen !== "app" && error && <p className="message error" role="alert">{error}</p>}
      {screen !== "app" && notice && <p className="message success" role="status">{notice}</p>}

      {screen === "loading" && <p role="status">Comprobando la sesión…</p>}

      {screen === "register" && (
        <section className="panel narrow">
          <h2>Crear la primera cuenta</h2>
          <p>Después de crearla, inicia sesión para acceder a la aplicación.</p>
          <form onSubmit={(event) => submitForm(event, createInitialAccount)}>
            <label>Nombre<input name="name" autoComplete="name" required maxLength={150} /></label>
            <label>Correo electrónico<input name="email" type="email" autoComplete="email" required maxLength={320} /></label>
            <label>Contraseña<input name="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} /></label>
            <small>Entre 8 y 128 caracteres; se admiten espacios y caracteres Unicode.</small>
            <button disabled={loading}>{loading ? "Creando…" : "Crear cuenta"}</button>
          </form>
        </section>
      )}

      {screen === "login" && (
        <section className="panel narrow">
          <h2>Iniciar sesión</h2>
          <form onSubmit={(event) => submitForm(event, signIn)}>
            <label>Correo electrónico<input name="email" type="email" autoComplete="username" required maxLength={320} /></label>
            <label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>
            <button disabled={loading}>{loading ? "Accediendo…" : "Entrar"}</button>
          </form>
          <button type="button" className="link-button" onClick={() => { setError(""); setNotice(""); setScreen("reset-request"); }}>
            ¿Olvidaste tu contraseña?
          </button>
        </section>
      )}

      {screen === "reset-request" && (
        <section className="panel narrow">
          <h2>Recuperar contraseña</h2>
          <p>Si el correo pertenece a una cuenta, recibirás instrucciones para restablecerla.</p>
          <form onSubmit={(event) => submitForm(event, requestReset)}>
            <label>Correo electrónico<input name="email" type="email" autoComplete="email" required maxLength={320} /></label>
            <button disabled={loading}>{loading ? "Enviando…" : "Enviar instrucciones"}</button>
          </form>
          <button type="button" className="link-button" onClick={() => setScreen("login")}>Volver al inicio de sesión</button>
        </section>
      )}

      {screen === "reset-confirm" && (
        <section className="panel narrow">
          <h2>Elegir una nueva contraseña</h2>
          <form onSubmit={(event) => submitForm(event, confirmReset)}>
            <label>Nueva contraseña<input name="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} /></label>
            <button disabled={loading || !resetToken}>{loading ? "Guardando…" : "Restablecer contraseña"}</button>
          </form>
          {!resetToken && <p className="message error">El enlace no incluye un token válido.</p>}
        </section>
      )}

      {screen === "app" && currentUser && (
        <AppWorkspace
          view={view}
          onViewChange={(nextView) => { setView(nextView); setError(""); setNotice(""); }}
          disabled={loading}
          sessionTools={<div className="session-tools"><div className="session-identity"><span className="session-avatar" aria-hidden="true">{currentUser.name.trim().charAt(0).toLocaleUpperCase("es")}</span><div><small>Tu cuenta</small><strong>{currentUser.name}</strong></div></div><button type="button" className="secondary sign-out" disabled={loading} onClick={() => void perform(signOut)}><AppIcon name="logout" />Cerrar sesión</button></div>}
          notifications={<>{error && <p className="message error" role="alert">{error}</p>}{notice && <p className="message success" role="status">{notice}</p>}</>}
          mealPlanning={<MealPlanning csrfToken={csrfToken} onSessionExpired={mealSessionExpired} />}
          userManagement={<div className="dashboard">
            <section className="panel">
              <p className="eyebrow">Tu familia</p>
              <h2>Gestión de usuarios</h2>
              <p>Todos los usuarios activos pueden administrar las cuentas familiares.</p>
              {users.length === 0 ? <p role="status">Cargando usuarios…</p> : (
                <div className="user-list">
                  {users.map((user) => (
                    <UserCard
                      key={user.id}
                      user={user}
                      isCurrentUser={user.id === currentUser.id}
                      loading={loading}
                      onUpdate={(form) => updateUser(user.id, form)}
                      onActivation={() => mutateUser(user, changeActivation)}
                      onDelete={() => mutateUser(user, deleteUser)}
                      onPassword={(form) => updatePassword(user.id, form)}
                      onSubmit={submitForm}
                    />
                  ))}
                </div>
              )}
            </section>

            <section className="panel narrow">
              <h2>Añadir familiar</h2>
              <form onSubmit={(event) => submitForm(event, createUser)}>
                <label>Nombre<input name="name" autoComplete="name" required maxLength={150} /></label>
                <label>Correo electrónico<input name="email" type="email" autoComplete="email" required maxLength={320} /></label>
                <label>Contraseña inicial<input name="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} /></label>
                <button disabled={loading}>{loading ? "Creando…" : "Crear usuario"}</button>
              </form>
            </section>
          </div>}
        />
      )}
    </main>
  );
}

type UserCardProps = {
  user: User;
  isCurrentUser: boolean;
  loading: boolean;
  onUpdate: (form: FormData) => Promise<void>;
  onActivation: () => void;
  onDelete: () => void;
  onPassword: (form: FormData) => Promise<void>;
  onSubmit: (event: FormEvent<HTMLFormElement>, action: (form: FormData) => Promise<void>) => void;
};

function UserCard({ user, isCurrentUser, loading, onUpdate, onActivation, onDelete, onPassword, onSubmit }: UserCardProps) {
  const [editing, setEditing] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);
  return (
    <article className="user-card">
      <div className="user-card-heading">
        <div>
          <h3>{user.name}{isCurrentUser ? " (tú)" : ""}</h3>
          <p>{user.email}</p>
        </div>
        <span className={user.is_active ? "status active" : "status inactive"}>
          {user.is_active ? "Activa" : "Desactivada"}
        </span>
      </div>

      {editing && (
        <form className="inline-form" onSubmit={(event) => { onSubmit(event, onUpdate); setEditing(false); }}>
          <label>Nombre<input name="name" defaultValue={user.name} required maxLength={150} /></label>
          <label>Correo electrónico<input name="email" type="email" defaultValue={user.email} required maxLength={320} /></label>
          <div className="button-row">
            <button disabled={loading}>Guardar cambios</button>
            <button type="button" className="secondary" onClick={() => setEditing(false)}>Cancelar</button>
          </div>
        </form>
      )}

      {passwordOpen && (
        <form className="inline-form" onSubmit={(event) => { onSubmit(event, onPassword); setPasswordOpen(false); }}>
          {isCurrentUser && <label>Contraseña actual<input name="current_password" type="password" autoComplete="current-password" required /></label>}
          <label>Nueva contraseña<input name="new_password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} /></label>
          <div className="button-row">
            <button disabled={loading}>Guardar contraseña</button>
            <button type="button" className="secondary" onClick={() => setPasswordOpen(false)}>Cancelar</button>
          </div>
        </form>
      )}

      <div className="button-row actions">
        <button type="button" className="secondary" disabled={loading} onClick={() => setEditing(!editing)}>Editar perfil</button>
        <button type="button" className="secondary" disabled={loading} onClick={() => setPasswordOpen(!passwordOpen)}>Cambiar contraseña</button>
        {!isCurrentUser && (
          <>
            <button type="button" className="secondary" disabled={loading} onClick={onActivation}>
              {user.is_active ? "Desactivar" : "Activar"}
            </button>
            <button type="button" className="danger" disabled={loading} onClick={onDelete}>Eliminar</button>
          </>
        )}
      </div>
    </article>
  );
}
