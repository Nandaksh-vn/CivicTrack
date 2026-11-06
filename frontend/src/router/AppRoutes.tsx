import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { ForbiddenPage } from "@/components/states/PageStates";
import { useAuth } from "@/features/auth/AuthProvider";
import AdminActivityPage from "@/pages/admin/AdminActivityPage";
import AdminAuditPage from "@/pages/admin/AdminAuditPage";
import AdminCategoriesPage from "@/pages/admin/AdminCategoriesPage";
import AdminDepartmentsPage from "@/pages/admin/AdminDepartmentsPage";
import AdminUsersPage from "@/pages/admin/AdminUsersPage";
import LoginPage from "@/pages/auth/LoginPage";
import ProfilePage from "@/pages/auth/ProfilePage";
import RegisterPage from "@/pages/auth/RegisterPage";
import ComplaintDetailPage from "@/pages/citizen/ComplaintDetailPage";
import MyComplaintsPage from "@/pages/citizen/MyComplaintsPage";
import NewComplaintPage from "@/pages/citizen/NewComplaintPage";
import NotificationsPage from "@/pages/citizen/NotificationsPage";
import DepartmentDetailPage from "@/pages/department/DepartmentDetailPage";
import DepartmentQueuePage from "@/pages/department/DepartmentQueuePage";
import EscalationDetailPage from "@/pages/superintendent/EscalationDetailPage";
import EscalationQueuePage from "@/pages/superintendent/EscalationQueuePage";
import NotFoundPage from "@/pages/NotFoundPage";
import { ProtectedRoute, PublicOnly } from "@/router/ProtectedRoute";
import { roleHome } from "@/lib/status";

function RoleHome() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={roleHome(user.role)} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<RoleHome />} />
        <Route
          path="login"
          element={
            <PublicOnly>
              <LoginPage />
            </PublicOnly>
          }
        />
        <Route
          path="register"
          element={
            <PublicOnly>
              <RegisterPage />
            </PublicOnly>
          }
        />

        <Route
          path="complaints"
          element={
            <ProtectedRoute roles={["CITIZEN"]}>
              <MyComplaintsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="complaints/new"
          element={
            <ProtectedRoute roles={["CITIZEN"]}>
              <NewComplaintPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="complaints/:id"
          element={
            <ProtectedRoute>
              <ComplaintDetailPage />
            </ProtectedRoute>
          }
        />
        {/* Aliases used by the shared department/citizen queue pages. */}
        <Route
          path="citizen/complaints"
          element={
            <ProtectedRoute roles={["CITIZEN"]}>
              <MyComplaintsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="citizen/complaints/:id"
          element={
            <ProtectedRoute>
              <ComplaintDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="department"
          element={
            <ProtectedRoute roles={["DEPARTMENT_OFFICER"]}>
              <DepartmentQueuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="department/complaints"
          element={
            <ProtectedRoute roles={["DEPARTMENT_OFFICER"]}>
              <DepartmentQueuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="department/summary"
          element={
            <ProtectedRoute roles={["DEPARTMENT_OFFICER"]}>
              <DepartmentQueuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="department/:id"
          element={
            <ProtectedRoute roles={["DEPARTMENT_OFFICER"]}>
              <DepartmentDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="department/complaints/:id"
          element={
            <ProtectedRoute roles={["DEPARTMENT_OFFICER"]}>
              <DepartmentDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="superintendent"
          element={
            <ProtectedRoute roles={["SUPERINTENDENT_OFFICER"]}>
              <EscalationQueuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="superintendent/summary"
          element={
            <ProtectedRoute roles={["SUPERINTENDENT_OFFICER"]}>
              <EscalationQueuePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="superintendent/:id"
          element={
            <ProtectedRoute roles={["SUPERINTENDENT_OFFICER"]}>
              <EscalationDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/users"
          element={
            <ProtectedRoute roles={["PLATFORM_ADMIN"]}>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/departments"
          element={
            <ProtectedRoute roles={["PLATFORM_ADMIN"]}>
              <AdminDepartmentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/categories"
          element={
            <ProtectedRoute roles={["PLATFORM_ADMIN"]}>
              <AdminCategoriesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/activity"
          element={
            <ProtectedRoute roles={["PLATFORM_ADMIN"]}>
              <AdminActivityPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/audit"
          element={
            <ProtectedRoute roles={["PLATFORM_ADMIN"]}>
              <AdminAuditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="notifications"
          element={
            <ProtectedRoute>
              <NotificationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route path="forbidden" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
