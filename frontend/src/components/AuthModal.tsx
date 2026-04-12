import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/utils/api";

interface AuthModalProps {
  mode: "login" | "register";
  onClose: () => void;
  onSwitch: (mode: "login" | "register") => void;
  onSuccess?: () => void;
}

export function AuthModal({ mode, onClose, onSwitch, onSuccess }: AuthModalProps) {
  const { authPending, login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    setErrorMessage("");
  }, [mode]);

  const title = useMemo(
    () => (mode === "login" ? "С возвращением" : "Создать аккаунт"),
    [mode],
  );

  const subtitle = useMemo(
    () =>
      mode === "login"
        ? "Войдите, чтобы сохранить историю диалога и продолжить разговор."
        : "Регистрация нужна, чтобы сохранить чат и статистику в личном кабинете.",
    [mode],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");

    try {
      if (mode === "register") {
        await register({
          email,
          display_name: displayName.trim(),
          password,
        });
      } else {
        await login({ email, password });
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
        return;
      }

      setErrorMessage("Не удалось выполнить запрос. Попробуйте ещё раз.");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm"
      onClick={(event) => {
        if (event.target === event.currentTarget && !authPending) {
          onClose();
        }
      }}
    >
      <div className="w-full max-w-md overflow-hidden rounded-[28px] bg-white shadow-2xl shadow-slate-900/20">
        <div className="h-2 bg-gradient-to-r from-cyan-400 via-sky-500 to-indigo-500" />
        <div className="p-8">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-50 text-sky-600">
                <HeartIcon />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">{subtitle}</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              disabled={authPending}
              className="rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Закрыть"
            >
              <CloseIcon />
            </button>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {mode === "register" && (
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Имя
                </span>
                <input
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  required
                  minLength={2}
                  placeholder="Как к вам обращаться"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100"
                />
              </label>
            )}

            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Email
              </span>
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                required
                placeholder="name@example.com"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Пароль
              </span>
              <div className="relative">
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={8}
                  placeholder="Не менее 8 символов"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-28 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full px-3 py-1 text-xs font-semibold text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
                >
                  {showPassword ? "Скрыть" : "Показать"}
                </button>
              </div>
            </label>

            {errorMessage && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {errorMessage}
              </div>
            )}

            <button
              type="submit"
              disabled={authPending}
              className="w-full rounded-2xl bg-gradient-to-r from-sky-500 to-indigo-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-200 transition hover:from-sky-400 hover:to-indigo-400 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {authPending
                ? "Пожалуйста, подождите..."
                : mode === "login"
                  ? "Войти"
                  : "Зарегистрироваться"}
            </button>
          </form>

          <div className="mt-6 rounded-2xl bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500">
            История чата хранится в личном кабинете, а доступ к ней будет только у авторизованного
            пользователя и администратора сервиса.
          </div>

          <p className="mt-5 text-center text-sm text-slate-500">
            {mode === "login" ? "Ещё нет аккаунта? " : "Уже есть аккаунт? "}
            <button
              type="button"
              onClick={() => onSwitch(mode === "login" ? "register" : "login")}
              className="font-semibold text-sky-600 transition hover:text-sky-700"
            >
              {mode === "login" ? "Зарегистрироваться" : "Войти"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

function HeartIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.3 5.71 12 12l6.3 6.29-1.41 1.42L10.59 13.4 4.29 19.71 2.88 18.3 9.17 12 2.88 5.71 4.29 4.29l6.3 6.3 6.29-6.3z" />
    </svg>
  );
}
