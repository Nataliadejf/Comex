import React, { useState, useCallback } from 'react';
import {
  Alert, AutoComplete, Badge, Button, Card, Col, Descriptions, Divider,
  Empty, Input, Row, Spin, Table, Tag, Tabs, Tooltip, Typography, message,
} from 'antd';
import {
  ApartmentOutlined,
  BankOutlined,
  EnvironmentOutlined,
  ExportOutlined,
  ImportOutlined,
  PhoneOutlined,
  SearchOutlined,
  ShopOutlined,
  TagsOutlined,
} from '@ant-design/icons';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend,
  ResponsiveContainer, Tooltip as RTooltip, XAxis, YAxis,
} from 'recharts';
import api from '../services/api';

const { Title, Text } = Typography;

const COLORS = ['#667eea', '#4facfe', '#f093fb', '#43e97b', '#fa709a', '#fee140'];

const fmtUsd = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v || 0);

const fmtNum = (v) =>
  new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(v || 0);

const fmtCnpj = (v) => {
  const s = String(v || '').replace(/\D/g, '').padStart(14, '0');
  return `${s.slice(0, 2)}.${s.slice(2, 5)}.${s.slice(5, 8)}/${s.slice(8, 12)}-${s.slice(12, 14)}`;
};

const SETOR_COLORS = {
  INDÚSTRIA: 'blue',
  DISTRIBUIDOR: 'purple',
  SERVIÇOS: 'cyan',
  VAREJO: 'orange',
  PRIMÁRIO: 'green',
};

const BadgeTipo = ({ t }) => (
  <Tag color={t === 'IMP' || t === 'Importação' ? 'blue' : 'green'} style={{ fontSize: 11 }}>
    {t === 'IMP' || t === 'Importação' ? 'Importação' : 'Exportação'}
  </Tag>
);

// ─── KPI Card ────────────────────────────────────────────────────────────────
const KpiCard = ({ title, value, icon, gradient, subtitle }) => (
  <Card
    style={{ borderRadius: 10, background: gradient, border: 'none', height: '100%' }}
    bodyStyle={{ padding: '18px 20px' }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12, marginBottom: 4 }}>{title}</div>
        <div style={{ color: '#fff', fontSize: 20, fontWeight: 700, lineHeight: 1.2 }}>{value}</div>
        {subtitle && <div style={{ color: 'rgba(255,255,255,0.65)', fontSize: 11, marginTop: 4 }}>{subtitle}</div>}
      </div>
      <div style={{ fontSize: 32, color: 'rgba(255,255,255,0.25)' }}>{icon}</div>
    </div>
  </Card>
);

// ─── Hierarquia CNAE Badge ────────────────────────────────────────────────────
const CnaeBreadcrumb = ({ cnae }) => {
  if (!cnae) return null;
  const partes = [
    cnae.setor && { label: cnae.setor, color: SETOR_COLORS[cnae.setor] || 'default' },
    cnae.segmento && { label: cnae.segmento, color: 'geekblue' },
    cnae.ramo && { label: cnae.ramo, color: 'volcano' },
    cnae.categoria && { label: cnae.categoria, color: 'gold' },
  ].filter(Boolean);
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
      {partes.map((p, i) => (
        <Tag key={i} color={p.color} style={{ margin: 0 }}>{p.label}</Tag>
      ))}
    </div>
  );
};

