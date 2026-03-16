import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import AppShell from "./components/AppShell";
import { useSession } from "./context/SessionContext.jsx";
import DashboardPage from "./pages/DashboardPage";
import MarketingPage from "./pages/MarketingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import AttachmentsPage from "./pages/AttachmentsPage";
import CommentsPage from "./pages/CommentsPage";
import NotificationsPage from "./pages/NotificationsPage";
import OrganizationsPage from "./pages/OrganizationsPage";
import ProjectsPage from "./pages/ProjectsPage";
import TasksPage from "./pages/TasksPage";
import TaskWorkspacePage from "./pages/TaskWorkspacePage";
import PeopleAccessPage from "./pages/PeopleAccessPage";
import ActivityLogsPage from "./pages/ActivityLogsPage";
import AccountSettingsPage from "./pages/AccountSettingsPage";

function ProtectedRoute() {
  const location = useLocation();
  const { isAuthenticated } = useSession();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

function GuestOnlyRoute() {
  const { isAuthenticated } = useSession();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/product" element={<MarketingPage pageKey="product" />} />
      <Route path="/solutions" element={<MarketingPage pageKey="solutions" />} />
      <Route path="/learn" element={<MarketingPage pageKey="learn" />} />
      <Route path="/pricing" element={<MarketingPage pageKey="pricing" />} />
      <Route path="/enterprise" element={<MarketingPage pageKey="enterprise" />} />

      <Route element={<GuestOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>

      <Route path="/dashboard" element={<DashboardPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="organizations" element={<OrganizationsPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="tasks/:taskId" element={<TaskWorkspacePage />} />
          <Route path="comments" element={<CommentsPage />} />
          <Route path="attachments" element={<AttachmentsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="people" element={<PeopleAccessPage />} />
          <Route path="activity" element={<ActivityLogsPage />} />
          <Route path="account" element={<AccountSettingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
