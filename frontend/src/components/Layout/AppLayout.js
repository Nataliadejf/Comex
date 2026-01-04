import React, { useState } from 'react';
import { Layout, Menu, Button, Space, message } from 'antd';
import {
  DashboardOutlined,
  SearchOutlined,
  BarChartOutlined,
  SyncOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider } = Layout;

const AppLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/busca',
      icon: <SearchOutlined />,
      label: 'Busca Avançada',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    message.success('Logout realizado com sucesso!');
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={200}
      >
        <div
          style={{
            height: 32,
            margin: 16,
            background: 'rgba(255, 255, 255, 0.3)',
            borderRadius: 4,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
          }}
        >
          {collapsed ? 'CA' : 'Comex Analyzer'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
            Análise de Comércio Exterior
          </h1>
          <Button
            type="primary"
            danger
            icon={<LogoutOutlined />}
            onClick={handleLogout}
          >
            Sair
          </Button>
        </Header>
        {children}
      </Layout>
    </Layout>
  );
};

export default AppLayout;

