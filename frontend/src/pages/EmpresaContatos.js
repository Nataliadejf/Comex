import React, { useState, useCallback, useRef } from 'react';
import {
  Alert, AutoComplete, Badge, Button, Card, Col, Descriptions, Divider,
  Empty, Input, Row, Spin, Table, Tag, Tabs, Tooltip, Typography, message,
  Statistic,
} from 'antd';
import {
  ApartmentOutlined,
  BankOutlined,
  BulbOutlined,
  EnvironmentOutlined,
  ExportOutlined,
  GlobalOutlined,
  ImportOutlined,
  LinkedinOutlined,
  MailOutlined,
  PhoneOutlined,
  SearchOutlined,
  ShopOutlined,
  TagsOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend,
  ResponsiveContainer, Tooltip as RTooltip, XAxis, YAxis,
} from 'recharts';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;

const COLORS = ['#667eea', '#4facfe', '#f093fb', '#43e97b', '#fa709a', '#fee140'];

const SETOR_COLORS = {
  INDÚSTRIA: 'blue',
  DISTRIBUIDOR: 'purple',
  SERVIÇOS: 'cyan',
  VAREJO: 'orange',
  PRIMÁRIO: 'green',
};

// ─── Formatação ───────────────────────────────────────────────────────────────
const fmtUsd = (v) =>
  v == null ? '—'
  : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v);

const fmtNum = (v) =>
  v == null ? '—'
  : new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(v);

const fmtCnpj = (v) => {
  const s = String(v || '').replace(/\D/g, '').padStart(14, '0');
  return `${s.slice(0, 2)}.${s.slice(2, 5)}.${s.slice(5, 8)}/${s.slice(8, 12)}-${s.slice(12, 14)}`;
};

const fmtRange = (v) => {
  if (!v) return '—';
  if (v >= 1e9) return `US$ ${(v / 1e9).toFixed(1)} Bi`;
  if (v >= 1e6) return `US$ ${(v / 1e6).toFixed(1)} Mi`;
  if (v >= 1e3) return `US$ ${(v / 1e3).toFixed(0)} Mil`;
  return fmtUsd(v);
};

// ─── Componentes reutilizáveis ────────────────────────────────────────────────

const KpiCard = ({ title, value, icon, gradient, subtitle, small }) => (
  <Card
    style={{ borderRadius: 10, background: gradient, border: 'none', height: '100%' }}
    bodyStyle={{ padding: small ? '12px 16px' : '18px 20px' }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: small ? 11 : 12, marginBottom: 4 }}>{title}</div>
        <div style={{ color: '#fff', fontSize: small ? 16 : 20, fontWeight: 700, lineHeight: 1.2 }}>{value}</div>
        {subtitle && <div style={{ color: 'rgba(255,255,255,0.65)', fontSize: 11, marginTop: 4 }}>{subtitle}</div>}
      </div>
      <div style={{ fontSize: small ? 24 : 32, color: 'rgba(255,255,255,0.25)' }}>{icon}</div>
    </div>
  </Card>
);

const CnaeBreadcrumb = ({ cnae }) => {
  if (!cnae) return null;
  const partes = [
    cnae.setor && { label: cnae.setor, color: SETOR_COLORS[cnae.setor] || 'default' },
    cnae.segmento && { label: cnae.segmento, color: 'geekblue' },
    cnae.ramo && { label: cnae.ramo, color: 'volcano' },
    cnae.categoria && { label: cnae.categoria, color: 'gold' },
  ].filter(Boolean);
  if (!partes.length) return null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
      {partes.map((p, i) => <Tag key={i} color={p.color} style={{ margin: 0 }}>{p.label}</Tag>)}
    </div>
  );
};

