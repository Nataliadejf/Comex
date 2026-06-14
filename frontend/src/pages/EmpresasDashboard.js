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
    if (termo.length < 2) { setOptions([]); return; }
    setLoadingSearch(true);
    try {
      // Usar API BQ de contatos (tem dados reais da Receita Federal)
      const res = await comexDashboardBqAPI.autocompleteEmpresa(termo, '', 25);
      const items = res?.data?.items || [];
      setOptions(
        items.map((e) => ({
          value: e.cnpj || e.nome,
          label: (
            <div style={{ lineHeight: 1.4 }}>
              <div style={{ fontWeight: 600 }}>{e.nome}</div>
              <div style={{ fontSize: 11, color: '#888' }}>
                {e.cnpj || ''}{e.uf ? ` · ${e.uf}` : ''}{e.setor ? ` · ${e.setor}` : ''}
              </div>
            </div>
          ),
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
    const digitos = cnpj.replace(/\D/g, '');
    setCnpjSel(digitos || cnpj);
    setLoading(true);
    setPerfil(null);
    setNcms([]); setUfs([]); setSerieBq([]); setDouItems([]); setRanking([]);
    try {
      // Perfil via BQ contatos (não depende de Postgres)
      const pRes = await import('../services/api').then(m => m.default.get(`/api/contatos/empresa/${encodeURIComponent(digitos || cnpj)}`));
      const dadosBq = pRes.data;

      // Montar perfil no formato esperado pelo componente
      const perfilMapeado = {
        razao_social: dadosBq.perfil?.razao_social || '—',
        cnpj: dadosBq.perfil?.cnpj || cnpj,
        uf_sede: dadosBq.perfil?.uf_sede || dadosBq.contato_rf?.uf || '—',
        kpis: dadosBq.kpis || {},
        fonte: 'BigQuery (Receita Federal)',
        cnae_info: dadosBq.cnae_info,
        estabelecimentos: dadosBq.estabelecimentos?.length || 0,
      };
      setPerfil(perfilMapeado);
      // NCMs da empresa via comex
      const ncmsBq = (dadosBq.ncms || []).filter(n =>
        tipoNcm === 'IMP'
          ? ['IMP', 'IMPORTAÇÃO', 'IMPORTACAO'].includes(String(n.tipo || '').toUpperCase())
          : !['IMP', 'IMPORTAÇÃO', 'IMPORTACAO'].includes(String(n.tipo || '').toUpperCase())
      );
      setNcms(ncmsBq);
      // UFs dos estabelecimentos
      const ufMap = {};
      (dadosBq.estabelecimentos || []).forEach(e => {
        if (e.uf) ufMap[e.uf] = (ufMap[e.uf] || 0) + 1;
      });
      setUfs(Object.entries(ufMap).map(([uf, cnt]) => ({ uf, valor_usd: 0, percentual: 0, estabelecimentos: cnt })));
      // Série temporal via comex_por_ano
      const serie = (dadosBq.comex_por_ano || []).map(r => ({
        ym: `${r.ano}-06`,
        total_importacao_fob: r.valor_importacao || 0,
        total_exportacao_fob: r.valor_exportacao || 0,
      }));
      setSerieBq(serie);
      setAvisoSerie(dadosBq.aviso || null);

      // DOU via endpoint específico (tentativa, ignora erros)
      try {
        const dRes = await import('../services/api').then(m => m.default.get(`/api/contatos/empresa/${encodeURIComponent(digitos || cnpj)}/dou`));
        setDouItems(dRes.data?.publicacoes || []);
      } catch { setDouItems([]); }

    } catch (e) {
      message.error(e?.response?.data?.detail || 'Empresa não encontrada ou erro ao carregar dados.');
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
        Busque uma empresa por nome ou CNPJ para ver NCMs, evolução anual, estabelecimentos e publicações no DOU.
        Dados via BigQuery (Receita Federal + comex).
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
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
            message={`${perfil.razao_social}`}
            description={
              `CNPJ: ${perfil.cnpj} · UF Sede: ${perfil.uf_sede || '—'} · Estabelecimentos: ${perfil.estabelecimentos || 0}` +
              (perfil.cnae_info?.setor ? ` · Setor: ${perfil.cnae_info.setor}` : '') +
              (perfil.cnae_info?.segmento ? ` · Segmento: ${perfil.cnae_info.segmento}` : '')
            }
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
