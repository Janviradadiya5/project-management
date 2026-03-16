import { createContext, useCallback, useContext, useMemo, useState } from "react";

const NotificationContext = createContext(null);

function buildToast(message, type, duration) {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    message,
    type,
    duration
  };
}

export function NotificationProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback((message, type = "info", duration = 3200) => {
    const toast = buildToast(message, type, duration);
    setToasts((current) => [toast, ...current].slice(0, 4));

    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== toast.id));
    }, duration);

    return toast.id;
  }, []);

  const value = useMemo(
    () => ({
      pushToast,
      removeToast
    }),
    [pushToast, removeToast]
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <div className="toast-stack" aria-live="polite" aria-label="Notifications">
        {toasts.map((toast) => (
          <article key={toast.id} className={`toast toast-${toast.type}`}>
            <p>{toast.message}</p>
            <button type="button" className="toast-close" onClick={() => removeToast(toast.id)} aria-label="Dismiss notification">
              x
            </button>
          </article>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);

  if (!context) {
    throw new Error("useNotifications must be used within NotificationProvider");
  }

  return context;
}