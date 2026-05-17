import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, AutoComplete, Card, Col, Input, Row, Spin, Table, Tabs, Tag, Typography, message,
} from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { empresasApi } from '../api/empresasApi';
import { comexDashboardBqAPI } from '../services/api';
import EmpresaTimeline from '../components/empresas/EmpresaTimeline';

const { Title, Text } = Typography;

const fmtUsd = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v || 0);

const fmtKg = (v) =>
  new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(v || 0);

const badgeTipo = (t) => (
  <Tag color={t === 'IMP' ? 'blue' : 'green'}>{t === 'IMP' ? 'Importação' : 'Exportação'}</Tag>
);

const badgeDou = (tipo) => {
  const colors = { Habilitação: 'green', Penalidade: 'red', Portaria: 'default' };
  return <Tag color={colors[tipo] || 'default'}>{tipo || 'Outros'}</Tag>;
};

export default function EmpresasDashboard() {
  const [search, setSearch] = useState('');
  const [options, setOptions] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [cnpjSel, setCnpjSel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [perfil, setPerfil] = useState(null);
  const [ncms, setNcms] = useState([]);
  const [ufs, setUfs] = useState([]);
  const [serieBq, setSerieBq] = useState([]);
  const [avisoSerie, setAvisoSerie] = useState(null);
  const [projecao, setProjecao] = useState([]);
  const [douItems, setDouItems] = useState([]);
  const [ranking, setRanking] = useState([]);
  const [tipoNcm, setTipoNcm] = useState('IMP');

  const buscarSugestoes = useCallback(async (q) => {
    const termo = (q || '').trim();
    setSearch(termo);
    if (termo.length < 2) {
      setOptions([]);
      return;
    }
    setLoadingSearch(true);
    try {
      const res = await comexDashboardBqAPI.autocompleteEmpresa(termo, '', 25);
      const items = res?.data?.items || [];
      setOptions(
        items.map((e) => ({
          value: e.cnpj || e.nome,
          label: `${e.nome}${e.cnpj ? ` — ${e.cnpj}` : ''}`,
          nome: e.nome,
          cnpj: e.cnpj,
        }))
      );
    } catch {
      setOptions([]);
    } finally {
      setLoadingSearch(false);
    }
  }, []);

  const carregarEmpresa = useCallback(async (cnpj) => {
    if (!cnpj) return;
    setCnpjSel(cnpj);
    setLoading(true);
    try {
      const [pRes, nRes, eRes, sRes, prRes, dRes, rRes] = await Promise.all([
        empresasApi.perfil(cnpj),
        empresasApi.ncms(cnpj, { tipo: tipoNcm, page: 1, size: 20 }),
        empresasApi.estados(cnpj, { tipo: tipoNcm }),
        empresasApi.serieTemporal(cnpj, { meses: 36 }),
        empresasApi.projecao(cnpj, { tipo: tipoNcm, n_meses: 6 }),
        empresasApi.douEmpresa(cnpj, { page: 1, size: 20 }),
        empresasApi.ranking({ tipo: tipoNcm, n: 10 }),
      ]);
      setPerfil(pRes.data);
      setNcms(nRes.data?.items || []);
      setUfs(eRes.data?.ufs || []);
      setSerieBq(sRes.data?.serie || []);
      setAvisoSerie(sRes.data?.aviso || null);
      setProjecao(prRes.data?.projecao || []);
      setDouItems(dRes.data?.items || []);
      setRanking(rRes.data?.items || []);
    } catch (e) {
      message.error(e?.response?.data?.detail || 'Erro ao carregar empresa');
      setPerfil(null);
    } finally {
      setLoading(false);
    }
  }, [tipoNcm]);

  useEffect(() => {
    if (cnpjSel) carregarEmpresa(cnpjSel);
  }, [tipoNcm, cnpjSel, carregarEmpresa]);

  const onSelect = (_, opt) => {
    const cnpj = opt.cnpj || opt.value;
    carregarEmpresa(cnpj);
  };

  const kpis = perfil?.kpis || {};

  const ncmColumns = [
    { title: 'NCM', dataIndex: 'ncm', key: 'ncm', width: 110 },
    { title: 'Descrição', dataIndex: 'descricao', key: 'descricao', ellipsis: true },
    { title: 'Tipo', dataIndex: 'tipo', key: 'tipo', render: badgeTipo },
    { title: 'Valor USD', dataIndex: 'valor_usd', key: 'valor_usd', render: fmtUsd },
    { title: 'Peso KG', dataIndex: 'peso_kg', key: 'peso_kg', render: fmtKg },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Title level={2}>Painel de Empresas — Importação &amp; Exportação</Title>
      <Text type="secondary">
        Série temporal via BigQuery (empresas_base + import/export UF×NCM). Use BQ_PIPELINE_SOURCE=unified se tiver tabela por CNPJ.
      </Text>

      <Card style={{ marginTop: 16, marginBottom: 16 }}>
        <AutoComplete
          style={{ width: '100%' }}
          options={options}
          onSearch={buscarSugestoes}
          onSelect={onSelect}
          value={search}
          notFoundContent={loadingSearch ? <Spin size="small" /> : 'Digite ao menos 2 caracteres'}
        >
          <Input size="large" placeholder="CNPJ ou razão social (ex.: Vale)" prefix={<SearchOutlined />} />
        </AutoComplete>
      </Card>

      {loading && (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Spin size="large" />
        </div>
      )}

      {perfil && !loading && (
        <>
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message={`${perfil.razao_social} (${perfil.cnpj})`}
            description={`UF sede: ${perfil.uf_sede || '—'} · Fonte: ${perfil.fonte}`}
          />

          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card><Text type="secondary">Importação</Text><Title level={4}>{fmtUsd(kpis.valor_importacao_usd)}</Title></Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card><Text type="secondary">Exportação</Text><Title level={4}>{fmtUsd(kpis.valor_exportacao_usd)}</Title></Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card><Text type="secondary">NCMs distintos</Text><Title level={4}>{kpis.num_ncms ?? 0}</Title></Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card><Text type="secondary">Países</Text><Title level={4}>{kpis.num_paises ?? 0}</Title></Card>
            </Col>
          </Row>

          <Tabs
            style={{ marginTop: 16 }}
            activeKey={tipoNcm}
            onChange={setTipoNcm}
            items={[
              { key: 'IMP', label: 'Importação' },
              { key: 'EXP', label: 'Exportação' },
            ]}
          />

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} lg={14}>
              <Card title="Operações por NCM">
                <Table
                  rowKey={(r, i) => `${r.ncm}-${i}`}
                  columns={ncmColumns}
                  dataSource={ncms}
                  pagination={false}
                  size="small"
                />
              </Card>
            </Col>
            <Col xs={24} lg={10}>
              <Card title="Volume por UF">
                {ufs.length === 0 ? (
                  <Text type="secondary">Sem dados por UF</Text>
                ) : (
                  ufs.map((u) => (
                    <div key={u.uf} style={{ marginBottom: 8 }}>
                      <strong>{u.uf}</strong>: {fmtUsd(u.valor_usd)} ({u.percentual}%)
                    </div>
                  ))
                )}
              </Card>
            </Col>
          </Row>

          <Card title="Série temporal (BigQuery)" style={{ marginTop: 16 }}>
            <EmpresaTimeline
              serie={serieBq}
              projecao={projecao}
              aviso={avisoSerie}
              loading={false}
              height={300}
            />
          </Card>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} lg={12}>
              <Card title="Diário Oficial">
                {douItems.map((d) => (
                  <Card key={d.id} size="small" style={{ marginBottom: 8 }}>
                    {badgeDou(d.tipo_ato)}
                    <Text style={{ marginLeft: 8 }}>{d.data_pub}</Text>
                    <div style={{ marginTop: 8 }}>{(d.resumo || '').slice(0, 300)}</div>
                    {d.url && (
                      <a href={d.url} target="_blank" rel="noreferrer">Ver no DOU</a>
                    )}
                  </Card>
                ))}
                {douItems.length === 0 && <Text type="secondary">Nenhum registro DOU. Ative DOU_SCRAPING_ENABLED no backend.</Text>}
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Ranking (top 10)">
                <Table
                  size="small"
                  pagination={false}
                  rowKey="cnpj"
                  dataSource={ranking}
                  columns={[
                    { title: 'Empresa', dataIndex: 'razao_social', ellipsis: true },
                    { title: 'UF', dataIndex: 'uf', width: 50 },
                    { title: 'USD', dataIndex: 'valor_usd', render: fmtUsd },
                  ]}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
}
