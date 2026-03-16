import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { NotificationProvider } from "./context/NotificationContext.jsx";
import { SessionProvider } from "./context/SessionContext.jsx";
import "./styles.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <NotificationProvider>
        <SessionProvider>
          <App />
        </SessionProvider>
      </NotificationProvider>
    </BrowserRouter>
  </StrictMode>,
);
