import React, { useCallback, useEffect, useState } from "react";
import {
  Alert, AutoComplete, Button, Card, Col, Input, Row, Spin, Statistic, Table, Tag,
  Typography, message,
} from "antd";
import {
  ArrowDownOutlined, ArrowUpOutlined, BulbOutlined, GlobalOutlined,
  RiseOutlined, SearchOutlined,
} from "@ant-design/icons";
import {
  Bar, CartesianGrid, ComposedChart, Legend,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import api from "../services/api";

const { Title, Text } = Typography;

const COLORS = ["#1890ff", "#52c41a", "#faad14", "#f5222d", "#722ed1", "#13c2c2", "#eb2f96", "#fa8c16"];

const fmtUsd = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v || 0);

const fmtM = (v: number) => {
  if (v >= 1e9) return `US$ ${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `US$ ${(v / 1e6).toFixed(1)}M`;
  return fmtUsd(v);
};

interface TimelineItem { ym: string; v_imp: number; v_exp: number }
interface HeatItem { uf: string; v_imp: number; v_exp: number }
interface TopItem { nome: string; valor: number }
interface NcmItem { ncm: string; v_imp: number; v_exp: number }
interface UfItem { uf: string; v_imp: number; v_exp: number }

interface Mercado {
  total_imp: number; total_exp: number; saldo: number;
  timeline: TimelineItem[]; heatmap: HeatItem[];
  top_importadores: TopItem[]; top_exportadores: TopItem[];
  total_br_imp: number; total_br_exp: number;
}

interface CnaeHierarquia {
  descricao?: string | null; setor?: string | null; segmento?: string | null;
  ramo?: string | null; categoria?: string | null; produto?: string | null;
}
interface NcmUfItem { ncm: string; v_imp: number; v_exp: number }
interface Potencial {
  tipo: string; uf: string;
  mercado_imp_uf: number; mercado_exp_uf: number;
  top_ncms_uf: NcmUfItem[];
  cnae_hierarquia: CnaeHierarquia | null;
  metodologia: string;
}

interface EstimadoUf { uf: string; imp: number; exp: number; empresas_uf: number; n_cnpjs: number }

interface EmpresaIntel {
  razao_social: string; uf_sede: string | null; municipio: string | null;
  cnae: string | null; cnae_hierarquia: CnaeHierarquia | null; num_estabelecimentos: number;
  tem_dados_comex: boolean; aviso: string | null;
  fonte_valores: "real" | "estimado" | "indisponivel";
  periodo_estimativa: string | null;
  estimado_por_uf: EstimadoUf[];
  kpis: { total_imp: number; total_exp: number; saldo: number; num_ncms: number; num_ufs: number };
  timeline: TimelineItem[];
  ncms: NcmItem[];
  ufs: UfItem[];
  mercado_uf: { uf: string | null; total_imp: number; total_exp: number; timeline: TimelineItem[] };
  potencial: Potencial | null;
}

// ─── Autocomplete helper ───────────────────────────────────────────────────
const useAutocomplete = () => {
  const [opts, setOpts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const search = useCallback(async (q: string) => {
    if (!q || q.length < 2) { setOpts([]); return; }
    setLoading(true);
    try {
      const res = await api.get("/api/contatos/autocomplete", { params: { q, limit: 20 } });
      const items: any[] = res.data?.items || res.data || [];
      setOpts(items.map((e: any) => ({
        value: e.cnpj || e.nome,
        label: (
          <div>
            <div style={{ fontWeight: 600 }}>{e.nome}</div>
            <div style={{ fontSize: 11, color: "#888" }}>{e.cnpj || ""}{e.uf ? ` · ${e.uf}` : ""}</div>
          </div>
        ),
        cnpj: e.cnpj,
        nome: e.nome,
      })));
    } catch { setOpts([]); } finally { setLoading(false); }
  }, []);
  return { opts, loading, search };
};

// ─── Charts ───────────────────────────────────────────────────────────────
const TimelineChart: React.FC<{ data: TimelineItem[]; height?: number }> = ({ data, height = 260 }) => (
  <ResponsiveContainer width="100%" height={height}>
    <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="ym" tick={{ fontSize: 10 }} tickFormatter={(v) => v?.slice(0, 7)} />
      <YAxis tickFormatter={(v) => fmtM(v)} tick={{ fontSize: 10 }} width={80} />
      <Tooltip formatter={(v: number) => fmtUsd(v)} />
      <Legend />
      <Bar dataKey="v_imp" name="Importação" fill="#1890ff" opacity={0.8} />
      <Bar dataKey="v_exp" name="Exportação" fill="#52c41a" opacity={0.8} />
    </ComposedChart>
  </ResponsiveContainer>
);

const HeatmapTable: React.FC<{ data: HeatItem[] }> = ({ data }) => {
  const maxV = Math.max(...data.map((d) => d.v_imp + d.v_exp), 1);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: 8 }}>
      {data.slice(0, 27).map((d) => {
        const pct = ((d.v_imp + d.v_exp) / maxV) * 100;
        const bg = `rgba(24, 144, 255, ${Math.max(0.05, pct / 100)})`;
        return (
          <div key={d.uf} style={{ background: bg, borderRadius: 6, padding: "8px 12px", border: "1px solid #e8f4ff" }}>
            <div style={{ fontWeight: 700, fontSize: 16 }}>{d.uf}</div>
            <div style={{ fontSize: 11, color: "#555" }}>Imp: {fmtM(d.v_imp)}</div>
            <div style={{ fontSize: 11, color: "#389e0d" }}>Exp: {fmtM(d.v_exp)}</div>
          </div>
        );
      })}
    </div>
  );
};

const TopBar: React.FC<{ data: TopItem[]; color: string; label: string }> = ({ data, color, label }) => {
  const max = Math.max(...data.map((d) => d.valor), 1);
  return (
    <div>
      {data.slice(0, 10).map((d, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
            <Text style={{ fontSize: 12 }} ellipsis>{d.nome}</Text>
            <Text style={{ fontSize: 12, whiteSpace: "nowrap", marginLeft: 8 }}>{fmtM(d.valor)}</Text>
          </div>
          <div style={{ background: "#f0f0f0", borderRadius: 4, height: 6 }}>
            <div style={{ background: color, width: `${(d.valor / max) * 100}%`, height: 6, borderRadius: 4 }} />
          </div>
        </div>
      ))}
    </div>
  );
};

// ─── Potencial Panel (mercado UF+NCM) ──────────────────────────────────────
const PotencialPanel: React.FC<{ potencial: Potencial; razao: string }> = ({ potencial, razao }) => {
  const h = potencial.cnae_hierarquia;
  const topNcms = potencial.top_ncms_uf || [];
  const ncmColumns = [
    { title: "NCM", dataIndex: "ncm", key: "ncm", width: 110 },
    { title: `Importação ${potencial.uf}`, dataIndex: "v_imp", key: "v_imp", render: (v: number) => fmtUsd(v), sorter: (a: NcmUfItem, b: NcmUfItem) => a.v_imp - b.v_imp },
    { title: `Exportação ${potencial.uf}`, dataIndex: "v_exp", key: "v_exp", render: (v: number) => fmtUsd(v), sorter: (a: NcmUfItem, b: NcmUfItem) => a.v_exp - b.v_exp },
    { title: "Total", key: "total", render: (_: any, r: NcmUfItem) => fmtUsd(r.v_imp + r.v_exp), defaultSortOrder: "descend" as const, sorter: (a: NcmUfItem, b: NcmUfItem) => (a.v_imp + a.v_exp) - (b.v_imp + b.v_exp) },
  ];
  return (
    <div>
      <Alert
        type="info" showIcon icon={<BulbOutlined />}
        message={`Potencial de mercado para ${razao}`}
        description={potencial.metodologia}
        style={{ marginBottom: 16 }}
      />
      {/* Hierarquia CNAE */}
      {h && (h.setor || h.segmento || h.ramo) && (
        <Card size="small" style={{ marginBottom: 16 }} title="Segmento de Atuação (CNAE)">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {h.setor && <Tag color="blue">Setor: {h.setor}</Tag>}
            {h.segmento && <Tag color="geekblue">Segmento: {h.segmento}</Tag>}
            {h.ramo && <Tag color="purple">Ramo: {h.ramo}</Tag>}
            {h.categoria && <Tag color="magenta">Categoria: {h.categoria}</Tag>}
            {h.produto && <Tag>Produto: {h.produto}</Tag>}
          </div>
        </Card>
      )}
      {/* Mercado da UF */}
      <Row gutter={[16, 16]}>
        <Col xs={12} md={8}>
          <Card style={{ background: "linear-gradient(135deg, #1890ff20, #1890ff05)", border: "1px solid #1890ff40" }}>
            <Statistic title={`Mercado Importação — ${potencial.uf}`} value={potencial.mercado_imp_uf} formatter={(v) => fmtM(Number(v))} prefix={<ArrowDownOutlined style={{ color: "#1890ff" }} />} />
          </Card>
        </Col>
        <Col xs={12} md={8}>
          <Card style={{ background: "linear-gradient(135deg, #52c41a20, #52c41a05)", border: "1px solid #52c41a40" }}>
            <Statistic title={`Mercado Exportação — ${potencial.uf}`} value={potencial.mercado_exp_uf} formatter={(v) => fmtM(Number(v))} prefix={<ArrowUpOutlined style={{ color: "#52c41a" }} />} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic title="NCMs no Estado" value={topNcms.length} prefix={<GlobalOutlined />} suffix="principais" />
          </Card>
        </Col>
      </Row>
      {/* Top NCMs movimentados na UF */}
      {topNcms.length > 0 && (
        <Card title={`NCMs Mais Movimentados em ${potencial.uf} (valores FOB reais)`} style={{ marginTop: 16 }}>
          <Table
            rowKey={(r: NcmUfItem) => r.ncm}
            columns={ncmColumns}
            dataSource={topNcms}
            pagination={false}
            size="small"
          />
        </Card>
      )}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────
const DashboardComexBigQuery: React.FC = () => {
  const [mercado, setMercado] = useState<Mercado | null>(null);
  const [empresa, setEmpresa] = useState<EmpresaIntel | null>(null);
  const [loadingMercado, setLoadingMercado] = useState(true);
  const [loadingEmpresa, setLoadingEmpresa] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [anoInicio, setAnoInicio] = useState(2022);
  const [anoFim, setAnoFim] = useState(2024);
  const { opts, loading: loadingAuto, search: doAutoComplete } = useAutocomplete();

  // Carregar visão geral do mercado
  const loadMercado = useCallback(async () => {
    setLoadingMercado(true);
    try {
      const res = await api.get("/api/empresa-intel/mercado", { params: { ano_inicio: anoInicio, ano_fim: anoFim } });
      setMercado(res.data);
    } catch (e: any) {
      message.error("Erro ao carregar dados de mercado: " + (e?.message || ""));
    } finally {
      setLoadingMercado(false);
    }
  }, [anoInicio, anoFim]);

  const buscarEmpresa = useCallback(async (q: string) => {
    if (!q || q.length < 2) return;
    setLoadingEmpresa(true);
    setEmpresa(null);
    try {
      const res = await api.get("/api/empresa-intel/empresa", { params: { q, ano_inicio: anoInicio, ano_fim: anoFim } });
      setEmpresa(res.data);
    } catch (e: any) {
      message.error("Empresa não encontrada: " + (e?.response?.data?.detail || e?.message || ""));
    } finally {
      setLoadingEmpresa(false);
    }
  }, [anoInicio, anoFim]);

  useEffect(() => { loadMercado(); }, [loadMercado]);

  const onSelect = (_: string, opt: any) => {
    const q = opt.cnpj || opt.nome || opt.value;
    setSearchText(opt.nome || opt.value);
    buscarEmpresa(q);
  };

  const onSearch = () => buscarEmpresa(searchText);

  const ncmColumns = [
    { title: "NCM", dataIndex: "ncm", key: "ncm", width: 110 },
    { title: "Importação", dataIndex: "v_imp", key: "v_imp", render: (v: number) => fmtUsd(v), sorter: (a: NcmItem, b: NcmItem) => a.v_imp - b.v_imp },
    { title: "Exportação", dataIndex: "v_exp", key: "v_exp", render: (v: number) => fmtUsd(v), sorter: (a: NcmItem, b: NcmItem) => a.v_exp - b.v_exp },
    {
      title: "Total", key: "total",
      render: (_: any, r: NcmItem) => fmtUsd(r.v_imp + r.v_exp),
      sorter: (a: NcmItem, b: NcmItem) => (a.v_imp + a.v_exp) - (b.v_imp + b.v_exp),
      defaultSortOrder: "descend" as const,
    },
  ];

  const anos = [2020, 2021, 2022, 2023, 2024, 2025];

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      {/* ── Cabeçalho ── */}
      <div style={{ background: "linear-gradient(135deg, #001529, #003a8c)", borderRadius: 12, padding: "32px 40px", marginBottom: 24, color: "#fff" }}>
        <Title level={2} style={{ color: "#fff", margin: 0 }}>🌐 Inteligência de Comércio Exterior</Title>
        <Text style={{ color: "#afc6e9", fontSize: 15 }}>
          Análise de importação, exportação e potencial de mercado por empresa, NCM e UF
        </Text>
        <div style={{ marginTop: 20, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <AutoComplete
            options={opts}
            onSearch={doAutoComplete}
            onSelect={onSelect}
            value={searchText}
            onChange={(v) => setSearchText(v)}
            style={{ width: 380 }}
            notFoundContent={loadingAuto ? <Spin size="small" /> : "Digite ao menos 2 caracteres"}
          >
            <Input
              size="large"
              placeholder="Buscar empresa por nome ou CNPJ..."
              prefix={<SearchOutlined />}
              style={{ borderRadius: 8 }}
            />
          </AutoComplete>
          <select
            value={anoInicio}
            onChange={(e) => setAnoInicio(Number(e.target.value))}
            style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #d9d9d9", fontSize: 14 }}
          >
            {anos.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <Text style={{ color: "#aaa" }}>até</Text>
          <select
            value={anoFim}
            onChange={(e) => setAnoFim(Number(e.target.value))}
            style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #d9d9d9", fontSize: 14 }}
          >
            {anos.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <Button type="primary" size="large" icon={<SearchOutlined />} onClick={onSearch} loading={loadingEmpresa}>
            Buscar
          </Button>
          {empresa && (
            <Button size="large" onClick={() => { setEmpresa(null); setSearchText(""); }}>
              Limpar
            </Button>
          )}
        </div>
      </div>

      {/* ── Loading empresa ── */}
      {loadingEmpresa && (
        <div style={{ textAlign: "center", padding: 48 }}>
          <Spin size="large" tip="Buscando inteligência da empresa..." />
        </div>
      )}

      {/* ══ MODO EMPRESA ══════════════════════════════════════════════════ */}
      {empresa && !loadingEmpresa && (
        <>
          {/* Cabeçalho empresa */}
          <Card style={{ marginBottom: 16, borderLeft: "4px solid #1890ff" }}>
            <Row gutter={16} align="middle">
              <Col flex="auto">
                <Title level={3} style={{ margin: 0 }}>{empresa.razao_social}</Title>
                <div style={{ marginTop: 4 }}>
                  {empresa.uf_sede && <Tag color="blue">UF: {empresa.uf_sede}</Tag>}
                  {empresa.municipio && <Tag>{empresa.municipio}</Tag>}
                  {empresa.cnae && <Tag color="purple">CNAE: {empresa.cnae}</Tag>}
                  {empresa.num_estabelecimentos > 0 && <Tag color="geekblue">{empresa.num_estabelecimentos} estabelecimentos</Tag>}
                </div>
              </Col>
            </Row>
          </Card>

          {/* Banner conforme a fonte dos valores */}
          {empresa.fonte_valores === "estimado" && (
            <Alert
              type="info" showIcon icon={<BulbOutlined />}
              message={`Valores ESTIMADOS (período ${empresa.periodo_estimativa || "—"})`}
              description={empresa.aviso}
              style={{ marginBottom: 16 }}
            />
          )}
          {empresa.fonte_valores === "indisponivel" && empresa.aviso && (
            <Alert type="warning" showIcon message="Dados de Comércio por CNPJ Indisponíveis" description={empresa.aviso} style={{ marginBottom: 16 }} />
          )}

          {/* KPIs empresa (reais ou estimados) */}
          {empresa.tem_dados_comex && (
            <>
              {empresa.fonte_valores === "estimado" && (
                <div style={{ marginBottom: 8 }}>
                  <Tag color="orange" style={{ fontSize: 13, padding: "2px 10px" }}>⚠ Estimativa estatística — não é histórico real</Tag>
                </div>
              )}
              <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                <Col xs={12} md={6}>
                  <Card style={{ background: "linear-gradient(135deg, #1890ff, #096dd9)", color: "#fff", position: "relative" }}>
                    {empresa.fonte_valores === "estimado" && <Tag color="orange" style={{ position: "absolute", top: 8, right: 8 }}>est.</Tag>}
                    <div style={{ color: "rgba(255,255,255,0.8)", fontSize: 13 }}>Importações {empresa.fonte_valores === "estimado" ? "(estimadas)" : "Totais"}</div>
                    <div style={{ color: "#fff", fontSize: 22, fontWeight: 700, marginTop: 4 }}>{fmtM(empresa.kpis.total_imp)}</div>
                  </Card>
                </Col>
                <Col xs={12} md={6}>
                  <Card style={{ background: "linear-gradient(135deg, #52c41a, #389e0d)", color: "#fff", position: "relative" }}>
                    {empresa.fonte_valores === "estimado" && <Tag color="orange" style={{ position: "absolute", top: 8, right: 8 }}>est.</Tag>}
                    <div style={{ color: "rgba(255,255,255,0.8)", fontSize: 13 }}>Exportações {empresa.fonte_valores === "estimado" ? "(estimadas)" : "Totais"}</div>
                    <div style={{ color: "#fff", fontSize: 22, fontWeight: 700, marginTop: 4 }}>{fmtM(empresa.kpis.total_exp)}</div>
                  </Card>
                </Col>
                <Col xs={12} md={6}>
                  <Card>
                    <Statistic title="Saldo Comercial" value={empresa.kpis.saldo}
                      formatter={(v) => fmtM(Number(v))}
                      valueStyle={{ color: empresa.kpis.saldo >= 0 ? "#52c41a" : "#f5222d" }}
                      prefix={empresa.kpis.saldo >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={12} md={6}>
                  <Card>
                    <Statistic title={empresa.fonte_valores === "estimado" ? "UFs de Atuação" : "NCMs Operados"} value={empresa.fonte_valores === "estimado" ? empresa.kpis.num_ufs : empresa.kpis.num_ncms} />
                  </Card>
                </Col>
              </Row>

              {/* Timeline empresa (só dados reais) */}
              {empresa.timeline.length > 0 && (
                <Card title="Evolução Mensal" style={{ marginBottom: 16 }}>
                  <TimelineChart data={empresa.timeline} />
                </Card>
              )}

              {/* NCMs (reais) + Distribuição por UF */}
              <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                {empresa.ncms.length > 0 && (
                  <Col xs={24} lg={14}>
                    <Card title="Principais NCMs Operados">
                      <Table
                        rowKey={(r: NcmItem) => r.ncm}
                        columns={ncmColumns}
                        dataSource={empresa.ncms}
                        pagination={false}
                        size="small"
                      />
                    </Card>
                  </Col>
                )}
                <Col xs={24} lg={empresa.ncms.length > 0 ? 10 : 24}>
                  <Card title={empresa.fonte_valores === "estimado" ? "Distribuição Estimada por UF" : "Distribuição por UF"}>
                    {empresa.ufs.map((u, i) => {
                      const total = u.v_imp + u.v_exp;
                      const maxTotal = Math.max(...empresa.ufs.map((x) => x.v_imp + x.v_exp), 1);
                      return (
                        <div key={u.uf} style={{ marginBottom: 10 }}>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <Text strong>{u.uf}</Text>
                            <Text style={{ fontSize: 12 }}>{fmtM(total)}</Text>
                          </div>
                          <div style={{ background: "#f0f0f0", borderRadius: 4, height: 8, marginTop: 2 }}>
                            <div style={{ background: COLORS[i % COLORS.length], width: `${(total / maxTotal) * 100}%`, height: 8, borderRadius: 4 }} />
                          </div>
                        </div>
                      );
                    })}
                  </Card>
                </Col>
              </Row>
            </>
          )}

          {/* Contexto de Mercado (UF da empresa) */}
          {empresa.mercado_uf?.uf && (
            <Card
              title={`📊 Mercado — ${empresa.mercado_uf.uf} (${anoInicio}–${anoFim})`}
              style={{ marginBottom: 16 }}
              extra={<Tag color="blue">Contexto do Estado</Tag>}
            >
              <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                <Col xs={12} md={8}>
                  <Statistic title={`Total Importado ${empresa.mercado_uf.uf}`} value={empresa.mercado_uf.total_imp} formatter={(v) => fmtM(Number(v))} prefix={<ArrowDownOutlined style={{ color: "#1890ff" }} />} />
                </Col>
                <Col xs={12} md={8}>
                  <Statistic title={`Total Exportado ${empresa.mercado_uf.uf}`} value={empresa.mercado_uf.total_exp} formatter={(v) => fmtM(Number(v))} prefix={<ArrowUpOutlined style={{ color: "#52c41a" }} />} />
                </Col>
                <Col xs={24} md={8}>
                  {empresa.fonte_valores === "real" && empresa.kpis.total_imp + empresa.kpis.total_exp > 0 && empresa.mercado_uf.total_imp + empresa.mercado_uf.total_exp > 0 && (
                    <Statistic
                      title="Market Share"
                      value={((empresa.kpis.total_imp + empresa.kpis.total_exp) / (empresa.mercado_uf.total_imp + empresa.mercado_uf.total_exp) * 100).toFixed(2)}
                      suffix="%"
                      prefix={<RiseOutlined style={{ color: "#722ed1" }} />}
                    />
                  )}
                </Col>
              </Row>
              {empresa.mercado_uf.timeline.length > 0 && (
                <TimelineChart data={empresa.mercado_uf.timeline} height={200} />
              )}
            </Card>
          )}

          {/* Potencial de mercado (UF+NCM) quando sem dados por CNPJ */}
          {!empresa.tem_dados_comex && (
            <Card title="🔮 Potencial de Mercado por Segmento e UF" style={{ marginBottom: 16 }}>
              {empresa.potencial ? (
                <PotencialPanel potencial={empresa.potencial} razao={empresa.razao_social} />
              ) : (
                <Alert type="info" showIcon message="Estimativa de mercado indisponível para esta UF." />
              )}
            </Card>
          )}
        </>
      )}

      {/* ══ MODO MERCADO (sem empresa selecionada) ═════════════════════════ */}
      {!empresa && !loadingEmpresa && (
        <>
          {loadingMercado ? (
            <div style={{ textAlign: "center", padding: 64 }}>
              <Spin size="large" tip="Carregando visão geral do mercado..." />
            </div>
          ) : mercado ? (
            <>
              {/* KPIs Mercado Brasil */}
              <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} md={8}>
                  <Card style={{ background: "linear-gradient(135deg, #1890ff, #0050b3)", color: "#fff" }}>
                    <div style={{ color: "rgba(255,255,255,.8)", fontSize: 13, marginBottom: 4 }}>🇧🇷 Importações Brasil</div>
                    <div style={{ color: "#fff", fontSize: 28, fontWeight: 700 }}>{fmtM(mercado.total_imp)}</div>
                    <div style={{ color: "rgba(255,255,255,.6)", fontSize: 12 }}>{anoInicio}–{anoFim}</div>
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card style={{ background: "linear-gradient(135deg, #52c41a, #237804)", color: "#fff" }}>
                    <div style={{ color: "rgba(255,255,255,.8)", fontSize: 13, marginBottom: 4 }}>🇧🇷 Exportações Brasil</div>
                    <div style={{ color: "#fff", fontSize: 28, fontWeight: 700 }}>{fmtM(mercado.total_exp)}</div>
                    <div style={{ color: "rgba(255,255,255,.6)", fontSize: 12 }}>{anoInicio}–{anoFim}</div>
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card style={{ background: mercado.saldo >= 0 ? "linear-gradient(135deg, #722ed1, #531dab)" : "linear-gradient(135deg, #f5222d, #a8071a)", color: "#fff" }}>
                    <div style={{ color: "rgba(255,255,255,.8)", fontSize: 13, marginBottom: 4 }}>⚖️ Saldo Comercial</div>
                    <div style={{ color: "#fff", fontSize: 28, fontWeight: 700 }}>{fmtM(mercado.saldo)}</div>
                    <div style={{ color: "rgba(255,255,255,.6)", fontSize: 12 }}>{mercado.saldo >= 0 ? "Superávit" : "Déficit"}</div>
                  </Card>
                </Col>
              </Row>

              {/* Timeline Mercado */}
              {mercado.timeline?.length > 0 && (
                <Card title="📈 Evolução do Comércio Exterior Brasileiro" style={{ marginBottom: 16 }}>
                  <TimelineChart data={mercado.timeline} height={300} />
                </Card>
              )}

              {/* Top Empresas */}
              <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                <Col xs={24} md={12}>
                  <Card title="🏆 Top Importadores">
                    <TopBar data={mercado.top_importadores} color="#1890ff" label="Importação" />
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card title="🏆 Top Exportadores">
                    <TopBar data={mercado.top_exportadores} color="#52c41a" label="Exportação" />
                  </Card>
                </Col>
              </Row>

              {/* Heatmap UF */}
              {mercado.heatmap?.length > 0 && (
                <Card title="🗺️ Volume por UF" style={{ marginBottom: 16 }}>
                  <HeatmapTable data={mercado.heatmap} />
                </Card>
              )}

              <Alert
                type="info"
                showIcon
                message="Use a busca acima para analisar uma empresa específica"
                description="Busque por nome ou CNPJ para ver importações, exportações, NCMs, distribuição por estado e potencial de mercado por segmento."
              />
            </>
          ) : (
            <Alert type="error" showIcon message="Não foi possível carregar os dados de mercado." />
          )}
        </>
      )}
    </div>
  );
};

export default DashboardComexBigQuery;