// ─── Tabela de Estabelecimentos ───────────────────────────────────────────────
const colsEstabelecimentos = [
  {
    title: 'UF / Município',
    key: 'local',
    width: 160,
    render: (_, r) => (
      <div>
        <Tag color="default">{r.uf || '—'}</Tag>
        <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{r.municipio || '—'}</div>
      </div>
    ),
  },
  {
    title: 'CNAE',
    key: 'cnae',
    width: 100,
    render: (_, r) => <Text code style={{ fontSize: 11 }}>{r.cnae_fiscal || '—'}</Text>,
  },
  {
    title: 'Classificação',
    key: 'classif',
    render: (_, r) => <CnaeBreadcrumb cnae={r.cnae_info} />,
  },
  {
    title: 'Contato',
    key: 'contato',
    width: 200,
    render: (_, r) => (
      <div style={{ fontSize: 12 }}>
        {r.email && (
          <div style={{ marginBottom: 2 }}>
            <Text copyable={{ text: r.email }} style={{ fontSize: 11 }}>{r.email}</Text>
          </div>
        )}
        {r.telefone1 && (
          <div>
            <PhoneOutlined style={{ marginRight: 4, color: '#52c41a' }} />
            <Text style={{ fontSize: 11 }}>{r.telefone1}</Text>
          </div>
        )}
        {!r.email && !r.telefone1 && <Text type="secondary" style={{ fontSize: 11 }}>Sem contato cadastrado</Text>}
      </div>
    ),
  },
  {
    title: 'Situação',
    dataIndex: 'situacao_cadastral',
    key: 'situacao',
    width: 100,
    render: (v) => (
      <Badge
        status={v === 'ATIVA' ? 'success' : v === 'BAIXADA' ? 'error' : 'warning'}
        text={<span style={{ fontSize: 11 }}>{v || '—'}</span>}
      />
    ),
  },
];

// ─── Tabela NCMs ──────────────────────────────────────────────────────────────
const colsNcm = [
  { title: 'NCM', dataIndex: 'ncm', key: 'ncm', width: 100, render: (v) => <Text code>{v}</Text> },
  { title: 'Descrição', dataIndex: 'descricao', key: 'desc', ellipsis: true },
  { title: 'Tipo', dataIndex: 'tipo', key: 'tipo', width: 110, render: (v) => <BadgeTipo t={v} /> },
  { title: 'Valor USD', dataIndex: 'valor_usd', key: 'fob', width: 130, render: fmtUsd, sorter: (a, b) => (a.valor_usd || 0) - (b.valor_usd || 0) },
  { title: 'Peso KG', dataIndex: 'peso_kg', key: 'peso', width: 110, render: fmtNum },
];

