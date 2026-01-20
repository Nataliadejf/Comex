import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Space, Dropdown } from 'antd';
import {
  DashboardOutlined,
  SearchOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { message } from 'antd';

const { Header, Sider } = Layout;

const AppLayout = ({ children }) => {
  // Começar com sidebar encolhido por padrão (desktop)
  const [collapsed, setCollapsed] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Detectar se está em mobile e ajustar sidebar
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      // Em mobile, começar com sidebar colapsado
      if (mobile) {
        setCollapsed(true);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

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
    // Em mobile, fechar sidebar ao selecionar item do menu
    if (isMobile) {
      setCollapsed(true);
    }
  };

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    message.success('Logout realizado com sucesso!');
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Sair',
    },
  ];

  const handleUserMenuClick = ({ key }) => {
    if (key === 'logout') {
      handleLogout();
    }
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Overlay escuro quando sidebar está aberto em mobile */}
      {isMobile && !collapsed && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.45)',
            zIndex: 998,
          }}
          onClick={() => setCollapsed(true)}
        />
      )}
      <Sider
        collapsible={!isMobile}
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={isMobile ? 250 : 200}
        collapsedWidth={isMobile ? 0 : 80}
        style={{
          position: isMobile ? 'fixed' : 'relative',
          height: '100vh',
          left: isMobile && collapsed ? -250 : 0,
          top: 0,
          zIndex: 999,
          transition: 'left 0.2s',
        }}
        trigger={null}
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
            fontSize: collapsed && !isMobile ? '14px' : '16px',
          }}
        >
          {collapsed && !isMobile ? 'CA' : 'Comex Analyzer'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: isMobile ? 0 : (collapsed ? 80 : 200) }}>
        <Header
          style={{
            background: '#fff',
            padding: isMobile ? '0 12px' : '0 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            position: 'sticky',
            top: 0,
            zIndex: 100,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Botão toggle do sidebar - sempre visível em mobile */}
            {(isMobile || !collapsed) && (
              <Button
                type="text"
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={toggleSidebar}
                style={{
                  fontSize: '18px',
                  width: 40,
                  height: 40,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              />
            )}
            <h1 
              style={{ 
                margin: 0, 
                fontSize: isMobile ? 'clamp(14px, 4vw, 18px)' : '20px', 
                fontWeight: 600,
                display: isMobile && !collapsed ? 'none' : 'block',
              }}
            >
              Análise de Comércio Exterior
            </h1>
          </div>
          <Space>
            <Dropdown 
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }} 
              placement="bottomRight"
            >
              <Button 
                type="text" 
                icon={<UserOutlined />}
                style={{
                  fontSize: isMobile ? '14px' : '16px',
                  padding: isMobile ? '4px 8px' : '4px 15px',
                }}
              >
                {isMobile ? (user.nome_completo?.split(' ')[0] || user.email?.split('@')[0] || 'Usuário') : (user.nome_completo || user.email || 'Usuário')}
              </Button>
            </Dropdown>
          </Space>
        </Header>
        {children}
      </Layout>
    </Layout>
  );
};

export default AppLayout;

