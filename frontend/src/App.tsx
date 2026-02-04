import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { LoginForm } from './components/LoginForm';
import { Dashboard } from './components/Dashboard';
import { AnalyticsDashboard } from './pages/AnalyticsDashboard';
import { LayoutProvider } from './components/LayoutProvider';

// Dynamic Master Data Pages
import { MetaEntitiesPage } from './pages/MetaEntitiesPage';
import { MasterDataPage } from './pages/MasterDataPage';
import { EntityEditPage } from './pages/EntityEditPage';
import { AuditLogsPage } from './pages/AuditLogsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((state) => state.token);
  return token ? (
    <LayoutProvider>{children}</LayoutProvider>
  ) : (
    <Navigate to="/login" />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginForm />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <AnalyticsDashboard />
            </ProtectedRoute>
          }
        />

        {/* Dynamic Master Data Routes */}
        <Route
          path="/meta-entities"
          element={
            <ProtectedRoute>
              <MetaEntitiesPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/meta-entities/:entityId/edit"
          element={
            <ProtectedRoute>
              <EntityEditPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/master-data/:entityId"
          element={
            <ProtectedRoute>
              <MasterDataPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/audit-logs"
          element={
            <ProtectedRoute>
              <AuditLogsPage />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </BrowserRouter>
  );
}
