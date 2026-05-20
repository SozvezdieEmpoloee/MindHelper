import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthModal } from "./components/AuthModal";
import { MapSection } from "./components/MapSection";
import { useAuth } from "./context/AuthContext";
import { ApiError, getChatMessages, sendChatMessage, type CrisisEvent } from "./utils/api";

type ChatSender = "user" | "bot" | "system";

interface UiChatMessage {
  id: string;
  sender: ChatSender;
  text: string;
}

const QUICK_REPLIES = [
  "Мне тревожно и трудно успокоиться",
  "Я чувствую сильную усталость и напряжение",
  "Хочу разобраться в своём состоянии",
  "Мне нужна поддержка прямо сейчас",
];

const SERVICE_FEATURES = [
  {
    title: "Бережный диалог",
    text: "Можно начать с короткого сообщения и постепенно рассказать о том, что беспокоит именно сейчас.",
  },
  {
    title: "Понятные ориентиры",
    text: "Сервис помогает структурировать переживания и подсказывает, когда лучше обратиться за очной помощью.",
  },
  {
    title: "Контакты рядом",
    text: "На сайте доступны экстренные номера и список специалистов в Воронеже с адресами и точками на карте.",
  },
];

const USER_STEPS = [
  {
    step: "01",
    title: "Опишите, что с вами происходит",
    text: "Вы можете написать своими словами о тревоге, усталости, напряжении, страхе или растерянности.",
  },
  {
    step: "02",
    title: "Получите спокойный ответ",
    text: "Сервис отвечает простым языком и помогает сфокусироваться на текущем состоянии без давления и осуждения.",
  },
  {
    step: "03",
    title: "При необходимости перейдите к следующему шагу",
    text: "Если нужно, вы сможете продолжить диалог, сохранить историю в кабинете и найти очного специалиста.",
  },
];

const INITIAL_MESSAGE: UiChatMessage = {
  id: "local-welcome",
  sender: "bot",
  text: "Здравствуйте. Я рядом и готов выслушать. Расскажите, пожалуйста, что вы чувствуете сейчас.",
};

function normalizeMessages(messages: Array<{ id: string; sender_role: ChatSender; content_text: string }>) {
  return messages.map((message) => ({
    id: message.id,
    sender: message.sender_role,
    text: message.content_text,
  }));
}

