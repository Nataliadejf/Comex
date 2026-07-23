import React, { useState, useCallback } from 'react';
import {
  Card, Row, Col, Statistic, Table, Tag, Spin, Alert, Input, Button, Typography, Select, Empty,
} from 'antd';
import { GlobalOutlined, SearchOutlined, ArrowDownOutlined, ArrowUpOutlined } from '@ant-design/icons';
import { ncmAPI } from '../services/api';

const { Title, Text } = Typography;

const fmtUsd = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v || 0);
const fmtM = (v) => {
  if (v >= 1e9) return `US$ ${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `US$ ${(v / 1e6).toFixed(1)}M`;
  return fmtUsd(v);
};

export default function PanoramaGlobal() {
  const [ncm, setNcm] = useState('');
  const [ano, setAno] = useState(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [erro, setErro] = useState(null);

  const buscar = useCallback(async (anoSel) => {
    const dig = ncm.replace(/\D/g, '');
    if (dig.length < 6) { setErro('Informe um NCM com ao menos 6 dígitos'); return; }
    setLoading(true); setErro(null);
    try {
      const res = await ncmAPI.panoramaGlobal(dig, anoSel ?? ano);
      if (res.data?.error) { setErro(res.data.error); setData(null); }
      else setData(res.data);
    } catch (e) {
      setErro('Erro ao consultar o panorama global');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [ncm, ano]);

  const colPaises = (uf) => [
    { title: '#', key: 'rk', width: 44, render: (_, __, i) => i + 1 },
    { title: 'País', dataIndex: 'pais', key: 'pais', render: (v, r) => <span>{v} {r.iso3 && <Tag>{r.iso3}</Tag>}</span> },
    { title: `Valor ${uf} (US$)`, dataIndex: 'valor_usd', key: 'v', width: 160, render: fmtUsd,
      defaultSortOrder: 'descend', sorter: (a, b) => a.valor_usd - b.valor_usd },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <GlobalOutlined style={{ marginRight: 10, color: '#1890ff' }} />
          Panorama Global do Produto
        </Title>
        <Text type="secondary">
          Comércio internacional do produto (HS6) — maiores países importadores e exportadores no mundo. Fonte: UN Comtrade.
        </Text>
      </div>

      <Card style={{ marginBottom: 16 }} bodyStyle={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <Input
            placeholder="Código NCM/HS (ex.: 843149)"
            value={ncm}
            onChange={(e) => setNcm(e.target.value)}
            onPressEnter={() => buscar()}
            maxLength={8}
            prefix={<SearchOutlined style={{ color: '#aaa' }} />}
            style={{ maxWidth: 260 }}
          />
          {data?.anos_disponiveis?.length > 0 && (
            <Select
              value={data.ano}
              style={{ width: 110 }}
              onChange={(v) => { setAno(v); buscar(v); }}
              options={data.anos_disponiveis.map((a) => ({ value: a, label: String(a) }))}
            />
          )}
          <Button type="primary" icon={<SearchOutlined />} onClick={() => buscar()} loading={loading}>Buscar</Button>
        </div>
        {erro && <Alert message={erro} type="error" showIcon style={{ marginTop: 12 }} />}
      </Card>

      {loading && <div style={{ textAlign: 'center', padding: 50 }}><Spin size="large" /></div>}

      {!loading && data && data.disponivel === false && (
        <Alert type="warning" showIcon message="Produto fora da amostra curada"
          description={data.aviso || 'Este HS6 ainda não foi carregado na base global. A amostra atual cobre os principais produtos.'} />
      )}

      {!loading && data && data.disponivel && (
        <>
          <Card style={{ marginBottom: 16 }}
            title={<span>HS6 <Text code>{data.hs6}</Text> {data.descricao ? `— ${data.descricao}` : ''}</span>}
            extra={<Tag color="blue">Ano {data.ano}</Tag>}>
            <Row gutter={[16, 16]}>
              <Col xs={12} md={6}>
                <Card style={{ background: 'linear-gradient(135deg,#1890ff,#0050b3)', color: '#fff' }}>
                  <div style={{ color: 'rgba(255,255,255,.8)', fontSize: 13 }}>Importação mundial</div>
                  <div style={{ color: '#fff', fontSize: 22, fontWeight: 700 }}>{fmtM(data.total_importacao_mundial)}</div>
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card style={{ background: 'linear-gradient(135deg,#52c41a,#237804)', color: '#fff' }}>
                  <div style={{ color: 'rgba(255,255,255,.8)', fontSize: 13 }}>Exportação mundial</div>
                  <div style={{ color: '#fff', fontSize: 22, fontWeight: 700 }}>{fmtM(data.total_exportacao_mundial)}</div>
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card><Statistic title="Países importadores" value={data.n_paises_importadores} prefix={<ArrowDownOutlined style={{ color: '#1890ff' }} />} /></Card>
              </Col>
              <Col xs={12} md={6}>
                <Card><Statistic title="Países exportadores" value={data.n_paises_exportadores} prefix={<ArrowUpOutlined style={{ color: '#52c41a' }} />} /></Card>
              </Col>
            </Row>
          </Card>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="🌍 Maiores Importadores do mundo" size="small">
                {data.top_importadores?.length > 0
                  ? <Table rowKey="pais" columns={colPaises('Import.')} dataSource={data.top_importadores} pagination={false} size="small" />
                  : <Empty description="Sem dados" />}
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="🌍 Maiores Exportadores do mundo" size="small">
                {data.top_exportadores?.length > 0
                  ? <Table rowKey="pais" columns={colPaises('Export.')} dataSource={data.top_exportadores} pagination={false} size="small" />
                  : <Empty description="Sem dados" />}
              </Card>
            </Col>
          </Row>
          <div style={{ marginTop: 12, fontSize: 12, color: '#999' }}>{data.fonte}</div>
        </>
      )}

      {!loading && !data && (
        <Card style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>
          Digite um código NCM/HS (6+ dígitos) para ver o panorama do produto no comércio mundial.
        </Card>
      )}
    </div>
  );
}
