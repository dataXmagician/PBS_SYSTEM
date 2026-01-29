import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { LoginForm } from './components/LoginForm';
import { Dashboard } from './components/Dashboard';
import { DataEntryPage } from './pages/DataEntryPage';
import { AnalyticsDashboard } from './pages/AnalyticsDashboard';
import { LayoutProvider } from './components/LayoutProvider';

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
          path="/data-entry"
          element={
            <ProtectedRoute>
              <DataEntryPage />
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
        
        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </BrowserRouter>
  );
}
