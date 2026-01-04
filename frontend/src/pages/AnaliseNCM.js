import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Spin,
  Alert,
  Input,
  Button,
} from 'antd';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { ncmAPI } from '../services/api';

const AnaliseNCM = () => {
  const { ncm } = useParams();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [inputNCM, setInputNCM] = useState(ncm || '');

  useEffect(() => {
    if (ncm) {
      loadAnalise(ncm);
    }
  }, [ncm]);

  const loadAnalise = async (ncmCode) => {
    if (!ncmCode || ncmCode.length !== 8) {
      setError('NCM deve ter 8 dígitos');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await ncmAPI.getAnalise(ncmCode);
      setData(response.data);
    } catch (err) {
      setError('Erro ao carregar análise do NCM');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (inputNCM.length === 8) {
      window.location.href = `/ncm/${inputNCM}`;
    } else {
      setError('NCM deve ter 8 dígitos');
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <Card>
        <Alert message={error} type="error" showIcon />
        <div style={{ marginTop: 16 }}>
          <Input
            placeholder="Digite o código NCM (8 dígitos)"
            value={inputNCM}
            onChange={(e) => setInputNCM(e.target.value)}
            maxLength={8}
            style={{ width: 300, marginRight: 8 }}
          />
          <Button type="primary" onClick={handleSearch}>
            Buscar
          </Button>
        </div>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <Alert message="Digite um código NCM para análise" type="info" showIcon />
        <div style={{ marginTop: 16 }}>
          <Input
            placeholder="Digite o código NCM (8 dígitos)"
            value={inputNCM}
            onChange={(e) => setInputNCM(e.target.value)}
            maxLength={8}
            style={{ width: 300, marginRight: 8 }}
          />
          <Button type="primary" onClick={handleSearch}>
            Buscar
          </Button>
        </div>
      </Card>
    );
  }

  const evolucaoData = data.evolucao_temporal.map((item) => ({
    mes: item.mes,
    [item.tipo_operacao]: item.valor_total,
    [`${item.tipo_operacao}_qtd`]: item.quantidade,
  }));

  const paisesColumns = [
    {
      title: 'País',
      dataIndex: 'pais',
      key: 'pais',
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_operacao',
      key: 'tipo_operacao',
      render: (tipo) => (
        <Tag color={tipo === 'Importação' ? 'green' : 'blue'}>
          {tipo}
        </Tag>
      ),
    },
    {
      title: 'Valor Total (USD)',
      dataIndex: 'valor_total',
      key: 'valor_total',
      render: (value) =>
        `$${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Input
            placeholder="Digite o código NCM (8 dígitos)"
            value={inputNCM}
            onChange={(e) => setInputNCM(e.target.value)}
            maxLength={8}
            style={{ width: 300, marginRight: 8 }}
          />
          <Button type="primary" onClick={handleSearch}>
            Buscar
          </Button>
        </div>
      </Card>

      <Card title={`Análise do NCM ${data.ncm}`} bordered={false}>
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total de Operações"
              value={data.estatisticas.total_operacoes}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Valor Total (USD)"
              value={data.estatisticas.valor_total}
              precision={2}
              prefix="$"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Peso Total (kg)"
              value={data.estatisticas.peso_total}
              precision={2}
              suffix="kg"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Valor Médio (USD)"
              value={data.estatisticas.valor_medio}
              precision={2}
              prefix="$"
            />
          </Col>
        </Row>

        <Row gutter={16}>
          <Col xs={24} lg={12}>
            <Card title="Evolução Temporal" bordered={false}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={evolucaoData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="Importação"
                    stroke="#3f8600"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="Exportação"
                    stroke="#cf1322"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="Principais Países" bordered={false}>
              <Table
                columns={paisesColumns}
                dataSource={data.principais_paises.map((item, index) => ({
                  ...item,
                  key: index,
                }))}
                pagination={{ pageSize: 5 }}
                size="small"
              />
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default AnaliseNCM;

