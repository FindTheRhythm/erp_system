import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CatalogList from './pages/CatalogList';
import CatalogForm from './pages/CatalogForm';
import CatalogDetail from './pages/CatalogDetail';
import InventoryList from './pages/InventoryList';
import OperationsList from './pages/OperationsList';
import WarehousePage from './pages/WarehousePage';

function App() {
  console.log('App: Rendering, current path:', window.location.pathname);
  
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalog"
            element={
              <ProtectedRoute>
                <CatalogList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalog/new"
            element={
              <ProtectedRoute>
                <CatalogForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalog/:id"
            element={
              <ProtectedRoute>
                <CatalogDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/catalog/:id/edit"
            element={
              <ProtectedRoute>
                <CatalogForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/inventory"
            element={
              <ProtectedRoute>
                <InventoryList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/inventory/operations"
            element={
              <ProtectedRoute>
                <OperationsList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/warehouse"
            element={
              <ProtectedRoute>
                <WarehousePage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;

