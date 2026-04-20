import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { 
  Row, Col, Card, Statistic, Spin, Alert, Table, Tag, 
  DatePicker, Select, Input, Button, Space, Divider, AutoComplete
} from 'antd';
import {
  DollarOutlined,
  GlobalOutlined,
  DownloadOutlined,
  SearchOutlined,
  ReloadOutlined,
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
import { dashboardAPI, buscaAPI, empresasAPI, sinergiasAPI, empresasRecomendadasAPI, comexstatAPI, dadosReaisAPI, adminSyncAPI, dashboardLocalAPI } from '../services/api';
import dayjs from 'dayjs';
import 'dayjs/locale/pt-br';

dayjs.locale('pt-br');

const { RangePicker } = DatePicker;
const { Option } = Select;

const COLORS = ['#0088FE', '#FF8042', '#FFBB28', '#00C49F', '#8884d8', '#82ca9d'];

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
  const [sinergiasEstado, setSinergiasEstado] = useState(null);
  const [sugestoesEmpresas, setSugestoesEmpresas] = useState([]);
  const [loadingSinergias, setLoadingSinergias] = useState(false);
  const [loadingSugestoes, setLoadingSugestoes] = useState(false);
  
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
        try {
          const response = await empresasAPI.autocompleteImportadoras(termo, 25);
          const data = response?.data;
          if (data != null && Array.isArray(data)) {
            lista = data;
          } else if (data != null && !Array.isArray(data) && Array.isArray(data?.data)) {
            lista = data.data;
          }
        } catch (e) {
          console.warn('⚠️ Autocomplete importadoras falhou, usando fallback debug:', e.message);
          const res = await empresasAPI.debugEmpresas('importador', 25, termo);
          if (res && res.data && Array.isArray(res.data.importadoras)) {
            lista = res.data.importadoras;
          }
        }
        const options = lista.map((empresa) => ({
          value: empresa.nome || empresa.empresa || '',
          label: `${empresa.nome || empresa.empresa || 'N/A'} (${empresa.total_operacoes ?? 0} operações)`,
        })).filter((o) => o.value);
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
        try {
          const response = await empresasAPI.autocompleteExportadoras(termo, 25);
          const data = response?.data;
          if (data != null && Array.isArray(data)) {
            lista = data;
          } else if (data != null && !Array.isArray(data) && Array.isArray(data?.data)) {
            lista = data.data;
          }
        } catch (e) {
          console.warn('⚠️ Autocomplete exportadoras falhou, usando fallback debug:', e.message);
          const res = await empresasAPI.debugEmpresas('exportador', 25, termo);
          if (res && res.data && Array.isArray(res.data.exportadoras)) {
            lista = res.data.exportadoras;
          }
        }
        const options = lista.map((empresa) => ({
          value: empresa.nome || empresa.empresa || '',
          label: `${empresa.nome || empresa.empresa || 'N/A'} (${empresa.total_operacoes ?? 0} operações)`,
        })).filter((o) => o.value);
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
    
    // NUNCA usar cache quando há filtro de empresa ou busca manual (garantir dados atualizados)
    const cachedData = (temFiltroEmpresa || ehBuscaComFiltro) ? null : localStorage.getItem('dashboard_stats_cache');
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
      
      // Filtros de empresa: só envia com ≥3 caracteres (evita busca a cada letra)
      if (filtroImportador && String(filtroImportador).trim().length >= 3) {
        params.empresa_importadora = String(filtroImportador).trim();
      }
      if (filtroExportador && String(filtroExportador).trim().length >= 3) {
        params.empresa_exportadora = String(filtroExportador).trim();
      }
      console.log('📤 Parâmetros enviados ao backend:', { ...params });
      if (params.empresa_importadora || params.empresa_exportadora) {
        console.log('🔍 Filtro de empresa na requisição:', { empresa_importadora: params.empresa_importadora || null, empresa_exportadora: params.empresa_exportadora || null });
      }
      
      const response = await dashboardAPI.getStats(params);
      
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
        
        if (dadosVazios) {
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
            _timestamp: Date.now(), // Adicionar timestamp para forçar atualização
            _filtro_empresa: filtroImportador || filtroExportador || null // Adicionar filtro aplicado
          };
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
          
          // Só cachear quando não há filtro por empresa (evitar sobrescrever com dados de uma empresa)
          if (!temFiltroEmpresa && !ehBuscaComFiltro) {
            try {
              localStorage.setItem('dashboard_stats_cache', JSON.stringify(response.data));
              localStorage.setItem('dashboard_stats_cache_timestamp', Date.now().toString());
              console.log('💾 Dados salvos no cache');
            } catch (e) {
              console.warn('⚠️ Erro ao salvar cache:', e);
            }
          } else {
            console.log('🚫 Cache não salvo devido a filtro de empresa ou busca manual');
          }
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
        // Erro de conexão - tentar usar cache se disponível
        const cachedData = localStorage.getItem('dashboard_stats_cache');
        if (cachedData) {
          try {
            const parsedCache = JSON.parse(cachedData);
            console.log('📦 Backend offline, usando dados do cache');
            setStats(parsedCache);
            setError('⚠️ Backend temporariamente indisponível. Exibindo dados em cache. Tente novamente em alguns instantes.');
            isLoadingRef.current = false;
            setLoading(false);
            return; // Sair sem mostrar erro crítico
          } catch (e) {
            console.warn('⚠️ Erro ao ler cache:', e);
          }
        }
        
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
        // 503 = serviço/banco temporariamente indisponível: manter dados atuais ou cache, só mostrar aviso
        if (err.response?.status === 503) {
          const detail = err.response?.data?.detail;
          setError(detail || 'Serviço temporariamente indisponível. Tente novamente em alguns segundos.');
          if (!stats) {
            const cachedData = localStorage.getItem('dashboard_stats_cache');
            if (cachedData) {
              try {
                setStats(JSON.parse(cachedData));
              } catch (e) { /* ignorar */ }
            }
          }
        } else {
          // Outros erros: tentar cache antes de mostrar erro
          const cachedData = localStorage.getItem('dashboard_stats_cache');
          if (cachedData) {
            try {
              const parsedCache = JSON.parse(cachedData);
              console.log('📦 Usando dados do cache devido a erro de conexão');
              setStats(parsedCache);
              setError('⚠️ Backend temporariamente indisponível. Exibindo dados em cache. Clique em "Tentar Novamente" para atualizar.');
            } catch (e) {
              setError(`Erro ao carregar dados do dashboard: ${errorMessage}`);
            }
          } else {
            setError(`Erro ao carregar dados do dashboard: ${errorMessage}`);
          }
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
      
      // Em caso de erro, manter dados anteriores se existirem (ou cache)
      if (!stats) {
        const cachedData = localStorage.getItem('dashboard_stats_cache');
        if (cachedData) {
          try {
            setStats(JSON.parse(cachedData));
          } catch (e) {
            // Ignorar erro de parse
          }
        }
      }
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
      searchInProgressRef.current = false; // Buscar concluído; próximo useEffect pode rodar de novo
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
    // Carga inicial apenas; demais atualizações via botão Buscar / Limpar
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  // Função para carregar sugestões de empresas
  const loadSugestoesEmpresas = useCallback(async (tipo = null) => {
    setLoadingSugestoes(true);
    try {
      const data = await sinergiasAPI.getSugestoesEmpresas(20, tipo, null);
      if (data.success && data.sugestoes) {
        setSugestoesEmpresas(data.sugestoes);
      }
    } catch (error) {
      console.error('Erro ao carregar sugestões:', error);
      setSugestoesEmpresas([]);
    } finally {
      setLoadingSugestoes(false);
    }
  }, []);

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

  // Carregar sinergias e sugestões ao montar componente
  useEffect(() => {
    // Carregar sinergias
    const loadSinergias = async () => {
      try {
        const data = await sinergiasAPI.getSinergiasEstado();
        setSinergiasEstado(data);
      } catch (error) {
        console.error('Erro ao carregar sinergias:', error);
      }
    };

    // Carregar sugestões
    loadSugestoesEmpresas();
    
    // Carregar empresas recomendadas
    loadEmpresasRecomendadas();
    
    // Carregar dados ComexStat
    loadDadosComexstat();

    // Carregar sinergias após um pequeno delay para não sobrecarregar
    setTimeout(loadSinergias, 2000);
  }, [loadSugestoesEmpresas, loadEmpresasRecomendadas, loadDadosComexstat]);

  const handleSearch = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    // Usar refs como fonte principal (atualizados a cada digitação); DOM como fallback
    let importadorVal = (importadorInputRef.current != null && importadorInputRef.current !== undefined)
      ? String(importadorInputRef.current).trim()
      : (empresaImportadoraInput || empresaImportadora || '').toString().trim();
    let exportadorVal = (exportadorInputRef.current != null && exportadorInputRef.current !== undefined)
      ? String(exportadorInputRef.current).trim()
      : (empresaExportadoraInput || empresaExportadora || '').toString().trim();
    try {
      const imp = document.querySelector('[data-filter="empresa-importadora"] input');
      const exp = document.querySelector('[data-filter="empresa-exportadora"] input');
      if (imp && imp.value != null && String(imp.value).trim()) importadorVal = String(imp.value).trim();
      if (exp && exp.value != null && String(exp.value).trim()) exportadorVal = String(exp.value).trim();
    } catch (_) {}
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
      };

      // Adicionar filtros de data
      if (periodo && periodo[0] && periodo[1]) {
        filtros.data_inicio = periodo[0].format('YYYY-MM-DD');
        filtros.data_fim = periodo[1].format('YYYY-MM-DD');
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

      // Adicionar filtros de empresa
      if (empresaImportadora) {
        filtros.empresa_importadora = empresaImportadora;
      }
      
      if (empresaExportadora) {
        filtros.empresa_exportadora = empresaExportadora;
      }

      const response = await buscaAPI.buscar(filtros);
      
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
  }, [periodo, tipoOperacao, ncmFiltro, ncmsFiltro, empresaImportadora, empresaExportadora]);

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

  // Top Importadores (quando há filtro por empresa, mostrar a empresa filtrada; senão lista geral)
  const topImportadores = (() => {
    if (!statsFinal) return [];
    
    const temFiltroImp = (empresaImportadora && String(empresaImportadora).trim()) || (empresaImportadoraInput && String(empresaImportadoraInput).trim());
    const nomeFiltroImp = (empresaImportadora || empresaImportadoraInput || '').toString().trim();
    if (temFiltroImp && nomeFiltroImp) {
      const valorImp = statsFinal.valor_total_importacoes ?? statsFinal.valor_total_usd ?? 0;
      const pesoImp = statsFinal.volume_importacoes ?? 0;
      return [{
        cor: COLORS[0],
        nome: nomeFiltroImp.length > 50 ? nomeFiltroImp.substring(0, 50) + '...' : nomeFiltroImp,
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
    
    const temFiltroExp = (empresaExportadora && String(empresaExportadora).trim()) || (empresaExportadoraInput && String(empresaExportadoraInput).trim());
    const nomeFiltroExp = (empresaExportadora || empresaExportadoraInput || '').toString().trim();
    if (temFiltroExp && nomeFiltroExp) {
      const valorExp = statsFinal.valor_total_exportacoes ?? statsFinal.valor_total_usd ?? 0;
      const pesoExp = statsFinal.volume_exportacoes ?? 0;
      return [{
        cor: COLORS[0],
        nome: nomeFiltroExp.length > 50 ? nomeFiltroExp.substring(0, 50) + '...' : nomeFiltroExp,
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
  const importadoresTempoData = statsFinal && mesesDoPeriodoCompleto.length > 0
    ? mesesDoPeriodoCompleto.map((mes) => {
        const [ano, mesNum] = mes.split('-');
        const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
        const valorTotalMes = statsFinal.valores_por_mes?.[mes] || 0;
        const data = { mes: mesFormatado };
        topImportadores.forEach((imp, idx) => {
          const percentual = (imp.percentual || 0) / 100;
          data[`imp_${idx}`] = valorTotalMes * percentual;
        });
        return data;
      })
    : [];

  const exportadoresTempoData = statsFinal && mesesDoPeriodoCompleto.length > 0
    ? mesesDoPeriodoCompleto.map((mes) => {
        const [ano, mesNum] = mes.split('-');
        const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
        const valorTotalMes = statsFinal.valores_por_mes?.[mes] || 0;
        const data = { mes: mesFormatado };
        topExportadores.forEach((exp, idx) => {
          const percentual = (exp.percentual || 0) / 100;
          data[`exp_${idx}`] = valorTotalMes * percentual;
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
          <Col xs={24} sm={8} md={6}>
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="NCMs (múltiplos)"
              value={ncmsFiltro}
              onChange={(values) => {
                setNcmsFiltro(values);
                if (values.length > 0) setNcmFiltro(null);
              }}
              tokenSeparators={[',', ' ']}
              filterOption={(input, option) =>
                (option?.value ?? '').includes(input.replace(/[^\d]/g, ''))
              }
              allowClear
            />
          </Col>
        </Row>
        <Row gutter={[16, 16]} align="middle" style={{ marginTop: '16px' }}>
          <Col xs={24} sm={24} md={12} lg={8} style={{ minWidth: 0 }} data-filter="empresa-importadora">
            <AutoComplete
              style={{ width: '100%', minWidth: 0 }}
              placeholder="Provável Importador"
              dropdownStyle={{ maxWidth: 'min(100vw - 32px, 400px)' }}
              value={empresaImportadoraInput !== '' ? empresaImportadoraInput : (empresaImportadora ?? '')}
              onFocus={() => {
                if (importadorasOptions.length === 0) buscarImportadoras(empresaImportadoraInput || '');
              }}
              onChange={(value) => {
                const v = value ?? '';
                importadorInputRef.current = v;
                setEmpresaImportadoraInput(v);
                setEmpresaImportadora(v.trim() ? v : null);
                if (v) buscarImportadoras(v);
                else setImportadorasOptions([]);
              }}
              onSearch={(text) => {
                const t = text ?? '';
                importadorInputRef.current = t;
                setEmpresaImportadoraInput(t);
                buscarImportadoras(t);
              }}
              onSelect={(value) => {
                const v = (value ?? '').toString().trim();
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
              loading={loadingImportadoras}
              allowClear
              filterOption={false}
            />
          </Col>
          <Col xs={24} sm={24} md={12} lg={8} style={{ minWidth: 0 }} data-filter="empresa-exportadora">
            <AutoComplete
              style={{ width: '100%', minWidth: 0 }}
              placeholder="Provável Exportador"
              dropdownStyle={{ maxWidth: 'min(100vw - 32px, 400px)' }}
              value={empresaExportadoraInput !== '' ? empresaExportadoraInput : (empresaExportadora ?? '')}
              onFocus={() => {
                if (exportadorasOptions.length === 0) buscarExportadoras(empresaExportadoraInput || '');
              }}
              onChange={(value) => {
                const v = value ?? '';
                exportadorInputRef.current = v;
                setEmpresaExportadoraInput(v);
                setEmpresaExportadora(v.trim() ? v : null);
                if (v) buscarExportadoras(v);
                else setExportadorasOptions([]);
              }}
              onSearch={(text) => {
                const t = text ?? '';
                exportadorInputRef.current = t;
                setEmpresaExportadoraInput(t);
                buscarExportadoras(t);
              }}
              onSelect={(value) => {
                const v = (value ?? '').toString().trim();
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
              loading={loadingExportadoras}
              allowClear
              filterOption={false}
            />
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

      {stats && !error && (empresaImportadora || empresaExportadora || ncmFiltro || (ncmsFiltro && ncmsFiltro.length > 0)) &&
        (stats.valor_total_importacoes ?? 0) === 0 && (stats.valor_total_exportacoes ?? 0) === 0 && (stats.valor_total_usd ?? 0) === 0 && (
          <Alert
            message="Nenhuma operação encontrada para os filtros aplicados."
            description="Confira o período, o NCM (8 dígitos) e o nome da empresa. Se o banco ainda não tiver operações importadas, os totais ficarão zerados."
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />
        )}

      {stats && !error && stats.aviso_dados_sem_empresa && (
        <Alert
          message="Filtro por empresa sem efeito nos dados atuais"
          description="As operações no banco não têm importador/exportador (ou CNPJ) preenchidos. O Excel importado hoje é agregado por NCM, UF e país, sem nome de empresa por linha. Para ver atividade da Vale S.A, Hidrau Torque etc., é preciso importar uma base que tenha colunas de importador/exportador por operação (ex.: dados desagregados do MDIC/Aliceweb)."
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Cards de Métricas Principais */}
      {/* Usar key única baseada nos filtros para forçar re-render quando filtros mudarem */}
      <Row gutter={[8, 8]} style={{ marginBottom: 'clamp(12px, 3vw, 24px)' }} key={`cards-${empresaImportadora || ''}-${empresaExportadora || ''}-${stats?._timestamp || 0}`}>
        <Col xs={24} sm={12} lg={6}>
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
        <Col xs={24} sm={12} lg={6}>
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
        <Col xs={24} sm={12} lg={6}>
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
                  Quantidade Estatística
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
                  {formatQuantity(quantidadeTotal)}
                </div>
                <div style={{ 
                  color: 'rgba(255,255,255,0.7)', 
                  fontSize: isMobile ? '11px' : '10px', 
                  marginTop: '4px', 
                  lineHeight: '1.3',
                  display: isMobile ? 'none' : 'block',
                }}>
                  Soma das quantidades estatísticas
                </div>
              </div>
              <GlobalOutlined style={{ fontSize: 'clamp(24px, 6vw, 40px)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
            </div>
          </Card>
        </Col>
        {(statsFinal.valor_provavel_empresas != null && statsFinal.valor_provavel_empresas > 0) && (
        <Col xs={24} sm={12} lg={6}>
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
        <Col xs={24} sm={12} lg={6}>
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
              Valor total importado e peso
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
                  <YAxis 
                    yAxisId="right"
                    orientation="right"
                    label={{ value: 'Peso (Kg)', angle: 90, position: 'insideRight', style: { fontSize: 'clamp(10px, 2.5vw, 12px)' } }}
                    tick={{ fontSize: 'clamp(10px, 2.5vw, 12px)' }}
                  />
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

      {/* Seção de Sinergias e Sugestões */}
      <Row gutter={[8, 8]} style={{ marginTop: 'clamp(12px, 3vw, 24px)' }}>
        <Col xs={24} lg={12}>
          <Card 
            title="📊 Sinergias por Estado" 
            extra={
              <Button 
                size="small" 
                icon={<ReloadOutlined />}
                onClick={async () => {
                  setLoadingSinergias(true);
                  try {
                    const data = await sinergiasAPI.getSinergiasEstado();
                    setSinergiasEstado(data);
                  } catch (error) {
                    console.error('Erro ao carregar sinergias:', error);
                  } finally {
                    setLoadingSinergias(false);
                  }
                }}
                loading={loadingSinergias}
              >
                Atualizar
              </Button>
            }
          >
            <Spin spinning={loadingSinergias}>
              {sinergiasEstado ? (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Statistic 
                      title="Estados com Sinergia" 
                      value={sinergiasEstado.estados_com_sinergia} 
                      suffix={`/ ${sinergiasEstado.total_estados}`}
                    />
                  </div>
                  <Table
                    size="small"
                    dataSource={sinergiasEstado.sinergias || []}
                    rowKey="uf"
                    pagination={false}
                    columns={[
                      {
                        title: 'Estado',
                        dataIndex: 'uf',
                        key: 'uf',
                        width: isMobile ? 160 : 200,
                        render: (uf) => {
                          const texto = obterNomeEstado(uf) || uf || '-';
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
                          const nomeA = obterNomeEstado(a.uf) || '';
                          const nomeB = obterNomeEstado(b.uf) || '';
                          return nomeA.localeCompare(nomeB);
                        },
                      },
                      {
                        title: 'Índice Sinergia',
                        dataIndex: 'indice_sinergia',
                        key: 'indice_sinergia',
                        width: 120,
                        render: (valor) => (valor * 100).toFixed(1) + '%',
                        sorter: (a, b) => a.indice_sinergia - b.indice_sinergia,
                      },
                      {
                        title: 'Importações',
                        dataIndex: ['importacoes', 'valor_total'],
                        key: 'imp_valor',
                        width: 120,
                        render: (valor) => formatCurrency(valor || 0),
                      },
                      {
                        title: 'Exportações',
                        dataIndex: ['exportacoes', 'valor_total'],
                        key: 'exp_valor',
                        width: 120,
                        render: (valor) => formatCurrency(valor || 0),
                      },
                      {
                        title: 'Sugestão',
                        dataIndex: 'sugestao',
                        key: 'sugestao',
                        ellipsis: true,
                      },
                    ]}
                  />
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 20 }}>
                  <Button 
                    type="primary" 
                    onClick={async () => {
                      setLoadingSinergias(true);
                      try {
                        const data = await sinergiasAPI.getSinergiasEstado();
                        setSinergiasEstado(data);
                      } catch (error) {
                        console.error('Erro ao carregar sinergias:', error);
                      } finally {
                        setLoadingSinergias(false);
                      }
                    }}
                    loading={loadingSinergias}
                  >
                    Carregar Sinergias
                  </Button>
                </div>
              )}
            </Spin>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card 
            title="💡 Sugestões de Empresas" 
            extra={
              <Space>
                <Select
                  size="small"
                  style={{ width: 120 }}
                  placeholder="Tipo"
                  onChange={(tipo) => {
                    loadSugestoesEmpresas(tipo);
                  }}
                >
                  <Option value={null}>Todos</Option>
                  <Option value="importacao">Importação</Option>
                  <Option value="exportacao">Exportação</Option>
                </Select>
                <Button 
                  size="small" 
                  icon={<ReloadOutlined />}
                  onClick={() => loadSugestoesEmpresas()}
                  loading={loadingSugestoes}
                >
                  Atualizar
                </Button>
              </Space>
            }
          >
            <Spin spinning={loadingSugestoes}>
              {sugestoesEmpresas.length > 0 ? (
                <Table
                  size="small"
                  dataSource={sugestoesEmpresas}
                  rowKey={(r, i) => r.cnpj || r.razao_social || `${i}`}
                  pagination={{ pageSize: 5 }}
                  columns={[
                    {
                      title: 'Empresa',
                      dataIndex: 'nome',
                      key: 'empresa',
                      ellipsis: true,
                      render: (text, record) => (
                        <div>
                          <div style={{ fontWeight: 600 }}>{text || record.razao_social || record.nome_fantasia}</div>
                          {(record.uf || record.estado) && (
                            <Tag size="small">
                              {obterNomeEstado(record.uf || record.estado) || record.uf || record.estado}
                            </Tag>
                          )}
                          {record.cnae && <Tag size="small" color="blue">CNAE: {record.cnae}</Tag>}
                        </div>
                      ),
                    },
                    {
                      title: 'Valor provável (por empresas)',
                      dataIndex: 'valor_total',
                      key: 'valor_total',
                      width: 140,
                      align: 'right',
                      render: (v) => v != null ? `US$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '-',
                      sorter: (a, b) => (a.valor_total || 0) - (b.valor_total || 0),
                    },
                    {
                      title: 'Potencial',
                      dataIndex: 'peso_participacao',
                      key: 'potencial',
                      width: 100,
                      render: (valor, record) => {
                        const v = valor ?? record.potencial_sinergia;
                        if (v == null) return '-';
                        const percent = typeof v === 'number' && v <= 1 ? (v * 100).toFixed(0) : Number(v).toFixed(1);
                        const color = v > 0.7 || v > 70 ? 'green' : v > 0.3 || v > 30 ? 'orange' : 'default';
                        return <Tag color={color}>{percent}%</Tag>;
                      },
                      sorter: (a, b) => (a.peso_participacao ?? a.potencial_sinergia ?? 0) - (b.peso_participacao ?? b.potencial_sinergia ?? 0),
                    },
                    {
                      title: 'Tipo',
                      dataIndex: 'tipo',
                      key: 'tipo',
                      width: 100,
                      render: (v) => v ? (v === 'importadora' ? 'Importadora' : v === 'exportadora' ? 'Exportadora' : v) : '-',
                    },
                    {
                      title: 'Sugestão / Fonte',
                      dataIndex: 'fonte',
                      key: 'sugestao',
                      width: 120,
                      render: (text, record) => (
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {text || record.sugestao || (record.fonte === 'empresas_recomendadas' ? 'BigQuery/cruzamento' : '')}
                        </div>
                      ),
                    },
                  ]}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: 20 }}>
                  <Button 
                    type="primary" 
                    onClick={() => loadSugestoesEmpresas()}
                    loading={loadingSugestoes}
                  >
                    Carregar Sugestões
                  </Button>
                </div>
              )}
            </Spin>
          </Card>
        </Col>
      </Row>
      
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
    </div>
  );
};

export default Dashboard;
