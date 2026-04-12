import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  ensureCsrfCookie,
  getCurrentUser,
  isAuthError,
  loginUser,
  logoutUser,
  registerUser,
  type AuthUser,
  type LoginPayload,
  type RegisterPayload,
} from "@/utils/api";

interface AuthContextValue {
  user: AuthUser | null;
  initialized: boolean;
  authPending: boolean;
  login: (payload: LoginPayload) => Promise<AuthUser>;
  register: (payload: RegisterPayload) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<AuthUser | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [authPending, setAuthPending] = useState(false);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      return currentUser;
    } catch (error) {
      if (isAuthError(error)) {
        setUser(null);
        return null;
      }
      throw error;
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    const bootstrap = async () => {
      try {
        await ensureCsrfCookie();
        const currentUser = await refreshUser();
        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setInitialized(true);
        }
      }
    };

    void bootstrap();

    return () => {
      isMounted = false;
    };
  }, [refreshUser]);

  const login = useCallback(async (payload: LoginPayload) => {
    setAuthPending(true);
    try {
      await ensureCsrfCookie();
      const currentUser = await loginUser(payload);
      setUser(currentUser);
      return currentUser;
    } finally {
      setAuthPending(false);
    }
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    setAuthPending(true);
    try {
      await ensureCsrfCookie();
      const currentUser = await registerUser(payload);
      setUser(currentUser);
      return currentUser;
    } finally {
      setAuthPending(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setAuthPending(true);
    try {
      await ensureCsrfCookie();
      await logoutUser();
      setUser(null);
    } finally {
      setAuthPending(false);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      initialized,
      authPending,
      login,
      register,
      logout,
      refreshUser,
    }),
    [authPending, initialized, login, logout, refreshUser, register, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}