const ContatoCard = ({ contato }) => {
  if (!contato) return null;
  const temContato = contato.telefone1 || contato.telefone2 || contato.email;
  return (
    <Card
      title={<span><PhoneOutlined style={{ color: '#52c41a', marginRight: 8 }} />Contato Receita Federal</span>}
      size="small"
      style={{ marginTop: 16, borderLeft: '4px solid #52c41a' }}
    >
      <Descriptions column={1} size="small">
        {contato.cnpj_completo && (
          <Descriptions.Item label="CNPJ Matriz">
            <Text copyable={{ text: contato.cnpj_completo }}>{fmtCnpj(contato.cnpj_completo)}</Text>
          </Descriptions.Item>
        )}
        {contato.uf && (
          <Descriptions.Item label="Localização">
            <Tag color="geekblue">{contato.uf}</Tag>
            {contato.municipio && <span style={{ marginLeft: 4 }}>{contato.municipio}</span>}
          </Descriptions.Item>
        )}
        {contato.telefone1 && (
          <Descriptions.Item label="Telefone 1">
            <PhoneOutlined style={{ color: '#52c41a', marginRight: 6 }} />
            <Text copyable={{ text: contato.telefone1 }}>{contato.telefone1}</Text>
          </Descriptions.Item>
        )}
        {contato.telefone2 && (
          <Descriptions.Item label="Telefone 2">
            <PhoneOutlined style={{ color: '#52c41a', marginRight: 6 }} />
            <Text copyable={{ text: contato.telefone2 }}>{contato.telefone2}</Text>
          </Descriptions.Item>
        )}
        {contato.email && (
          <Descriptions.Item label="E-mail">
            <MailOutlined style={{ color: '#1890ff', marginRight: 6 }} />
            <Text copyable={{ text: contato.email }}>{contato.email}</Text>
          </Descriptions.Item>
        )}
        {contato.situacao_cadastral && (
          <Descriptions.Item label="Situação">
            <Badge
              status={contato.situacao_cadastral === 'ATIVA' ? 'success' : 'error'}
              text={contato.situacao_cadastral}
            />
          </Descriptions.Item>
        )}
      </Descriptions>
      {!temContato && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          Sem telefone ou e-mail cadastrado na Receita Federal para esta empresa.
        </Text>
      )}
    </Card>
  );
};

