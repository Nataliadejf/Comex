import React, { useState, useCallback } from 'react';
import {
  Card, Col, Row, Input, Select, Button, Table, Tag, Typography, Alert, Space, message,
} from 'antd';
import { SearchOutlined, SafetyCertificateOutlined, DownloadOutlined } from '@ant-design/icons';
import api from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
  'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

const ANOS = Array.from({ length: 25 }, (_, i) => 2021 - i); // 2021..1997

export default function EmpresasHabilitadas() {
  const [uf, setUf] = useState(undefined);
  const [cnaePrefixo, setCnaePrefixo] = useState('');
  const [ano, setAno] = useState(undefined);
  const [loading, setLoading] = useState(false);
  const [empresas, setEmpresas] = useState([]);
  const [buscou, setBuscou] = useState(false);

  const buscar = useCallback(async () => {
    setLoading(true);
    setBuscou(true);
    try {
      const params = { limit: 200 };
      if (uf) params.uf = uf;
      if (cnaePrefixo && cnaePrefixo.trim()) params.cnae_prefixo = cnaePrefixo.trim();
      if (ano) params.ano = ano;
      const res = await api.get('/api/empresa-intel/habilitadas', { params });
      if (res.data?.error) {
        message.error('Erro: ' + res.data.error);
        setEmpresas([]);
      } else {
        setEmpresas(res.data?.empresas || []);
      }
    } catch (e) {
      message.error('Erro ao buscar empresas habilitadas.');
      setEmpresas([]);
    } finally {
      setLoading(false);
    }
  }, [uf, cnaePrefixo, ano]);

  const exportarCsv = () => {
    if (!empresas.length) return;
    const header = ['cnpj', 'razao_social', 'uf', 'cnae', 'primeiro_ano', 'ultimo_ano', 'anos_ativos'];
    const linhas = empresas.map((e) =>
      header.map((h) => `"${String(e[h] ?? '').replace(/"/g, '""')}"`).join(',')
    );
    const csv = [header.join(','), ...linhas].join('\n');
    const blob = new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `empresas_habilitadas${uf ? '_' + uf : ''}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const columns = [
    { title: 'CNPJ', dataIndex: 'cnpj', key: 'cnpj', width: 140 },
    { title: 'Razão Social', dataIndex: 'razao_social', key: 'razao_social', ellipsis: true },
    { title: 'UF', dataIndex: 'uf', key: 'uf', width: 60, render: (v) => <Tag color="blue">{v}</Tag> },
    { title: 'CNAE', dataIndex: 'cnae', key: 'cnae', width: 90 },
    {
      title: 'Período', key: 'periodo', width: 130,
      render: (_, r) => `${r.primeiro_ano}–${r.ultimo_ano}`,
    },
    {
      title: 'Anos Ativos', dataIndex: 'anos_ativos', key: 'anos_ativos', width: 110,
      sorter: (a, b) => a.anos_ativos - b.anos_ativos,
      defaultSortOrder: 'descend',
      render: (v) => <Tag color={v >= 10 ? 'green' : v >= 3 ? 'gold' : 'default'}>{v} anos</Tag>,
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Title level={2}>
        <SafetyCertificateOutlined style={{ color: '#52c41a', marginRight: 8 }} />
        Empresas Habilitadas para Comércio Exterior
      </Title>
      <Text type="secondary">
        Empresas que operaram importação/exportação (RADAR/Siscomex) — base MDIC (1997–2021).
        Filtre por UF, segmento (CNAE) e ano de atividade.
      </Text>

      <Card style={{ marginTop: 16, marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="bottom">
          <Col xs={24} sm={6}>
            <Text style={{ fontSize: 12 }}>UF</Text>
            <Select
              allowClear placeholder="Todas" style={{ width: '100%' }}
              value={uf} onChange={setUf} showSearch
            >
              {UFS.map((u) => <Option key={u} value={u}>{u}</Option>)}
            </Select>
          </Col>
          <Col xs={24} sm={6}>
            <Text style={{ fontSize: 12 }}>CNAE (prefixo)</Text>
            <Input
              placeholder="ex.: 0710 (mineração)" value={cnaePrefixo}
              onChange={(e) => setCnaePrefixo(e.target.value)}
              onPressEnter={buscar}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Text style={{ fontSize: 12 }}>Ano de atividade</Text>
            <Select allowClear placeholder="Qualquer" style={{ width: '100%' }} value={ano} onChange={setAno}>
              {ANOS.map((a) => <Option key={a} value={a}>{a}</Option>)}
            </Select>
          </Col>
          <Col xs={24} sm={6}>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={buscar} loading={loading}>
                Buscar
              </Button>
              {empresas.length > 0 && (
                <Button icon={<DownloadOutlined />} onClick={exportarCsv}>CSV</Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {buscou && !loading && empresas.length === 0 && (
        <Alert type="info" showIcon message="Nenhuma empresa encontrada com esses filtros." />
      )}

      {empresas.length > 0 && (
        <Card title={`${empresas.length} empresa(s) habilitada(s)`} size="small">
          <Table
            rowKey="cnpj"
            columns={columns}
            dataSource={empresas}
            size="small"
            loading={loading}
            pagination={{ pageSize: 20, showSizeChanger: true }}
            scroll={{ x: 800 }}
          />
        </Card>
      )}
    </div>
  );
}
