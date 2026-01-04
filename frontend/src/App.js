import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import BuscaAvancada from './pages/BuscaAvancada';
import AnaliseNCM from './pages/AnaliseNCM';
import Login from './pages/Login';
import './App.css';

const { Content } = Layout;

// Componente para proteger rotas (requer login)
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
};

function App() {
  const token = localStorage.getItem('token');
  
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Content style={{ padding: '24px', minHeight: '100vh' }}>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/busca" element={<BuscaAvancada />} />
                    <Route path="/ncm/:ncm" element={<AnaliseNCM />} />
                  </Routes>
                </Content>
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;

