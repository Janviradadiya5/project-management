import { createContext, useContext, useEffect, useRef, useState } from "react";
import {
  getOrganization,
  logoutUser,
  refreshAuthTokens,
  setAuthFailureHandler,
  setAuthRefreshHandler,
  setAuthStateAccessor
} from "../api/client.js";
import { useNotifications } from "./NotificationContext.jsx";

const ACCESS_TOKEN_KEY = "projectpulse.accessToken";
const REFRESH_TOKEN_KEY = "projectpulse.refreshToken";
const USER_KEY = "projectpulse.user";
const ORGANIZATION_KEY = "projectpulse.organizationId";

const SessionContext = createContext(null);

function readStoredJson(key) {
  if (typeof window === "undefined") {
    return null;
  }

  const value = window.localStorage.getItem(key);
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function readStoredValue(key) {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) || "";
}

export function SessionProvider({ children }) {
  const { pushToast } = useNotifications();
  const [accessToken, setAccessToken] = useState(() => readStoredValue(ACCESS_TOKEN_KEY));
  const [refreshToken, setRefreshToken] = useState(() => readStoredValue(REFRESH_TOKEN_KEY));
  const [organizationId, setOrganizationId] = useState(() => readStoredValue(ORGANIZATION_KEY));
  const [user, setUser] = useState(() => readStoredJson(USER_KEY));
  const [currentOrganization, setCurrentOrganization] = useState(null);
  const [organizationRole, setOrganizationRole] = useState("");
  const [authNotice, setAuthNotice] = useState("");
  const lastAuthFailureAt = useRef(0);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    if (accessToken) {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    } else {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    }

    if (refreshToken) {
      window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    } else {
      window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    }

    if (organizationId) {
      window.localStorage.setItem(ORGANIZATION_KEY, organizationId);
    } else {
      window.localStorage.removeItem(ORGANIZATION_KEY);
    }

    if (user) {
      window.localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      window.localStorage.removeItem(USER_KEY);
    }
  }, [accessToken, refreshToken, organizationId, user]);

  function login(authData) {
    setAccessToken(authData?.tokens?.access_token || "");
    setRefreshToken(authData?.tokens?.refresh_token || "");
    setUser(authData?.user || null);
    setAuthNotice("");
    pushToast("Signed in successfully.", "success");
  }

  function clearLocalSession() {
    setAccessToken("");
    setRefreshToken("");
    setOrganizationId("");
    setCurrentOrganization(null);
    setOrganizationRole("");
    setUser(null);
  }

  useEffect(() => {
    let active = true;

    async function hydrateOrganizationContext() {
      if (!accessToken || !organizationId) {
        setCurrentOrganization(null);
        setOrganizationRole("");
        return;
      }

      try {
        const response = await getOrganization(accessToken, organizationId);
        if (!active) {
          return;
        }

        const organization = response?.data || null;
        setCurrentOrganization(organization);
        setOrganizationRole(organization?.current_user_role_code || (user?.is_superuser ? "super_admin" : ""));
      } catch {
        if (!active) {
          return;
        }

        setCurrentOrganization(null);
        setOrganizationRole(user?.is_superuser ? "super_admin" : "");
      }
    }

    hydrateOrganizationContext();

    return () => {
      active = false;
    };
  }, [accessToken, organizationId, user?.is_superuser]);

  async function refreshSessionTokens(currentAccessToken, currentRefreshToken) {
    const response = await refreshAuthTokens(currentAccessToken, currentRefreshToken);
    const tokens = response?.data?.tokens;

    const nextAccessToken = tokens?.access_token || "";
    const nextRefreshToken = tokens?.refresh_token || "";

    if (!nextAccessToken || !nextRefreshToken) {
      throw new Error("Token refresh returned an invalid payload.");
    }

    setAccessToken(nextAccessToken);
    setRefreshToken(nextRefreshToken);

    return {
      accessToken: nextAccessToken,
      refreshToken: nextRefreshToken
    };
  }

  async function logout() {
    try {
      if (accessToken && refreshToken) {
        await logoutUser(accessToken, refreshToken);
      }
    } catch {
      // Always clear local state even if server-side logout fails.
    } finally {
      clearLocalSession();
      pushToast("Signed out.", "info");
    }
  }

  function consumeAuthNotice() {
    setAuthNotice("");
  }

  useEffect(() => {
    setAuthRefreshHandler(async ({ accessToken: activeAccess, refreshToken: activeRefresh }) => {
      return refreshSessionTokens(activeAccess, activeRefresh);
    });

    return () => {
      setAuthRefreshHandler(null);
    };
  }, []);

  useEffect(() => {
    setAuthFailureHandler(() => {
      const now = Date.now();
      if (now - lastAuthFailureAt.current < 1500) {
        return;
      }

      lastAuthFailureAt.current = now;
      setAuthNotice("Your session expired. Please sign in again.");
      clearLocalSession();
      pushToast("Session expired. Please sign in again.", "warning");
    });

    return () => {
      setAuthFailureHandler(null);
    };
  }, [pushToast]);

  useEffect(() => {
    setAuthStateAccessor(() => ({
      accessToken,
      refreshToken
    }));

    return () => {
      setAuthStateAccessor(null);
    };
  }, [accessToken, refreshToken]);

  function selectOrganization(nextOrganizationId, organization = null) {
    setOrganizationId(nextOrganizationId || "");

    if (!nextOrganizationId) {
      setCurrentOrganization(null);
      setOrganizationRole("");
      return;
    }

    if (organization) {
      setCurrentOrganization(organization);
      setOrganizationRole(organization?.current_user_role_code || (user?.is_superuser ? "super_admin" : ""));
    }
  }

  return (
    <SessionContext.Provider
      value={{
        accessToken,
        refreshToken,
        organizationId,
        organizationRole,
        currentOrganization,
        user,
        authNotice,
        isAuthenticated: Boolean(accessToken),
        isSuperAdmin: Boolean(user?.is_superuser),
        login,
        logout,
        consumeAuthNotice,
        setUser,
        selectOrganization
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);

  if (!context) {
    throw new Error("useSession must be used within a SessionProvider");
  }

  return context;
}