// ─── Componente principal ─────────────────────────────────────────────────────
export default function EmpresaContatos() {
  const [query, setQuery] = useState('');
  const [options, setOptions] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dados, setDados] = useState(null);
  const [activeTab, setActiveTab] = useState('perfil');

  // Autocomplete: busca por nome ou CNPJ
  const buscarSugestoes = useCallback(async (q) => {
    const termo = (q || '').trim();
    setQuery(termo);
    if (termo.length < 2) { setOptions([]); return; }
    setLoadingSearch(true);
    try {
      // Tenta autocomplete unificado (nome + CNPJ)
      const res = await api.get('/api/contatos/autocomplete', { params: { q: termo, limit: 20 } });
      const items = res?.data?.items || [];
      setOptions(
        items.map((e) => ({
          value: e.cnpj || e.value,
          label: (
            <div style={{ lineHeight: 1.4 }}>
              <div style={{ fontWeight: 600, fontSize: 13 }}>{e.razao_social || e.nome}</div>
              <div style={{ fontSize: 11, color: '#888' }}>
                {e.cnpj ? fmtCnpj(e.cnpj) : ''}{e.uf ? ` · ${e.uf}` : ''}{e.cnae_descricao ? ` · ${e.cnae_descricao}` : ''}
              </div>
            </div>
          ),
          cnpj: e.cnpj,
          nome: e.razao_social || e.nome,
        }))
      );
    } catch {
      setOptions([]);
    } finally {
      setLoadingSearch(false);
    }
  }, []);

  // Carregar perfil completo da empresa
  const carregarEmpresa = useCallback(async (cnpj) => {
    if (!cnpj) return;
    setLoading(true);
    setDados(null);
    setActiveTab('perfil');
    try {
      const res = await api.get(`/api/contatos/empresa/${encodeURIComponent(cnpj)}`);
      setDados(res.data);
    } catch (e) {
      message.error(e?.response?.data?.detail || 'Empresa não encontrada ou erro ao carregar dados.');
    } finally {
      setLoading(false);
    }
  }, []);

  const onSelect = (_, opt) => {
    const cnpj = opt.cnpj || opt.value;
    setQuery(opt.nome || cnpj);
    carregarEmpresa(cnpj);
  };

  const onSearch = () => {
    const q = query.trim().replace(/\D/g, '');
    if (q.length === 14) {
      carregarEmpresa(q);
    } else {
      message.info('Para busca direta, informe o CNPJ completo (14 dígitos) ou selecione uma sugestão.');
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────────────
  const kpis = dados?.kpis || {};
  const perfil = dados?.perfil || {};
  const estabelecimentos = dados?.estabelecimentos || [];
  const ncms = dados?.ncms || [];
  const comexPorAno = dados?.comex_por_ano || [];
  const cnaeInfo = dados?.cnae_info || null;
  const totalEstab = estabelecimentos.length;
  const ufsUnicas = [...new Set(estabelecimentos.map((e) => e.uf).filter(Boolean))];

  // Dados para gráfico comex por ano
  const comexChartData = comexPorAno.map((r) => ({
    ano: String(r.ano),
    Importação: Number(r.valor_importacao) || 0,
    Exportação: Number(r.valor_exportacao) || 0,
  }));

  const tabItems = [
    {
      key: 'perfil',
      label: <span><BankOutlined /> Perfil</span>,
      children: (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={16}>
            <Card title="Dados Cadastrais" size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={{ xs: 1, sm: 2 }} size="small">
                <Descriptions.Item label="Razão Social">
                  <strong>{perfil.razao_social || '—'}</strong>
                </Descriptions.Item>
                <Descriptions.Item label="CNPJ">
                  <Text copyable>{perfil.cnpj ? fmtCnpj(perfil.cnpj) : '—'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Natureza Jurídica">{perfil.natureza_juridica || '—'}</Descriptions.Item>
                <Descriptions.Item label="Porte">{perfil.porte || '—'}</Descriptions.Item>
                <Descriptions.Item label="UF Sede">{perfil.uf_sede || '—'}</Descriptions.Item>
                <Descriptions.Item label="Município Sede">{perfil.municipio_sede || '—'}</Descriptions.Item>
                <Descriptions.Item label="Situação">
                  <Badge
                    status={perfil.situacao === 'ATIVA' ? 'success' : 'error'}
                    text={perfil.situacao || '—'}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Data Abertura">{perfil.data_abertura || '—'}</Descriptions.Item>
              </Descriptions>
            </Card>

            <Card
              title={<span><TagsOutlined /> CNAE Principal</span>}
              size="small"
              extra={cnaeInfo && <Tag color={SETOR_COLORS[cnaeInfo.setor] || 'default'}>{cnaeInfo.setor}</Tag>}
            >
              <div style={{ marginBottom: 8 }}>
                <Text code style={{ fontSize: 13 }}>{perfil.cnae_fiscal || '—'}</Text>
                <Text style={{ marginLeft: 12 }}>{perfil.cnae_descricao || cnaeInfo?.descricao || '—'}</Text>
              </div>
              <CnaeBreadcrumb cnae={cnaeInfo} />
              {cnaeInfo?.produto && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>Produto: </Text>
                  <Tag color="lime">{cnaeInfo.produto}</Tag>
                </div>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card title="Presença Nacional" size="small">
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary">Estados com estabelecimentos:</Text>
                <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {ufsUnicas.length > 0
                    ? ufsUnicas.map((uf) => <Tag key={uf} color="geekblue">{uf}</Tag>)
                    : <Text type="secondary">—</Text>}
                </div>
              </div>
              <Divider style={{ margin: '12px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: 11, color: '#888' }}>Estabelecimentos</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: '#667eea' }}>{totalEstab}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#888' }}>Estados</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: '#4facfe' }}>{ufsUnicas.length}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#888' }}>NCMs ativos</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: '#f093fb' }}>{kpis.num_ncms ?? '—'}</div>
                </div>
              </div>
            </Card>

            {cnaeInfo && (
              <Card title="Segmento de Mercado" size="small" style={{ marginTop: 16 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {[
                    { label: 'Setor', value: cnaeInfo.setor, color: SETOR_COLORS[cnaeInfo.setor] },
                    { label: 'Segmento', value: cnaeInfo.segmento, color: 'geekblue' },
                    { label: 'Ramo', value: cnaeInfo.ramo, color: 'volcano' },
                    { label: 'Categoria', value: cnaeInfo.categoria, color: 'gold' },
                  ].filter((r) => r.value).map((r) => (
                    <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Text type="secondary" style={{ fontSize: 11, width: 70, flexShrink: 0 }}>{r.label}:</Text>
                      <Tag color={r.color} style={{ margin: 0 }}>{r.value}</Tag>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </Col>
        </Row>
      ),
    },
    {
      key: 'estabelecimentos',
      label: <span><ShopOutlined /> Estabelecimentos <Tag>{totalEstab}</Tag></span>,
      children: (
        <Card size="small">
          {estabelecimentos.length === 0 ? (
            <Empty description="Nenhum estabelecimento encontrado" />
          ) : (
            <Table
              rowKey={(r, i) => `${r.cnpj_completo || i}`}
              columns={colsEstabelecimentos}
              dataSource={estabelecimentos}
              pagination={{ pageSize: 10, showSizeChanger: false }}
              size="small"
              scroll={{ x: 700 }}
            />
          )}
        </Card>
      ),
    },
    {
      key: 'comex',
      label: <span><ExportOutlined /> Comex</span>,
      children: (
        <Row gutter={[16, 16]}>
          <Col xs={24}>
            <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="Total Importado"
                  value={fmtUsd(kpis.valor_importacao_usd)}
                  icon={<ImportOutlined />}
                  gradient="linear-gradient(135deg,#667eea,#764ba2)"
                  subtitle="Valor FOB USD"
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="Total Exportado"
                  value={fmtUsd(kpis.valor_exportacao_usd)}
                  icon={<ExportOutlined />}
                  gradient="linear-gradient(135deg,#4facfe,#00f2fe)"
                  subtitle="Valor FOB USD"
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="Saldo Comercial"
                  value={fmtUsd((kpis.valor_exportacao_usd || 0) - (kpis.valor_importacao_usd || 0))}
                  icon={<ApartmentOutlined />}
                  gradient={
                    (kpis.valor_exportacao_usd || 0) >= (kpis.valor_importacao_usd || 0)
                      ? 'linear-gradient(135deg,#43e97b,#38f9d7)'
                      : 'linear-gradient(135deg,#f093fb,#f5576c)'
                  }
                  subtitle="Exportação − Importação"
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="Países Parceiros"
                  value={kpis.num_paises ?? '—'}
                  icon={<EnvironmentOutlined />}
                  gradient="linear-gradient(135deg,#fa709a,#fee140)"
                  subtitle="Destinos/origens distintos"
                />
              </Col>
            </Row>
          </Col>

          {comexChartData.length > 0 && (
            <Col xs={24} lg={14}>
              <Card title="Evolução Anual — Importação vs Exportação (USD FOB)" size="small">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={comexChartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="ano" tick={{ fontSize: 12 }} />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) =>
                        v >= 1e9 ? `US$${(v / 1e9).toFixed(1)}B`
                        : v >= 1e6 ? `US$${(v / 1e6).toFixed(1)}M`
                        : `US$${(v / 1e3).toFixed(0)}K`
                      }
                    />
                    <RTooltip
                      formatter={(v, name) => [fmtUsd(v), name]}
                      contentStyle={{ fontSize: 12 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Importação" fill="#667eea" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Exportação" fill="#43e97b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}

          <Col xs={24} lg={comexChartData.length > 0 ? 10 : 24}>
            <Card title="Operações por NCM" size="small">
              <Table
                rowKey={(r, i) => `${r.ncm}-${i}`}
                columns={colsNcm}
                dataSource={ncms}
                pagination={{ pageSize: 8, showSizeChanger: false }}
                size="small"
                scroll={{ x: 500 }}
              />
            </Card>
          </Col>
        </Row>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* ── Cabeçalho ── */}
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <BankOutlined style={{ marginRight: 10, color: '#667eea' }} />
          Empresas & Contatos
        </Title>
        <Text type="secondary">
          Busque por razão social ou CNPJ — visualize perfil, estabelecimentos, contatos, CNAE e desempenho no comércio exterior.
        </Text>
      </div>

      {/* ── Barra de busca ── */}
      <Card style={{ marginBottom: 20, borderRadius: 10 }} bodyStyle={{ padding: '16px 20px' }}>
        <Row gutter={12} align="middle">
          <Col flex="auto">
            <AutoComplete
              style={{ width: '100%' }}
              options={options}
              onSearch={buscarSugestoes}
              onSelect={onSelect}
              value={query}
              notFoundContent={
                loadingSearch ? <Spin size="small" /> :
                query.length >= 2 ? 'Nenhuma empresa encontrada' :
                'Digite ao menos 2 caracteres ou o CNPJ completo'
              }
            >
              <Input
                size="large"
                placeholder="Razão social, nome fantasia ou CNPJ (ex.: Vale, Embraer, 33.000.167/0001-01)"
                prefix={<SearchOutlined style={{ color: '#667eea' }} />}
                onPressEnter={onSearch}
                allowClear
              />
            </AutoComplete>
          </Col>
          <Col>
            <Button
              size="large"
              type="primary"
              icon={<SearchOutlined />}
              onClick={onSearch}
              style={{ background: '#667eea', borderColor: '#667eea' }}
            >
              Buscar
            </Button>
          </Col>
        </Row>
        <div style={{ marginTop: 10, fontSize: 12, color: '#aaa' }}>
          <Text type="secondary">
            Fonte: Receita Federal (Estabelecimentos) + BigQuery (empresas_base + comex UF×NCM) + tabela CNAE proprietária.
          </Text>
        </div>
      </Card>

      {/* ── Estado de carregamento ── */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
          <div style={{ marginTop: 12, color: '#888' }}>Carregando dados da empresa…</div>
        </div>
      )}

      {/* ── Resultado ── */}
      {dados && !loading && (
        <>
          {/* Alerta de fonte */}
          {dados.aviso && (
            <Alert
              type={dados.aviso_tipo || 'info'}
              showIcon
              message={dados.aviso}
              style={{ marginBottom: 16 }}
              closable
            />
          )}

          {/* Cabeçalho da empresa */}
          <Card
            style={{ marginBottom: 16, borderRadius: 10, borderLeft: '4px solid #667eea' }}
            bodyStyle={{ padding: '16px 20px' }}
          >
            <Row align="middle" gutter={16}>
              <Col flex="auto">
                <Title level={4} style={{ margin: 0 }}>
                  {perfil.razao_social || '—'}
                </Title>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  CNPJ: {perfil.cnpj ? fmtCnpj(perfil.cnpj) : '—'}
                  {perfil.uf_sede ? ` · ${perfil.uf_sede}` : ''}
                  {perfil.municipio_sede ? ` · ${perfil.municipio_sede}` : ''}
                </Text>
              </Col>
              <Col>
                {cnaeInfo?.setor && (
                  <Tag color={SETOR_COLORS[cnaeInfo.setor] || 'default'} style={{ fontSize: 13, padding: '4px 10px' }}>
                    {cnaeInfo.setor}
                  </Tag>
                )}
                <Badge
                  status={perfil.situacao === 'ATIVA' ? 'success' : 'error'}
                  text={
                    <span style={{ fontSize: 13, fontWeight: 600, color: perfil.situacao === 'ATIVA' ? '#52c41a' : '#ff4d4f' }}>
                      {perfil.situacao || '—'}
                    </span>
                  }
                />
              </Col>
            </Row>
          </Card>

          {/* Tabs com conteúdo */}
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            tabBarStyle={{ marginBottom: 0 }}
          />
        </>
      )}

      {/* ── Estado vazio inicial ── */}
      {!dados && !loading && (
        <Card style={{ borderRadius: 10, textAlign: 'center', padding: '40px 20px' }}>
          <BankOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
          <Title level={5} type="secondary">Pesquise uma empresa para começar</Title>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            Digite a razão social ou CNPJ na barra acima. Os resultados incluem perfil cadastral,
            contatos por estabelecimento, classificação CNAE e dados de importação/exportação.
          </Text>
          <Divider />
          <Row gutter={24} justify="center">
            {[
              { icon: <ShopOutlined />, texto: 'Todos os estabelecimentos ativos com contatos' },
              { icon: <TagsOutlined />, texto: 'Classificação CNAE: Setor → Segmento → Ramo → Categoria' },
              { icon: <ExportOutlined />, texto: 'Comex: importações e exportações por NCM e ano' },
            ].map((item, i) => (
              <Col key={i} xs={24} sm={8} style={{ textAlign: 'center', padding: '12px 16px' }}>
                <div style={{ fontSize: 28, color: COLORS[i], marginBottom: 8 }}>{item.icon}</div>
                <Text type="secondary" style={{ fontSize: 12 }}>{item.texto}</Text>
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </div>
  );
}
