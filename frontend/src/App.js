import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import DashboardComexBigQuery from './pages/DashboardComexBigQuery';
import BuscaAvancada from './pages/BuscaAvancada';
import AnaliseNCM from './pages/AnaliseNCM';
import EmpresasDashboard from './pages/EmpresasDashboard';
import EmpresaContatos from './pages/EmpresaContatos';
import EmpresasHabilitadas from './pages/EmpresasHabilitadas';
import GerenciarUsuarios from './pages/GerenciarUsuarios';
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
                    <Route path="/dashboard-comex-bq" element={<DashboardComexBigQuery />} />
                    <Route path="/busca" element={<BuscaAvancada />} />
                    <Route path="/ncm" element={<AnaliseNCM />} />
                    <Route path="/ncm/:ncm" element={<AnaliseNCM />} />
                    <Route path="/empresas" element={<EmpresasDashboard />} />
                    <Route path="/contatos" element={<EmpresaContatos />} />
                    <Route path="/habilitadas" element={<EmpresasHabilitadas />} />
                    <Route path="/usuarios" element={<GerenciarUsuarios />} />
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

