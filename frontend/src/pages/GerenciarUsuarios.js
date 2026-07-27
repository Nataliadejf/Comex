import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Table, Button, Tag, Typography, Space, Popconfirm, message, Empty, Spin, Alert,
  Row, Col, Statistic, Progress,
} from 'antd';
import {
  CheckOutlined, CloseOutlined, ReloadOutlined, TeamOutlined,
  UserOutlined, LoginOutlined, ClockCircleOutlined, EyeOutlined,
} from '@ant-design/icons';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { adminUsuariosAPI } from '../services/api';

const { Title, Text } = Typography;

export default function GerenciarUsuarios() {
  const [loading, setLoading] = useState(true);
  // Inicia do cache p/ não bloquear a tela enquanto o backend acorda (cold start)
  const [isAdmin, setIsAdmin] = useState(() => {
    try { return localStorage.getItem('is_admin') === '1' ? true : null; } catch { return null; }
  });
  const [pendentes, setPendentes] = useState([]);
  const [uso, setUso] = useState([]);
  const [usoResumo, setUsoResumo] = useState(null);
  const [telasRanking, setTelasRanking] = useState([]);
  const [porMes, setPorMes] = useState([]);
  const [acao, setAcao] = useState(null); // email em processamento

  const carregar = useCallback(async () => {
    setLoading(true);
    let admin = false;
    try {
      const meRes = await adminUsuariosAPI.me();
      admin = !!meRes.data?.is_admin;
      setIsAdmin(admin);
      try { localStorage.setItem('is_admin', admin ? '1' : '0'); } catch (_) {}
    } catch (e) {
      const status = e?.response?.status;
      if (status === 401 || status === 403) {
        setIsAdmin(false);
      } else {
        // erro de rede/cold start → mantém o que já estava (cache); tenta carregar os dados mesmo assim
        admin = localStorage.getItem('is_admin') === '1';
      }
    }
    if (admin) {
      try {
        const res = await adminUsuariosAPI.pendentes();
        setPendentes(res.data?.pendentes || []);
      } catch (_) {}
      try {
        const u = await adminUsuariosAPI.uso(90);
        setUso(u.data?.usuarios || []);
        setUsoResumo(u.data?.resumo || null);
        setTelasRanking(u.data?.telas_ranking || []);
        setPorMes(u.data?.por_mes || []);
      } catch (_) { setUso([]); setUsoResumo(null); setTelasRanking([]); setPorMes([]); }
    }
    setLoading(false);
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

  if (isAdmin === false) {
    return (
      <Alert
        type="warning" showIcon
        message="Acesso restrito"
        description="Esta página é exclusiva para administradores."
      />
    );
  }
  if (isAdmin == null) {
    // Status ainda desconhecido (ex.: backend acordando). Não bloqueia — oferece retry.
    return (
      <Alert
        type="info" showIcon
        message="Não foi possível confirmar seu acesso agora"
        description={<span>O servidor pode estar iniciando. <Button size="small" type="link" onClick={carregar}>Tentar novamente</Button></span>}
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

      <Card title="📊 Dashboard de Uso (últimos 90 dias)" style={{ marginTop: 16 }}
        extra={<Button size="small" icon={<ReloadOutlined />} onClick={carregar}>Atualizar</Button>}>
        {uso.length === 0 ? (
          <Empty description="Ainda sem dados de uso registrados. O rastreamento começa a partir de agora — conforme os usuários acessarem, os números aparecem aqui." />
        ) : (
          <>
            {/* KPIs */}
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col xs={12} md={6}>
                <Card size="small" style={{ background: 'linear-gradient(135deg,#667eea,#764ba2)', color: '#fff' }}>
                  <Statistic title={<span style={{ color: 'rgba(255,255,255,.85)' }}>Usuários ativos</span>}
                    value={usoResumo?.usuarios_ativos ?? uso.length}
                    valueStyle={{ color: '#fff' }} prefix={<UserOutlined />} />
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card size="small" style={{ background: 'linear-gradient(135deg,#4facfe,#00f2fe)', color: '#fff' }}>
                  <Statistic title={<span style={{ color: 'rgba(255,255,255,.85)' }}>Total de acessos</span>}
                    value={usoResumo?.total_acessos ?? 0}
                    valueStyle={{ color: '#fff' }} prefix={<LoginOutlined />} />
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card size="small" style={{ background: 'linear-gradient(135deg,#43e97b,#38f9d7)', color: '#fff' }}>
                  <Statistic title={<span style={{ color: 'rgba(255,255,255,.85)' }}>Tempo total</span>}
                    value={usoResumo?.tempo_total_min ?? 0} suffix="min"
                    valueStyle={{ color: '#fff' }} prefix={<ClockCircleOutlined />} />
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card size="small" style={{ background: 'linear-gradient(135deg,#fa709a,#fee140)', color: '#fff' }}>
                  <div style={{ color: 'rgba(255,255,255,.85)', fontSize: 14 }}><EyeOutlined /> Tela mais acessada</div>
                  <div style={{ color: '#fff', fontSize: 18, fontWeight: 700, marginTop: 6 }}>
                    {usoResumo?.tela_mais_acessada || '—'}
                  </div>
                </Card>
              </Col>
            </Row>

            {/* Histórico mês a mês (últimos 12 meses) */}
            {porMes.length > 0 && (
              <Card size="small" title="📅 Acessos por mês (últimos 12 meses)" style={{ marginBottom: 16 }}>
                <ResponsiveContainer width="100%" height={260}>
                  <ComposedChart data={porMes} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="mes" tick={{ fontSize: 11 }} tickFormatter={(v) => (v || '').slice(2)} />
                    <YAxis yAxisId="l" tick={{ fontSize: 11 }} allowDecimals={false} />
                    <YAxis yAxisId="r" orientation="right" tick={{ fontSize: 11 }} allowDecimals={false} />
                    <RTooltip formatter={(v, n) => [v, n === 'tempo_min' ? 'Tempo (min)' : n === 'usuarios' ? 'Usuários' : 'Acessos']} />
                    <Legend formatter={(n) => (n === 'acessos' ? 'Acessos' : n === 'usuarios' ? 'Usuários ativos' : 'Tempo (min)')} />
                    <Bar yAxisId="l" dataKey="acessos" fill="#667eea" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="r" type="monotone" dataKey="usuarios" stroke="#fa709a" strokeWidth={2} dot={{ r: 3 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            )}

            <Row gutter={[16, 16]}>
              {/* Ranking global de telas */}
              <Col xs={24} lg={9}>
                <Card size="small" title="🖥️ Telas mais acessadas">
                  {telasRanking.length === 0 ? <Empty description="Sem dados" /> : (() => {
                    const max = Math.max(...telasRanking.map((t) => t.visitas), 1);
                    return telasRanking.slice(0, 8).map((t) => (
                      <div key={t.tela} style={{ marginBottom: 10 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                          <span>{t.tela}</span><span>{t.visitas}</span>
                        </div>
                        <Progress percent={Math.round((t.visitas / max) * 100)} showInfo={false} size="small" />
                      </div>
                    ));
                  })()}
                </Card>
              </Col>

              {/* Tabela por usuário */}
              <Col xs={24} lg={15}>
                <Card size="small" title="👤 Por usuário">
                  <Table
                    rowKey="email"
                    dataSource={uso}
                    pagination={false}
                    size="small"
                    scroll={{ x: 700 }}
                    columns={[
                      { title: 'Usuário', dataIndex: 'email', key: 'email', ellipsis: true },
                      { title: 'Acessos', dataIndex: 'acessos', key: 'acessos', width: 90,
                        sorter: (a, b) => a.acessos - b.acessos, defaultSortOrder: 'descend' },
                      { title: 'Tempo total', dataIndex: 'tempo_total_min', key: 'tt', width: 110,
                        render: (v) => `${(v || 0).toLocaleString('pt-BR')} min` },
                      { title: 'Média/sessão', dataIndex: 'tempo_medio_min', key: 'tm', width: 120,
                        render: (v) => `${(v || 0).toLocaleString('pt-BR')} min` },
                      { title: 'Último acesso', dataIndex: 'ultimo_acesso', key: 'ua', width: 160,
                        render: (v) => v ? new Date(v).toLocaleString('pt-BR') : '—' },
                      { title: 'Telas mais usadas', key: 'telas',
                        render: (_, r) => (r.telas || []).slice(0, 3).map((t) => (
                          <Tag key={t.tela}>{t.tela} ({t.visitas})</Tag>
                        )) },
                    ]}
                  />
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Card>
    </div>
  );
}