export function App() {
  const navigate = useNavigate();
  const { user, initialized, logout } = useAuth();

  const [authModalMode, setAuthModalMode] = useState<"login" | "register" | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatExpanded, setChatExpanded] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState<UiChatMessage[]>([INITIAL_MESSAGE]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatSending, setChatSending] = useState(false);
  const [chatError, setChatError] = useState("");
  const [crisisEvent, setCrisisEvent] = useState<CrisisEvent | null>(null);

  useEffect(() => {
    if (!initialized) {
      return;
    }

    if (!user) {
      setMessages([INITIAL_MESSAGE]);
      setCrisisEvent(null);
      setChatError("");
      return;
    }

    let cancelled = false;

    const loadMessages = async () => {
      setChatLoading(true);
      setChatError("");

      try {
        const response = await getChatMessages();
        if (cancelled) {
          return;
        }
        const normalized = normalizeMessages(response);
        setMessages(normalized.length > 0 ? normalized : [INITIAL_MESSAGE]);
      } catch (error) {
        if (cancelled) {
          return;
        }
        setChatError(error instanceof ApiError ? error.message : "Не удалось загрузить историю диалога.");
        setMessages([INITIAL_MESSAGE]);
      } finally {
        if (!cancelled) {
          setChatLoading(false);
        }
      }
    };

    void loadMessages();

    return () => {
      cancelled = true;
    };
  }, [initialized, user]);

  async function handleLogout() {
    await logout();
    setMessages([INITIAL_MESSAGE]);
    setCrisisEvent(null);
    navigate("/");
  }

  async function handleSendMessage(rawText: string) {
    const content = rawText.trim();
    if (!content) {
      return;
    }

    if (!user) {
      setAuthModalMode("login");
      setChatOpen(true);
      return;
    }

    setChatSending(true);
    setChatError("");

      try {
        const response = await sendChatMessage(content);
        const nextMessages = normalizeMessages([response.user_message, response.bot_message]);
        setMessages((current) => {
          const existing = current[0]?.id === INITIAL_MESSAGE.id ? current.slice(1) : current;
          return [...existing, ...nextMessages];
        });
        setCrisisEvent(response.crisis_event);
        setInputValue("");
        setChatOpen(true);
    } catch (error) {
      setChatError(error instanceof ApiError ? error.message : "Не удалось отправить сообщение.");
    } finally {
      setChatSending(false);
    }
  }

  function openAuth(mode: "login" | "register") {
    setAuthModalMode(mode);
    setChatOpen(true);
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(103,232,249,0.16),_transparent_30%),radial-gradient(circle_at_top_right,_rgba(129,140,248,0.12),_transparent_28%),linear-gradient(180deg,_#f8fafc_0%,_#ffffff_48%,_#eef6ff_100%)] text-slate-900">
      <header className="sticky top-0 z-40 border-b border-white/60 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <button type="button" onClick={() => navigate("/")} className="flex items-center gap-3 text-left">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-indigo-500 text-white shadow-lg shadow-cyan-200">
              <BrainIcon />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
                Психологическая поддержка
              </p>
              <p className="text-lg font-bold text-slate-900">MindSupport</p>
            </div>
          </button>

          <nav className="hidden items-center gap-6 text-sm font-medium text-slate-500 md:flex">
            <a href="#about" className="transition hover:text-sky-600">
              О сервисе
            </a>
            <a href="#support-chat" className="transition hover:text-sky-600">
              Чат
            </a>
            <a href="#help-route" className="transition hover:text-sky-600">
              Как это помогает
            </a>
            <a href="#clinics" className="transition hover:text-sky-600">
              Специалисты
            </a>
          </nav>

          <div className="flex items-center gap-2">
            {user ? (
              <>
                <button
                  type="button"
                  onClick={() => navigate("/dashboard")}
                  className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-300 hover:text-sky-600"
                >
                  {user.display_name}
                </button>
                <button
                  type="button"
                  onClick={() => void handleLogout()}
                  className="rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
                >
                  Выйти
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => openAuth("login")}
                  className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-300 hover:text-sky-600"
                >
                  Войти
                </button>
                <button
                  type="button"
                  onClick={() => openAuth("register")}
                  className="rounded-2xl bg-gradient-to-r from-sky-500 to-indigo-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-200 transition hover:from-sky-400 hover:to-indigo-400"
                >
                  Регистрация
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden px-6 pb-20 pt-16" id="about">
          <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
            <div className="space-y-7">
              <span className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Поддержка 24/7
              </span>

              <div className="space-y-4">
                <h1 className="max-w-3xl text-4xl font-black leading-tight text-slate-950 md:text-6xl">
                  Пространство, где можно спокойно рассказать о своём состоянии и получить опору.
                </h1>
                <p className="max-w-2xl text-lg leading-relaxed text-slate-600">
                  MindSupport помогает начать разговор о тревоге, стрессе, подавленности и
                  внутреннем напряжении. Здесь можно написать о своих переживаниях, сохранить
                  историю диалога и при необходимости быстро перейти к экстренным контактам и
                  очной помощи.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={() => {
                    setChatOpen(true);
                    setChatExpanded(true);
                  }}
                  className="rounded-[22px] bg-gradient-to-r from-sky-500 to-indigo-500 px-7 py-4 text-base font-semibold text-white shadow-xl shadow-sky-200 transition hover:from-sky-400 hover:to-indigo-400"
                >
                  Открыть чат поддержки
                </button>
                <button
                  type="button"
                  onClick={() => (user ? navigate("/dashboard") : openAuth("register"))}
                  className="rounded-[22px] border border-slate-200 bg-white px-7 py-4 text-base font-semibold text-slate-700 transition hover:border-sky-200 hover:text-sky-600"
                >
                  {user ? "Перейти в кабинет" : "Создать аккаунт"}
                </button>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                {SERVICE_FEATURES.map((card) => (
                  <article
                    key={card.title}
                    className="rounded-[24px] border border-white/70 bg-white/80 p-5 shadow-lg shadow-slate-200/50 backdrop-blur"
                  >
                    <h2 className="text-base font-bold text-slate-900">{card.title}</h2>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">{card.text}</p>
                  </article>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-2xl shadow-sky-100">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-400">Ваш статус</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {user ? "Личный кабинет активен" : "Гостевой просмотр"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
                    Онлайн
                  </div>
                </div>

                <div className="space-y-4">
                  <InfoRow label="Диалог" value={user ? "Можно продолжить общение" : "Доступен после входа"} />
                  <InfoRow
                    label="История сообщений"
                    value={user ? `${Math.max(messages.length - 1, 0)} сохранено` : "Появится в вашем кабинете"}
                  />
                  <InfoRow
                    label="Экстренные контакты"
                    value="Всегда доступны на сайте и в Telegram-боте"
                  />
                </div>

                <div className="mt-6 rounded-[28px] bg-slate-950 p-5 text-white">
                  <p className="text-sm font-semibold text-sky-300">Важно помнить</p>
                  <ul className="mt-4 space-y-3 text-sm text-slate-200">
                    <li>Сервис помогает начать разговор о состоянии и получить ориентиры для следующих шагов.</li>
                    <li>Если ситуация кажется острой или опасной, лучше сразу воспользоваться экстренными контактами.</li>
                    <li>Очная помощь специалиста особенно важна, если симптомы мешают сну, работе и повседневной жизни.</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="px-6 py-20" id="help-route">
          <div className="mx-auto max-w-6xl">
            <SectionHeading
              eyebrow="Как это помогает"
              title="Сервис помогает сделать первый шаг к поддержке"
              description="Если трудно подобрать слова, можно начать с короткой фразы. Дальше диалог поможет спокойнее посмотреть на своё состояние и понять, что делать дальше."
            />
            <div className="mt-12 grid gap-6 md:grid-cols-3">
              {USER_STEPS.map((item) => (
                <article
                  key={item.step}
                  className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70"
                >
                  <p className="text-sm font-black tracking-[0.3em] text-sky-500">{item.step}</p>
                  <h3 className="mt-4 text-xl font-bold text-slate-900">{item.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-slate-600">{item.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="px-6 pb-20" id="support-chat">
          <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[0.85fr_1.15fr]">
            <div className="rounded-[32px] bg-slate-950 p-8 text-white shadow-2xl shadow-slate-300/40">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-sky-300">
                Чат поддержки
              </p>
              <h2 className="mt-4 text-3xl font-bold">Один личный диалог для спокойного и последовательного общения</h2>
              <p className="mt-4 text-sm leading-relaxed text-slate-300">
                Вы можете возвращаться к разговору в удобное время. История помогает не начинать всё
                заново и бережно сохраняет контекст ваших сообщений.
              </p>

              <div className="mt-8 grid gap-3">
                {QUICK_REPLIES.map((reply) => (
                  <button
                    key={reply}
                    type="button"
                    onClick={() => void handleSendMessage(reply)}
                    className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-white transition hover:border-sky-300/50 hover:bg-sky-400/10"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            </div>

            <ChatCard
              messages={messages}
              inputValue={inputValue}
              onInputChange={setInputValue}
              onSubmit={handleSendMessage}
              loading={chatLoading}
              sending={chatSending}
              error={chatError}
              crisisEvent={crisisEvent}
            />
          </div>
        </section>

        <MapSection />

        <section className="px-6 py-20">
          <div className="mx-auto max-w-5xl rounded-[36px] bg-gradient-to-r from-sky-500 to-indigo-600 px-8 py-12 text-center text-white shadow-2xl shadow-sky-200">
            <p className="text-sm font-semibold uppercase tracking-[0.28em] text-sky-100">
              Следующий шаг
            </p>
            <h2 className="mt-4 text-3xl font-black md:text-4xl">
              Если хочется продолжить разговор, сервис уже готов к диалогу на сайте и в Telegram.
            </h2>
            <p className="mx-auto mt-4 max-w-3xl text-base leading-relaxed text-sky-100">
              Вы можете общаться в личном кабинете, переходить к специалистам на карте и пользоваться
              теми же экстренными контактами в Telegram-боте.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => (user ? navigate("/dashboard") : openAuth("register"))}
                className="rounded-[22px] bg-white px-7 py-4 text-base font-semibold text-sky-700 transition hover:bg-sky-50"
              >
                {user ? "Открыть кабинет" : "Зарегистрироваться"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setChatOpen(true);
                  setChatExpanded(true);
                }}
                className="rounded-[22px] border border-white/40 px-7 py-4 text-base font-semibold text-white transition hover:bg-white/10"
              >
                Продолжить диалог
              </button>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/60 bg-white/70 px-6 py-8 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 text-sm text-slate-500 md:flex-row md:items-center md:justify-between">
          <p>MindSupport. Онлайн-сервис предварительной психологической поддержки и маршрутизации к помощи.</p>
          <p>Если есть непосредственная угроза жизни или безопасности, лучше сразу обратиться в экстренные службы.</p>
        </div>
      </footer>

      <button
        type="button"
        onClick={() => setChatOpen(true)}
        className="fixed bottom-6 right-6 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-sky-500 to-indigo-500 text-white shadow-2xl shadow-sky-300 transition hover:scale-105"
      >
        <ChatIcon />
      </button>

      {chatOpen && !chatExpanded && (
        <div className="fixed bottom-24 right-6 z-40 w-[22rem] overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-2xl shadow-slate-300/60">
          <div className="flex items-center justify-between bg-slate-950 px-4 py-3 text-white">
            <div>
              <p className="text-sm font-semibold">MindSupport</p>
              <p className="text-xs text-slate-300">
                {user ? "История связана с вашим кабинетом" : "Войдите, чтобы сохранить историю диалога"}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setChatExpanded(true)}
                className="rounded-full p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
              >
                <ExpandIcon />
              </button>
              <button
                type="button"
                onClick={() => setChatOpen(false)}
                className="rounded-full p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
              >
                <CloseTinyIcon />
              </button>
            </div>
          </div>
          <div className="max-h-72 overflow-y-auto bg-slate-50 p-4">
            <MiniMessages messages={messages} loading={chatLoading} />
          </div>
          <div className="border-t border-slate-200 p-3">
            <div className="flex gap-2">
              <input
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    void handleSendMessage(inputValue);
                  }
                }}
                placeholder="Напишите сообщение..."
                className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none transition focus:border-sky-400 focus:bg-white"
              />
              <button
                type="button"
                onClick={() => void handleSendMessage(inputValue)}
                disabled={chatSending}
                className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-500 text-white transition hover:from-sky-400 hover:to-indigo-400 disabled:cursor-not-allowed disabled:opacity-70"
              >
                <SendIcon />
              </button>
            </div>
          </div>
        </div>
      )}

      {chatExpanded && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
          <div className="flex h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-[32px] bg-white shadow-2xl shadow-slate-950/20">
            <div className="flex items-center justify-between bg-slate-950 px-6 py-4 text-white">
              <div>
                <p className="text-lg font-semibold">MindSupport</p>
                <p className="text-sm text-slate-300">
                  {user
                    ? "Вы продолжаете личный диалог в безопасном и спокойном формате."
                    : "Войдите, чтобы сохранить историю общения и вернуться к ней позже."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setChatExpanded(false)}
                className="rounded-2xl border border-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Свернуть
              </button>
            </div>

            <ChatCard
              messages={messages}
              inputValue={inputValue}
              onInputChange={setInputValue}
              onSubmit={handleSendMessage}
              loading={chatLoading}
              sending={chatSending}
              error={chatError}
              crisisEvent={crisisEvent}
              compact={false}
            />
          </div>
        </div>
      )}

      {authModalMode && (
        <AuthModal
          mode={authModalMode}
          onClose={() => setAuthModalMode(null)}
          onSwitch={setAuthModalMode}
          onSuccess={() => {
            setChatError("");
            setChatOpen(true);
          }}
        />
      )}
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-sky-600">{eyebrow}</p>
      <h2 className="mt-4 text-3xl font-black text-slate-950 md:text-4xl">{title}</h2>
      <p className="mt-4 text-base leading-relaxed text-slate-600">{description}</p>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-right text-sm font-semibold text-slate-900">{value}</span>
    </div>
  );
}

function ChatCard({
  messages,
  inputValue,
  onInputChange,
  onSubmit,
  loading,
  sending,
  error,
  crisisEvent,
  compact = true,
}: {
  messages: UiChatMessage[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (message: string) => Promise<void>;
  loading: boolean;
  sending: boolean;
  error: string;
  crisisEvent: CrisisEvent | null;
  compact?: boolean;
}) {
  const messagesViewportRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const viewport = messagesViewportRef.current;
    const endMarker = messagesEndRef.current;
    if (!viewport || !endMarker) {
      return;
    }

    endMarker.scrollIntoView({
      behavior: compact ? "auto" : "smooth",
      block: "end",
    });
  }, [messages, loading, sending, compact]);

  return (
    <div
      className={`overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-xl shadow-slate-200/60 ${
        compact ? "" : "flex h-full min-h-0 flex-col"
      }`}
    >
      <div className="border-b border-slate-200 px-6 py-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-600">Личный диалог</p>
            <h3 className="mt-2 text-2xl font-bold text-slate-950">Чат поддержки</h3>
          </div>
          <div className="rounded-2xl bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
            Доступен сейчас
          </div>
        </div>
        {crisisEvent && (
          <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            В сообщении обнаружены признаки высокого риска. Пожалуйста, обратите внимание на
            экстренные контакты и не оставайтесь с этим состоянием в одиночку.
          </div>
        )}
        {error && (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}
      </div>

      <div className={compact ? "" : "flex min-h-0 flex-1 flex-col"}>
        <div
          ref={messagesViewportRef}
          className={`space-y-4 overflow-y-auto overscroll-contain bg-slate-50/80 p-6 ${
            compact ? "h-[24rem]" : "min-h-0 flex-1"
          }`}
        >
          {loading ? (
            <div className="flex h-full items-center justify-center">
              <div className="inline-flex items-center gap-3 rounded-2xl bg-white px-5 py-3 text-sm font-medium text-slate-600 shadow">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-sky-200 border-t-sky-500" />
                Загружаем историю диалога...
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.sender !== "user" && (
                  <div className="mr-3 mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-500 to-indigo-500 text-white">
                    <BrainIcon />
                  </div>
                )}
                <div
                  className={`min-w-0 max-w-[78%] whitespace-pre-wrap break-words rounded-[24px] px-4 py-3 text-sm leading-relaxed ${
                    message.sender === "user"
                      ? "rounded-br-md bg-gradient-to-r from-sky-500 to-indigo-500 text-white"
                      : "rounded-bl-md border border-slate-200 bg-white text-slate-700 shadow-sm"
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-slate-200 bg-white px-6 py-5">
          <div className="mb-3 flex flex-wrap gap-2">
            {QUICK_REPLIES.map((reply) => (
              <button
                key={reply}
                type="button"
                onClick={() => void onSubmit(reply)}
                disabled={sending}
                className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-semibold text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {reply}
              </button>
            ))}
          </div>
          <div className="flex gap-3">
            <input
              value={inputValue}
              onChange={(event) => onInputChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void onSubmit(inputValue);
                }
              }}
              placeholder="Напишите сообщение..."
              className="flex-1 rounded-[22px] border border-slate-200 bg-slate-50 px-5 py-3 text-sm outline-none transition focus:border-sky-400 focus:bg-white"
            />
            <button
              type="button"
              onClick={() => void onSubmit(inputValue)}
              disabled={sending}
              className="rounded-[22px] bg-gradient-to-r from-sky-500 to-indigo-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-200 transition hover:from-sky-400 hover:to-indigo-400 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {sending ? "..." : "Отправить"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniMessages({ messages, loading }: { messages: UiChatMessage[]; loading: boolean }) {
  if (loading) {
    return <p className="text-sm text-slate-500">Загружаем историю...</p>;
  }

  return (
    <div className="space-y-3">
      {messages.map((message) => (
        <div key={message.id} className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
          <div
            className={`min-w-0 max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-3 py-2 text-xs leading-relaxed ${
              message.sender === "user"
                ? "bg-gradient-to-r from-sky-500 to-indigo-500 text-white"
                : "border border-slate-200 bg-white text-slate-700"
            }`}
          >
            {message.text}
          </div>
        </div>
      ))}
    </div>
  );
}

function BrainIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M9.5 2a3.5 3.5 0 0 0-3.37 2.56A3.5 3.5 0 0 0 3 8a3.5 3.5 0 0 0 1.5 2.86A3.47 3.47 0 0 0 3 13.5 3.5 3.5 0 0 0 6.5 17h.08A3.5 3.5 0 0 0 10 20.5V14h1v6.5a3.5 3.5 0 0 0 3.42-3.5h.08A3.5 3.5 0 0 0 18 13.5a3.47 3.47 0 0 0-1.5-2.64A3.5 3.5 0 0 0 18 8a3.5 3.5 0 0 0-3.13-3.44A3.5 3.5 0 0 0 11.5 2H9.5Z" />
      <path d="M8 8a1 1 0 0 1 1-1h1v2H9a1 1 0 0 1-1-1Zm5-1h1a1 1 0 1 1 0 2h-1V7Zm-3 4h4v2h-4v-2Z" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M4 4h16a2 2 0 0 1 2 2v14l-4-4H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
      <path d="M2 21 23 12 2 3v7l15 2-15 2v7Z" />
    </svg>
  );
}

function ExpandIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
      <path d="M14 3h7v7h-2V6.41l-4.29 4.3-1.42-1.42L17.59 5H14V3ZM10.71 13.29l-1.42 1.42L5 10.41V14H3V7h7v2H6.41l4.3 4.29ZM19 19h-3v2h5v-5h-2v3ZM5 16H3v5h5v-2H5v-3Z" />
    </svg>
  );
}

function CloseTinyIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
      <path d="m19 6.41-1.41-1.41L12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41Z" />
    </svg>
  );
}
