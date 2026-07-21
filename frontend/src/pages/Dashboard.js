import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { 
  Row, Col, Card, Statistic, Spin, Alert, Table, Tag, 
  DatePicker, Select, Input, Button, Space, Divider, AutoComplete, message
} from 'antd';
import {
  DollarOutlined,
  GlobalOutlined,
  DownloadOutlined,
  SearchOutlined,
  ReloadOutlined,
  BulbOutlined,
  ImportOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { empresasRecomendadasAPI, comexstatAPI, dadosReaisAPI, adminSyncAPI, dashboardLocalAPI, comexDashboardBqAPI } from '../services/api';
import api from '../services/api';
import dayjs from 'dayjs';
import 'dayjs/locale/pt-br';

dayjs.locale('pt-br');

const { RangePicker } = DatePicker;
const { Option } = Select;

const COLORS = ['#0088FE', '#FF8042', '#FFBB28', '#00C49F', '#8884d8', '#82ca9d'];

/** Nome para exibir/autocomplete — a API pode retornar `nome`, `razao_social`, etc. */
const nomeEmpresaListaItem = (empresa) => {
  if (empresa == null) return '';
  if (typeof empresa === 'string') return String(empresa).trim();
  const n =
    empresa.nome ??
    empresa.razao_social ??
    empresa.empresa ??
    empresa.razao_social_importador ??
    empresa.razao_social_exportador ??
    '';
  return String(n).trim();
};

const MIN_CHARS_FILTRO_EMPRESA = 2;

/** Lê o texto atual do campo AutoComplete (Ant Design 5 usa input dentro de .ant-select). */
const lerInputEmpresaNoDom = (dataFilterAttr) => {
  try {
    const root = document.querySelector(`[data-filter="${dataFilterAttr}"]`);
    if (!root) return '';
    const input =
      root.querySelector('input.ant-select-selection-search-input') ||
      root.querySelector('.ant-select-selection-search input') ||
      root.querySelector('input');
    if (!input || input.value == null) return '';
    return String(input.value).trim();
  } catch (_) {
    return '';
  }
};

// Tooltip seguro para Recharts: evita getBoundingClientRect em elemento nulo ao mudar filtros (ex.: Hidrau Torque)
const SafeTooltip = ({ active, payload, formatter, label, ...rest }) => {
  if (!active || !payload || payload.length === 0) return null;
  const format = typeof formatter === 'function' ? formatter : (v) => v;
  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.96)',
        border: '1px solid #ddd',
        borderRadius: '6px',
        padding: '8px 12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        maxWidth: '320px',
      }}
      {...rest}
    >
      {label && <div style={{ marginBottom: '4px', fontWeight: 600, fontSize: '12px' }}>{label}</div>}
      {payload.map((entry, i) => (
        <div key={i} style={{ color: entry.color, fontSize: '12px' }}>
          {entry.name}: {format(entry.value, entry.name, entry, i)}
        </div>
      ))}
    </div>
  );
};

// Mapeamento de UF para Nome Completo do Estado
const UF_PARA_ESTADO = {
  'AC': 'Acre',
  'AL': 'Alagoas',
  'AP': 'Amapá',
  'AM': 'Amazonas',
  'BA': 'Bahia',
  'CE': 'Ceará',
  'DF': 'Distrito Federal',
  'ES': 'Espírito Santo',
  'GO': 'Goiás',
  'MA': 'Maranhão',
  'MT': 'Mato Grosso',
  'MS': 'Mato Grosso do Sul',
  'MG': 'Minas Gerais',
  'PA': 'Pará',
  'PB': 'Paraíba',
  'PR': 'Paraná',
  'PE': 'Pernambuco',
  'PI': 'Piauí',
  'RJ': 'Rio de Janeiro',
  'RN': 'Rio Grande do Norte',
  'RS': 'Rio Grande do Sul',
  'RO': 'Rondônia',
  'RR': 'Roraima',
  'SC': 'Santa Catarina',
  'SP': 'São Paulo',
  'SE': 'Sergipe',
  'TO': 'Tocantins',
};

// Função para obter nome completo do estado
const obterNomeEstado = (uf) => {
  if (!uf) return '';
  const ufUpper = String(uf).trim().toUpperCase().substring(0, 2);
  return UF_PARA_ESTADO[ufUpper] || ufUpper;
};

// ─── Formatação numérica para sugestão ────────────────────────────────────────
const fmtRange = (v) => {
  if (!v) return 'Sem dados';
  if (v >= 1e9) return `US$ ${(v / 1e9).toFixed(1)} Bi`;
  if (v >= 1e6) return `US$ ${(v / 1e6).toFixed(1)} Mi`;
  if (v >= 1e3) return `US$ ${(v / 1e3).toFixed(0)} Mil`;
  return `US$ ${v.toFixed(0)}`;
};

