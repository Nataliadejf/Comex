import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card, Row, Col, Statistic, Table, Tag, Spin, Alert, Input, Button, Typography,
} from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined, SearchOutlined, TagsOutlined,
} from '@ant-design/icons';
import {
  ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { ncmAPI } from '../services/api';

const { Title, Text } = Typography;

const fmtUsd = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v || 0);
const fmtM = (v) => {
  if (v >= 1e9) return `US$ ${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `US$ ${(v / 1e6).toFixed(1)}M`;
  return fmtUsd(v);
};

const AnaliseNCM = () => {
  const { ncm } = useParams();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [inputNCM, setInputNCM] = useState(ncm || '');

  const loadAnalise = useCallback(async (ncmCode) => {
    const dig = String(ncmCode || '').replace(/\D/g, '');
    if (dig.length < 2) {
      setError('Informe um NCM válido (até 8 dígitos)');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await ncmAPI.getAnalise(dig);
      if (response.data?.error) {
        setError(response.data.error);
        setData(null);
      } else {
        setData(response.data);
      }
    } catch (err) {
      setError('Erro ao carregar análise do NCM');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ncm) {
      setInputNCM(ncm);
      loadAnalise(ncm);
    }
  }, [ncm, loadAnalise]);

  const handleSearch = () => {
    const dig = inputNCM.replace(/\D/g, '');
    if (dig.length >= 2) {
      window.history.pushState({}, '', `/ncm/${dig}`);
      loadAnalise(dig);
    } else {
      setError('Informe um NCM válido (até 8 dígitos)');
    }
  };

  const barra = (
    <Card style={{ marginBottom: 16, borderRadius: 10 }} bodyStyle={{ padding: '16px 20px' }}>
      <Title level={4} style={{ marginTop: 0 }}>
        <TagsOutlined style={{ marginRight: 8, color: '#1890ff' }} />
        Análise por NCM
      </Title>
      <Text type="secondary">Importação e exportação reais do produto (NCM) por UF e mês — dados oficiais MDIC.</Text>
      <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
        <Input
          placeholder="Código NCM (ex.: 84213100)"
          value={inputNCM}
          onChange={(e) => setInputNCM(e.target.value)}
          onPressEnter={handleSearch}
          maxLength={8}
          prefix={<SearchOutlined style={{ color: '#aaa' }} />}
          style={{ maxWidth: 300 }}
        />
        <Button type="primary" onClick={handleSearch} loading={loading}>Buscar</Button>
      </div>
      {error && <Alert message={error} type="error" showIcon style={{ marginTop: 12 }} />}
    </Card>
  );

  if (loading) {
    return <div>{barra}<div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" tip="Carregando análise do NCM..." /></div></div>;
  }

  if (!data) {
    return <div>{barra}<Card style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>Digite um código NCM para ver a análise.</Card></div>;
  }

  const ufColumns = [
    { title: 'UF', dataIndex: 'uf', key: 'uf', width: 70 },
    { title: 'Importação', dataIndex: 'v_imp', key: 'v_imp', render: fmtUsd, sorter: (a, b) => a.v_imp - b.v_imp },
    { title: 'Exportação', dataIndex: 'v_exp', key: 'v_exp', render: fmtUsd, sorter: (a, b) => a.v_exp - b.v_exp },
    { title: 'Total', key: 'total', render: (_, r) => fmtUsd(r.v_imp + r.v_exp),
      defaultSortOrder: 'descend', sorter: (a, b) => (a.v_imp + a.v_exp) - (b.v_imp + b.v_exp) },
  ];
  const empColumns = [
    { title: 'Empresa', dataIndex: 'nome', key: 'nome', ellipsis: true },
    { title: 'Valor (US$)', dataIndex: 'valor_total', key: 'valor_total', width: 140, render: fmtUsd,
      defaultSortOrder: 'descend', sorter: (a, b) => a.valor_total - b.valor_total },
    { title: 'Operações', dataIndex: 'total_operacoes', key: 'ops', width: 110 },
  ];

  return (
    <div>
      {barra}
      <Card
        title={<span>NCM <Text code>{data.ncm}</Text> — {data.descricao || 'sem descrição'}</span>}
        style={{ marginBottom: 16 }}
        extra={<Tag color="blue">{data.periodo?.ano_inicio}–{data.periodo?.ano_fim}</Tag>}
      >
        <Row gutter={[16, 16]}>
          <Col xs={12} md={8}>
            <Card style={{ background: 'linear-gradient(135deg,#1890ff,#0050b3)', color: '#fff' }}>
              <div style={{ color: 'rgba(255,255,255,.8)', fontSize: 13 }}>Importações Brasil</div>
              <div style={{ color: '#fff', fontSize: 24, fontWeight: 700 }}>{fmtM(data.total_imp)}</div>
            </Card>
          </Col>
          <Col xs={12} md={8}>
            <Card style={{ background: 'linear-gradient(135deg,#52c41a,#237804)', color: '#fff' }}>
              <div style={{ color: 'rgba(255,255,255,.8)', fontSize: 13 }}>Exportações Brasil</div>
              <div style={{ color: '#fff', fontSize: 24, fontWeight: 700 }}>{fmtM(data.total_exp)}</div>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Statistic title="Saldo Comercial" value={data.saldo} formatter={(v) => fmtM(Number(v))}
                valueStyle={{ color: data.saldo >= 0 ? '#52c41a' : '#f5222d' }}
                prefix={data.saldo >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />} />
            </Card>
          </Col>
        </Row>

        {data.timeline?.length > 0 && (
          <Card title="Evolução Mensal (Importação × Exportação)" size="small" style={{ marginTop: 16 }}>
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart data={data.timeline} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ym" tick={{ fontSize: 10 }} />
                <YAxis tickFormatter={fmtM} tick={{ fontSize: 10 }} width={70} />
                <Tooltip formatter={(v) => fmtUsd(v)} />
                <Legend />
                <Bar dataKey="v_imp" name="Importação" fill="#1890ff" />
                <Bar dataKey="v_exp" name="Exportação" fill="#52c41a" />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        )}

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={12}>
            <Card title="Distribuição por UF" size="small">
              <Table rowKey="uf" columns={ufColumns} dataSource={data.por_uf}
                pagination={{ pageSize: 10 }} size="small" scroll={{ x: 420 }} />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Principais Importadores (reais — Logcomex)" size="small" style={{ marginBottom: 16 }}>
              {data.top_importadores?.length > 0 ? (
                <Table rowKey={(r, i) => `imp-${i}`} columns={empColumns} dataSource={data.top_importadores}
                  pagination={false} size="small" scroll={{ x: 360 }} />
              ) : <Text type="secondary">Sem importadores identificados para este NCM na base.</Text>}
            </Card>
            <Card title="Principais Exportadores estrangeiros (reais — Logcomex)" size="small">
              {data.top_exportadores?.length > 0 ? (
                <Table rowKey={(r, i) => `exp-${i}`} columns={empColumns} dataSource={data.top_exportadores}
                  pagination={false} size="small" scroll={{ x: 360 }} />
              ) : <Text type="secondary">Sem exportadores identificados para este NCM na base.</Text>}
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default AnaliseNCM;
