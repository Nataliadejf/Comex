import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import { dashboardAPI, buscaAPI, empresasAPI } from '../services/api';
import dayjs from 'dayjs';
import 'dayjs/locale/pt-br';

dayjs.locale('pt-br');

const { RangePicker } = DatePicker;
const { Option } = Select;

const COLORS = ['#0088FE', '#FF8042', '#FFBB28', '#00C49F', '#8884d8', '#82ca9d'];

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [periodo, setPeriodo] = useState([dayjs().subtract(2, 'year'), dayjs()]);
  const [tipoOperacao, setTipoOperacao] = useState(null);
  const [ncmFiltro, setNcmFiltro] = useState(null);
  const [ncmsFiltro, setNcmsFiltro] = useState([]);
  const [meses, setMeses] = useState(24); // Padrão: 2 anos
  const [tabelaDados, setTabelaDados] = useState([]);
  const [loadingTabela, setLoadingTabela] = useState(false);
  const [paginacaoTabela, setPaginacaoTabela] = useState({ current: 1, pageSize: 10, total: 0 });
  const [empresaImportadora, setEmpresaImportadora] = useState(null);
  const [empresaExportadora, setEmpresaExportadora] = useState(null);
  const [importadorasOptions, setImportadorasOptions] = useState([]);
  const [exportadorasOptions, setExportadorasOptions] = useState([]);
  const [loadingImportadoras, setLoadingImportadoras] = useState(false);
  const [loadingExportadoras, setLoadingExportadoras] = useState(false);
  const isLoadingRef = useRef(false);

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

  // Função de busca de importadoras com debounce
  const buscarImportadoras = useCallback(
    debounce(async (query) => {
      if (!query || query.length < 2) {
        setImportadorasOptions([]);
        return;
      }
      
      setLoadingImportadoras(true);
      try {
        const response = await empresasAPI.autocompleteImportadoras(query);
        const options = response.data.map((empresa) => ({
          value: empresa.nome,
          label: `${empresa.nome} (${empresa.total_operacoes} operações)`,
        }));
        setImportadorasOptions(options);
      } catch (error) {
        console.error('Erro ao buscar importadoras:', error);
        setImportadorasOptions([]);
      } finally {
        setLoadingImportadoras(false);
      }
    }, 300),
    []
  );

  // Função de busca de exportadoras com debounce
  const buscarExportadoras = useCallback(
    debounce(async (query) => {
      if (!query || query.length < 2) {
        setExportadorasOptions([]);
        return;
      }
      
      setLoadingExportadoras(true);
      try {
        const response = await empresasAPI.autocompleteExportadoras(query);
        const options = response.data.map((empresa) => ({
          value: empresa.nome,
          label: `${empresa.nome} (${empresa.total_operacoes} operações)`,
        }));
        setExportadorasOptions(options);
      } catch (error) {
        console.error('Erro ao buscar exportadoras:', error);
        setExportadorasOptions([]);
      } finally {
        setLoadingExportadoras(false);
      }
    }, 300),
    []
  );

  // Atualizar meses quando período mudar
  useEffect(() => {
    if (periodo && periodo[0] && periodo[1]) {
      const mesesCalculados = Math.ceil(periodo[1].diff(periodo[0], 'month', true)) + 1;
      const mesesAjustados = Math.max(1, Math.min(24, Math.round(mesesCalculados)));
      setMeses((prevMeses) => {
        if (prevMeses !== mesesAjustados) {
          return mesesAjustados;
        }
        return prevMeses;
      });
    }
  }, [periodo]);

  const loadDashboardData = useCallback(async () => {
    // Evitar múltiplas chamadas simultâneas
    if (isLoadingRef.current) {
      console.log('⚠️ Requisição já em andamento, ignorando...');
      return;
    }

    isLoadingRef.current = true;
    setLoading(true);
    setError(null);
    
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

      // Usar múltiplos NCMs se disponível
      const params = {
        meses,
        tipoOperacao,
      };
      
      if (ncmsFiltro && ncmsFiltro.length > 0) {
        params.ncms = ncmsFiltro;
      } else if (ncmFiltro) {
        params.ncm = ncmFiltro;
      }
      
      // Adicionar filtros de empresa
      if (empresaImportadora) {
        params.empresa_importadora = empresaImportadora;
      }
      
      if (empresaExportadora) {
        params.empresa_exportadora = empresaExportadora;
      }
      
      const response = await dashboardAPI.getStats(params);
      
      console.log('✅ Dados recebidos:', response.data);
      
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
        setStats(response.data);
      } else {
        // Fallback: definir stats vazio se resposta não tiver data
        setStats({
          volume_importacoes: 0,
          volume_exportacoes: 0,
          valor_total_usd: 0,
          principais_ncms: [],
          principais_paises: [],
          registros_por_mes: {},
          valores_por_mes: {},
          pesos_por_mes: {}
        });
      }
    } catch (err) {
      let errorMessage = 'Erro ao carregar dados do dashboard';
      
      if (err.response) {
        // Erro do servidor
        if (err.response.data) {
          if (typeof err.response.data === 'string' && err.response.data.includes('<!')) {
            errorMessage = 'Servidor retornou HTML ao invés de JSON. Verifique se o backend está rodando corretamente.';
          } else if (err.response.data.detail) {
            errorMessage = err.response.data.detail;
          } else if (typeof err.response.data === 'string') {
            errorMessage = err.response.data;
          }
        } else {
          errorMessage = `Erro ${err.response.status}: ${err.response.statusText}`;
        }
      } else if (err.request) {
        // Erro de conexão
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        errorMessage = `Não foi possível conectar ao backend em ${apiUrl}. Verifique se o servidor está rodando.`;
      } else {
        // Outro erro
        errorMessage = err.message || 'Erro desconhecido';
      }
      
      setError(`Erro ao carregar dados do dashboard: ${errorMessage}`);
      console.error('❌ Erro completo:', err);
      console.error('❌ Detalhes:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        url: err.config?.url
      });
      
      // Em caso de erro, manter dados anteriores se existirem
      setStats((prevStats) => prevStats || null);
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  }, [meses, tipoOperacao, ncmFiltro, ncmsFiltro, empresaImportadora, empresaExportadora]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleSearch = () => {
    loadDashboardData();
    loadTabelaDados();
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
    setPeriodo([dayjs().subtract(2, 'year'), dayjs()]);
    setMeses(24);
  };

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
      </div>
    );
  }

  if (!stats) {
    return (
      <div style={{ padding: '20px' }}>
        <Alert 
          message="Nenhum dado disponível" 
          description="Não foi possível carregar os dados do dashboard. Verifique se o backend está rodando e tente novamente."
          type="info" 
          showIcon 
          action={
            <Button size="small" onClick={loadDashboardData}>
              Recarregar
            </Button>
          }
        />
      </div>
    );
  }

  // Preparar dados para gráficos
  const evolucaoData = Object.entries(stats.registros_por_mes || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([mes, count]) => {
      // Formato do backend é "YYYY-MM", converter para formato legível
      const [ano, mesNum] = mes.split('-');
      const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
      return {
        mes: mesFormatado,
        registros: count,
      };
    });

  // Dados para gráfico combinado (FOB e Peso) - usar dados reais
  const tendenciasData = Object.entries(stats.valores_por_mes || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([mes]) => {
      // Usar dados reais de valores_por_mes e pesos_por_mes
      const valorMensal = stats.valores_por_mes?.[mes] || 0;
      const pesoMensal = stats.pesos_por_mes?.[mes] || 0;
      // Formato do backend é "YYYY-MM", converter para formato legível
      const [ano, mesNum] = mes.split('-');
      const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
      return {
        mes: mesFormatado,
        fob: valorMensal,
        peso: pesoMensal,
      };
    });

  // Top Importadores (usando países para importação)
  const topImportadores = stats.principais_paises
    ?.filter((_, idx) => idx < 5)
    .map((pais, idx) => ({
      ...pais,
      cor: COLORS[idx % COLORS.length],
      nome: pais.pais || 'N/A',
      fob: pais.valor_total || 0,
      peso: (stats.volume_importacoes * (pais.valor_total / stats.valor_total_usd)) || 0,
      percentual: ((pais.valor_total / stats.valor_total_usd) * 100) || 0,
    })) || [];

  // Top Exportadores (usando países para exportação)
  const topExportadores = stats.principais_paises
    ?.filter((_, idx) => idx < 5)
    .map((pais, idx) => ({
      ...pais,
      cor: COLORS[idx % COLORS.length],
      nome: pais.pais || 'N/A',
      fob: pais.valor_total || 0,
      peso: (stats.volume_exportacoes * (pais.valor_total / stats.valor_total_usd)) || 0,
      percentual: ((pais.valor_total / stats.valor_total_usd) * 100) || 0,
    })) || [];

  // Dados para gráfico de linha de importadores/exportadores ao longo do tempo
  // Usar dados reais de valores_por_mes distribuídos proporcionalmente
  const importadoresTempoData = Object.entries(stats.valores_por_mes || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([mes]) => {
      const [ano, mesNum] = mes.split('-');
      const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
      const valorTotalMes = stats.valores_por_mes?.[mes] || 0;
      const data = { mes: mesFormatado };
      topImportadores.forEach((imp, idx) => {
        // Distribuir proporcionalmente ao percentual de cada importador
        const percentual = imp.percentual / 100;
        data[`imp_${idx}`] = valorTotalMes * percentual;
      });
      return data;
    });

  const exportadoresTempoData = Object.entries(stats.valores_por_mes || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([mes]) => {
      const [ano, mesNum] = mes.split('-');
      const mesFormatado = dayjs(`${ano}-${mesNum}-01`).format('MMM/YY');
      const valorTotalMes = stats.valores_por_mes?.[mes] || 0;
      const data = { mes: mesFormatado };
      topExportadores.forEach((exp, idx) => {
        // Distribuir proporcionalmente ao percentual de cada exportador
        const percentual = exp.percentual / 100;
        data[`exp_${idx}`] = valorTotalMes * percentual;
      });
      return data;
    });

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

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      {/* Barra de Filtros */}
      <Card 
        style={{ marginBottom: '24px', borderRadius: '8px' }}
        bodyStyle={{ padding: '16px' }}
      >
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <RangePicker
              style={{ width: '100%' }}
              value={periodo}
              onChange={(dates) => {
                setPeriodo(dates);
                if (dates && dates[0] && dates[1]) {
                  const diff = Math.ceil(dates[1].diff(dates[0], 'month', true)) + 1;
                  setMeses(Math.max(1, Math.min(24, Math.round(diff))));
                }
              }}
              format="DD/MM/YYYY"
              placeholder={['Data Início', 'Data Fim']}
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
                // Limpar campo antigo se usar múltiplos
                if (values.length > 0) {
                  setNcmFiltro(null);
                }
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
          <Col xs={24} sm={12} md={8}>
            <AutoComplete
              style={{ width: '100%' }}
              placeholder="Provável Importador"
              value={empresaImportadora}
              onChange={(value) => {
                setEmpresaImportadora(value);
                if (value) {
                  buscarImportadoras(value);
                } else {
                  setImportadorasOptions([]);
                }
              }}
              onSearch={buscarImportadoras}
              options={importadorasOptions}
              loading={loadingImportadoras}
              allowClear
              filterOption={false}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <AutoComplete
              style={{ width: '100%' }}
              placeholder="Provável Exportador"
              value={empresaExportadora}
              onChange={(value) => {
                setEmpresaExportadora(value);
                if (value) {
                  buscarExportadoras(value);
                } else {
                  setExportadorasOptions([]);
                }
              }}
              onSearch={buscarExportadoras}
              options={exportadorasOptions}
              loading={loadingExportadoras}
              allowClear
              filterOption={false}
            />
          </Col>
          <Col xs={24} sm={24} md={8}>
            <Space>
              <Button 
                type="primary" 
                icon={<SearchOutlined />} 
                onClick={handleSearch}
                style={{ background: '#722ed1', borderColor: '#722ed1' }}
              >
                Buscar
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleClearFilters}>
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

      {/* Cards de Métricas Principais */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={8}>
          <Card 
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px', marginBottom: '8px' }}>
                  Valor Total Importado no Período
                </div>
                <div style={{ color: '#fff', fontSize: '28px', fontWeight: 'bold' }}>
                  {formatCurrency(
                    tipoOperacao === 'Exportação' ? 0 : 
                    (stats.valor_total_importacoes ?? (tipoOperacao === null ? stats.valor_total_usd : 0))
                  )}
                </div>
                <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', marginTop: '8px' }}>
                  Total FOB pago pelo mercado na importação dos produtos desta pesquisa
                </div>
              </div>
              <DollarOutlined style={{ fontSize: '48px', color: 'rgba(255,255,255,0.3)' }} />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card 
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px', marginBottom: '8px' }}>
                  Quantidade em Peso
                </div>
                <div style={{ color: '#fff', fontSize: '28px', fontWeight: 'bold' }}>
                  {formatWeight(stats.volume_importacoes || 0)} KG
                </div>
                <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', marginTop: '8px' }}>
                  Peso total transportado no período
                </div>
              </div>
              <GlobalOutlined style={{ fontSize: '48px', color: 'rgba(255,255,255,0.3)' }} />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card 
            style={{ 
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              border: 'none',
              height: '100%',
            }}
            bodyStyle={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px', marginBottom: '8px' }}>
                  Valor Total Exportado no Período
                </div>
                <div style={{ color: '#fff', fontSize: '28px', fontWeight: 'bold' }}>
                  {formatCurrency(
                    tipoOperacao === 'Importação' ? 0 : 
                    (stats.valor_total_exportacoes ?? (tipoOperacao === null ? stats.valor_total_usd : 0))
                  )}
                </div>
                <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', marginTop: '8px' }}>
                  Total FOB recebido pelo mercado na exportação dos produtos desta pesquisa
                </div>
              </div>
              <DollarOutlined style={{ fontSize: '48px', color: 'rgba(255,255,255,0.3)' }} />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Seção Principal: Importadores e Exportadores */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
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
                        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                          {imp.nome}
                        </div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          FOB: {formatCurrency(imp.fob)} ({imp.percentual.toFixed(2)}%) | 
                          Peso: {formatWeight(imp.peso)} KG
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
                    Top {topImportadores.length} do total de {stats.principais_paises?.length || 0}
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
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={importadoresTempoData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  {topImportadores.map((imp, idx) => (
                    <Line
                      key={idx}
                      type="monotone"
                      dataKey={`imp_${idx}`}
                      stroke={imp.cor}
                      strokeWidth={2}
                      name={imp.nome.length > 15 ? imp.nome.substring(0, 15) + '...' : imp.nome}
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
                        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                          {exp.nome}
                        </div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          FOB: {formatCurrency(exp.fob)} ({exp.percentual.toFixed(2)}%) | 
                          Peso: {formatWeight(exp.peso)} KG
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
                    Top {topExportadores.length} do total de {stats.principais_paises?.length || 0}
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
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={exportadoresTempoData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  {topExportadores.map((exp, idx) => (
                    <Line
                      key={idx}
                      type="monotone"
                      dataKey={`exp_${idx}`}
                      stroke={exp.cor}
                      strokeWidth={2}
                      name={exp.nome.length > 15 ? exp.nome.substring(0, 15) + '...' : exp.nome}
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
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24}>
          <Card 
            title="Tendências"
            style={{ borderRadius: '8px' }}
          >
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '16px' }}>
              Valor total importado e peso
            </div>
            {tendenciasData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={tendenciasData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" />
                  <YAxis 
                    yAxisId="left"
                    label={{ value: 'FOB (USD)', angle: -90, position: 'insideLeft' }}
                  />
                  <YAxis 
                    yAxisId="right"
                    orientation="right"
                    label={{ value: 'Peso (Kg)', angle: 90, position: 'insideRight' }}
                  />
                  <Tooltip 
                    formatter={(value, name) => {
                      if (name === 'fob') return formatCurrency(value);
                      if (name === 'peso') return formatWeight(value) + ' KG';
                      return value;
                    }}
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
      <Row gutter={[16, 16]}>
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
            {stats.principais_ncms && stats.principais_ncms.length > 0 ? (
              <div>
                {stats.principais_ncms.slice(0, 5).map((ncm, idx) => {
                  const percentual = (ncm.valor_total / stats.valor_total_usd) * 100;
                  return (
                    <div key={idx} style={{ marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 'bold' }}>
                          {ncm.ncm} {ncm.descricao ? ncm.descricao.substring(0, 50) + '...' : ''}
                        </span>
                        <span style={{ fontWeight: 'bold', color: '#722ed1' }}>
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
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
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
                  title: 'UF',
                  dataIndex: 'uf',
                  key: 'uf',
                  width: 80,
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
              scroll={{ x: 1500 }}
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
    </div>
  );
};

export default Dashboard;