// ─── Tabela de Estabelecimentos ───────────────────────────────────────────────
const colsEstabelecimentos = [
  {
    title: 'UF / Município',
    key: 'local',
    width: 170,
    render: (_, r) => (
      <div>
        <Tag color="geekblue">{r.uf || '—'}</Tag>
        <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{r.municipio || '—'}</div>
      </div>
    ),
  },
  {
    title: 'CNPJ',
    dataIndex: 'cnpj_completo',
    key: 'cnpj',
    width: 160,
    render: (v) => v ? <Text copyable={{ text: v }} style={{ fontSize: 11 }}>{fmtCnpj(v)}</Text> : '—',
  },
  {
    title: 'CNAE',
    key: 'cnae',
    width: 90,
    render: (_, r) => <Text code style={{ fontSize: 11 }}>{r.cnae_fiscal || '—'}</Text>,
  },
  {
    title: 'Setor / Segmento',
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
            <MailOutlined style={{ color: '#1890ff', marginRight: 4 }} />
            <Text copyable={{ text: r.email }} style={{ fontSize: 11 }}>{r.email}</Text>
          </div>
        )}
        {r.telefone1 && (
          <div>
            <PhoneOutlined style={{ marginRight: 4, color: '#52c41a' }} />
            <Text copyable={{ text: r.telefone1 }} style={{ fontSize: 11 }}>{r.telefone1}</Text>
          </div>
        )}
        {r.telefone2 && r.telefone2 !== r.telefone1 && (
          <div>
            <PhoneOutlined style={{ marginRight: 4, color: '#52c41a' }} />
            <Text style={{ fontSize: 11 }}>{r.telefone2}</Text>
          </div>
        )}
        {!r.email && !r.telefone1 && (
          <Text type="secondary" style={{ fontSize: 11 }}>Sem contato</Text>
        )}
      </div>
    ),
  },
  {
    title: 'Situação',
    dataIndex: 'situacao_cadastral',
    key: 'situacao',
    width: 90,
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
  { title: 'Descrição', dataIndex: 'descricao', key: 'desc', ellipsis: true, render: (v) => v || <Text type="secondary">—</Text> },
  {
    title: 'Tipo', dataIndex: 'tipo', key: 'tipo', width: 110,
    render: (v) => {
      const isImp = ['IMP', 'IMPORTAÇÃO', 'IMPORTACAO'].includes(String(v || '').toUpperCase());
      return <Tag color={isImp ? 'blue' : 'green'}>{isImp ? 'Importação' : 'Exportação'}</Tag>;
    }
  },
  {
    title: 'Valor USD', dataIndex: 'valor_usd', key: 'fob', width: 130,
    render: fmtUsd,
    sorter: (a, b) => (a.valor_usd || 0) - (b.valor_usd || 0),
    defaultSortOrder: 'descend',
  },
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
  const [sugestao, setSugestao] = useState(null);
  const [loadingSugestao, setLoadingSugestao] = useState(false);
  const [selectedCnpj, setSelectedCnpj] = useState(null);

  const debounceRef = useRef(null);
  const reqIdRef = useRef(0);

  const buscarSugestoes = useCallback((q) => {
    // Mantém o texto CRU (sem trim) para não apagar o espaço enquanto digita dois nomes.
    const raw = q || '';
    setQuery(raw);
    const termo = raw.trim();
    if (termo.length < 2) {
      setOptions([]);
      setLoadingSearch(false);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      return;
    }
    setLoadingSearch(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const meuId = ++reqIdRef.current;
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await api.get('/api/contatos/autocomplete', { params: { q: termo, limit: 20 } });
        if (meuId !== reqIdRef.current) return; // ignora resposta obsoleta
        const items = res?.data?.items || [];
        setOptions(
          items.map((e) => ({
            value: e.cnpj || e.value,
            label: (
              <div style={{ lineHeight: 1.4 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{e.razao_social || e.nome}</div>
                <div style={{ fontSize: 11, color: '#888' }}>
                  {e.cnpj ? fmtCnpj(e.cnpj) : ''}
                  {e.uf ? ` · ${e.uf}` : ''}
                  {e.setor ? ` · ${e.setor}` : ''}
                  {e.cnae_descricao ? ` · ${e.cnae_descricao}` : ''}
                </div>
              </div>
            ),
            cnpj: e.cnpj,
            nome: e.razao_social || e.nome,
          }))
        );
      } catch {
        if (meuId === reqIdRef.current) setOptions([]);
      } finally {
        if (meuId === reqIdRef.current) setLoadingSearch(false);
      }
    }, 350);
  }, []);

  const carregarEmpresa = useCallback(async (cnpj) => {
    if (!cnpj) return;
    setLoading(true);
    setDados(null);
    setSugestao(null);
    setActiveTab('perfil');
    setSelectedCnpj(cnpj);
    try {
      const res = await api.get(`/api/contatos/empresa/${encodeURIComponent(cnpj)}`);
      setDados(res.data);
    } catch (e) {
      message.error(e?.response?.data?.detail || 'Empresa não encontrada ou erro ao carregar dados.');
    } finally {
      setLoading(false);
    }
  }, []);

  const carregarSugestao = useCallback(async () => {
    if (!selectedCnpj) return;
    setLoadingSugestao(true);
    try {
      const res = await api.get(`/api/contatos/empresa/${encodeURIComponent(selectedCnpj)}/sugestao`);
      setSugestao(res.data);
    } catch (e) {
      message.error('Erro ao carregar sugestão comex.');
    } finally {
      setLoadingSugestao(false);
    }
  }, [selectedCnpj]);

  const onTabChange = (key) => {
    setActiveTab(key);
    if (key === 'sugestao' && !sugestao && !loadingSugestao) carregarSugestao();
  };

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

  // ─── Dados extraídos ─────────────────────────────────────────────────────────
  const kpis = dados?.kpis || {};
  const perfil = dados?.perfil || {};
  const estabelecimentos = dados?.estabelecimentos || [];
  const ncms = dados?.ncms || [];
  const comexPorAno = dados?.comex_por_ano || [];
  const cnaeInfo = dados?.cnae_info || null;
  const contato_rf = dados?.contato_rf || null;
  const totalEstab = estabelecimentos.length;
  const ufsUnicas = kpis.ufs_atuacao || [...new Set(estabelecimentos.map((e) => e.uf).filter(Boolean))];
  const temComex = dados?.tem_comex;

  const comexChartData = comexPorAno.map((r) => ({
    ano: String(r.ano),
    Importação: Number(r.valor_importacao) || 0,
    Exportação: Number(r.valor_exportacao) || 0,
  }));

  // ─── Abas ────────────────────────────────────────────────────────────────────
  const tabItems = dados ? [
    {
      key: 'perfil',
      label: <span><BankOutlined /> Perfil</span>,
      children: (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={16}>
            <Card title={<span><UserOutlined /> Dados Cadastrais</span>} size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={{ xs: 1, sm: 2 }} size="small">
                <Descriptions.Item label="Razão Social" span={2}>
                  <strong style={{ fontSize: 14 }}>{perfil.razao_social || '—'}</strong>
                </Descriptions.Item>
                <Descriptions.Item label="CNPJ">
                  <Text copyable>{perfil.cnpj ? fmtCnpj(perfil.cnpj) : '—'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Porte">{perfil.porte || '—'}</Descriptions.Item>
                <Descriptions.Item label="Natureza Jurídica">{perfil.natureza_juridica || '—'}</Descriptions.Item>
                <Descriptions.Item label="Data Abertura">{perfil.data_abertura || '—'}</Descriptions.Item>
                <Descriptions.Item label="UF Sede">
                  {perfil.uf_sede ? <Tag color="geekblue">{perfil.uf_sede}</Tag> : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Município Sede">{perfil.municipio_sede || '—'}</Descriptions.Item>
                <Descriptions.Item label="Situação">
                  <Badge
                    status={perfil.situacao === 'ATIVA' ? 'success' : perfil.situacao ? 'error' : 'default'}
                    text={perfil.situacao || '—'}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Estabelecimentos">{totalEstab || '—'}</Descriptions.Item>
              </Descriptions>
            </Card>

            <Card
              title={<span><TagsOutlined /> Classificação CNAE</span>}
              size="small"
              extra={cnaeInfo?.setor && <Tag color={SETOR_COLORS[cnaeInfo.setor] || 'default'}>{cnaeInfo.setor}</Tag>}
            >
              <div style={{ marginBottom: 8 }}>
                <Text code style={{ fontSize: 13 }}>{perfil.cnae_fiscal || '—'}</Text>
                <Text style={{ marginLeft: 12, color: '#555' }}>{perfil.cnae_descricao || cnaeInfo?.descricao || '—'}</Text>
              </div>
              <CnaeBreadcrumb cnae={cnaeInfo} />
              {cnaeInfo?.produto && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>Produto/Subproduto: </Text>
                  <Tag color="lime">{cnaeInfo.produto}</Tag>
                </div>
              )}
              {cnaeInfo && (
                <div style={{ marginTop: 14 }}>
                  <Divider style={{ margin: '8px 0' }} />
                  <Row gutter={8}>
                    {[
                      { label: 'Setor', value: cnaeInfo.setor, color: SETOR_COLORS[cnaeInfo.setor] },
                      { label: 'Segmento', value: cnaeInfo.segmento, color: 'geekblue' },
                      { label: 'Ramo', value: cnaeInfo.ramo, color: 'volcano' },
                      { label: 'Categoria', value: cnaeInfo.categoria, color: 'gold' },
                    ].filter((r) => r.value).map((r) => (
                      <Col key={r.label} xs={24} sm={12} style={{ marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Text type="secondary" style={{ fontSize: 11, width: 70, flexShrink: 0 }}>{r.label}:</Text>
                          <Tag color={r.color} style={{ margin: 0 }}>{r.value}</Tag>
                        </div>
                      </Col>
                    ))}
                  </Row>
                </div>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card title={<span><EnvironmentOutlined /> Presença Nacional</span>} size="small">
              <Row gutter={8} style={{ marginBottom: 12 }}>
                <Col span={8}>
                  <Statistic title="Unidades" value={totalEstab || 0} valueStyle={{ fontSize: 20, color: '#667eea' }} />
                </Col>
                <Col span={8}>
                  <Statistic title="Estados" value={ufsUnicas.length} valueStyle={{ fontSize: 20, color: '#4facfe' }} />
                </Col>
                <Col span={8}>
                  <Statistic title="NCMs" value={kpis.num_ncms ?? '—'} valueStyle={{ fontSize: 20, color: '#f093fb' }} />
                </Col>
              </Row>
              <Divider style={{ margin: '8px 0' }} />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {ufsUnicas.length > 0
                  ? ufsUnicas.map((uf) => <Tag key={uf} color="geekblue">{uf}</Tag>)
                  : <Text type="secondary" style={{ fontSize: 12 }}>Nenhuma UF identificada</Text>}
              </div>
            </Card>

            <ContatoCard contato={contato_rf} />

            {dados?.aviso && (
              <Alert
                message={dados.aviso}
                type={dados.aviso_tipo || 'info'}
                showIcon
                style={{ marginTop: 16 }}
                action={
                  !temComex && (
                    <Button size="small" onClick={() => onTabChange('sugestao')}>
                      Ver Sugestão
                    </Button>
                  )
                }
              />
            )}
          </Col>
        </Row>
      ),
    },
    {
      key: 'estabelecimentos',
      label: (
        <span>
          <ShopOutlined /> Estabelecimentos
          {totalEstab > 0 && <Tag style={{ marginLeft: 4 }}>{totalEstab}</Tag>}
        </span>
      ),
      children: (
        <Card size="small">
          {estabelecimentos.length === 0 ? (
            <Empty description="Nenhum estabelecimento encontrado" />
          ) : (
            <>
              <div style={{ marginBottom: 10, fontSize: 12, color: '#666' }}>
                Dados de contato extraídos do cadastro da Receita Federal.
                Telefone e e-mail são os informados no momento do cadastro/última atualização.
              </div>
              <Table
                rowKey={(r, i) => `${r.cnpj_completo || i}`}
                columns={colsEstabelecimentos}
                dataSource={estabelecimentos}
                pagination={{ pageSize: 15, showSizeChanger: true, pageSizeOptions: ['10', '15', '25', '50'] }}
                size="small"
                scroll={{ x: 800 }}
              />
            </>
          )}
        </Card>
      ),
    },
    {
      key: 'comex',
      label: <span><ExportOutlined /> Comex</span>,
      children: (
        <Row gutter={[16, 16]}>
          {!temComex && (
            <Col xs={24}>
              <Alert
                message="Sem histórico de comércio exterior"
                description={
                  dados?.aviso ||
                  'Esta empresa não possui operações registradas na base disponível. ' +
                  'Consulte a aba "Sugestão Comex" para ver o potencial estimado com base no segmento.'
                }
                type="warning"
                showIcon
                action={
                  <Button size="small" onClick={() => onTabChange('sugestao')}>
                    Ver Sugestão
                  </Button>
                }
              />
            </Col>
          )}

          {temComex && (
            <>
              <Col xs={24}>
                <Row gutter={[12, 12]}>
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
                      title="Saldo"
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
                      title="NCMs Distintos"
                      value={kpis.num_ncms ?? '—'}
                      icon={<TagsOutlined />}
                      gradient="linear-gradient(135deg,#fa709a,#fee140)"
                      subtitle="Produtos negociados"
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
                        <RTooltip formatter={(v, name) => [fmtUsd(v), name]} contentStyle={{ fontSize: 12 }} />
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
            </>
          )}
        </Row>
      ),
    },
    {
      key: 'sugestao',
      label: <span><BulbOutlined /> Sugestão Comex</span>,
      children: (
        <div>
          {loadingSugestao ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <Spin tip="Calculando sugestão com base no segmento..." />
            </div>
          ) : !sugestao ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Button type="primary" icon={<BulbOutlined />} onClick={carregarSugestao}>
                Calcular Sugestão de Potencial Comex
              </Button>
              <Paragraph type="secondary" style={{ marginTop: 12, fontSize: 12 }}>
                Baseado em empresas do mesmo CNAE/segmento que já operam no comércio exterior.
                Similar à análise de viabilidade da Logcomex.
              </Paragraph>
            </div>
          ) : !sugestao.tem_sugestao ? (
            <Alert
              message="Sugestão não disponível"
              description={sugestao.motivo || sugestao.metodologia}
              type="info"
              showIcon
            />
          ) : (
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <Alert
                  message="Análise de Potencial — Dados Estimados"
                  description={sugestao.metodologia}
                  type="info"
                  showIcon
                  style={{ marginBottom: 8 }}
                />
              </Col>

              {/* CNAE da empresa */}
              {sugestao.cnae_info && (
                <Col xs={24}>
                  <Card size="small" title="Segmento de Referência">
                    <CnaeBreadcrumb cnae={sugestao.cnae_info} />
                    <Text style={{ marginLeft: 0, marginTop: 6, display: 'block', fontSize: 12, color: '#888' }}>
                      CNAE {sugestao.cnae} · {sugestao.num_empresas_referencia} empresa(s) analisada(s) · últimos {sugestao.anos_base} anos
                    </Text>
                  </Card>
                </Col>
              )}

              {/* KPIs sugeridos */}
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="Import. Potencial (mediana)"
                  value={fmtRange(sugestao.mediana_imp)}
                  icon={<ImportOutlined />}
                  gradient="linear-gradient(135deg,#667eea,#764ba2)"
                  subtitle={`Média: ${fmtRange(sugestao.media_imp)}`}
                  small
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="Export. Potencial (mediana)"
                  value={fmtRange(sugestao.mediana_exp)}
                  icon={<ExportOutlined />}
                  gradient="linear-gradient(135deg,#43e97b,#38f9d7)"
                  subtitle={`Média: ${fmtRange(sugestao.media_exp)}`}
                  small
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="Empresas de Referência"
                  value={sugestao.num_empresas_referencia ?? '—'}
                  icon={<GlobalOutlined />}
                  gradient="linear-gradient(135deg,#4facfe,#00f2fe)"
                  subtitle="Mesmo CNAE com comex ativo"
                  small
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <KpiCard
                  title="NCMs Típicos"
                  value={sugestao.ncms_tipicos?.length ?? 0}
                  icon={<TagsOutlined />}
                  gradient="linear-gradient(135deg,#fa709a,#fee140)"
                  subtitle="Produtos do segmento"
                  small
                />
              </Col>

              {/* NCMs típicos do segmento */}
              {sugestao.ncms_tipicos?.length > 0 && (
                <Col xs={24}>
                  <Card title="NCMs Mais Usados no Segmento" size="small">
                    <Table
                      rowKey={(r, i) => `${r.ncm}-${i}`}
                      size="small"
                      pagination={{ pageSize: 10, showSizeChanger: false }}
                      dataSource={sugestao.ncms_tipicos}
                      columns={[
                        { title: 'NCM', dataIndex: 'ncm', key: 'ncm', width: 100, render: (v) => <Text code>{v}</Text> },
                        { title: 'Descrição', dataIndex: 'descricao', key: 'desc', ellipsis: true, render: (v) => v || <Text type="secondary">—</Text> },
                        {
                          title: 'Empresas', dataIndex: 'freq_empresas', key: 'freq', width: 90,
                          render: (v) => <Tag color="blue">{v}</Tag>,
                          sorter: (a, b) => (a.freq_empresas || 0) - (b.freq_empresas || 0),
                          defaultSortOrder: 'descend',
                        },
                        { title: 'Total IMP (US$)', dataIndex: 'total_imp', key: 'imp', width: 140, render: (v) => fmtRange(v) },
                        { title: 'Total EXP (US$)', dataIndex: 'total_exp', key: 'exp', width: 140, render: (v) => fmtRange(v) },
                      ]}
                      scroll={{ x: 600 }}
                    />
                  </Card>
                </Col>
              )}
            </Row>
          )}
        </div>
      ),
    },
    {
      key: 'web',
      label: <span><GlobalOutlined /> Contatos na Web</span>,
      children: (
        (() => {
          const nome = perfil.razao_social || '';
          const nomeQ = encodeURIComponent(nome);
          const links = [
            { icon: <LinkedinOutlined style={{ color: '#0a66c2' }} />, titulo: 'Empresa no LinkedIn',
              desc: 'Página e informações institucionais da empresa',
              url: `https://www.linkedin.com/search/results/companies/?keywords=${nomeQ}` },
            { icon: <UserOutlined style={{ color: '#0a66c2' }} />, titulo: 'Pessoas no LinkedIn',
              desc: 'Funcionários e contatos que trabalham na empresa',
              url: `https://www.linkedin.com/search/results/people/?keywords=${nomeQ}` },
            { icon: <MailOutlined style={{ color: '#ea4335' }} />, titulo: 'E-mail e telefone (Google)',
              desc: 'Busca por contatos publicados na web',
              url: `https://www.google.com/search?q=${encodeURIComponent('"' + nome + '" contato email telefone')}` },
            { icon: <GlobalOutlined style={{ color: '#34a853' }} />, titulo: 'Site oficial',
              desc: 'Encontrar o website da empresa',
              url: `https://www.google.com/search?q=${encodeURIComponent(nome + ' site oficial')}` },
          ];
          return (
            <div>
              <Alert
                type="info" showIcon style={{ marginBottom: 16 }}
                message="Buscar contatos na web"
                description="Links de busca externos para localizar contatos, funcionários e presença online da empresa. Abrem em nova aba."
              />
              <Row gutter={[16, 16]}>
                {links.map((l) => (
                  <Col xs={24} sm={12} key={l.titulo}>
                    <a href={l.url} target="_blank" rel="noopener noreferrer" style={{ display: 'block' }}>
                      <Card size="small" hoverable>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <div style={{ fontSize: 24 }}>{l.icon}</div>
                          <div>
                            <div style={{ fontWeight: 600 }}>{l.titulo}</div>
                            <Text type="secondary" style={{ fontSize: 12 }}>{l.desc}</Text>
                          </div>
                        </div>
                      </Card>
                    </a>
                  </Col>
                ))}
              </Row>
              <Paragraph type="secondary" style={{ marginTop: 16, fontSize: 12 }}>
                Observação: LinkedIn e buscadores exigem acesso externo e podem pedir login. Os contatos
                oficiais da Receita Federal (quando disponíveis) estão na aba Perfil.
              </Paragraph>
            </div>
          );
        })()
      ),
    },
  ] : [];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      {/* ── Cabeçalho ── */}
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          <BankOutlined style={{ marginRight: 10, color: '#667eea' }} />
          Empresas & Contatos
        </Title>
        <Text type="secondary">
          Busque por razão social ou CNPJ — visualize perfil cadastral, contatos da Receita Federal,
          CNAE, desempenho no comércio exterior, sugestão de potencial e publicações no DOU.
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
              onChange={(v) => setQuery(v)}
              value={query}
              filterOption={false}
              notFoundContent={
                loadingSearch ? <Spin size="small" /> : query.trim().length >= 2 ? 'Nenhuma empresa encontrada' : null
              }
            >
              <Input
                size="large"
                placeholder="Buscar por razão social ou CNPJ (ex.: VALE S.A. ou 33.000.167/0001-01)"
                prefix={<SearchOutlined style={{ color: '#aaa' }} />}
                onPressEnter={onSearch}
              />
            </AutoComplete>
          </Col>
          <Col>
            <Button
              size="large"
              type="primary"
              icon={<SearchOutlined />}
              onClick={onSearch}
              loading={loading}
              style={{ background: '#667eea', borderColor: '#667eea' }}
            >
              Buscar
            </Button>
          </Col>
        </Row>
        {dados && (
          <div style={{ marginTop: 10, fontSize: 12, color: '#888' }}>
            Exibindo: <strong>{perfil.razao_social || '—'}</strong>
            {perfil.cnpj && <> · CNPJ: <Text copyable={{ text: perfil.cnpj }}>{fmtCnpj(perfil.cnpj)}</Text></>}
          </div>
        )}
      </Card>

      {/* ── Conteúdo ── */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Spin size="large" tip="Carregando dados da empresa..." />
        </div>
      )}

      {!loading && !dados && (
        <Card style={{ borderRadius: 10, textAlign: 'center', padding: '40px 20px' }}>
          <BankOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
          <div style={{ fontSize: 14, color: '#999' }}>
            Busque uma empresa pelo nome ou CNPJ para ver perfil, contatos, CNAE,
            histórico de comércio exterior e potencial estimado.
          </div>
        </Card>
      )}

      {!loading && dados && (
        <Tabs
          activeKey={activeTab}
          onChange={onTabChange}
          type="card"
          items={tabItems}
          style={{ background: 'transparent' }}
        />
      )}
    </div>
  );
}
