import React, { useState, useCallback } from 'react';
import {
  Card, Form, Input, DatePicker, Select, Button, Row, Col, Table, Space, Tag, Alert, message,
} from 'antd';
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '../services/api';

const { RangePicker } = DatePicker;
const { Option } = Select;

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

const fmtUsd = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v || 0);

const BuscaAvancada = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [total, setTotal] = useState(0);
  const [ncmOptions, setNcmOptions] = useState([]);

  // Autocomplete de NCM (por código)
  const buscarNcm = useCallback(async (q) => {
    const digitos = (q || '').replace(/\D/g, '');
    if (digitos.length < 2) { setNcmOptions([]); return; }
    try {
      const res = await api.get('/api/empresa-intel/ncm-autocomplete', { params: { q: digitos, limit: 20 } });
      setNcmOptions((res.data?.items || []).map((i) => ({ value: i.ncm, label: i.ncm })));
    } catch {
      setNcmOptions([]);
    }
  }, []);

  const handleSearch = async (values, page = 1) => {
    setLoading(true);
    try {
      const tipoMap = { 'Importação': 'importacao', 'Exportação': 'exportacao' };
      const params = {
        page,
        page_size: 100,
      };
      if (values.ncms && values.ncms.length) params.ncms = values.ncms;
      if (values.tipo_operacao) params.tipo = tipoMap[values.tipo_operacao] || values.tipo_operacao;
      if (values.uf) params.uf = values.uf;
      if (values.periodo?.[0]) params.data_inicio = values.periodo[0].format('YYYY-MM-DD');
      if (values.periodo?.[1]) params.data_fim = values.periodo[1].format('YYYY-MM-DD');
      if (values.valor_fob_min) params.fob_min = Number(values.valor_fob_min);
      if (values.valor_fob_max) params.fob_max = Number(values.valor_fob_max);

      const res = await api.get('/api/empresa-intel/busca-comex', { params });
      if (res.data?.error) {
        message.error('Erro: ' + res.data.error);
        setResults([]); setTotal(0);
      } else {
        setResults(res.data?.results || []);
        setTotal(res.data?.total || 0);
      }
    } catch (e) {
      message.error('Erro ao buscar dados.');
      setResults([]); setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const exportarCsv = () => {
    if (!results?.length) return;
    const header = ['ncm', 'tipo_operacao', 'uf', 'valor_fob', 'data_operacao'];
    const linhas = results.map((r) => header.map((h) => `"${String(r[h] ?? '')}"`).join(','));
    const csv = [header.join(','), ...linhas].join('\n');
    const blob = new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'busca_comex.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const columns = [
    { title: 'NCM', dataIndex: 'ncm', key: 'ncm', width: 120 },
    {
      title: 'Tipo', dataIndex: 'tipo_operacao', key: 'tipo_operacao', width: 130,
      render: (t) => <Tag color={t === 'Importação' ? 'blue' : 'green'}>{t}</Tag>,
    },
    { title: 'UF', dataIndex: 'uf', key: 'uf', width: 70, render: (v) => <Tag>{v}</Tag> },
    {
      title: 'Valor FOB (USD)', dataIndex: 'valor_fob', key: 'valor_fob', width: 180,
      sorter: (a, b) => a.valor_fob - b.valor_fob, defaultSortOrder: 'descend',
      render: (v) => fmtUsd(v),
    },
    {
      title: 'Período', dataIndex: 'data_operacao', key: 'data_operacao', width: 120,
      render: (d) => (d ? dayjs(d).format('MM/YYYY') : '—'),
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card title="Busca Avançada — Comércio Exterior por NCM e UF" bordered={false}>
        <Alert
          type="info" showIcon style={{ marginBottom: 16 }}
          message="Dados oficiais reais (MDIC) agregados por NCM × UF × mês"
          description="Digite o NCM (o autocomplete sugere códigos válidos), escolha o tipo e o período. Os valores são o FOB total real por estado — independem de importador/exportador."
        />
        <Form form={form} layout="vertical" onFinish={(values) => handleSearch(values, 1)}>
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="ncms" label="NCM (código)">
                <Select
                  mode="tags"
                  placeholder="Digite o NCM (ex.: 8708...)"
                  tokenSeparators={[',', ' ']}
                  onSearch={buscarNcm}
                  options={ncmOptions}
                  filterOption={false}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={5}>
              <Form.Item name="tipo_operacao" label="Tipo de Operação">
                <Select placeholder="Ambos" allowClear>
                  <Option value="Importação">Importação</Option>
                  <Option value="Exportação">Exportação</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={5}>
              <Form.Item name="uf" label="UF">
                <Select placeholder="Todas" showSearch allowClear>
                  {UFS.map((uf) => <Option key={uf} value={uf}>{uf}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="periodo" label="Período" initialValue={[dayjs().subtract(1, 'year'), dayjs()]}>
                <RangePicker style={{ width: '100%' }} picker="month" format="MM/YYYY" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={5}>
              <Form.Item name="valor_fob_min" label="Valor FOB Mínimo (USD)">
                <Input type="number" placeholder="0" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={5}>
              <Form.Item name="valor_fob_max" label="Valor FOB Máximo (USD)">
                <Input type="number" placeholder="0" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} htmlType="submit" loading={loading}>
                Buscar
              </Button>
              <Button icon={<DownloadOutlined />} onClick={exportarCsv} disabled={!results?.length}>
                Exportar CSV
              </Button>
              <Button onClick={() => { form.resetFields(); setResults(null); setTotal(0); }}>Limpar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {results && (
        <Card
          title={`Resultados — ${total.toLocaleString('pt-BR')} registro(s) (NCM × UF × mês)`}
          bordered={false}
          style={{ marginTop: 16 }}
        >
          {results.length === 0 ? (
            <Alert type="warning" showIcon message="Nenhum resultado para os filtros informados." />
          ) : (
            <Table
              rowKey={(r, i) => `${r.ncm}-${r.uf}-${r.data_operacao}-${r.tipo_operacao}-${i}`}
              columns={columns}
              dataSource={results}
              loading={loading}
              size="small"
              pagination={{ pageSize: 20, showSizeChanger: true }}
              scroll={{ x: 700 }}
            />
          )}
        </Card>
      )}
    </div>
  );
};

export default BuscaAvancada;
