import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Table, Button, Tag, Typography, Space, Popconfirm, message, Empty, Spin, Alert,
} from 'antd';
import {
  CheckOutlined, CloseOutlined, ReloadOutlined, TeamOutlined,
} from '@ant-design/icons';
import { adminUsuariosAPI } from '../services/api';

const { Title, Text } = Typography;

export default function GerenciarUsuarios() {
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(null);
  const [pendentes, setPendentes] = useState([]);
  const [acao, setAcao] = useState(null); // email em processamento

  const carregar = useCallback(async () => {
    setLoading(true);
    try {
      const meRes = await adminUsuariosAPI.me();
      const admin = !!meRes.data?.is_admin;
      setIsAdmin(admin);
      if (admin) {
        const res = await adminUsuariosAPI.pendentes();
        setPendentes(res.data?.pendentes || []);
      }
    } catch (e) {
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { carregar(); }, [carregar]);

  const aprovar = async (email) => {
    setAcao(email);
    try {
      await adminUsuariosAPI.aprovar(email);
      message.success(`${email} aprovado`);
      setPendentes((p) => p.filter((u) => u.email !== email));
    } catch (e) {
      message.error(e?.response?.data?.detail || 'Falha ao aprovar');
    } finally {
      setAcao(null);
    }
  };

  const recusar = async (email) => {
    setAcao(email);
    try {
      await adminUsuariosAPI.recusar(email);
      message.success(`${email} recusado`);
      setPendentes((p) => p.filter((u) => u.email !== email));
    } catch (e) {
      message.error(e?.response?.data?.detail || 'Falha ao recusar');
    } finally {
      setAcao(null);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" tip="Carregando..." /></div>;
  }

  if (!isAdmin) {
    return (
      <Alert
        type="warning" showIcon
        message="Acesso restrito"
        description="Esta página é exclusiva para administradores."
      />
    );
  }

  const columns = [
    { title: 'Nome', dataIndex: 'nome_completo', key: 'nome', render: (v) => v || <Text type="secondary">—</Text> },
    { title: 'E-mail', dataIndex: 'email', key: 'email', render: (v) => <Text copyable>{v}</Text> },
    { title: 'Empresa', dataIndex: 'nome_empresa', key: 'empresa', render: (v) => v || <Text type="secondary">—</Text> },
    {
      title: 'Cadastrado em', dataIndex: 'criado_em', key: 'criado_em', width: 180,
      render: (v) => v ? new Date(v).toLocaleString('pt-BR') : '—',
    },
    {
      title: 'Ações', key: 'acoes', width: 220,
      render: (_, r) => (
        <Space>
          <Popconfirm title={`Aprovar ${r.email}?`} onConfirm={() => aprovar(r.email)} okText="Aprovar" cancelText="Cancelar">
            <Button type="primary" size="small" icon={<CheckOutlined />} loading={acao === r.email}>Aprovar</Button>
          </Popconfirm>
          <Popconfirm title={`Recusar ${r.email}?`} onConfirm={() => recusar(r.email)} okText="Recusar" okButtonProps={{ danger: true }} cancelText="Cancelar">
            <Button danger size="small" icon={<CloseOutlined />} loading={acao === r.email}>Recusar</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <TeamOutlined style={{ marginRight: 10, color: '#667eea' }} />
          Gerenciar Usuários
        </Title>
        <Text type="secondary">Aprove ou recuse os cadastros que estão aguardando liberação de acesso.</Text>
      </div>
      <Card
        title={<span>Cadastros pendentes {pendentes.length > 0 && <Tag color="orange">{pendentes.length}</Tag>}</span>}
        extra={<Button size="small" icon={<ReloadOutlined />} onClick={carregar}>Atualizar</Button>}
      >
        {pendentes.length === 0 ? (
          <Empty description="Nenhum cadastro pendente no momento." />
        ) : (
          <Table rowKey="email" columns={columns} dataSource={pendentes} pagination={false} size="small" scroll={{ x: 700 }} />
        )}
      </Card>
    </div>
  );
}
