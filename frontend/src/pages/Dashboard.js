import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Spin, Alert, Table, Tag } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { dashboardAPI } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await dashboardAPI.getStats(3);
      setStats(response.data);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Erro ao carregar dados do dashboard';
      setError(`Erro ao carregar dados do dashboard: ${errorMessage}`);
      console.error('Erro completo:', err);
      console.error('URL da API:', process.env.REACT_APP_API_URL || 'http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return <Alert message={error} type="error" showIcon />;
  }

  if (!stats) {
    return <Alert message="Nenhum dado disponível" type="info" showIcon />;
  }

  // Preparar dados para gráficos
  const evolucaoData = Object.entries(stats.registros_por_mes).map(([mes, count]) => ({
    mes,
    registros: count,
  }));

  const topNCMsData = stats.principais_ncms.slice(0, 10).map((item) => ({
    name: item.ncm,
    value: item.valor_total,
    descricao: item.descricao,
  }));

  const topPaisesData = stats.principais_paises.slice(0, 10).map((item) => ({
    name: item.pais,
    value: item.valor_total,
  }));

  const columnsNCM = [
    {
      title: 'NCM',
      dataIndex: 'ncm',
      key: 'ncm',
    },
    {
      title: 'Descrição',
      dataIndex: 'descricao',
      key: 'descricao',
      ellipsis: true,
    },
    {
      title: 'Valor Total (USD)',
      dataIndex: 'valor_total',
      key: 'valor_total',
      render: (value) => `$${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
    },
    {
      title: 'Operações',
      dataIndex: 'total_operacoes',
      key: 'total_operacoes',
    },
  ];

  return (
    <div>
      <Row gutter={[16, 16]}>
        {/* Cards de Métricas */}
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Volume Importações"
              value={stats.volume_importacoes}
              precision={2}
              suffix="kg"
              prefix={<ArrowDownOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Volume Exportações"
              value={stats.volume_exportacoes}
              precision={2}
              suffix="kg"
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Valor Total Movimentado"
              value={stats.valor_total_usd}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Principais Países"
              value={stats.principais_paises.length}
              prefix={<GlobalOutlined />}
            />
          </Card>
        </Col>

        {/* Gráfico de Evolução Temporal */}
        <Col xs={24} lg={12}>
          <Card title="Evolução Temporal de Registros" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={evolucaoData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="registros"
                  stroke="#1890ff"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Gráfico de Pizza - Top NCMs */}
        <Col xs={24} lg={12}>
          <Card title="Top 10 NCMs por Valor" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={topNCMsData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {topNCMsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Gráfico de Barras - Top Países */}
        <Col xs={24} lg={12}>
          <Card title="Top 10 Países por Valor" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topPaisesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Tabela de Top NCMs */}
        <Col xs={24}>
          <Card title="Principais NCMs" bordered={false}>
            <Table
              columns={columnsNCM}
              dataSource={stats.principais_ncms.map((item, index) => ({
                ...item,
                key: index,
              }))}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;

