import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ApiError, getChatMessages, getDashboardStats, type ChatMessage, type DashboardStats } from "@/utils/api";

function formatDate(value: string | null) {
  if (!value) {
    return "Пока нет";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { initialized, user, logout } = useAuth();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!initialized) {
      return;
    }

    if (!user) {
      navigate("/", { replace: true });
      return;
    }

    let cancelled = false;

    const loadDashboard = async () => {
      setLoading(true);
      setError("");

      try {
        const [statsResponse, chatResponse] = await Promise.all([getDashboardStats(), getChatMessages()]);
        if (cancelled) {
          return;
        }
        setStats(statsResponse);
        setMessages(chatResponse);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(
          loadError instanceof ApiError ? loadError.message : "Не удалось загрузить данные личного кабинета.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [initialized, navigate, user]);

  const lastMessages = useMemo(() => messages.slice(-5).reverse(), [messages]);

  if (!initialized || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="rounded-3xl bg-white px-6 py-5 text-sm font-medium text-slate-600 shadow-lg">
          Подготавливаем личный кабинет...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#f8fafc_0%,_#ffffff_48%,_#eef6ff_100%)]">
      <header className="sticky top-0 z-40 border-b border-white/70 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-300 hover:text-sky-600"
            >
              На главную
            </button>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Личный кабинет</p>
              <h1 className="text-lg font-bold text-slate-900">{user.display_name}</h1>
            </div>
          </div>

          <button
            type="button"
            onClick={() => void logout().then(() => navigate("/", { replace: true }))}
            className="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
          >
            Выйти
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">
        <section className="rounded-[32px] bg-slate-950 px-8 py-10 text-white shadow-2xl shadow-slate-300/40">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-sky-300">Ваша сводка</p>
          <h2 className="mt-4 text-4xl font-black">Здравствуйте, {user.display_name}</h2>
          <p className="mt-4 max-w-3xl text-base leading-relaxed text-slate-300">
            Здесь собрана ваша личная история общения: последние сообщения, активность в чате и
            важные точки взаимодействия с сервисом.
          </p>
        </section>

        {error && (
          <div className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
            {error}
          </div>
        )}

        <section className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Всего сообщений"
            value={loading ? "..." : String(stats?.total_messages ?? 0)}
            hint="Количество сообщений в вашем личном диалоге"
          />
          <StatCard
            title="Опросники"
            value={loading ? "..." : String(stats?.assessment_sessions ?? 0)}
            hint="Сохранённые сессии самооценки"
          />
          <StatCard
            title="Последняя активность"
            value={loading ? "..." : formatDate(stats?.last_message_at ?? null)}
            hint="Когда вы в последний раз возвращались в чат"
          />
          <StatCard
            title="Ближайшая запись"
            value={loading ? "..." : stats?.next_appointment ? "Запланирована" : "Пока нет"}
            hint={
              loading
                ? "Загружаем данные..."
                : stats?.next_appointment
                  ? formatDate(stats.next_appointment.start_at)
                  : "Вы ещё не записывались к специалисту"
            }
          />
        </section>

        <section className="mt-8 grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-600">История чата</p>
                <h3 className="mt-2 text-2xl font-bold text-slate-950">Последние сообщения</h3>
              </div>
              <button
                type="button"
                onClick={() => navigate("/")}
                className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-300 hover:text-sky-600"
              >
                Открыть чат
              </button>
            </div>

            <div className="mt-6 space-y-4">
              {loading ? (
                <div className="rounded-2xl bg-slate-50 px-4 py-6 text-sm text-slate-500">
                  Загружаем сообщения...
                </div>
              ) : lastMessages.length === 0 ? (
                <div className="rounded-2xl bg-slate-50 px-4 py-6 text-sm text-slate-500">
                  Сообщений пока нет. Можно вернуться на главную и начать первый диалог.
                </div>
              ) : (
                lastMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`rounded-[24px] px-4 py-4 ${
                      message.sender_role === "user"
                        ? "bg-gradient-to-r from-sky-500 to-indigo-500 text-white"
                        : "border border-slate-200 bg-slate-50 text-slate-700"
                    }`}
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] opacity-75">
                      {message.sender_role === "user" ? "Вы" : "MindSupport"}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed">{message.content_text}</p>
                  </div>
                ))
              )}
            </div>
          </article>

          <article className="space-y-6">
            <div className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/60">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-600">Профиль</p>
              <h3 className="mt-2 text-2xl font-bold text-slate-950">Данные аккаунта</h3>
              <div className="mt-6 space-y-4">
                <ProfileRow label="Имя" value={user.display_name} />
                <ProfileRow label="Email" value={user.email} />
                <ProfileRow label="Статус" value={user.status} />
                <ProfileRow label="Дата регистрации" value={formatDate(user.created_at)} />
              </div>
            </div>

            <div className="rounded-[32px] bg-gradient-to-br from-sky-500 to-indigo-600 p-6 text-white shadow-2xl shadow-sky-200">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-100">Что можно дальше</p>
              <h3 className="mt-2 text-2xl font-bold">Продолжить диалог или перейти к очной помощи</h3>
              <p className="mt-4 text-sm leading-relaxed text-sky-100">
                Личный кабинет помогает вернуться к разговору позже, посмотреть последние сообщения и
                постепенно перейти к поиску специалиста, если это станет важным следующим шагом.
              </p>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}

function StatCard({ title, value, hint }: { title: string; value: string; hint: string }) {
  return (
    <article className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-lg shadow-slate-200/60">
      <p className="text-sm font-semibold text-slate-500">{title}</p>
      <p className="mt-3 text-3xl font-black text-slate-950">{value}</p>
      <p className="mt-3 text-sm leading-relaxed text-slate-500">{hint}</p>
    </article>
  );
}

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}