// ─── Painel de sugestão estatística no Dashboard ──────────────────────────────
const SugestaoComexPanel = ({ stats, sugestao, loading, onBuscar }) => {
  const nomeEmpresa = (stats?._filtro_empresa || 'empresa filtrada');
  const cnpjs = stats?.cnpjs_resolvidos || [];

  return (
    <Card
      style={{ marginBottom: 24, borderLeft: '4px solid #667eea', borderRadius: 8 }}
      bodyStyle={{ padding: '16px 20px' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <BulbOutlined style={{ color: '#667eea', fontSize: 18 }} />
            <span style={{ fontWeight: 700, fontSize: 15 }}>
              Potencial Estimado — {nomeEmpresa}
            </span>
            {cnpjs.length > 0 && (
              <Tag color="geekblue" style={{ fontSize: 10 }}>
                CNPJ: {cnpjs[0]}
              </Tag>
            )}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginBottom: 10 }}>
            Empresa encontrada na base cadastral mas sem histórico de comex disponível.
            Calculamos o potencial com base em empresas do mesmo segmento (CNAE) que já operam no comércio exterior.
          </div>

          {loading && (
            <div style={{ padding: '12px 0' }}>
              <Spin size="small" /> <span style={{ marginLeft: 8, fontSize: 12, color: '#888' }}>Calculando potencial do segmento...</span>
            </div>
          )}

          {!loading && !sugestao && (
            <Button
              type="primary"
              icon={<BulbOutlined />}
              onClick={onBuscar}
              size="small"
              style={{ background: '#667eea', borderColor: '#667eea' }}
            >
              Calcular Potencial do Segmento
            </Button>
          )}

          {!loading && sugestao && !sugestao.tem_sugestao && (
            <Alert
              message={sugestao.motivo || sugestao.metodologia}
              type="info"
              showIcon
              style={{ fontSize: 12 }}
            />
          )}

          {!loading && sugestao?.tem_sugestao && (
            <div>
              <Row gutter={[12, 8]}>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ background: 'linear-gradient(135deg,#667eea,#764ba2)', borderRadius: 8, padding: '10px 14px' }}>
                    <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 10, marginBottom: 2 }}>
                      <ImportOutlined style={{ marginRight: 4 }} />Importação Estimada
                    </div>
                    <div style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>
                      {fmtRange(sugestao.mediana_imp || sugestao.valor_imp_sugerido)}
                    </div>
                    <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 10 }}>mediana/ano do segmento</div>
                  </div>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ background: 'linear-gradient(135deg,#43e97b,#38f9d7)', borderRadius: 8, padding: '10px 14px' }}>
                    <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 10, marginBottom: 2 }}>
                      <ExportOutlined style={{ marginRight: 4 }} />Exportação Estimada
                    </div>
                    <div style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>
                      {fmtRange(sugestao.mediana_exp || sugestao.valor_exp_sugerido)}
                    </div>
                    <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 10 }}>mediana/ano do segmento</div>
                  </div>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <div style={{ background: '#f6f8ff', borderRadius: 8, padding: '10px 14px', border: '1px solid #e8ecff' }}>
                    <div style={{ color: '#888', fontSize: 10, marginBottom: 2 }}>Empresas de Referência</div>
                    <div style={{ color: '#667eea', fontWeight: 700, fontSize: 18 }}>{sugestao.num_empresas_referencia}</div>
                    <div style={{ color: '#aaa', fontSize: 10 }}>mesmo CNAE com comex ativo</div>
                  </div>
                </Col>
                {sugestao.cnae_info && (
                  <Col xs={24} sm={12} md={6}>
                    <div style={{ background: '#f6f8ff', borderRadius: 8, padding: '10px 14px', border: '1px solid #e8ecff' }}>
                      <div style={{ color: '#888', fontSize: 10, marginBottom: 4 }}>Segmento</div>
                      {sugestao.cnae_info.setor && (
                        <Tag color="blue" style={{ fontSize: 10, margin: '2px 0' }}>{sugestao.cnae_info.setor}</Tag>
                      )}
                      {sugestao.cnae_info.segmento && (
                        <Tag color="geekblue" style={{ fontSize: 10, margin: '2px 0' }}>{sugestao.cnae_info.segmento}</Tag>
                      )}
                    </div>
                  </Col>
                )}
              </Row>
              {sugestao.ncms_tipicos?.length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>
                    NCMs mais frequentes no segmento:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {sugestao.ncms_tipicos.slice(0, 8).map((n, i) => (
                      <Tag key={i} color="purple" style={{ fontSize: 10 }}>
                        {n.ncm}{n.descricao ? ` — ${n.descricao.slice(0, 30)}` : ''}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
              <div style={{ marginTop: 8, fontSize: 10, color: '#bbb', fontStyle: 'italic' }}>
                {sugestao.metodologia}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  // Período padrão: 01/01/2024 até a data atual (gráficos de 2024 até hoje)
  const [periodo, setPeriodo] = useState([
    dayjs('2024-01-01'),
    dayjs().endOf('day'),
  ]);
  const [tipoOperacao, setTipoOperacao] = useState(null);
  const [ncmFiltro, setNcmFiltro] = useState(null);
  const [ncmsFiltro, setNcmsFiltro] = useState([]);
  const [meses, setMeses] = useState(() => {
    const start = dayjs('2024-01-01');
    const end = dayjs();
    return Math.min(120, Math.max(1, end.diff(start, 'month') + 1));
  }); // Padrão: de jan/2024 até hoje (máx. 120 meses = 10 anos, conforme backend)
  const [tabelaDados, setTabelaDados] = useState([]);
  const [loadingTabela, setLoadingTabela] = useState(false);
  const [paginacaoTabela, setPaginacaoTabela] = useState({ current: 1, pageSize: 10, total: 0 });
  const [empresaImportadora, setEmpresaImportadora] = useState(null);
  const [empresaExportadora, setEmpresaExportadora] = useState(null);
  const [sugestaoComex, setSugestaoComex] = useState(null);
  const [loadingSugestao, setLoadingSugestao] = useState(false);
  const [empresaImportadoraInput, setEmpresaImportadoraInput] = useState('');
  const [empresaExportadoraInput, setEmpresaExportadoraInput] = useState('');
  const [importadorasOptions, setImportadorasOptions] = useState([]);
  const [exportadorasOptions, setExportadorasOptions] = useState([]);
  const [loadingImportadoras, setLoadingImportadoras] = useState(false);
  const [loadingExportadoras, setLoadingExportadoras] = useState(false);
  const isLoadingRef = useRef(false);
  const requestIdRef = useRef(0);
  const searchInProgressRef = useRef(false); // true após Buscar até a requisição terminar (evita useEffect sobrescrever dados filtrados)
  const importadorInputRef = useRef('');
  const exportadorInputRef = useRef('');
  
  // Estados para sinergias e sugestões
  
  // Estados para empresas recomendadas e dados ComexStat
  const [empresasRecomendadas, setEmpresasRecomendadas] = useState([]);
  const [loadingEmpresasRecomendadas, setLoadingEmpresasRecomendadas] = useState(false);
  const [dadosComexstat, setDadosComexstat] = useState(null);
  const [loadingDadosComexstat, setLoadingDadosComexstat] = useState(false);
  
  // Estados para empresas importadoras/exportadoras recomendadas (movido para cima para evitar erro React #310)
  const [empresasImportadorasRecomendadas, setEmpresasImportadorasRecomendadas] = useState([]);
  const [empresasExportadorasRecomendadas, setEmpresasExportadorasRecomendadas] = useState([]);
  
  // Estado para detectar mobile
  const [isMobile, setIsMobile] = useState(false);

  // Dados reais BigQuery / relatório estado–NCM
  const [bqAno, setBqAno] = useState(2021);
  const [bqRanking, setBqRanking] = useState([]);
  const [bqRelatorioRows, setBqRelatorioRows] = useState([]);
  const [filtBqUf, setFiltBqUf] = useState(null);
  const [filtBqTipo, setFiltBqTipo] = useState(null);
  const [filtBqNcm, setFiltBqNcm] = useState('');
  const [loadingBq, setLoadingBq] = useState(false);
  const [syncingBq, setSyncingBq] = useState(false);
  const [cnpjNcmBusca, setCnpjNcmBusca] = useState('');
  const [ncmsCnpjResult, setNcmsCnpjResult] = useState([]);
  const [adminSyncToken, setAdminSyncToken] = useState(() => {
    try {
      return localStorage.getItem('admin_sync_token') || '';
    } catch {
      return '';
    }
  });
  const [localPgRows, setLocalPgRows] = useState([]);
  const [loadingLocalPg, setLoadingLocalPg] = useState(false);

  const mesesRef = useRef(meses);
  mesesRef.current = meses;
  const tipoOperacaoRef = useRef(tipoOperacao);
  tipoOperacaoRef.current = tipoOperacao;
  const ncmFiltroRef = useRef(ncmFiltro);
  ncmFiltroRef.current = ncmFiltro;
  const ncmsFiltroRef = useRef(ncmsFiltro);
  ncmsFiltroRef.current = ncmsFiltro;
  const empresaImportadoraRef = useRef(empresaImportadora);
  empresaImportadoraRef.current = empresaImportadora;
  const empresaExportadoraRef = useRef(empresaExportadora);
  empresaExportadoraRef.current = empresaExportadora;
  const periodoRef = useRef(periodo);
  periodoRef.current = periodo;

  const flattenRelatorioTree = useCallback((tree) => {
    const rows = [];
    Object.entries(tree || {}).forEach(([uf, ncmMap]) => {
      Object.entries(ncmMap || {}).forEach(([ncm, empresas]) => {
        (empresas || []).forEach((emp) => {
          rows.push({ estado: uf, ncm, nome: emp.nome, tipo: emp.tipo, valor_fob: emp.valor_fob });
        });
      });
    });
    return rows;
  }, []);

  const carregarBigQueryRanking = useCallback(async () => {
    setLoadingBq(true);
    try {
      const [ex, im] = await Promise.all([
        dadosReaisAPI.getExportadoras(bqAno, 100),
        dadosReaisAPI.getImportadoras(bqAno, 100),
      ]);
      const dEx = ex.data?.dados || [];
      const dIm = im.data?.dados || [];
      const merged = [
        ...dEx.map((r) => ({ ...r, tipo: 'exportadora' })),
        ...dIm.map((r) => ({ ...r, tipo: 'importadora' })),
      ].sort((a, b) => (Number(b.valor_total_fob) || 0) - (Number(a.valor_total_fob) || 0));
      setBqRanking(merged);
    } catch (e) {
      console.warn('BigQuery ranking:', e?.message || e);
      setBqRanking([]);
    } finally {
      setLoadingBq(false);
    }
  }, [bqAno]);

  const carregarRelatorioBq = useCallback(async () => {
    try {
      const res = await dadosReaisAPI.getRelatorioEstadoNcm(bqAno);
      const tree = res.data || {};
      setBqRelatorioRows(flattenRelatorioTree(tree));
    } catch (e) {
      console.warn('Relatório estado-NCM:', e?.message || e);
      setBqRelatorioRows([]);
    }
  }, [bqAno, flattenRelatorioTree]);

  useEffect(() => {
    carregarBigQueryRanking();
  }, [carregarBigQueryRanking]);

  const bqRankingFiltrado = useMemo(() => {
    return bqRanking.filter((r) => {
      if (filtBqUf && String(r.estado || '').toUpperCase() !== filtBqUf) return false;
      if (filtBqTipo && r.tipo !== filtBqTipo) return false;
      return true;
    });
  }, [bqRanking, filtBqUf, filtBqTipo]);

  const bqRelatorioFiltrado = useMemo(() => {
    const n = (filtBqNcm || '').trim().replace(/\D/g, '');
    if (!n) return bqRelatorioRows;
    return bqRelatorioRows.filter((r) => {
      const raw = String(r.ncm || '').replace(/\D/g, '');
      return raw.includes(n);
    });
  }, [bqRelatorioRows, filtBqNcm]);

  // Detectar se está em mobile (deve estar antes de qualquer cálculo)
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Função debounce simples
  const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };

  // Função de busca de importadoras com debounce (com fallback para /dashboard/debug/empresas)
  const buscarImportadoras = useCallback(
    debounce(async (query) => {
      const termo = typeof query === 'string' ? query.trim() : '';
      setLoadingImportadoras(true);
      try {
        let lista = [];
        if (termo.length >= 1) {
          try {
            const bqRes = await comexDashboardBqAPI.autocompleteEmpresa(termo, 'importacao', 25);
            const items = bqRes?.data?.items;
            if (Array.isArray(items)) lista = items;
          } catch (e) {
            console.warn('⚠️ Autocomplete BigQuery empresas_ncm_import_export_uf (importador):', e?.message || e);
          }
        }
        const options = lista
          .map((empresa) => {
            const nome = nomeEmpresaListaItem(empresa);
            const ops = empresa.total_operacoes ?? empresa.total ?? 0;
            const cnpj = empresa.cnpj != null && String(empresa.cnpj).trim() ? String(empresa.cnpj).trim() : '';
            const label = cnpj
              ? `${nome || 'N/A'} — ${cnpj} (${ops} reg.)`
              : `${nome || 'N/A'} (${ops} operações)`;
            return { value: nome, label };
          })
          .filter((o) => o.value);
        setImportadorasOptions(options);
      } catch (error) {
        console.error('❌ Erro ao buscar importadoras:', error?.message || error);
        setImportadorasOptions([]);
      } finally {
        setLoadingImportadoras(false);
      }
    }, 300),
    []
  );

  // Função de busca de exportadoras com debounce (com fallback para /dashboard/debug/empresas)
  const buscarExportadoras = useCallback(
    debounce(async (query) => {
      const termo = typeof query === 'string' ? query.trim() : '';
      setLoadingExportadoras(true);
      try {
        let lista = [];
        if (termo.length >= 1) {
          try {
            const bqRes = await comexDashboardBqAPI.autocompleteEmpresa(termo, 'exportacao', 25);
            const items = bqRes?.data?.items;
            if (Array.isArray(items)) lista = items;
          } catch (e) {
            console.warn('⚠️ Autocomplete BigQuery empresas_ncm_import_export_uf (exportador):', e?.message || e);
          }
        }
        const options = lista
          .map((empresa) => {
            const nome = nomeEmpresaListaItem(empresa);
            const ops = empresa.total_operacoes ?? empresa.total ?? 0;
            const cnpj = empresa.cnpj != null && String(empresa.cnpj).trim() ? String(empresa.cnpj).trim() : '';
            const label = cnpj
              ? `${nome || 'N/A'} — ${cnpj} (${ops} reg.)`
              : `${nome || 'N/A'} (${ops} operações)`;
            return { value: nome, label };
          })
          .filter((o) => o.value);
        setExportadorasOptions(options);
      } catch (error) {
        console.error('❌ Erro ao buscar exportadoras:', error?.message || error);
        setExportadorasOptions([]);
      } finally {
        setLoadingExportadoras(false);
      }
    }, 300),
    []
  );

  // Atualizar meses quando período mudar (2024 até hoje; máx. 120 meses = 10 anos, conforme backend)
  useEffect(() => {
    if (periodo && periodo[0] && periodo[1]) {
      const mesesCalculados = Math.ceil(periodo[1].diff(periodo[0], 'month', true)) + 1;
      const mesesAjustados = Math.max(1, Math.min(120, Math.round(mesesCalculados)));
      setMeses((prevMeses) => {
        if (prevMeses !== mesesAjustados) {
          return mesesAjustados;
        }
        return prevMeses;
      });
    }
  }, [periodo]);

  const loadDashboardData = useCallback(async (overrides = {}) => {
    // Usar overrides quando vieram do clique em Buscar; caso contrário refs (evita requisição a cada mudança de estado)
    const filtroImportador = overrides.empresa_importadora !== undefined
      ? (overrides.empresa_importadora && String(overrides.empresa_importadora).trim())
      : (empresaImportadoraRef.current && String(empresaImportadoraRef.current).trim());
    const filtroExportador = overrides.empresa_exportadora !== undefined
      ? (overrides.empresa_exportadora && String(overrides.empresa_exportadora).trim())
      : (empresaExportadoraRef.current && String(empresaExportadoraRef.current).trim());
    const temFiltroEmpresa = !!(filtroImportador || filtroExportador);

    const currentRequestId = ++requestIdRef.current;
    // Se o usuário clicou em Buscar (qualquer override: empresa, período, NCM, tipo), não usar cache e não pular a requisição
    const ehBuscaComFiltro = Object.keys(overrides).length > 0;
    if (isLoadingRef.current && !ehBuscaComFiltro) {
      console.log('⚠️ Requisição já em andamento, ignorando...');
      return;
    }

    isLoadingRef.current = true;
    setLoading(true);
    setError(null);
    
    // Dashboard principal: totais e gráficos vêm só do BigQuery (sem cache local de stats).
    const cachedData = null;
    if (temFiltroEmpresa || ehBuscaComFiltro) {
      console.log('🚫 Cache desabilitado devido a filtro de empresa ou busca manual');
      // Limpar cache do localStorage quando há filtro de empresa
      try {
        localStorage.removeItem('dashboard_stats_cache');
        localStorage.removeItem('dashboard_stats_cache_timestamp');
      } catch (e) {
        console.warn('⚠️ Erro ao limpar cache:', e);
      }
      // Limpar stats antigos quando há filtro de empresa para evitar mostrar dados incorretos
      if (temFiltroEmpresa) {
        console.log('🔄 Limpando stats anteriores devido a filtro de empresa');
        setStats(null);
        // Forçar um pequeno delay para garantir que o estado seja limpo
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    }
    const cacheTimestamp = localStorage.getItem('dashboard_stats_cache_timestamp');
    if (cachedData && cacheTimestamp && !ehBuscaComFiltro) {
      const cacheAge = Date.now() - parseInt(cacheTimestamp);
      if (cacheAge < 5 * 60 * 1000) {
        try {
          const parsedCache = JSON.parse(cachedData);
          console.log('📦 Usando dados do cache (idade:', Math.round(cacheAge / 1000), 'segundos)');
          setStats(parsedCache);
          setLoading(false);
          isLoadingRef.current = false;
          return;
        } catch (e) {
          console.warn('⚠️ Erro ao ler cache, continuando com requisição...');
        }
      }
    }
    
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      // Usar múltiplos NCMs se disponível, senão usar NCM único
      const ncmParaBusca = ncmsFiltro && ncmsFiltro.length > 0 ? ncmsFiltro[0] : ncmFiltro;
      
      console.log('📊 Carregando dados do dashboard...', { 
        meses, 
        tipoOperacao, 
        ncmFiltro,
        ncmsFiltro,
        ncmParaBusca,
        apiUrl 
      });

      // Usar overrides quando fornecidos (ex.: clique em Buscar), senão state
      const dataInicioOverride = overrides.data_inicio;
      const dataFimOverride = overrides.data_fim;
      const tipoOverride = overrides.tipoOperacao !== undefined ? overrides.tipoOperacao : tipoOperacaoRef.current;
      const ncmOverride = overrides.ncm !== undefined ? overrides.ncm : ncmFiltroRef.current;
      const ncmsOverride = overrides.ncms !== undefined ? overrides.ncms : ncmsFiltroRef.current;

      const params = {
        meses: Number(overrides.meses !== undefined ? overrides.meses : mesesRef.current) || 24,
        tipoOperacao: tipoOverride || undefined,
      };
      // Enviar data_inicio e data_fim (overrides do Buscar ou período do state)
      if (dataInicioOverride && dataFimOverride && /^\d{4}-\d{2}-\d{2}$/.test(String(dataInicioOverride)) && /^\d{4}-\d{2}-\d{2}$/.test(String(dataFimOverride))) {
        params.data_inicio = dataInicioOverride;
        params.data_fim = dataFimOverride;
      } else {
        const p = periodoRef.current;
        if (p && p[0] && p[1] && p[0].isValid?.() && p[1].isValid?.()) {
          params.data_inicio = p[0].format('YYYY-MM-DD');
          params.data_fim = p[1].isAfter(dayjs()) ? dayjs().format('YYYY-MM-DD') : p[1].format('YYYY-MM-DD');
        }
      }
      
      if (ncmsOverride && ncmsOverride.length > 0) {
        params.ncms = ncmsOverride;
      } else if (ncmOverride) {
        params.ncm = ncmOverride;
      }
      
      // Filtros de empresa: mínimo de caracteres (evita consultas triviais; 2 permite siglas como VW)
      if (filtroImportador && String(filtroImportador).trim().length >= MIN_CHARS_FILTRO_EMPRESA) {
        params.empresa_importadora = String(filtroImportador).trim();
      }
      if (filtroExportador && String(filtroExportador).trim().length >= MIN_CHARS_FILTRO_EMPRESA) {
        params.empresa_exportadora = String(filtroExportador).trim();
      }
      console.log('📤 Parâmetros enviados ao backend:', { ...params });
      if (params.empresa_importadora || params.empresa_exportadora) {
        console.log('🔍 Filtro de empresa na requisição:', { empresa_importadora: params.empresa_importadora || null, empresa_exportadora: params.empresa_exportadora || null });
      }
      
      const response = await comexDashboardBqAPI.getDashboardStats(params);
      
      // Ignorar resposta se outra requisição já foi disparada (evitar sobrescrever filtro com dados antigos)
      if (currentRequestId !== requestIdRef.current) {
        setLoading(false);
        isLoadingRef.current = false;
        return;
      }
      
      console.log('✅ Dados recebidos:', response.data);
      console.log('📊 Filtros usados nesta resposta:', { empresa_importadora: params.empresa_importadora || null, empresa_exportadora: params.empresa_exportadora || null });
      console.log('💰 Valores nos dados recebidos:', { 
        valor_total_importacoes: response.data?.valor_total_importacoes, 
        valor_total_exportacoes: response.data?.valor_total_exportacoes,
        valor_total_usd: response.data?.valor_total_usd 
      });
      
      // Verificar se os valores realmente mudaram quando há filtro de empresa
      if (temFiltroEmpresa && stats) {
        const valorAnteriorImp = stats.valor_total_importacoes ?? stats.valor_total_usd ?? 0;
        const valorNovoImp = response.data?.valor_total_importacoes ?? response.data?.valor_total_usd ?? 0;
        if (Math.abs(valorAnteriorImp - valorNovoImp) < 0.01) {
          console.warn('⚠️ ATENÇÃO: Valores não mudaram após aplicar filtro de empresa!', {
            empresa: filtroImportador || filtroExportador,
            valor_anterior: valorAnteriorImp,
            valor_novo: valorNovoImp
          });
        }
      }
      
      // Validar se a resposta é válida
      if (!response || !response.data) {
        throw new Error('Resposta vazia do servidor');
      }
      
      // Verificar se não é HTML
      if (typeof response.data === 'string' && response.data.trim().startsWith('<!')) {
        console.error('❌ Resposta HTML detectada:', response.data.substring(0, 300));
        throw new Error('Servidor retornou HTML ao invés de JSON. Verifique se o backend está rodando corretamente.');
      }
      
      // Aceitar dados mesmo se estiverem vazios (banco pode não ter dados ainda)
      if (response.data) {
        // Verificar se os dados estão realmente vazios
        const dadosVazios = (
          (!response.data.volume_importacoes || response.data.volume_importacoes === 0) &&
          (!response.data.volume_exportacoes || response.data.volume_exportacoes === 0) &&
          (!response.data.valor_total_usd || response.data.valor_total_usd === 0) &&
          (!response.data.principais_ncms || response.data.principais_ncms.length === 0) &&
          (!response.data.principais_paises || response.data.principais_paises.length === 0)
        );
        
        const respostaComAvisoEmpresa = Boolean(
          response.data.kpis_empresa_indisponiveis ||
          response.data.aviso_dados_sem_empresa ||
          response.data.filtro_empresa_aplicado
        );

        if (dadosVazios && !respostaComAvisoEmpresa) {
          console.log('⚠️ Dados vazios recebidos do backend');
          // Definir stats vazio mas válido
          const emptyStats = {
            volume_importacoes: 0,
            volume_exportacoes: 0,
            valor_total_usd: 0,
            valor_total_importacoes: null,
            valor_total_exportacoes: null,
            principais_ncms: [],
            principais_paises: [],
            registros_por_mes: {},
            valores_por_mes: {},
            pesos_por_mes: {}
          };
          setStats(emptyStats);
          // Não cachear dados vazios
        } else {
          // SEMPRE atualizar stats com os novos dados recebidos (força atualização mesmo se parecer igual)
          // Criar um novo objeto para forçar re-render do React
          const novosStats = {
            ...response.data,
            _timestamp: Date.now(),
            _filtro_empresa: filtroImportador || filtroExportador || null
          };
          // Resetar sugestão ao receber novos dados
          setSugestaoComex(null);
          console.log('🔄 Atualizando stats com novos dados:', {
            valor_total_importacoes: novosStats.valor_total_importacoes,
            valor_total_exportacoes: novosStats.valor_total_exportacoes,
            filtro_empresa: filtroImportador || filtroExportador || 'nenhum',
            timestamp: novosStats._timestamp
          });
          // Forçar atualização do estado mesmo se os valores parecerem iguais
          setStats(null); // Limpar primeiro
          await new Promise(resolve => setTimeout(resolve, 10)); // Pequeno delay
          setStats(novosStats); // Depois atualizar com novos dados
          
          console.log('📊 Stats BigQuery aplicados (cache local desativado).');
        }
      } else {
        // Fallback: definir stats vazio se resposta não tiver data
        setStats({
          volume_importacoes: 0,
          volume_exportacoes: 0,
          valor_total_usd: 0,
          valor_total_importacoes: null,
          valor_total_exportacoes: null,
          principais_ncms: [],
          principais_paises: [],
          registros_por_mes: {},
          valores_por_mes: {},
          pesos_por_mes: {}
        });
      }
    } catch (err) {
      if (currentRequestId !== requestIdRef.current) {
        setLoading(false);
        isLoadingRef.current = false;
        return;
      }
      let errorMessage = 'Erro ao carregar dados do dashboard';
      
      if (err.response) {
        // Erro do servidor
        if (err.response.data) {
          if (typeof err.response.data === 'string' && err.response.data.includes('<!')) {
            errorMessage = 'Servidor retornou HTML ao invés de JSON. Verifique se o backend está rodando corretamente.';
          } else if (err.response.data.detail !== undefined) {
            const d = err.response.data.detail;
            errorMessage = typeof d === 'string' ? d : (Array.isArray(d) ? d.map(x => x?.msg || JSON.stringify(x)).join(', ') : JSON.stringify(d));
          } else if (typeof err.response.data === 'string') {
            errorMessage = err.response.data;
          }
        } else {
          errorMessage = `Erro ${err.response.status}: ${err.response.statusText}`;
        }
      } else if (err.request) {
        // Sem fallback em localStorage: o cache antigo era de /dashboard/stats (PostgreSQL) e misturava com o dashboard só BigQuery.
        const apiUrl = process.env.REACT_APP_API_URL || 'https://comex-backend-gecp.onrender.com';
        errorMessage = `Não foi possível conectar ao servidor em ${apiUrl}. O backend pode estar temporariamente indisponível ou em modo sleep. Tente novamente em alguns instantes.`;
      } else {
        // Outro erro
        errorMessage = err.message || 'Erro desconhecido';
      }
      
      // Não mostrar erro se for apenas falta de dados (404 ou banco vazio)
      if (err.response?.status === 404 || err.response?.status === 200) {
        // Banco pode estar vazio, não é um erro crítico
        setError(null);
        setStats({
          volume_importacoes: 0,
          volume_exportacoes: 0,
          valor_total_usd: 0,
          quantidade_estatistica_importacoes: 0,
          quantidade_estatistica_exportacoes: 0,
          quantidade_estatistica_total: 0,
          principais_ncms: [],
          principais_paises: [],
          registros_por_mes: {},
          valores_por_mes: {},
          pesos_por_mes: {}
        });
      } else {
        if (err.response?.status === 503) {
          const detail = err.response?.data?.detail;
          setError(detail || 'Serviço temporariamente indisponível. Tente novamente em alguns segundos.');
        } else {
          setError(`Erro ao carregar dados do dashboard: ${errorMessage}`);
        }

        console.error('❌ Erro completo:', err);
        console.error('❌ Detalhes:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status,
          url: err.config?.url,
          code: err.code
        });
      }
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
      searchInProgressRef.current = false; // Buscar concluído; próximo useEffect pode rodar de novo
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.removeItem('dashboard_stats_cache');
      localStorage.removeItem('dashboard_stats_cache_timestamp');
    } catch (e) {
      /* ignorar */
    }
    loadDashboardData();
    // Carga inicial apenas; demais atualizações via botão Buscar / Limpar
  }, []);

  // Carregar empresas recomendadas quando stats carregar
  useEffect(() => {
    const loadEmpresasRecomendadas = async () => {
      try {
        // Carregar empresas importadoras
        const impData = await empresasRecomendadasAPI.getEmpresasImportadoras(10);
        if (impData.success && impData.data) {
          setEmpresasImportadorasRecomendadas(impData.data);
        }

        // Carregar empresas exportadoras
        const expData = await empresasRecomendadasAPI.getEmpresasExportadoras(10);
        if (expData.success && expData.data) {
          setEmpresasExportadorasRecomendadas(expData.data);
        }
      } catch (error) {
        console.error('Erro ao carregar empresas recomendadas:', error);
      }
    };

    if (stats) {
      loadEmpresasRecomendadas();
    }
  }, [stats]);

  // Função para carregar empresas recomendadas
  const loadEmpresasRecomendadas = useCallback(async () => {
    setLoadingEmpresasRecomendadas(true);
    try {
      const data = await empresasRecomendadasAPI.getEmpresasRecomendadas(100);
      if (data.success && data.data) {
        setEmpresasRecomendadas(data.data);
      }
    } catch (error) {
      console.error('Erro ao carregar empresas recomendadas:', error);
      setEmpresasRecomendadas([]);
    } finally {
      setLoadingEmpresasRecomendadas(false);
    }
  }, []);

  // Função para carregar dados ComexStat
  const loadDadosComexstat = useCallback(async () => {
    setLoadingDadosComexstat(true);
    try {
      const data = await comexstatAPI.getDadosComexstat();
      if (data.success && data.data) {
        setDadosComexstat(data.data);
      }
    } catch (error) {
      console.error('Erro ao carregar dados ComexStat:', error);
      setDadosComexstat(null);
    } finally {
      setLoadingDadosComexstat(false);
    }
  }, []);

  // Carregar dados gerais ao montar componente
  useEffect(() => {
    loadEmpresasRecomendadas();
    loadDadosComexstat();
  }, [loadEmpresasRecomendadas, loadDadosComexstat]);

  const handleSearch = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    // Usar refs como fonte principal (atualizados a cada digitação); DOM como fallback
    let importadorVal = (importadorInputRef.current != null && importadorInputRef.current !== undefined)
      ? String(importadorInputRef.current).trim()
      : (empresaImportadoraInput || empresaImportadora || '').toString().trim();
    let exportadorVal = (exportadorInputRef.current != null && exportadorInputRef.current !== undefined)
      ? String(exportadorInputRef.current).trim()
      : (empresaExportadoraInput || empresaExportadora || '').toString().trim();
    const impDom = lerInputEmpresaNoDom('empresa-importadora');
    const expDom = lerInputEmpresaNoDom('empresa-exportadora');
    if (impDom) importadorVal = impDom;
    if (expDom) exportadorVal = expDom;

    const tinhaTextoImp = !!(importadorVal && String(importadorVal).trim());
    const tinhaTextoExp = !!(exportadorVal && String(exportadorVal).trim());
    if (
      (tinhaTextoImp && String(importadorVal).trim().length < MIN_CHARS_FILTRO_EMPRESA) ||
      (tinhaTextoExp && String(exportadorVal).trim().length < MIN_CHARS_FILTRO_EMPRESA)
    ) {
      message.warning(
        `Informe pelo menos ${MIN_CHARS_FILTRO_EMPRESA} caracteres em Provável Importador ou Exportador para aplicar o filtro.`
      );
    }
    setEmpresaImportadora(importadorVal || null);
    setEmpresaExportadora(exportadorVal || null);
    setEmpresaImportadoraInput(importadorVal);
    setEmpresaExportadoraInput(exportadorVal);
    importadorInputRef.current = importadorVal;
    exportadorInputRef.current = exportadorVal;

    // Limpar cache ANTES de buscar para garantir dados atualizados
    try {
      localStorage.removeItem('dashboard_stats_cache');
      localStorage.removeItem('dashboard_stats_cache_timestamp');
      console.log('🗑️ Cache limpo antes da busca');
    } catch (e) {
      console.warn('⚠️ Erro ao limpar cache:', e);
    }
    
    // Montar overrides com TODOS os filtros visíveis para garantir que cards/gráficos usem exatamente o que está na tela
    const overrides = {
      empresa_importadora: importadorVal || undefined,
      empresa_exportadora: exportadorVal || undefined,
      tipoOperacao: tipoOperacao || undefined,
      ncm: ncmFiltro || undefined,
      ncms: (ncmsFiltro && ncmsFiltro.length > 0) ? ncmsFiltro : undefined,
    };
    if (periodo && periodo[0] && periodo[1] && periodo[0].isValid?.() && periodo[1].isValid?.()) {
      overrides.data_inicio = periodo[0].format('YYYY-MM-DD');
      overrides.data_fim = periodo[1].isAfter(dayjs()) ? dayjs().format('YYYY-MM-DD') : periodo[1].format('YYYY-MM-DD');
    }
    console.log('🔍 Buscar com filtros:', overrides);
    console.log('📋 Valores dos inputs:', { importadorVal, exportadorVal });
    
    // Limpar stats antes de buscar para evitar mostrar dados antigos
    setStats(null);
    searchInProgressRef.current = true; // Evita que o useEffect dispare outra requisição e sobrescreva o resultado
    loadDashboardData(overrides);
  };

  const loadTabelaDados = useCallback(async (page = 1, pageSize = 10) => {
    setLoadingTabela(true);
    try {
      const filtros = {
        page,
        page_size: pageSize,
        meses: mesesRef.current != null ? Number(mesesRef.current) : 24,
      };

      // Adicionar filtros de data
      if (periodo && periodo[0] && periodo[1]) {
        filtros.data_inicio = periodo[0].format('YYYY-MM-DD');
        filtros.data_fim = periodo[1].isAfter(dayjs())
          ? dayjs().format('YYYY-MM-DD')
          : periodo[1].format('YYYY-MM-DD');
      }

      // Adicionar filtro de tipo de operação
      if (tipoOperacao) {
        filtros.tipo_operacao = tipoOperacao;
      }

      // Adicionar filtros de NCMs
      if (ncmsFiltro && ncmsFiltro.length > 0) {
        filtros.ncms = ncmsFiltro;
      } else if (ncmFiltro) {
        filtros.ncms = [ncmFiltro];
      }

      // Adicionar filtros de empresa (mesmo mínimo de caracteres que o carregamento dos stats)
      const ei = empresaImportadora && String(empresaImportadora).trim();
      const ee = empresaExportadora && String(empresaExportadora).trim();
      if (ei && ei.length >= MIN_CHARS_FILTRO_EMPRESA) {
        filtros.empresa_importadora = ei;
      }
      if (ee && ee.length >= MIN_CHARS_FILTRO_EMPRESA) {
        filtros.empresa_exportadora = ee;
      }

      const response = await comexDashboardBqAPI.getTabelaDetalhada(filtros);
      
      if (response && response.data) {
        setTabelaDados(response.data.results || []);
        setPaginacaoTabela({
          current: response.data.page || page,
          pageSize: response.data.page_size || pageSize,
          total: response.data.total || 0,
        });
      }
    } catch (err) {
      console.error('Erro ao carregar dados da tabela:', err);
      setTabelaDados([]);
    } finally {
      setLoadingTabela(false);
    }
  }, [periodo, tipoOperacao, ncmFiltro, ncmsFiltro, empresaImportadora, empresaExportadora, meses]);

  useEffect(() => {
    if (stats) {
      loadTabelaDados(1, 10);
    }
  }, [stats, loadTabelaDados]);

  const handleClearFilters = () => {
    setTipoOperacao(null);
    setNcmFiltro(null);
    setNcmsFiltro([]);
    setEmpresaImportadora(null);
    setEmpresaExportadora(null);
    setEmpresaImportadoraInput('');
    setEmpresaExportadoraInput('');
    importadorInputRef.current = '';
    exportadorInputRef.current = '';
    setPeriodo([dayjs('2024-01-01'), dayjs()]);
    setMeses(Math.min(120, dayjs().diff(dayjs('2024-01-01'), 'month') + 1));
    loadDashboardData();
  };

  // Não mostrar loading infinito - sempre mostrar o dashboard mesmo se vazio
  if (loading && !stats) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px', color: '#666' }}>
          Carregando dados do dashboard...
        </div>
      </div>
    );
  }

  // Garantir que stats sempre tenha estrutura válida
  const statsFinal = stats || {
    volume_importacoes: 0,
    volume_exportacoes: 0,
    valor_total_usd: 0,
    valor_total_importacoes: 0,
    valor_total_exportacoes: 0,
    quantidade_estatistica_importacoes: 0,
    quantidade_estatistica_exportacoes: 0,
    quantidade_estatistica_total: 0,
    valor_provavel_empresas: null,
    principais_ncms: [],
    principais_paises: [],
    principais_importadores: [],
    principais_exportadores: [],
    registros_por_mes: {},
    valores_por_mes: {},
    pesos_por_mes: {}
  };
  const principaisPaises = statsFinal.principais_paises || [];
  const principaisImportadores = statsFinal.principais_importadores || [];
  const principaisExportadores = statsFinal.principais_exportadores || [];
  const principaisNcms = statsFinal.principais_ncms || [];

  // Se houver erro mas não tiver stats, mostrar erro mas continuar renderizando
  if (error && !stats) {
    return (
      <div style={{ padding: '20px' }}>
        <Alert 
          message="Erro ao carregar dados" 
          description={error}
          type="error" 
          showIcon 
          style={{ marginBottom: '16px' }}
          action={
            <Button size="small" onClick={loadDashboardData}>
              Tentar Novamente
            </Button>
          }
        />
        {/* Continuar renderizando dashboard mesmo com erro */}
      </div>
    );
  }

  // Lista completa de meses do período para todos os gráficos (desde jan/2024 até fim do período)
  const mesesDoPeriodoCompleto = (() => {
    if (!periodo || !periodo[0] || !periodo[1]) return [];
    const inicioMinimo = dayjs('2024-01-01').startOf('month');
    const start = dayjs(periodo[0]).startOf('month').isBefore(inicioMinimo) ? inicioMinimo : dayjs(periodo[0]).startOf('month');
    const end = dayjs(periodo[1]).startOf('month');
    const meses = [];
    let cur = start;
    while (cur.isBefore(end) || cur.isSame(end, 'month')) {
      meses.push(cur.format('YYYY-MM'));
      cur = cur.add(1, 'month');
    }
    return meses;
  })();

  // Preparar dados para gráficos (todos os meses do período, com 0 quando não houver dado)
  const evolucaoData = mesesDoPeriodoCompleto.length > 0
    ? mesesDoPeriodoCompleto.map((mes) => {
        const [ano, mesNum] = mes.split('-');
        const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
        const count = (statsFinal.registros_por_mes || {})[mes] ?? 0;
        return { mes: mesFormatado, registros: count };
      })
    : [];

  // Dados para gráfico combinado (FOB e Peso) - todos os meses do período
  const tendenciasData = mesesDoPeriodoCompleto.length > 0
    ? mesesDoPeriodoCompleto.map((mes) => {
        const [ano, mesNum] = mes.split('-');
        const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
        const valorMensal = statsFinal.valores_por_mes?.[mes] || 0;
        const pesoMensal = statsFinal.pesos_por_mes?.[mes] || 0;
        return { mes: mesFormatado, fob: valorMensal, peso: pesoMensal };
      })
    : [];

  // Só mostra a linha/eixo de peso quando há dados de peso (estimativa não tem)
  const temPesoTendencias = tendenciasData.some((d) => (d.peso || 0) > 0);

  // Top Importadores (quando há filtro por empresa, mostrar a empresa filtrada; senão lista geral)
  // Nome da empresa filtrada (independente de estar no campo importador ou exportador)
  const nomeEmpresaFiltro = (empresaImportadora || empresaImportadoraInput || empresaExportadora || empresaExportadoraInput || '').toString().trim();
  const temFiltroEmpresa = Boolean(nomeEmpresaFiltro);

  const topImportadores = (() => {
    if (!statsFinal) return [];

    // Empresa filtrada → mostra a própria empresa com o valor de IMPORTAÇÃO
    if (temFiltroEmpresa && !statsFinal.kpis_empresa_indisponiveis) {
      const valorImp = statsFinal.valor_total_importacoes ?? 0;
      const pesoImp = statsFinal.volume_importacoes ?? 0;
      return [{
        cor: COLORS[0],
        nome: nomeEmpresaFiltro.length > 50 ? nomeEmpresaFiltro.substring(0, 50) + '...' : nomeEmpresaFiltro,
        fob: Number(valorImp) || 0,
        peso: Number(pesoImp) || 0,
        percentual: 100,
      }];
    }

    if (principaisImportadores && principaisImportadores.length > 0) {
      const valorTotalUsd = statsFinal.valor_total_usd || 1;
      return principaisImportadores
        .slice(0, 10)
        .map((emp, idx) => {
          const valorTotal = emp.valor_total || 0;
          const pesoTotal = emp.peso_total || 0;
          return {
            cor: COLORS[idx % COLORS.length],
            nome: String(emp.nome || 'N/A'),
            fob: Number(valorTotal) || 0,
            peso: Number(pesoTotal) || 0,
            percentual: valorTotalUsd > 0 ? ((valorTotal / valorTotalUsd) * 100) : 0,
          };
        });
    }
    
    if (empresasImportadorasRecomendadas.length > 0) {
      const volumeTotal = statsFinal.volume_importacoes || 0;
      const valorTotalUsd = statsFinal.valor_total_usd || 1;
      return empresasImportadorasRecomendadas
        .slice(0, 5)
        .map((empresa, idx) => {
          const valorTotal = empresa.valor_total || empresa.importado_rs || 0;
          const pesoKg = Number(empresa.peso_kg);
          const pesoProporcional = valorTotalUsd > 0 ? (volumeTotal * (valorTotal / valorTotalUsd)) : 0;
          return {
            cor: COLORS[idx % COLORS.length],
            nome: String(empresa.nome || empresa.pais || empresa.razao_social || 'N/A'),
            fob: Number(valorTotal) || 0,
            peso: (pesoKg > 0 ? pesoKg : pesoProporcional) || 0,
            percentual: valorTotalUsd > 0 ? ((valorTotal / valorTotalUsd) * 100) : 0,
          };
        });
    }
    
    if (principaisPaises && Array.isArray(principaisPaises)) {
      return principaisPaises
        .filter((_, idx) => idx < 5)
        .map((pais, idx) => {
          const valorTotal = pais.valor_total || 0;
          const valorTotalUsd = statsFinal.valor_total_usd || 1;
          return {
            cor: COLORS[idx % COLORS.length],
            nome: String(pais.pais || 'N/A'),
            fob: Number(valorTotal) || 0,
            peso: Number((statsFinal.volume_importacoes || 0) * (valorTotal / valorTotalUsd)) || 0,
            percentual: valorTotalUsd > 0 ? ((valorTotal / valorTotalUsd) * 100) : 0,
          };
        });
    }
    
    return [];
  })();

  // Top Exportadores (quando há filtro por empresa, mostrar a empresa filtrada; senão lista geral)
  const topExportadores = (() => {
    if (!statsFinal) return [];

    // Empresa filtrada → mostra a própria empresa com o valor de EXPORTAÇÃO
    if (temFiltroEmpresa && !statsFinal.kpis_empresa_indisponiveis) {
      const valorExp = statsFinal.valor_total_exportacoes ?? 0;
      const pesoExp = statsFinal.volume_exportacoes ?? 0;
      return [{
        cor: COLORS[0],
        nome: nomeEmpresaFiltro.length > 50 ? nomeEmpresaFiltro.substring(0, 50) + '...' : nomeEmpresaFiltro,
        fob: Number(valorExp) || 0,
        peso: Number(pesoExp) || 0,
        percentual: 100,
      }];
    }

    if (principaisExportadores && principaisExportadores.length > 0) {
      const valorTotalUsd = statsFinal.valor_total_usd || 1;
      return principaisExportadores
        .slice(0, 10)
        .map((emp, idx) => {
          const valorTotal = emp.valor_total || 0;
          const pesoTotal = emp.peso_total || 0;
          return {
            cor: COLORS[idx % COLORS.length],
            nome: String(emp.nome || 'N/A'),
            fob: Number(valorTotal) || 0,
            peso: Number(pesoTotal) || 0,
            percentual: valorTotalUsd > 0 ? ((valorTotal / valorTotalUsd) * 100) : 0,
          };
        });
    }
    
    if (empresasExportadorasRecomendadas.length > 0) {
      const volumeTotal = statsFinal.volume_exportacoes || 0;
      const valorTotalUsd = statsFinal.valor_total_usd || 1;
      return empresasExportadorasRecomendadas
        .slice(0, 5)
        .map((empresa, idx) => {
          const valorTotal = empresa.valor_total || empresa.exportado_rs || 0;
          const pesoKg = Number(empresa.peso_kg);
          const pesoProporcional = valorTotalUsd > 0 ? (volumeTotal * (valorTotal / valorTotalUsd)) : 0;
          return {
            cor: COLORS[idx % COLORS.length],
            nome: String(empresa.nome || empresa.pais || empresa.razao_social || 'N/A'),
            fob: Number(valorTotal) || 0,
            peso: (pesoKg > 0 ? pesoKg : pesoProporcional) || 0,
            percentual: valorTotalUsd > 0 ? ((valorTotal / valorTotalUsd) * 100) : 0,
          };
        });
    }
    
    if (principaisPaises && Array.isArray(principaisPaises)) {
      return principaisPaises
        .filter((_, idx) => idx < 5)
        .map((pais, idx) => {
          const valorTotal = pais.valor_total || 0;
          const valorTotalUsd = statsFinal.valor_total_usd || 1;
          return {
            cor: COLORS[idx % COLORS.length],
            nome: String(pais.pais || 'N/A'),
            fob: Number(valorTotal) || 0,
            peso: Number((statsFinal.volume_exportacoes || 0) * (valorTotal / valorTotalUsd)) || 0,
            percentual: valorTotalUsd > 0 ? ((valorTotal / valorTotalUsd) * 100) : 0,
          };
        });
    }
    
    return [];
  })();

  // Dados para gráfico de linha de importadores/exportadores ao longo do tempo
  // Usar TODOS os meses do período (incluindo 2024) com valor 0 quando não houver dado
  // Mapas mensais separados por imp/exp (presentes na estimativa). Fallback ao
  // combinado × percentual quando não houver (dados reais legados).
  const temSerieImpExp = Boolean(
    statsFinal && (statsFinal.valores_imp_por_mes || statsFinal.valores_exp_por_mes)
  );
  const importadoresTempoData = statsFinal && mesesDoPeriodoCompleto.length > 0
    ? mesesDoPeriodoCompleto.map((mes) => {
        const [ano, mesNum] = mes.split('-');
        const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
        const valorImpMes = temSerieImpExp
          ? (statsFinal.valores_imp_por_mes?.[mes] || 0)
          : (statsFinal.valores_por_mes?.[mes] || 0);
        const data = { mes: mesFormatado };
        topImportadores.forEach((imp, idx) => {
          const percentual = temSerieImpExp ? 1 : (imp.percentual || 0) / 100;
          data[`imp_${idx}`] = valorImpMes * percentual;
        });
        return data;
      })
    : [];

  const exportadoresTempoData = statsFinal && mesesDoPeriodoCompleto.length > 0
    ? mesesDoPeriodoCompleto.map((mes) => {
        const [ano, mesNum] = mes.split('-');
        const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
        const valorExpMes = temSerieImpExp
          ? (statsFinal.valores_exp_por_mes?.[mes] || 0)
          : (statsFinal.valores_por_mes?.[mes] || 0);
        const data = { mes: mesFormatado };
        topExportadores.forEach((exp, idx) => {
          const percentual = temSerieImpExp ? 1 : (exp.percentual || 0) / 100;
          data[`exp_${idx}`] = valorExpMes * percentual;
        });
        return data;
      })
    : [];

  // Key estável para forçar remount dos gráficos ao mudar filtro (evita getBoundingClientRect em null)
  const chartKey = `charts-${empresaImportadora || ''}-${empresaExportadora || ''}-${topImportadores.length}-${topExportadores.length}`;

  // Formatar valores
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatWeight = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatQuantity = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const quantidadeImportacoes = Number(statsFinal.quantidade_estatistica_importacoes) || 0;
  const quantidadeExportacoes = Number(statsFinal.quantidade_estatistica_exportacoes) || 0;
  const quantidadeTotal = tipoOperacao === 'Importação'
    ? quantidadeImportacoes
    : tipoOperacao === 'Exportação'
      ? quantidadeExportacoes
      : (Number(statsFinal.quantidade_estatistica_total) || quantidadeImportacoes + quantidadeExportacoes);

  const pesoTotal = tipoOperacao === 'Importação'
    ? (statsFinal.volume_importacoes || 0)
    : tipoOperacao === 'Exportação'
      ? (statsFinal.volume_exportacoes || 0)
      : ((statsFinal.volume_importacoes || 0) + (statsFinal.volume_exportacoes || 0));

  // Seções globais (sinergias, sugestões, recomendadas, dados gerais) não
  // respondem ao filtro de empresa — escondê-las quando uma empresa está filtrada.
  const filtroEmpresaAtivo = Boolean(
    (empresaImportadora || '').toString().trim() || (empresaExportadora || '').toString().trim()
  );

  return (
    <div style={{ padding: isMobile ? '8px' : 'clamp(8px, 2vw, 24px)', background: '#f5f5f5', minHeight: '100vh' }}>
      {/* Barra de Filtros */}
      <Card 
        style={{ marginBottom: isMobile ? '12px' : 'clamp(12px, 3vw, 24px)', borderRadius: '8px' }}
        bodyStyle={{ padding: isMobile ? '12px' : 'clamp(8px, 2vw, 16px)' }}
      >
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <RangePicker
              style={{ width: '100%' }}
              value={periodo}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  const fim = dates[1].isAfter(dayjs()) ? dayjs() : dates[1];
                  setPeriodo([dates[0], fim]);
                  const diff = Math.ceil(fim.diff(dates[0], 'month', true)) + 1;
                  setMeses(Math.max(1, Math.min(84, Math.round(diff))));
                } else {
                  setPeriodo(dates);
                }
              }}
              format="DD/MM/YYYY"
              placeholder={['Data Início', 'Data Fim']}
              disabledDate={(current) => current && current.isAfter(dayjs(), 'day')}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Tipo de Operação"
              value={tipoOperacao}
              onChange={setTipoOperacao}
              allowClear
            >
              <Option value="Importação">Importação</Option>
              <Option value="Exportação">Exportação</Option>
            </Select>
          </Col>
        </Row>
        <Row gutter={[16, 16]} align="middle" style={{ marginTop: '16px' }}>
          <Col xs={24} sm={24} md={12} lg={8} style={{ minWidth: 0 }}>
            <div data-filter="empresa-importadora" style={{ minWidth: 0 }}>
            <AutoComplete
              style={{ width: '100%', minWidth: 0 }}
              placeholder="Provável Importador"
              dropdownStyle={{ maxWidth: 'min(100vw - 32px, 400px)' }}
              value={empresaImportadoraInput !== '' ? empresaImportadoraInput : (empresaImportadora ?? '')}
              onFocus={() => {
                if (importadorasOptions.length === 0) buscarImportadoras(empresaImportadoraInput || '');
              }}
              onChange={(value) => {
                const v = value == null ? '' : String(value);
                importadorInputRef.current = v;
                setEmpresaImportadoraInput(v);
                setEmpresaImportadora(v.trim() ? v : null);
                if (v.trim()) buscarImportadoras(v);
                else setImportadorasOptions([]);
              }}
              onSearch={(text) => {
                const t = text == null ? '' : String(text);
                importadorInputRef.current = t;
                setEmpresaImportadoraInput(t);
                buscarImportadoras(t);
              }}
              onSelect={(value) => {
                const v = (value == null ? '' : String(value)).trim();
                importadorInputRef.current = v;
                // Marcar busca em progresso ANTES de atualizar estados para evitar que useEffect interfira
                searchInProgressRef.current = true;
                setEmpresaImportadoraInput(v);
                setEmpresaImportadora(v || null);
                if (v) {
                  const overrides = {
                    empresa_importadora: v,
                    empresa_exportadora: empresaExportadora || undefined,
                    tipoOperacao: tipoOperacao || undefined,
                    ncm: ncmFiltro || undefined,
                    ncms: (ncmsFiltro && ncmsFiltro.length > 0) ? ncmsFiltro : undefined,
                  };
                  if (periodo && periodo[0] && periodo[1] && periodo[0].isValid?.() && periodo[1].isValid?.()) {
                    overrides.data_inicio = periodo[0].format('YYYY-MM-DD');
                    overrides.data_fim = periodo[1].isAfter(dayjs()) ? dayjs().format('YYYY-MM-DD') : periodo[1].format('YYYY-MM-DD');
                  }
                  console.log('🔍 Seleção de empresa importadora:', v, 'Overrides:', overrides);
                  loadDashboardData(overrides);
                } else {
                  searchInProgressRef.current = false;
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearch(e);
              }}
              options={importadorasOptions}
              notFoundContent={loadingImportadoras ? <Spin size="small" /> : 'Nenhuma empresa encontrada'}
              allowClear
              filterOption={() => true}
            />
            </div>
          </Col>
          <Col xs={24} sm={24} md={12} lg={8} style={{ minWidth: 0 }}>
            <div data-filter="empresa-exportadora" style={{ minWidth: 0 }}>
            <AutoComplete
              style={{ width: '100%', minWidth: 0 }}
              placeholder="Provável Exportador"
              dropdownStyle={{ maxWidth: 'min(100vw - 32px, 400px)' }}
              value={empresaExportadoraInput !== '' ? empresaExportadoraInput : (empresaExportadora ?? '')}
              onFocus={() => {
                if (exportadorasOptions.length === 0) buscarExportadoras(empresaExportadoraInput || '');
              }}
              onChange={(value) => {
                const v = value == null ? '' : String(value);
                exportadorInputRef.current = v;
                setEmpresaExportadoraInput(v);
                setEmpresaExportadora(v.trim() ? v : null);
                if (v.trim()) buscarExportadoras(v);
                else setExportadorasOptions([]);
              }}
              onSearch={(text) => {
                const t = text == null ? '' : String(text);
                exportadorInputRef.current = t;
                setEmpresaExportadoraInput(t);
                buscarExportadoras(t);
              }}
              onSelect={(value) => {
                const v = (value == null ? '' : String(value)).trim();
                exportadorInputRef.current = v;
                // Marcar busca em progresso ANTES de atualizar estados para evitar que useEffect interfira
                searchInProgressRef.current = true;
                setEmpresaExportadoraInput(v);
                setEmpresaExportadora(v || null);
                if (v) {
                  const overrides = {
                    empresa_exportadora: v,
                    empresa_importadora: empresaImportadora || undefined,
                    tipoOperacao: tipoOperacao || undefined,
                    ncm: ncmFiltro || undefined,
                    ncms: (ncmsFiltro && ncmsFiltro.length > 0) ? ncmsFiltro : undefined,
                  };
                  if (periodo && periodo[0] && periodo[1] && periodo[0].isValid?.() && periodo[1].isValid?.()) {
                    overrides.data_inicio = periodo[0].format('YYYY-MM-DD');
                    overrides.data_fim = periodo[1].isAfter(dayjs()) ? dayjs().format('YYYY-MM-DD') : periodo[1].format('YYYY-MM-DD');
                  }
                  console.log('🔍 Seleção de empresa exportadora:', v, 'Overrides:', overrides);
                  loadDashboardData(overrides);
                } else {
                  searchInProgressRef.current = false;
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearch(e);
              }}
              options={exportadorasOptions}
              notFoundContent={loadingExportadoras ? <Spin size="small" /> : 'Nenhuma empresa encontrada'}
              allowClear
              filterOption={() => true}
            />
            </div>
          </Col>
          <Col xs={24} sm={24} md={24} lg={8} style={{ marginTop: isMobile ? '8px' : 0 }}>
            <Space wrap size="small">
              <Button 
                type="button"
                htmlType="button"
                icon={<SearchOutlined />} 
                onClick={handleSearch}
                style={{ background: '#722ed1', borderColor: '#722ed1', minWidth: isMobile ? '100%' : undefined }}
              >
                Buscar
              </Button>
              <Button 
                type="button" 
                htmlType="button" 
                icon={<ReloadOutlined />} 
                onClick={handleClearFilters}
                style={{ minWidth: isMobile ? '100%' : undefined }}
              >
                Limpar Filtros
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {error && (
        <Alert 
          message={error} 
          type="error" 
          showIcon 
          style={{ marginBottom: '24px' }}
          closable
          onClose={() => setError(null)}
        />
      )}

      {stats && !error && !stats.kpis_empresa_indisponiveis && (empresaImportadora || empresaExportadora || ncmFiltro || (ncmsFiltro && ncmsFiltro.length > 0)) &&
        (stats.valor_total_importacoes ?? 0) === 0 && (stats.valor_total_exportacoes ?? 0) === 0 && (stats.valor_total_usd ?? 0) === 0 && (
          <Alert
            message="Nenhuma operação encontrada para os filtros aplicados."
            description={
              'Confira o período, o NCM (8 dígitos) e o nome da empresa. Cards, gráficos e tabela desta página vêm exclusivamente do BigQuery (tabela empresas_ncm_import_export_uf). ' +
              'Configure GOOGLE_APPLICATION_CREDENTIALS ou GOOGLE_APPLICATION_CREDENTIALS_JSON no backend e permissão de leitura na tabela.'
            }
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />
        )}

      {stats && !error && stats.kpis_empresa_indisponiveis && stats.filtro_empresa_aplicado && (
        <Alert
          message="Valores por empresa indisponíveis nesta fonte"
          description={stats.aviso_dados_sem_empresa}
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {stats && !error && stats.aviso_dados_sem_empresa && stats.filtro_empresa_aplicado && !stats.kpis_empresa_indisponiveis && !stats.dados_empresa_reais && stats.fonte_valores !== 'estimado' && (
        <Alert
          message={
            Array.isArray(stats.ufs_filtradas_por_empresa) && stats.ufs_filtradas_por_empresa.length > 0
              ? `Atenção: os valores abaixo são TOTAIS DA(S) UF(S) ${stats.ufs_filtradas_por_empresa.join(', ')}, não da empresa filtrada`
              : 'Atenção: valores agregados por UF, não por empresa'
          }
          description={stats.aviso_dados_sem_empresa}
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Painel de Sugestão Estatística — visível quando empresa sem dados CNPJ */}
      {stats?.kpis_empresa_indisponiveis && (empresaImportadora || empresaExportadora) && (
        <SugestaoComexPanel
          stats={stats}
          sugestao={sugestaoComex}
          loading={loadingSugestao}
          onBuscar={async () => {
            const cnpjHint = stats.cnpj_hint;
            if (!cnpjHint && !stats.cnae_hint) return;
            setLoadingSugestao(true);
            setSugestaoComex(null);
            try {
              // Se temos CNPJ, buscar sugestão por CNPJ (usa CNAE da empresa)
              if (cnpjHint) {
                const res = await api.get(`/api/contatos/empresa/${encodeURIComponent(cnpjHint)}/sugestao`);
                setSugestaoComex(res.data);
              }
            } catch (e) {
              message.error('Erro ao carregar sugestão de potencial.');
            } finally {
              setLoadingSugestao(false);
            }
          }}
        />
      )}

      {/* Cards de Métricas Principais */}
      {stats?.kpis_empresa_indisponiveis && (empresaImportadora || empresaExportadora) ? null : null}
      <Row gutter={[8, 8]} style={{ marginBottom: 'clamp(12px, 3vw, 24px)', display: stats?.kpis_empresa_indisponiveis && (empresaImportadora || empresaExportadora) ? 'none' : undefined }} key={`cards-${empresaImportadora || ''}-${empresaExportadora || ''}-${stats?._timestamp || 0}`}>
        <Col xs={24} sm={12} lg={8}>
          <Card 
            className="dashboard-metric-card"
            key={`card-importacoes-${stats?._timestamp || 0}-${stats?.valor_total_importacoes || 0}`}
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: 'clamp(12px, 3vw, 24px)', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ flex: '1', minWidth: 0 }}>
                <div className="metric-title" style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px', marginBottom: '4px' }}>
                  Valor Importações
                </div>
                <div className="metric-value" style={{ 
                  color: '#fff', 
                  fontSize: isMobile ? 'clamp(18px, 5vw, 24px)' : 'clamp(16px, 4vw, 22px)', 
                  fontWeight: 'bold', 
                  lineHeight: '1.2', 
                  wordBreak: 'break-word',
                  whiteSpace: 'normal',
                  overflow: 'visible',
                }}>
                  {formatCurrency(
                    tipoOperacao === 'Exportação' ? 0 :
                    (statsFinal?.valor_total_importacoes != null && statsFinal.valor_total_importacoes !== undefined
                      ? statsFinal.valor_total_importacoes
                      : (tipoOperacao === 'Importação' ? (statsFinal?.valor_total_usd ?? 0) : 0))
                  )}
                </div>
                <div style={{ 
                  color: 'rgba(255,255,255,0.7)', 
                  fontSize: isMobile ? '11px' : '10px', 
                  marginTop: '4px', 
                  lineHeight: '1.3',
                  display: isMobile ? 'none' : 'block',
                }}>
                  Total FOB importado no período
                </div>
              </div>
              <DollarOutlined style={{ fontSize: 'clamp(24px, 6vw, 40px)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card 
            className="dashboard-metric-card"
            key={`card-exportacoes-${stats?._timestamp || 0}-${stats?.valor_total_exportacoes || 0}`}
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: 'clamp(12px, 3vw, 24px)', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ flex: '1', minWidth: 0 }}>
                <div className="metric-title" style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px', marginBottom: '4px' }}>
                  Valor Exportações
                </div>
                <div className="metric-value" style={{ 
                  color: '#fff', 
                  fontSize: isMobile ? 'clamp(18px, 5vw, 24px)' : 'clamp(16px, 4vw, 22px)', 
                  fontWeight: 'bold', 
                  lineHeight: '1.2', 
                  wordBreak: 'break-word',
                  whiteSpace: 'normal',
                  overflow: 'visible',
                }}>
                  {formatCurrency(
                    tipoOperacao === 'Importação' ? 0 :
                    (statsFinal?.valor_total_exportacoes != null && statsFinal.valor_total_exportacoes !== undefined
                      ? statsFinal.valor_total_exportacoes
                      : (tipoOperacao === 'Exportação' ? (statsFinal?.valor_total_usd ?? 0) : 0))
                  )}
                </div>
                <div style={{ 
                  color: 'rgba(255,255,255,0.7)', 
                  fontSize: isMobile ? '11px' : '10px', 
                  marginTop: '4px', 
                  lineHeight: '1.3',
                  display: isMobile ? 'none' : 'block',
                }}>
                  Total FOB exportado no período
                </div>
              </div>
              <DollarOutlined style={{ fontSize: 'clamp(24px, 6vw, 40px)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card 
            className="dashboard-metric-card"
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: 'clamp(12px, 3vw, 24px)', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ flex: '1', minWidth: 0 }}>
                <div className="metric-title" style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px', marginBottom: '4px' }}>
                  {statsFinal?.fonte_valores === 'estimado' ? 'Saldo Comercial (estimado)' : 'Quantidade Estatística'}
                </div>
                <div className="metric-value" style={{
                  color: '#fff',
                  fontSize: isMobile ? 'clamp(18px, 5vw, 24px)' : 'clamp(16px, 4vw, 22px)',
                  fontWeight: 'bold',
                  lineHeight: '1.2',
                  wordBreak: 'break-word',
                  whiteSpace: 'normal',
                  overflow: 'visible',
                }}>
                  {statsFinal?.fonte_valores === 'estimado'
                    ? formatCurrency((statsFinal.valor_total_exportacoes || 0) - (statsFinal.valor_total_importacoes || 0))
                    : formatQuantity(quantidadeTotal)}
                </div>
                <div style={{
                  color: 'rgba(255,255,255,0.7)',
                  fontSize: isMobile ? '11px' : '10px',
                  marginTop: '4px',
                  lineHeight: '1.3',
                  display: isMobile ? 'none' : 'block',
                }}>
                  {statsFinal?.fonte_valores === 'estimado' ? 'Exportações − Importações (estimado)' : 'Soma das quantidades estatísticas'}
                </div>
              </div>
              <GlobalOutlined style={{ fontSize: 'clamp(24px, 6vw, 40px)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
            </div>
          </Card>
        </Col>
        {(statsFinal.valor_provavel_empresas != null && statsFinal.valor_provavel_empresas > 0) && (
        <Col xs={24} sm={12} lg={8}>
          <Card 
            className="dashboard-metric-card"
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: 'clamp(12px, 3vw, 24px)', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ flex: '1', minWidth: 0 }}>
                <div className="metric-title" style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px', marginBottom: '4px' }}>
                  Valor provável (por empresas)
                </div>
                <div className="metric-value" style={{ 
                  color: '#fff', 
                  fontSize: isMobile ? 'clamp(18px, 5vw, 24px)' : 'clamp(16px, 4vw, 22px)', 
                  fontWeight: 'bold', 
                  lineHeight: '1.2', 
                  wordBreak: 'break-word',
                  whiteSpace: 'normal',
                  overflow: 'visible',
                }}>
                  {formatCurrency(statsFinal.valor_provavel_empresas)}
                </div>
                <div style={{ 
                  color: 'rgba(255,255,255,0.7)', 
                  fontSize: isMobile ? '11px' : '10px', 
                  marginTop: '4px', 
                  lineHeight: '1.3',
                  display: isMobile ? 'none' : 'block',
                }}>
                  Soma por empresas recomendadas (BigQuery/cruzamento)
                </div>
              </div>
              <DollarOutlined style={{ fontSize: 'clamp(24px, 6vw, 40px)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
            </div>
          </Card>
        </Col>
        )}
        {statsFinal.volume_disponivel !== false && (
        <Col xs={24} sm={12} lg={8}>
          <Card 
            className="dashboard-metric-card"
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: 'clamp(12px, 3vw, 24px)', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ flex: '1', minWidth: 0 }}>
                <div className="metric-title" style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px', marginBottom: '4px' }}>
                  Peso (Quilograma Líquido)
                </div>
                <div className="metric-value" style={{ 
                  color: '#fff', 
                  fontSize: isMobile ? 'clamp(18px, 5vw, 24px)' : 'clamp(16px, 4vw, 22px)', 
                  fontWeight: 'bold', 
                  lineHeight: '1.2', 
                  wordBreak: 'break-word',
                  whiteSpace: 'normal',
                  overflow: 'visible',
                }}>
                  {formatWeight(pesoTotal)} KG
                </div>
                <div style={{ 
                  color: 'rgba(255,255,255,0.7)', 
                  fontSize: isMobile ? '11px' : '10px', 
                  marginTop: '4px', 
                  lineHeight: '1.3',
                  display: isMobile ? 'none' : 'block',
                }}>
                  Peso total transportado no período
                </div>
              </div>
              <GlobalOutlined style={{ fontSize: 'clamp(24px, 6vw, 40px)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
            </div>
          </Card>
        </Col>
        )}
      </Row>

      {/* Seção Principal: Importadores e Exportadores */}
      <Row gutter={[8, 8]} style={{ marginBottom: 'clamp(12px, 3vw, 24px)' }}>
        {/* Top Importadores */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Prováveis Importadores</span>
                <DownloadOutlined style={{ cursor: 'pointer', color: '#722ed1' }} />
              </div>
            }
            style={{ borderRadius: '8px', height: '100%' }}
          >
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
              Principais importadores por valor FOB estimado
            </div>
            {topImportadores.length > 0 ? (
              <>
                {topImportadores.map((imp, idx) => (
                  <div 
                    key={idx}
                    style={{ 
                      padding: '12px',
                      marginBottom: '8px',
                      background: '#f9f9f9',
                      borderRadius: '4px',
                      borderLeft: `4px solid ${imp.cor}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 'bold', marginBottom: '4px', fontSize: 'clamp(12px, 3vw, 14px)' }}>
                          {imp.nome.length > (window.innerWidth < 768 ? 30 : 50) ? imp.nome.substring(0, window.innerWidth < 768 ? 30 : 50) + '...' : imp.nome}
                        </div>
                        <div style={{ fontSize: 'clamp(10px, 2.5vw, 12px)', color: '#666', lineHeight: '1.4' }}>
                          <div>FOB: {formatCurrency(imp.fob)} ({imp.percentual.toFixed(2)}%)</div>
                          <div>Peso: {formatWeight(imp.peso)} KG</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div style={{ textAlign: 'center', marginTop: '16px' }}>
                  <Button type="link" style={{ color: '#722ed1' }}>
                    VER MAIS
                  </Button>
                  <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                    Top {topImportadores.length} do total de {principaisPaises?.length || 0}
                  </div>
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                Nenhum dado disponível
              </div>
            )}
          </Card>
        </Col>

        {/* Gráfico Importadores no Tempo */}
        <Col xs={24} lg={12}>
          <Card 
            title="Valores no Tempo - Prováveis Importadores"
            style={{ borderRadius: '8px', height: '100%' }}
          >
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
              Total FOB estimado importado por mês
            </div>
            {importadoresTempoData.length > 0 ? (
              <ResponsiveContainer key={chartKey} width="100%" height={isMobile ? Math.max(320, window.innerHeight * 0.4) : Math.max(380, window.innerHeight * 0.42)}>
                <LineChart data={importadoresTempoData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" tick={{ fontSize: isMobile ? 'clamp(11px, 3vw, 13px)' : 'clamp(10px, 2.5vw, 12px)' }} />
                  <YAxis tick={{ fontSize: 'clamp(10px, 2.5vw, 12px)' }} />
                  <Tooltip content={<SafeTooltip formatter={(value) => formatCurrency(value)} />} />
                  <Legend />
                  {topImportadores.map((imp, idx) => (
                    <Line
                      key={idx}
                      type="monotone"
                      dataKey={`imp_${idx}`}
                      stroke={imp.cor}
                      strokeWidth={2}
                      name={imp.nome.length > (window.innerWidth < 768 ? 10 : 15) ? imp.nome.substring(0, window.innerWidth < 768 ? 10 : 15) + '...' : imp.nome}
                      dot={{ r: 4 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                Nenhum dado disponível
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Seção Exportadores */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        {/* Top Exportadores */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Prováveis Exportadores</span>
                <DownloadOutlined style={{ cursor: 'pointer', color: '#722ed1' }} />
              </div>
            }
            style={{ borderRadius: '8px', height: '100%' }}
          >
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
              Principais fornecedores por valor FOB estimado
            </div>
            {topExportadores.length > 0 ? (
              <>
                {topExportadores.map((exp, idx) => (
                  <div 
                    key={idx}
                    style={{ 
                      padding: '12px',
                      marginBottom: '8px',
                      background: '#f9f9f9',
                      borderRadius: '4px',
                      borderLeft: `4px solid ${exp.cor}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 'bold', marginBottom: '4px', fontSize: 'clamp(12px, 3vw, 14px)' }}>
                          {exp.nome.length > (window.innerWidth < 768 ? 30 : 50) ? exp.nome.substring(0, window.innerWidth < 768 ? 30 : 50) + '...' : exp.nome}
                        </div>
                        <div style={{ fontSize: 'clamp(10px, 2.5vw, 12px)', color: '#666', lineHeight: '1.4' }}>
                          <div>FOB: {formatCurrency(exp.fob)} ({exp.percentual.toFixed(2)}%)</div>
                          <div>Peso: {formatWeight(exp.peso)} KG</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div style={{ textAlign: 'center', marginTop: '16px' }}>
                  <Button type="link" style={{ color: '#722ed1' }}>
                    VER MAIS
                  </Button>
                  <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                    Top {topExportadores.length} do total de {principaisPaises?.length || 0}
                  </div>
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                Nenhum dado disponível
              </div>
            )}
          </Card>
        </Col>

        {/* Gráfico Exportadores no Tempo */}
        <Col xs={24} lg={12}>
          <Card 
            title="Valores no Tempo - Prováveis Exportadores"
            style={{ borderRadius: '8px', height: '100%' }}
          >
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
              Total FOB estimado exportado por mês
            </div>
            {exportadoresTempoData.length > 0 ? (
              <ResponsiveContainer key={chartKey} width="100%" height={isMobile ? Math.max(320, window.innerHeight * 0.4) : Math.max(380, window.innerHeight * 0.42)}>
                <LineChart data={exportadoresTempoData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" tick={{ fontSize: isMobile ? 'clamp(11px, 3vw, 13px)' : 'clamp(10px, 2.5vw, 12px)' }} />
                  <YAxis tick={{ fontSize: 'clamp(10px, 2.5vw, 12px)' }} />
                  <Tooltip content={<SafeTooltip formatter={(value) => formatCurrency(value)} />} />
                  <Legend />
                  {topExportadores.map((exp, idx) => (
                    <Line
                      key={idx}
                      type="monotone"
                      dataKey={`exp_${idx}`}
                      stroke={exp.cor}
                      strokeWidth={2}
                      name={exp.nome.length > (window.innerWidth < 768 ? 10 : 15) ? exp.nome.substring(0, window.innerWidth < 768 ? 10 : 15) + '...' : exp.nome}
                      dot={{ r: 4 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                Nenhum dado disponível
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Gráfico de Tendências (FOB e Peso) */}
      <Row gutter={[8, 8]} style={{ marginBottom: 'clamp(12px, 3vw, 24px)' }}>
        <Col xs={24}>
          <Card 
            title="Tendências"
            style={{ borderRadius: '8px' }}
          >
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
              {temPesoTendencias ? 'Valor total (FOB) e peso por mês' : 'Valor total (FOB) por mês'}
              {statsFinal?.fonte_valores === 'estimado' ? ' — valores estimados' : ''}
            </div>
            {tendenciasData.length > 0 ? (
              <ResponsiveContainer key={chartKey} width="100%" height={isMobile ? Math.max(280, window.innerHeight * 0.35) : Math.max(250, window.innerHeight * 0.3)}>
                <ComposedChart data={tendenciasData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" tick={{ fontSize: isMobile ? 'clamp(11px, 3vw, 13px)' : 'clamp(10px, 2.5vw, 12px)' }} />
                  <YAxis
                    yAxisId="left"
                    label={{ value: 'FOB (USD)', angle: -90, position: 'insideLeft', style: { fontSize: 'clamp(10px, 2.5vw, 12px)' } }}
                    tick={{ fontSize: 'clamp(10px, 2.5vw, 12px)' }}
                  />
                  {temPesoTendencias && (
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      label={{ value: 'Peso (Kg)', angle: 90, position: 'insideRight', style: { fontSize: 'clamp(10px, 2.5vw, 12px)' } }}
                      tick={{ fontSize: 'clamp(10px, 2.5vw, 12px)' }}
                    />
                  )}
                  <Tooltip
                    content={
                      <SafeTooltip
                        formatter={(value, name) => {
                          if (name === 'fob') return formatCurrency(value);
                          if (name === 'peso') return formatWeight(value) + ' KG';
                          return value;
                        }}
                      />
                    }
                  />
                  <Legend />
                  <Bar yAxisId="left" dataKey="fob" fill="#722ed1" name="FOB (USD)" />
                  {temPesoTendencias && (
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="peso"
                      stroke="#ff8042"
                      strokeWidth={3}
                      strokeDasharray="5 5"
                      name="Peso (Kg)"
                      dot={{ r: 5 }}
                    />
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                Nenhum dado disponível
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Top NCMs */}
      <Row gutter={[8, 8]}>
        <Col xs={24}>
          <Card 
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>NCM</span>
                <DownloadOutlined style={{ cursor: 'pointer', color: '#722ed1' }} />
              </div>
            }
            style={{ borderRadius: '8px' }}
          >
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
              Valor total importado por NCM
            </div>
            {principaisNcms && principaisNcms.length > 0 ? (
              <div>
                {principaisNcms.slice(0, 5).map((ncm, idx) => {
                  const percentual = (ncm.valor_total / statsFinal.valor_total_usd) * 100;
                  return (
                    <div key={idx} style={{ marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', flexWrap: 'wrap', gap: '4px' }}>
                        <span style={{ fontWeight: 'bold', fontSize: 'clamp(12px, 3vw, 14px)', flex: '1', minWidth: 0 }}>
                          {ncm.ncm} {ncm.descricao ? ncm.descricao.substring(0, window.innerWidth < 768 ? 30 : 50) + '...' : ''}
                        </span>
                        <span style={{ fontWeight: 'bold', color: '#722ed1', fontSize: 'clamp(11px, 2.8vw, 13px)', flexShrink: 0 }}>
                          {formatCurrency(ncm.valor_total)}
                        </span>
                      </div>
                      <div style={{ 
                        height: '8px', 
                        background: '#e8e8e8', 
                        borderRadius: '4px',
                        overflow: 'hidden'
                      }}>
                        <div style={{ 
                          height: '100%', 
                          width: `${percentual}%`, 
                          background: '#722ed1',
                          transition: 'width 0.3s'
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                Nenhum dado disponível
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Tabela de Dados Detalhados */}
      <Row gutter={[8, 8]} style={{ marginTop: 'clamp(12px, 3vw, 24px)' }}>
        <Col xs={24}>
          <Card 
            title="Dados Detalhados"
            style={{ borderRadius: '8px' }}
            extra={
              <Button 
                type="link" 
                icon={<DownloadOutlined />}
                onClick={() => loadTabelaDados(paginacaoTabela.current, paginacaoTabela.pageSize)}
              >
                Atualizar
              </Button>
            }
          >
            <Table
              columns={[
                {
                  title: 'NCM',
                  dataIndex: 'ncm',
                  key: 'ncm',
                  width: 100,
                  fixed: 'left',
                },
                {
                  title: 'Descrição do Produto',
                  dataIndex: 'descricao_produto',
                  key: 'descricao_produto',
                  ellipsis: true,
                  width: 300,
                },
                {
                  title: 'Tipo de Operação',
                  dataIndex: 'tipo_operacao',
                  key: 'tipo_operacao',
                  width: 120,
                  render: (tipo) => (
                    <Tag color={tipo === 'Importação' ? 'blue' : 'green'}>
                      {tipo}
                    </Tag>
                  ),
                },
                {
                  title: 'Empresa Importadora',
                  dataIndex: 'razao_social_importador',
                  key: 'razao_social_importador',
                  ellipsis: true,
                  width: 250,
                  render: (text) => text || '-',
                },
                {
                  title: 'Empresa Exportadora',
                  dataIndex: 'razao_social_exportador',
                  key: 'razao_social_exportador',
                  ellipsis: true,
                  width: 250,
                  render: (text) => text || '-',
                },
                {
                  title: 'País',
                  dataIndex: 'pais_origem_destino',
                  key: 'pais_origem_destino',
                  width: 150,
                },
                {
                  title: 'Estado',
                  dataIndex: 'uf',
                  key: 'uf',
                  width: isMobile ? 180 : 220,
                  render: (uf, record) => {
                    // Priorizar uf_nome_completo se disponível (vindo do backend)
                    const nomeCompleto = record.uf_nome_completo || obterNomeEstado(uf);
                    const texto = nomeCompleto || uf || '-';
                    return (
                      <div
                        style={{
                          whiteSpace: 'normal',
                          wordBreak: 'break-word',
                          lineHeight: 1.2,
                        }}
                      >
                        {texto}
                      </div>
                    );
                  },
                  sorter: (a, b) => {
                    const nomeA = a.uf_nome_completo || obterNomeEstado(a.uf) || '';
                    const nomeB = b.uf_nome_completo || obterNomeEstado(b.uf) || '';
                    return nomeA.localeCompare(nomeB);
                  },
                },
                {
                  title: 'Valor FOB (USD)',
                  dataIndex: 'valor_fob',
                  key: 'valor_fob',
                  width: 150,
                  align: 'right',
                  render: (valor) => formatCurrency(valor || 0),
                  sorter: (a, b) => (a.valor_fob || 0) - (b.valor_fob || 0),
                },
                {
                  title: 'Peso Líquido (KG)',
                  dataIndex: 'peso_liquido_kg',
                  key: 'peso_liquido_kg',
                  width: 150,
                  align: 'right',
                  render: (peso) => formatWeight(peso || 0),
                  sorter: (a, b) => (a.peso_liquido_kg || 0) - (b.peso_liquido_kg || 0),
                },
                {
                  title: 'Data',
                  dataIndex: 'data_operacao',
                  key: 'data_operacao',
                  width: 120,
                  render: (data) => data ? dayjs(data).format('DD/MM/YYYY') : '-',
                  sorter: (a, b) => {
                    if (!a.data_operacao || !b.data_operacao) return 0;
                    return dayjs(a.data_operacao).unix() - dayjs(b.data_operacao).unix();
                  },
                },
              ]}
              dataSource={tabelaDados}
              loading={loadingTabela}
              rowKey="id"
              scroll={{ x: 'max-content', y: isMobile ? Math.max(350, window.innerHeight * 0.45) : Math.max(300, window.innerHeight * 0.4) }}
              pagination={{
                current: paginacaoTabela.current,
                pageSize: paginacaoTabela.pageSize,
                total: paginacaoTabela.total,
                showSizeChanger: true,
                showTotal: (total) => `Total: ${total} registros`,
                pageSizeOptions: ['10', '20', '50', '100'],
                onChange: (page, pageSize) => {
                  loadTabelaDados(page, pageSize);
                },
                onShowSizeChange: (current, size) => {
                  loadTabelaDados(1, size);
                },
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Seções gerais (não específicas da empresa) — ocultas sob filtro de empresa */}
      {!filtroEmpresaAtivo && (
      <>

      {/* Seção de Empresas Recomendadas */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card
            title="Empresas Recomendadas"
            extra={
              <Button 
                size="small" 
                icon={<ReloadOutlined />}
                onClick={loadEmpresasRecomendadas}
                loading={loadingEmpresasRecomendadas}
              >
                Atualizar
              </Button>
            }
          >
            <Spin spinning={loadingEmpresasRecomendadas}>
              {empresasRecomendadas.length > 0 ? (
                <Table
                  size="small"
                  dataSource={empresasRecomendadas}
                  rowKey={(record, index) => `${record.cnpj || record.CNPJ || ''}-${index}`}
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: 1000 }}
                  columns={[
                    {
                      title: 'CNPJ',
                      dataIndex: 'cnpj',
                      key: 'cnpj',
                      width: 140,
                      render: (v, r) => v || r.CNPJ,
                    },
                    {
                      title: 'Razão Social',
                      dataIndex: 'nome',
                      key: 'nome',
                      ellipsis: true,
                      render: (v, r) => v || r['Razão Social'],
                    },
                    {
                      title: 'Estado',
                      dataIndex: 'uf',
                      key: 'uf',
                      width: 90,
                      render: (v, r) => obterNomeEstado(v || r.estado) || v || r.Estado,
                    },
                    {
                      title: 'Tipo',
                      dataIndex: 'tipo',
                      key: 'tipo',
                      width: 100,
                      render: (v) => v ? (v === 'importadora' ? 'Importadora' : v === 'exportadora' ? 'Exportadora' : v) : '-',
                    },
                    {
                      title: 'Valor provável (USD)',
                      dataIndex: 'valor_total',
                      key: 'valor_total',
                      width: 130,
                      render: (v, r) => {
                        const val = v ?? r.valor_importacao_usd + r.valor_exportacao_usd ?? 0;
                        return val ? `US$ ${Number(val).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '-';
                      },
                      align: 'right',
                      sorter: (a, b) => (a.valor_total || 0) - (b.valor_total || 0),
                    },
                    {
                      title: 'Imp. (USD)',
                      dataIndex: 'valor_importacao_usd',
                      key: 'valor_importacao_usd',
                      width: 100,
                      render: (v) => v ? `US$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 0 })}` : '-',
                      align: 'right',
                    },
                    {
                      title: 'Exp. (USD)',
                      dataIndex: 'valor_exportacao_usd',
                      key: 'valor_exportacao_usd',
                      width: 100,
                      render: (v) => v ? `US$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 0 })}` : '-',
                      align: 'right',
                    },
                    {
                      title: 'Peso',
                      dataIndex: 'peso_participacao',
                      key: 'peso',
                      width: 90,
                      render: (valor, r) => {
                        const v = valor ?? r['Peso Participação (0-100)'];
                        if (v == null) return '-';
                        const color = v > 50 ? 'green' : v > 20 ? 'orange' : 'default';
                        return <Tag color={color}>{Number(v).toFixed(1)}</Tag>;
                      },
                      sorter: (a, b) => (a.peso_participacao || 0) - (b.peso_participacao || 0),
                    },
                  ]}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: 20 }}>
                  <Button 
                    type="primary" 
                    onClick={loadEmpresasRecomendadas}
                    loading={loadingEmpresasRecomendadas}
                  >
                    Carregar Empresas Recomendadas
                  </Button>
                </div>
              )}
            </Spin>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card
            title="Dados reais (BigQuery — Base dos Dados)"
            extra={
              <Space wrap>
                <Select
                  size="small"
                  style={{ width: 100 }}
                  value={bqAno}
                  onChange={(v) => setBqAno(v)}
                  options={[2019, 2020, 2021, 2022, 2023, 2024, 2025].map((y) => ({ value: y, label: String(y) }))}
                />
                {localStorage.getItem('token') && (
                  <>
                    <Input.Password
                      size="small"
                      style={{ width: 160 }}
                      placeholder="X-Admin-Token"
                      value={adminSyncToken}
                      onChange={(e) => {
                        const v = e.target.value;
                        setAdminSyncToken(v);
                        try {
                          localStorage.setItem('admin_sync_token', v);
                        } catch (_) {}
                      }}
                    />
                    <Button
                      size="small"
                      type="primary"
                      loading={syncingBq}
                      onClick={async () => {
                        setSyncingBq(true);
                        try {
                          await adminSyncAPI.sincronizarTudo(bqAno, adminSyncToken || undefined);
                        } catch (e) {
                          console.warn(e);
                        } finally {
                          setSyncingBq(false);
                        }
                      }}
                    >
                      Sincronizar dados (admin)
                    </Button>
                  </>
                )}
                <Button
                  size="small"
                  loading={loadingLocalPg}
                  onClick={async () => {
                    setLoadingLocalPg(true);
                    try {
                      const res = await dashboardLocalAPI.buscar({
                        ano: bqAno,
                        limit: 50,
                        page: 1,
                      });
                      setLocalPgRows(res.data?.items || []);
                    } catch (e) {
                      console.warn(e);
                      setLocalPgRows([]);
                    } finally {
                      setLoadingLocalPg(false);
                    }
                  }}
                >
                  Carregar dados locais (PG)
                </Button>
                <Button
                  size="small"
                  icon={<ReloadOutlined />}
                  loading={loadingBq}
                  onClick={carregarBigQueryRanking}
                >
                  Atualizar ranking
                </Button>
                <Button
                  size="small"
                  loading={syncingBq}
                  onClick={async () => {
                    setSyncingBq(true);
                    try {
                      await dadosReaisAPI.popularEstadoNcmBq(bqAno);
                      await carregarRelatorioBq();
                    } catch (e) {
                      console.warn(e);
                    } finally {
                      setSyncingBq(false);
                    }
                  }}
                >
                  Sincronizar tabela estado×NCM
                </Button>
                <Button size="small" onClick={carregarRelatorioBq}>
                  Carregar relatório
                </Button>
              </Space>
            }
          >
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 12 }}
              message="Ranking agrega exportação/importação por município (comex_stat). O relatório agrupado usa a tabela PostgreSQL preenchida pelo botão Sincronizar."
            />
            <Space wrap style={{ marginBottom: 12 }}>
              <Select
                allowClear
                placeholder="UF"
                style={{ width: 90 }}
                value={filtBqUf}
                onChange={setFiltBqUf}
                options={Object.keys(UF_PARA_ESTADO).map((uf) => ({ value: uf, label: uf }))}
              />
              <Select
                allowClear
                placeholder="Tipo"
                style={{ width: 140 }}
                value={filtBqTipo}
                onChange={setFiltBqTipo}
              >
                <Option value="exportadora">Exportadora</Option>
                <Option value="importadora">Importadora</Option>
              </Select>
              <Input
                placeholder="Filtrar relatório por NCM (parcial)"
                style={{ width: 240 }}
                allowClear
                value={filtBqNcm}
                onChange={(e) => setFiltBqNcm(e.target.value)}
              />
            </Space>
            <Spin spinning={loadingBq}>
              <Table
                size="small"
                rowKey={(r, i) => `${r.nome_empresa}-${r.estado}-${r.tipo}-${i}`}
                dataSource={bqRankingFiltrado}
                pagination={{ pageSize: 15 }}
                scroll={{ x: 800 }}
                columns={[
                  { title: 'Empresa', dataIndex: 'nome_empresa', ellipsis: true },
                  { title: 'UF', dataIndex: 'estado', width: 70 },
                  { title: 'Tipo', dataIndex: 'tipo', width: 110 },
                  {
                    title: 'Valor FOB (US$)',
                    dataIndex: 'valor_total_fob',
                    align: 'right',
                    render: (v) =>
                      v != null
                        ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
                        : '-',
                    sorter: (a, b) =>
                      (Number(a.valor_total_fob) || 0) - (Number(b.valor_total_fob) || 0),
                  },
                  { title: 'Ops.', dataIndex: 'total_operacoes', width: 80 },
                ]}
              />
            </Spin>
            <Divider orientation="left">Dados locais (PostgreSQL — pós sincronização)</Divider>
            <Table
              size="small"
              rowKey={(r, i) => `${r.ncm}-${r.uf}-${r.tipo_operacao}-${i}`}
              dataSource={localPgRows}
              pagination={false}
              scroll={{ x: 900 }}
              columns={[
                { title: 'NCM', dataIndex: 'ncm', width: 100 },
                { title: 'UF', dataIndex: 'uf', width: 60 },
                { title: 'Tipo', dataIndex: 'tipo_operacao', width: 100 },
                {
                  title: 'Valor FOB US$',
                  dataIndex: 'valor_fob_usd',
                  align: 'right',
                  render: (v) =>
                    v != null
                      ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
                      : '-',
                },
                { title: 'Mês', dataIndex: 'mes', width: 60 },
              ]}
            />
            <Divider orientation="left">Relatório estado × NCM × empresa</Divider>
            <Table
              size="small"
              rowKey={(r, i) => `${r.estado}-${r.ncm}-${r.nome}-${i}`}
              dataSource={bqRelatorioFiltrado}
              pagination={{ pageSize: 12 }}
              columns={[
                { title: 'UF', dataIndex: 'estado', width: 70 },
                { title: 'NCM', dataIndex: 'ncm', width: 120 },
                { title: 'Empresa', dataIndex: 'nome', ellipsis: true },
                { title: 'Tipo', dataIndex: 'tipo', width: 100 },
                {
                  title: 'Valor FOB',
                  dataIndex: 'valor_fob',
                  align: 'right',
                  render: (v) =>
                    v != null
                      ? Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
                      : '-',
                },
              ]}
            />
            <Divider orientation="left">NCMs por CNPJ (PostgreSQL — operacoes_comex)</Divider>
            <Space.Compact style={{ maxWidth: 480, marginBottom: 8 }}>
              <Input
                placeholder="CNPJ (somente números)"
                value={cnpjNcmBusca}
                onChange={(e) => setCnpjNcmBusca(e.target.value)}
              />
              <Button
                type="primary"
                onClick={async () => {
                  try {
                    const res = await dadosReaisAPI.getNcmsPorCnpj(cnpjNcmBusca.trim());
                    setNcmsCnpjResult(res.data?.ncms || []);
                  } catch (e) {
                    setNcmsCnpjResult([]);
                    console.warn(e);
                  }
                }}
              >
                Buscar
              </Button>
            </Space.Compact>
            {ncmsCnpjResult.length > 0 && (
              <div style={{ fontSize: 13 }}>{ncmsCnpjResult.join(', ')}</div>
            )}
          </Card>
        </Col>
      </Row>
      
      {/* Seção de Dados ComexStat */}
      {dadosComexstat && (
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Card title="Resumo Importações ComexStat" loading={loadingDadosComexstat}>
              {dadosComexstat.importacoes && (
                <>
                  <Statistic
                    title="Valor Total (BRL)"
                    value={dadosComexstat.importacoes.valor_total_brl || 0}
                    prefix="R$"
                    precision={2}
                    valueStyle={{ color: '#cf1322' }}
                  />
                  <Divider />
                  <Statistic
                    title="Total de Registros"
                    value={dadosComexstat.importacoes.total_registros || 0}
                  />
                </>
              )}
            </Card>
          </Col>
          <Col span={12}>
            <Card title="Resumo Exportações ComexStat" loading={loadingDadosComexstat}>
              {dadosComexstat.exportacoes && (
                <>
                  <Statistic
                    title="Valor Total (BRL)"
                    value={dadosComexstat.exportacoes.valor_total_brl || 0}
                    prefix="R$"
                    precision={2}
                    valueStyle={{ color: '#3f8600' }}
                  />
                  <Divider />
                  <Statistic
                    title="Total de Registros"
                    value={dadosComexstat.exportacoes.total_registros || 0}
                  />
                </>
              )}
            </Card>
          </Col>
        </Row>
      )}
      </>
      )}
    </div>
  );
};

export default Dashboard;
