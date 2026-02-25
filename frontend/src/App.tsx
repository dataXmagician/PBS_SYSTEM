import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { LoginForm } from './components/LoginForm';
import { Dashboard } from './components/Dashboard';
import { AnalyticsDashboard } from './pages/AnalyticsDashboard';
import { LayoutProvider } from './components/LayoutProvider';

// System Data pages
import { SystemDataPage } from './pages/SystemDataPage';
import { VersionsPage } from './pages/VersionsPage';
import { PeriodsPage } from './pages/PeriodsPage';
import { ParametersPage } from './pages/ParametersPage';
import { CurrenciesPage } from './pages/CurrenciesPage';

// Dynamic Master Data Pages
import { MetaEntitiesPage } from './pages/MetaEntitiesPage';
import { MasterDataPage } from './pages/MasterDataPage';
import { EntityEditPage } from './pages/EntityEditPage';
import { AuditLogsPage } from './pages/AuditLogsPage';

// Budget Entry Pages
import { BudgetEntriesPage } from './pages/BudgetEntriesPage';
import { BudgetGridPage } from './pages/BudgetGridPage';

// Data Connections Page
import { DataConnectionsPage } from './pages/DataConnectionsPage';

// Data Flow Page
import { DataFlowPage } from './pages/DataFlowPage';

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

        {/* Budget Entry routes */}
        <Route
          path="/budget-entries"
          element={
            <ProtectedRoute>
              <BudgetEntriesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/budget-entries/:definitionId/grid"
          element={
            <ProtectedRoute>
              <BudgetGridPage />
            </ProtectedRoute>
          }
        />

        {/* Data Connections */}
        <Route
          path="/data-connections"
          element={
            <ProtectedRoute>
              <DataConnectionsPage />
            </ProtectedRoute>
          }
        />

        {/* Data Flow */}
        <Route
          path="/data-flows"
          element={
            <ProtectedRoute>
              <DataFlowPage />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" />} />
        {/* System Data routes */}
        <Route
          path="/system-data"
          element={
            <ProtectedRoute>
              <SystemDataPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/system-data/versions"
          element={
            <ProtectedRoute>
              <VersionsPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/system-data/periods"
          element={
            <ProtectedRoute>
              <PeriodsPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/system-data/parameters"
          element={
            <ProtectedRoute>
              <ParametersPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/system-data/currencies"
          element={
            <ProtectedRoute>
              <CurrenciesPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/system-data/:entity"
          element={
            <ProtectedRoute>
              <SystemDataRouteRedirect />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

function SystemDataRouteRedirect() {
  const params = useParams();
  const entity = params.entity || '';
  if (entity === 'versions') return <Navigate to="/system-data/versions" />;
  if (entity === 'periods') return <Navigate to="/system-data/periods" />;
  if (entity === 'parameters') return <Navigate to="/system-data/parameters" />;
  if (entity === 'currencies') return <Navigate to="/system-data/currencies" />;
  if (entity === 'currency') return <Navigate to="/system-data/currencies" />;
  return <Navigate to="/system-data" />;
}
 
