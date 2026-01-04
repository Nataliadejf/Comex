import React, { useState, useEffect } from 'react';
import { 
  Row, Col, Card, Statistic, Spin, Alert, Table, Tag, Button, Space, 
  DatePicker, Input, Select, AutoComplete, message, Typography, Divider 
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  GlobalOutlined,
  DownloadOutlined,
  ReloadOutlined,
  SearchOutlined,
  FilterOutlined,
  StarOutlined,
  StarFilled,
  PlusOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ComposedChart,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { dashboardAPI, empresasAPI, ncmsAPI } from '../services/api';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title, Text } = Typography;

const COLORS = ['#722ed1', '#9254de', '#b37feb', '#d3adf7', '#efdbff'];

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);
  
  // Filtros
  const [periodo, setPeriodo] = useState([dayjs().subtract(5, 'month'), dayjs()]);
  const [ncm, setNcm] = useState('');
  const [ncms, setNcms] = useState([]); // Array para até 3 NCMs
  const [tipoOperacao, setTipoOperacao] = useState('Importação');
  const [empresa, setEmpresa] = useState('');
  const [empresasOptions, setEmpresasOptions] = useState([]);
  
  // NCMs Monitorados
  const [ncmsMonitorados, setNcmsMonitorados] = useState(() => {
    try {
      const saved = localStorage.getItem('ncmsMonitorados');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  });
  const [mostrarMonitorados, setMostrarMonitorados] = useState(false);
  const [ncmsInfo, setNcmsInfo] = useState({}); // Informações sobre dados disponíveis
  const [verificandoNcms, setVerificandoNcms] = useState(false);

  useEffect(() => {
    // Carregar dados apenas na montagem inicial
    // Filtros são aplicados via botão "Buscar Dados"
    loadDashboardData();
  }, []); // Removido dependências para não recarregar automaticamente

  // Verificar dados dos NCMs monitorados quando a lista mudar
  useEffect(() => {
    if (ncmsMonitorados.length > 0) {
      verificarDadosNcms();
    }
  }, [ncmsMonitorados]);

  const verificarDadosNcms = async () => {
    if (ncmsMonitorados.length === 0) return;
    
    setVerificandoNcms(true);
    try {
      const ncmsString = ncmsMonitorados.join(',');
      const response = await ncmsAPI.verificar(ncmsString);
      const info = {};
      response.data.ncms.forEach(item => {
        info[item.ncm] = item;
      });
      setNcmsInfo(info);
    } catch (error) {
      console.error('Erro ao verificar dados dos NCMs:', error);
    } finally {
      setVerificandoNcms(false);
    }
  };

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Calcular meses, garantindo que está entre 1 e 24 (2 anos)
      let mesesDiff = periodo && periodo[1] && periodo[0] 
        ? Math.ceil(periodo[1].diff(periodo[0], 'month', true)) + 1
        : 3;
      
      // Garantir que está dentro do range aceito pela API (1-24)
      if (mesesDiff < 1) mesesDiff = 1;
      if (mesesDiff > 24) mesesDiff = 24; // Permitir até 2 anos
      
      // Preparar NCMs (até 3)
      // Se há NCM digitado mas não adicionado às tags, usar ele também
      let ncmsParam = null;
      const ncmLimpo = ncm ? ncm.replace(/[.\s]/g, '') : '';
      const ncmValido = ncmLimpo.length === 8;
      
      // Combinar NCMs das tags e NCM digitado (se válido)
      let todosNcms = [...(ncms || [])];
      if (ncmValido && !todosNcms.includes(ncmLimpo)) {
        todosNcms.push(ncmLimpo);
      }
      
      // Limpar e validar NCMs
      const ncmsLimpos = todosNcms
        .map(n => n ? n.replace(/[.\s]/g, '') : '')
        .filter(n => n.length === 8)
        .slice(0, 3); // Limitar a 3 NCMs
      
      if (ncmsLimpos.length > 0) {
        ncmsParam = ncmsLimpos.join(',');
        console.log('Buscando com NCMs:', ncmsLimpos);
      }
      
      console.log('Parâmetros da busca:', {
        meses: mesesDiff,
        tipoOperacao,
        empresa,
        ncms: ncmsParam
      });
      
      // Garantir que meses é um número inteiro
      const response = await dashboardAPI.getStats(
        parseInt(mesesDiff, 10), // Garantir que é inteiro
        tipoOperacao || null, 
        null, // ncm único (deprecated)
        empresa || null,
        ncmsParam // múltiplos NCMs
      );
      
      console.log('Resposta da API recebida:', response.data);
      const data = response.data || {
        volume_importacoes: 0.0,
        volume_exportacoes: 0.0,
        valor_total_usd: 0.0,
        principais_ncms: [],
        principais_paises: [],
        principais_empresas: [],
        registros_por_mes: {}
      };
      setStats(data);
    } catch (err) {
      console.error('Erro detalhado ao carregar dados:', err);
      console.error('Erro completo:', JSON.stringify(err, null, 2));
      
      // Mostrar erro específico ao usuário
      if (err.response) {
        setError(`Erro da API: ${err.response.status} - ${err.response.data?.detail || err.response.data?.message || 'Erro desconhecido'}`);
      } else if (err.request) {
        setError('Não foi possível conectar ao backend. Verifique se está rodando em http://localhost:8000');
      } else {
        setError(`Erro: ${err.message || 'Erro desconhecido'}`);
      }
      
      // Manter dados anteriores se houver erro (não limpar tudo)
      if (!stats) {
        setStats({
          volume_importacoes: 0.0,
          volume_exportacoes: 0.0,
          valor_total_usd: 0.0,
          principais_ncms: [],
          principais_paises: [],
          principais_empresas: [],
          registros_por_mes: {},
          valores_por_mes_com_peso: []
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGerarDashboard = async () => {
    setGenerating(true);
    try {
      await loadDashboardData();
      message.success('Dashboard atualizado com sucesso!');
    } catch (err) {
      message.error('Erro ao gerar dashboard');
    } finally {
      setGenerating(false);
    }
  };

  const handleExportTable = (data, filename) => {
    try {
      const XLSX = require('xlsx');
      const { saveAs } = require('file-saver');
      
      const worksheet = XLSX.utils.json_to_sheet(data);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Dados');
      const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      saveAs(blob, filename);
      message.success('Tabela exportada com sucesso!');
    } catch (err) {
      message.error('Erro ao exportar tabela');
      console.error(err);
    }
  };

  const handleExportRelatorio = async () => {
    try {
      setGenerating(true);
      const mesesDiff = periodo && periodo[1] && periodo[0] 
        ? Math.ceil(periodo[1].diff(periodo[0], 'month', true)) + 1
        : 3;
      
      const response = await dashboardAPI.exportRelatorio(
        mesesDiff,
        tipoOperacao || null,
        ncm || null,
        empresa || null,
        'excel'
      );
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const { saveAs } = require('file-saver');
      const filename = `relatorio_dashboard_${new Date().toISOString().split('T')[0]}.xlsx`;
      saveAs(blob, filename);
      message.success('Relatório exportado com sucesso!');
    } catch (err) {
      message.error('Erro ao exportar relatório');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  if (loading && !stats) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
            <p style={{ marginTop: '16px' }}>Carregando dados da API...</p>
          </div>
        </Card>
      </div>
    );
  }

  // Garantir que stats sempre tenha estrutura válida
  const dashboardStats = stats ? {
    ...stats,
    principais_empresas: Array.isArray(stats.principais_empresas) ? stats.principais_empresas : [],
    principais_ncms: Array.isArray(stats.principais_ncms) ? stats.principais_ncms : [],
    principais_paises: Array.isArray(stats.principais_paises) ? stats.principais_paises : [],
    registros_por_mes: stats.registros_por_mes && typeof stats.registros_por_mes === 'object' ? stats.registros_por_mes : {},
    valores_por_mes_com_peso: Array.isArray(stats.valores_por_mes_com_peso) ? stats.valores_por_mes_com_peso : [],
    volume_importacoes: Number(stats.volume_importacoes) || 0,
    volume_exportacoes: Number(stats.volume_exportacoes) || 0,
    valor_total_usd: Number(stats.valor_total_usd) || 0
  } : {
    volume_importacoes: 0.0,
    volume_exportacoes: 0.0,
    valor_total_usd: 0.0,
    principais_ncms: [],
    principais_paises: [],
    registros_por_mes: {},
    principais_empresas: [],
    provaveis_importadores: [],
    provaveis_exportadores: [],
    urf_entrada: [],
    estados_importadores: [],
    cidades_importadores: [],
    distribuicao_modal: [],
    rotas_pais_origem_aquisicao: [],
    valores_por_mes_com_peso: [],
    comparativo_historico: []
  };

  // Preparar dados para gráficos - usar valores reais por mês
  console.log('Dashboard Stats recebidos:', dashboardStats);
  console.log('valores_por_mes_com_peso:', dashboardStats.valores_por_mes_com_peso);
  
  let evolucaoData = [];
  
  // Priorizar valores_por_mes_com_peso se existir
  if (dashboardStats.valores_por_mes_com_peso && dashboardStats.valores_por_mes_com_peso.length > 0) {
    evolucaoData = dashboardStats.valores_por_mes_com_peso.map((item) => {
      try {
        const mes = item.mes || '';
        const mesFormatado = mes.length >= 7 ? mes.substring(5) + '/' + mes.substring(0, 4) : mes;
        const valor = Number(item.valor_fob || 0) || 0;
        
        console.log(`Processando mês ${mesFormatado}: valor=${valor}`);
        
        return {
          mes: mesFormatado,
          valor: valor
        };
      } catch (e) {
        console.error('Erro ao processar item de evolução:', e, item);
        return null;
      }
    }).filter(item => item !== null && item.valor > 0);
  } 
  // Se não houver valores_por_mes_com_peso, calcular a partir dos registros
  else if (dashboardStats.registros_por_mes && Object.keys(dashboardStats.registros_por_mes).length > 0) {
    console.log('Usando fallback: calculando valores a partir de registros_por_mes');
    const meses = Object.keys(dashboardStats.registros_por_mes || {});
    const totalMeses = meses.length;
    const valorTotal = Number(dashboardStats.valor_total_usd) || 0;
    
    // Distribuir o valor total proporcionalmente aos registros de cada mês
    const totalRegistros = Object.values(dashboardStats.registros_por_mes).reduce((sum, count) => sum + Number(count || 0), 0);
    
    evolucaoData = Object.entries(dashboardStats.registros_por_mes || {}).map(([mes, count]) => {
      try {
        const mesFormatado = mes.length >= 7 ? mes.substring(5) + '/' + mes.substring(0, 4) : mes;
        const registrosMes = Number(count) || 0;
        // Calcular valor proporcional aos registros
        const valorMes = totalRegistros > 0 ? (valorTotal * registrosMes) / totalRegistros : valorTotal / totalMeses;
        
        return {
          mes: mesFormatado,
          valor: valorMes
        };
      } catch (e) {
        console.error('Erro ao processar mês:', e, mes, count);
        return null;
      }
    }).filter(item => item !== null);
  }
  
  console.log('Dados finais para gráfico:', evolucaoData);

  // Dados de tendências (valor + peso)
  const tendenciasData = (dashboardStats.valores_por_mes_com_peso || []).map((item) => {
    try {
      const mes = item.mes || '';
      const mesFormatado = mes.length >= 7 ? mes.substring(5) + '/' + mes.substring(0, 4) : mes;
      return {
        mes: mesFormatado,
        valor_fob: Number(item.valor_fob || 0) || 0,
        peso_kg: Number(item.peso_kg || 0) || 0
      };
    } catch (e) {
      console.error('Erro ao processar item de tendências:', e, item);
      return null;
    }
  }).filter(item => item !== null);

  const topNCMsData = (dashboardStats.principais_ncms || []).slice(0, 10).map((item) => {
    try {
      return {
        name: item.ncm || 'N/A',
        value: Number(item.valor_total || 0) || 0,
        descricao: item.descricao || '',
      };
    } catch (e) {
      console.error('Erro ao processar NCM:', e, item);
      return { name: 'N/A', value: 0, descricao: '' };
    }
  }).filter(item => item.value > 0);

  const topPaisesData = (dashboardStats.principais_paises || []).slice(0, 10).map((item) => {
    try {
      return {
        name: item.pais || 'N/A',
        value: Number(item.valor_total || 0) || 0,
      };
    } catch (e) {
      console.error('Erro ao processar país:', e, item);
      return { name: 'N/A', value: 0 };
    }
  }).filter(item => item.value > 0);

  // Dados para gráficos novos
  const importadoresData = (dashboardStats.provaveis_importadores || []).map((item) => {
    try {
      return {
        nome: item.nome || 'N/A',
        fob: Number(item.fob || 0) || 0,
        peso: Number(item.peso || 0) || 0
      };
    } catch (e) {
      console.error('Erro ao processar importador:', e, item);
      return { nome: 'N/A', fob: 0, peso: 0 };
    }
  }).filter(item => item.fob > 0 || item.peso > 0);

  const exportadoresData = (dashboardStats.provaveis_exportadores || []).map((item) => {
    try {
      return {
        nome: item.nome || 'N/A',
        fob: Number(item.fob || 0) || 0,
        peso: Number(item.peso || 0) || 0
      };
    } catch (e) {
      console.error('Erro ao processar exportador:', e, item);
      return { nome: 'N/A', fob: 0, peso: 0 };
    }
  }).filter(item => item.fob > 0 || item.peso > 0);

  const urfData = (dashboardStats.urf_entrada || []).map((item) => {
    try {
      return {
        nome: item.nome || 'N/A',
        peso_kg: Number(item.peso_kg || 0) || 0
      };
    } catch (e) {
      console.error('Erro ao processar URF:', e, item);
      return { nome: 'N/A', peso_kg: 0 };
    }
  }).filter(item => item.peso_kg > 0);

  const estadosData = (dashboardStats.estados_importadores || []).map((item) => {
    try {
      return {
        nome: item.nome || item.estado || 'N/A',
        peso_kg: Number(item.peso_kg || item.peso_total || 0) || 0
      };
    } catch (e) {
      console.error('Erro ao processar estado:', e, item);
      return { nome: 'N/A', peso_kg: 0 };
    }
  }).filter(item => item.peso_kg > 0);

  const cidadesData = (dashboardStats.cidades_importadores || []).map((item) => {
    try {
      return {
        nome: item.nome || item.cidade || 'N/A',
        peso_kg: Number(item.peso_kg || item.peso_total || 0) || 0
      };
    } catch (e) {
      console.error('Erro ao processar cidade:', e, item);
      return { nome: 'N/A', peso_kg: 0 };
    }
  }).filter(item => item.peso_kg > 0);

  const modalData = (dashboardStats.distribuicao_modal || []).map((item) => {
    try {
      return {
        nome: item.modal || item.nome || 'N/A',
        peso_kg: Number(item.peso_kg || 0) || 0,
        percentual: Number(item.percentual || 0) || 0
      };
    } catch (e) {
      console.error('Erro ao processar modal:', e, item);
      return { nome: 'N/A', peso_kg: 0, percentual: 0 };
    }
  }).filter(item => item.peso_kg > 0);

  // Calcular resumo
  const totalOperacoes = (dashboardStats.principais_ncms || []).reduce((sum, item) => sum + (item.total_operacoes || 0), 0);
  const valorFrete = dashboardStats.valor_total_usd * 0.05; // Estimativa 5%
  const valorSeguro = dashboardStats.valor_total_usd * 0.001; // Estimativa 0.1%

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      {/* Header com Logo e Filtros */}
      <Card 
        style={{ 
          marginBottom: '24px', 
          background: 'linear-gradient(135deg, #722ed1 0%, #9254de 100%)',
          border: 'none',
          borderRadius: '8px'
        }}
        bodyStyle={{ padding: '20px' }}
      >
        <Row align="middle" justify="space-between">
          <Col>
            <Title level={2} style={{ color: 'white', margin: 0 }}>
              Comex Analyzer
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.9)' }}>
              {tipoOperacao} > Brasil {ncm && `> NCM: ${ncm}`}
            </Text>
          </Col>
          <Col>
            <Space>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                loading={generating || loading}
                onClick={handleGerarDashboard}
                style={{ background: 'white', color: '#722ed1', border: 'none' }}
              >
                Atualizar Dashboard
              </Button>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                loading={generating}
                onClick={handleExportRelatorio}
                style={{ background: 'white', color: '#722ed1', border: 'none' }}
              >
                Exportar Relatório
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* NCMs Monitorados */}
      {ncmsMonitorados.length > 0 && (
        <Card 
          style={{ marginBottom: '16px', borderRadius: '8px', background: '#f0f5ff' }}
          title={
            <Space>
              <StarFilled style={{ color: '#722ed1' }} />
              <Text strong>NCMs Monitorados ({ncmsMonitorados.length})</Text>
              <Button 
                type="link" 
                size="small"
                onClick={() => setMostrarMonitorados(!mostrarMonitorados)}
              >
                {mostrarMonitorados ? 'Ocultar' : 'Mostrar'}
              </Button>
            </Space>
          }
        >
          {mostrarMonitorados && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
              {ncmsMonitorados.map((ncmItem, index) => {
                const ncmLimpo = ncmItem.replace(/[.\s]/g, '');
                const info = ncmsInfo[ncmLimpo];
                const temDados = info?.tem_dados;
                const totalRegistros = info?.total_registros || 0;
                
                return (
                  <Tag
                    key={index}
                    closable
                    onClose={() => {
                      const novos = ncmsMonitorados.filter((_, i) => i !== index);
                      setNcmsMonitorados(novos);
                      localStorage.setItem('ncmsMonitorados', JSON.stringify(novos));
                    }}
                    color={temDados ? "green" : "default"}
                    style={{ fontSize: '14px', padding: '4px 12px', cursor: 'pointer' }}
                    onClick={() => {
                      // Adicionar aos filtros se não estiver lá
                      if (!ncms.includes(ncmLimpo) && ncms.length < 3) {
                        setNcms([...ncms, ncmLimpo]);
                        message.success(`NCM ${ncmItem.replace(/(\d{4})(\d{4})/, '$1.$2')} adicionado aos filtros`);
                      }
                    }}
                    title={temDados 
                      ? `${totalRegistros.toLocaleString('pt-BR')} registros disponíveis` 
                      : 'Nenhum dado disponível no banco'}
                  >
                    {ncmItem.replace(/(\d{4})(\d{4})/, '$1.$2')}
                    {temDados && (
                      <span style={{ marginLeft: '4px', fontWeight: 'bold' }}>
                        ✓ ({totalRegistros > 1000 ? `${(totalRegistros/1000).toFixed(1)}k` : totalRegistros})
                      </span>
                    )}
                    {!temDados && verificandoNcms && (
                      <span style={{ marginLeft: '4px' }}>...</span>
                    )}
                  </Tag>
                );
              })}
            </div>
          )}
          <Space>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={() => {
                // Buscar com todos os NCMs monitorados
                if (ncmsMonitorados.length > 0) {
                  const ncmsLimpos = ncmsMonitorados
                    .map(n => n.replace(/[.\s]/g, ''))
                    .filter(n => n.length === 8)
                    .slice(0, 3);
                  setNcms(ncmsLimpos);
                  setNcm('');
                  message.success(`${ncmsLimpos.length} NCM(s) monitorado(s) adicionado(s) aos filtros`);
                }
              }}
            >
              Usar Todos nos Filtros
            </Button>
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={() => {
                if (window.confirm('Deseja remover todos os NCMs monitorados?')) {
                  setNcmsMonitorados([]);
                  localStorage.removeItem('ncmsMonitorados');
                  message.success('NCMs monitorados removidos');
                }
              }}
            >
              Limpar Todos
            </Button>
          </Space>
        </Card>
      )}

      {/* Filtros */}
      <Card style={{ marginBottom: '24px', borderRadius: '8px' }}>
        <Row gutter={[16, 16]} align="bottom">
          <Col xs={24} sm={12} md={5}>
            <Text strong style={{ display: 'block', marginBottom: '8px' }}>Período:</Text>
            <RangePicker
              style={{ width: '100%' }}
              value={periodo}
              onChange={setPeriodo}
              format="MMM/YY"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Text strong style={{ display: 'block', marginBottom: '8px' }}>
              NCM (até 3):
              {ncmsMonitorados.length > 0 && (
                <Button
                  type="link"
                  size="small"
                  icon={<StarFilled style={{ color: '#722ed1' }} />}
                  onClick={() => setMostrarMonitorados(!mostrarMonitorados)}
                  style={{ padding: 0, marginLeft: '8px' }}
                >
                  {ncmsMonitorados.length}
                </Button>
              )}
            </Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {ncms.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '4px' }}>
                  {ncms.map((ncmItem, index) => (
                    <Tag
                      key={index}
                      closable
                      onClose={() => {
                        const newNcms = ncms.filter((_, i) => i !== index);
                        setNcms(newNcms);
                      }}
                      color="blue"
                      style={{ margin: 0 }}
                    >
                      {ncmItem.replace(/(\d{4})(\d{4})/, '$1.$2')}
                    </Tag>
                  ))}
                </div>
              )}
              {ncms.length < 3 && (
                <Input.Group compact>
                  <Input
                    placeholder={ncms.length === 0 ? "Digite NCM (ex: 87083090)" : `Digite mais NCMs (${ncms.length}/3)`}
                    value={ncm}
                    onChange={(e) => {
                      let value = e.target.value.replace(/[^\d.]/g, '');
                      const parts = value.split('.');
                      if (parts.length > 3) {
                        value = parts.slice(0, 3).join('.');
                      }
                      setNcm(value);
                    }}
                    onPressEnter={(e) => {
                      try {
                        const ncmLimpo = e.target.value.replace(/[.\s]/g, '');
                        if (ncmLimpo.length === 8 && !ncms.includes(ncmLimpo) && ncms.length < 3) {
                          const novosNcms = [...ncms, ncmLimpo];
                          setNcms(novosNcms);
                          setNcm('');
                          console.log('NCMs atualizados:', novosNcms);
                        } else if (ncms.includes(ncmLimpo)) {
                          message.warning('Este NCM já foi adicionado');
                        } else if (ncms.length >= 3) {
                          message.warning('Máximo de 3 NCMs permitidos');
                        } else if (ncmLimpo.length !== 8) {
                          message.warning('NCM deve ter 8 dígitos');
                        }
                      } catch (error) {
                        console.error('Erro ao adicionar NCM:', error);
                        message.error('Erro ao adicionar NCM');
                      }
                    }}
                    onBlur={(e) => {
                      try {
                        // Ao perder o foco, se o NCM for válido e não estiver nas tags, adicionar
                        const ncmLimpo = e.target.value.replace(/[.\s]/g, '');
                        if (ncmLimpo.length === 8 && !ncms.includes(ncmLimpo) && ncms.length < 3) {
                          const novosNcms = [...ncms, ncmLimpo];
                          setNcms(novosNcms);
                          setNcm('');
                          console.log('NCMs atualizados (onBlur):', novosNcms);
                        }
                      } catch (error) {
                        console.error('Erro ao adicionar NCM (onBlur):', error);
                      }
                    }}
                    maxLength={11}
                    style={{ width: 'calc(100% - 40px)' }}
                  />
                  <Button
                    type="primary"
                    icon={<StarOutlined />}
                    onClick={() => {
                      const ncmLimpo = ncm.replace(/[.\s]/g, '');
                      if (ncmLimpo.length === 8) {
                        if (!ncmsMonitorados.includes(ncmLimpo)) {
                          const novos = [...ncmsMonitorados, ncmLimpo];
                          setNcmsMonitorados(novos);
                          localStorage.setItem('ncmsMonitorados', JSON.stringify(novos));
                          message.success(`NCM ${ncmLimpo.replace(/(\d{4})(\d{4})/, '$1.$2')} adicionado aos monitorados`);
                        } else {
                          message.info('Este NCM já está sendo monitorado');
                        }
                      } else {
                        message.warning('Digite um NCM válido (8 dígitos)');
                      }
                    }}
                    title="Adicionar aos NCMs Monitorados"
                  />
                </Input.Group>
              )}
              {ncms.length > 0 && (
                <Space>
                  <Button 
                    type="link" 
                    size="small" 
                    onClick={() => {
                      setNcms([]);
                      setNcm('');
                    }}
                    style={{ padding: 0, height: 'auto' }}
                  >
                    Limpar todos
                  </Button>
                  <Button
                    type="link"
                    size="small"
                    icon={<StarOutlined />}
                    onClick={() => {
                      // Adicionar todos os NCMs atuais aos monitorados
                      const novos = [...ncmsMonitorados];
                      let adicionados = 0;
                      ncms.forEach(ncmItem => {
                        if (!novos.includes(ncmItem)) {
                          novos.push(ncmItem);
                          adicionados++;
                        }
                      });
                      if (adicionados > 0) {
                        setNcmsMonitorados(novos);
                        localStorage.setItem('ncmsMonitorados', JSON.stringify(novos));
                        message.success(`${adicionados} NCM(s) adicionado(s) aos monitorados`);
                      } else {
                        message.info('Todos os NCMs já estão sendo monitorados');
                      }
                    }}
                  >
                    Monitorar todos
                  </Button>
                </Space>
              )}
            </div>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Text strong style={{ display: 'block', marginBottom: '8px' }}>Tipo de Operação:</Text>
            <Select
              value={tipoOperacao}
              onChange={setTipoOperacao}
              style={{ width: '100%' }}
            >
              <Option value="Importação">Importação</Option>
              <Option value="Exportação">Exportação</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Text strong style={{ display: 'block', marginBottom: '8px' }}>Nome da Empresa:</Text>
            <AutoComplete
              placeholder="Digite o nome da empresa..."
              value={empresa}
              onChange={setEmpresa}
              onSearch={async (value) => {
                if (value && value.length >= 2) {
                  try {
                    const response = await empresasAPI.autocomplete(value, 10);
                    const empresas = response.data.empresas || [];
                    setEmpresasOptions(empresas.map(emp => ({ value: emp })));
                  } catch (error) {
                    console.error('Erro ao buscar empresas:', error);
                    setEmpresasOptions([]);
                  }
                } else {
                  setEmpresasOptions([]);
                }
              }}
              options={empresasOptions}
              allowClear
              style={{ width: '100%' }}
              filterOption={false}
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Text strong style={{ display: 'block', marginBottom: '8px', visibility: 'hidden' }}>Buscar:</Text>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              style={{ width: '100%', background: '#722ed1', border: 'none' }}
              onClick={loadDashboardData}
              loading={loading}
              block
            >
              Buscar Dados
            </Button>
          </Col>
        </Row>
      </Card>

      {error && (
        <Alert 
          message={error} 
          type="warning" 
          showIcon 
          closable
          style={{ marginBottom: '24px' }}
        />
      )}

      <Row gutter={[16, 16]}>
        {/* Métricas Principais - Estilo Logcomex */}
        <Col xs={24} lg={12}>
          <Card 
            style={{ 
              borderRadius: '8px',
              border: 'none',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
          >
            <Statistic
              title={
                <Text strong style={{ fontSize: '14px', color: '#666' }}>
                  Valor Total {tipoOperacao === 'Importação' ? 'Importado' : 'Exportado'} no Período
                </Text>
              }
              value={dashboardStats.valor_total_usd}
              precision={0}
              prefix={<DollarOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ 
                color: '#722ed1', 
                fontSize: '32px',
                fontWeight: 'bold'
              }}
              suffix="USD"
            />
            <Text type="secondary" style={{ fontSize: '12px', marginTop: '8px', display: 'block' }}>
              Total FOB {tipoOperacao === 'Importação' ? 'pago pelo mercado na importação' : 'recebido na exportação'} dos produtos desta pesquisa
            </Text>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card 
            style={{ 
              borderRadius: '8px',
              border: 'none',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
          >
            <Statistic
              title={
                <Text strong style={{ fontSize: '14px', color: '#666' }}>
                  Quantidade em Peso
                </Text>
              }
              value={tipoOperacao === 'Importação' 
                ? dashboardStats.volume_importacoes 
                : dashboardStats.volume_exportacoes}
              precision={0}
              prefix={tipoOperacao === 'Importação' 
                ? <ArrowDownOutlined style={{ color: '#52c41a' }} />
                : <ArrowUpOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ 
                color: tipoOperacao === 'Importação' ? '#52c41a' : '#ff4d4f',
                fontSize: '32px',
                fontWeight: 'bold'
              }}
              suffix="KG"
            />
            <Text type="secondary" style={{ fontSize: '12px', marginTop: '8px', display: 'block' }}>
              Peso total transportado no período
            </Text>
          </Card>
        </Col>

        {/* Resumo de Valores */}
        <Col xs={24} lg={8}>
          <Card 
            title={<Text strong>Resumo de Valores</Text>}
            style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>Qtd. operações estimada</Text>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#722ed1' }}>
                  {totalOperacoes.toLocaleString('pt-BR')}
                </div>
              </div>
              <Divider style={{ margin: '12px 0' }} />
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>Frete</Text>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  ${valorFrete.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} USD
                </div>
              </div>
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>Seguro</Text>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  ${valorSeguro.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} USD
                </div>
              </div>
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>Qtd. estatística</Text>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {((dashboardStats.volume_importacoes || 0) + (dashboardStats.volume_exportacoes || 0)).toLocaleString('pt-BR')}
                </div>
              </div>
            </Space>
          </Card>
        </Col>

        {/* Gráfico de Evolução Temporal */}
        <Col xs={24} lg={16}>
          <Card 
            title={<Text strong>Valores no Tempo - Total FOB {tipoOperacao === 'Importação' ? 'importado' : 'exportado'} por mês</Text>}
            style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={evolucaoData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="valor"
                  stroke="#722ed1"
                  strokeWidth={3}
                  name="Valor FOB (USD)"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Principais Países */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <Text strong>Principais Países Parceiros</Text>
                <Button
                  type="text"
                  icon={<DownloadOutlined />}
                  size="small"
                  onClick={() => handleExportTable(
                    (dashboardStats.principais_paises || []).map(item => ({
                      País: item.pais,
                      'Valor Total (USD)': item.valor_total,
                      'Total de Operações': item.total_operacoes,
                    })),
                    `top_paises_${new Date().toISOString().split('T')[0]}.xlsx`
                  )}
                />
              </Space>
            }
            style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topPaisesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#722ed1" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Top NCMs */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <Text strong>Top 10 NCMs por Valor</Text>
                <Button
                  type="text"
                  icon={<DownloadOutlined />}
                  size="small"
                  onClick={() => handleExportTable(
                    (dashboardStats.principais_ncms || []).map(item => ({
                      NCM: item.ncm,
                      Descrição: item.descricao,
                      'Valor Total (USD)': item.valor_total,
                      'Total de Operações': item.total_operacoes,
                    })),
                    `top_ncms_${new Date().toISOString().split('T')[0]}.xlsx`
                  )}
                />
              </Space>
            }
            style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={topNCMsData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {topNCMsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>


        {/* Prováveis Importadores */}
        {tipoOperacao === 'Importação' && importadoresData.length > 0 && (
          <Col xs={24} lg={12}>
            <Card 
              title={<Text strong>Prováveis Importadores - Top 5</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {importadoresData.map((item, idx) => (
                  <div key={idx} style={{ padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
                    <Text strong style={{ fontSize: '14px' }}>{item.nome}</Text>
                    <div style={{ marginTop: '8px' }}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>FOB: </Text>
                      <Text strong>${(item.fob || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</Text>
                      <Text type="secondary" style={{ fontSize: '12px', marginLeft: '12px' }}>Peso: </Text>
                      <Text strong>{(item.peso || 0).toLocaleString('pt-BR')} KG</Text>
                    </div>
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
        )}

        {/* Prováveis Exportadores */}
        {tipoOperacao === 'Exportação' && exportadoresData.length > 0 && (
          <Col xs={24} lg={12}>
            <Card 
              title={<Text strong>Prováveis Exportadores - Top 5</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {exportadoresData.map((item, idx) => (
                  <div key={idx} style={{ padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
                    <Text strong style={{ fontSize: '14px' }}>{item.nome}</Text>
                    <div style={{ marginTop: '8px' }}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>FOB: </Text>
                      <Text strong>${(item.fob || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</Text>
                      <Text type="secondary" style={{ fontSize: '12px', marginLeft: '12px' }}>Peso: </Text>
                      <Text strong>{(item.peso || 0).toLocaleString('pt-BR')} KG</Text>
                    </div>
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
        )}

        {/* Gráfico de Tendências - Valor + Peso */}
        {tendenciasData.length > 0 && (
          <Col xs={24}>
            <Card 
              title={<Text strong>Tendências - Valor Total Importado e Peso</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={tendenciasData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" />
                  <YAxis yAxisId="left" orientation="left" label={{ value: 'FOB (USD)', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" label={{ value: 'Peso (Kg)', angle: 90, position: 'insideRight' }} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="valor_fob" fill="#722ed1" name="FOB (USD)" />
                  <Line yAxisId="right" type="monotone" dataKey="peso_kg" stroke="#ff7a00" strokeWidth={2} strokeDasharray="5 5" name="Peso (Kg)" />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}

        {/* URF de Entrada */}
        {urfData.length > 0 && (
          <Col xs={24} lg={12}>
            <Card 
              title={<Text strong>URF de Entrada - Ranking das Unidades de Entrada</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={urfData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="nome" type="category" width={150} />
                  <Tooltip />
                  <Bar dataKey="peso_kg" fill="#722ed1" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}

        {/* Estados dos Importadores */}
        {estadosData.length > 0 && (
          <Col xs={24} lg={12}>
            <Card 
              title={<Text strong>Concentração do Volume das Importações por Estado</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={estadosData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="nome" type="category" width={120} />
                  <Tooltip />
                  <Bar dataKey="peso_kg" fill="#ff7a00" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}

        {/* Cidades dos Importadores */}
        {cidadesData.length > 0 && (
          <Col xs={24} lg={12}>
            <Card 
              title={<Text strong>Concentração do Volume de Importadores por Cidade</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={cidadesData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="nome" type="category" width={150} />
                  <Tooltip />
                  <Bar dataKey="peso_kg" fill="#1890ff" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}

        {/* Distribuição por Modal */}
        {modalData.length > 0 && (
          <Col xs={24} lg={12}>
            <Card 
              title={<Text strong>Distribuição da Quantidade em Peso por Modal de Transporte</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                {modalData.map((item, idx) => (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <Text strong>{item.nome}</Text>
                      <Text>{item.percentual.toFixed(2)}%</Text>
                    </div>
                    <div style={{ width: '100%', background: '#f0f0f0', borderRadius: '4px', height: '24px' }}>
                      <div 
                        style={{ 
                          width: `${item.percentual}%`, 
                          background: COLORS[idx % COLORS.length], 
                          height: '100%', 
                          borderRadius: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          paddingLeft: '8px'
                        }}
                      >
                        <Text style={{ color: 'white', fontSize: '12px' }}>
                          {(item.peso_kg || 0).toLocaleString('pt-BR')} KG
                        </Text>
                      </div>
                    </div>
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
        )}

        {/* Tabela de Rotas País de Origem e Aquisição */}
        {dashboardStats.rotas_pais_origem_aquisicao && dashboardStats.rotas_pais_origem_aquisicao.length > 0 && (
          <Col xs={24}>
            <Card 
              title={<Text strong>Rotas de País de Origem e Aquisição</Text>}
              style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            >
              <Table
                columns={[
                  {
                    title: '%',
                    dataIndex: 'percentual',
                    key: 'percentual',
                    width: 80,
                    render: (value) => `${value.toFixed(2)}%`,
                  },
                  {
                    title: 'País de Origem',
                    dataIndex: 'pais_origem',
                    key: 'pais_origem',
                  },
                  {
                    title: 'Provável País de Aquisição',
                    dataIndex: 'provavel_pais_aquisicao',
                    key: 'provavel_pais_aquisicao',
                  },
                  {
                    title: 'Valor Peso (KG)',
                    dataIndex: 'peso_kg',
                    key: 'peso_kg',
                    render: (value) => `${(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 3 })} KG`,
                  },
                ]}
                dataSource={(dashboardStats.rotas_pais_origem_aquisicao || []).map((item, index) => ({
                  ...item,
                  key: index,
                }))}
                pagination={false}
              />
            </Card>
          </Col>
        )}

        {/* Tabela de Principais Empresas - NO FINAL DA PÁGINA */}
        <Col xs={24}>
          <Card 
            title={
              <Space>
                <Text strong>Principais Empresas</Text>
                <Button
                  type="text"
                  icon={<DownloadOutlined />}
                  size="small"
                  onClick={() => handleExportTable(
                    (dashboardStats.principais_empresas || []).map(item => ({
                      'Nome da Empresa': item.nome,
                      'NCM': item.ncm ? item.ncm.replace(/(\d{4})(\d{4})/, '$1.$2') : '-',
                      'Valor Total (USD)': item.valor_total,
                      'Peso Total (KG)': item.peso_total,
                      'Total de Operações': item.total_operacoes,
                    })),
                    `principais_empresas_${new Date().toISOString().split('T')[0]}.xlsx`
                  )}
                />
              </Space>
            }
            style={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', marginTop: '24px' }}
          >
            <Table
              columns={[
                {
                  title: 'Nome da Empresa',
                  dataIndex: 'nome',
                  key: 'nome',
                  ellipsis: true,
                  width: '30%',
                },
                {
                  title: 'NCM',
                  dataIndex: 'ncm',
                  key: 'ncm',
                  width: '15%',
                  render: (ncm) => ncm ? ncm.replace(/(\d{4})(\d{4})/, '$1.$2') : '-',
                },
                {
                  title: 'Valor Total (USD)',
                  dataIndex: 'valor_total',
                  key: 'valor_total',
                  width: '18%',
                  render: (value) => `$${Number(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
                  sorter: (a, b) => (a.valor_total || 0) - (b.valor_total || 0),
                  defaultSortOrder: 'descend',
                },
                {
                  title: 'Peso Total (KG)',
                  dataIndex: 'peso_total',
                  key: 'peso_total',
                  width: '18%',
                  render: (value) => `${Number(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })} KG`,
                  sorter: (a, b) => (a.peso_total || 0) - (b.peso_total || 0),
                },
                {
                  title: 'Total de Operações',
                  dataIndex: 'total_operacoes',
                  key: 'total_operacoes',
                  width: '12%',
                  sorter: (a, b) => (a.total_operacoes || 0) - (b.total_operacoes || 0),
                },
              ]}
              dataSource={(dashboardStats.principais_empresas || []).length > 0 
                ? (dashboardStats.principais_empresas || []).map((item, index) => ({
                    ...item,
                    key: `${item.nome}-${item.ncm || 'sem-ncm'}-${index}`,
                  }))
                : []}
              locale={{
                emptyText: (
                  <div style={{ padding: '40px', textAlign: 'center' }}>
                    <Text type="secondary">
                      {ncms.length > 0 
                        ? `Nenhuma empresa encontrada para os NCMs filtrados. Verifique se há dados no banco para estes NCMs.`
                        : 'Nenhuma empresa encontrada. Aplique filtros para buscar empresas.'}
                    </Text>
                  </div>
                )
              }}
              pagination={{ 
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `Total de ${total} empresas`,
              }}
              scroll={{ x: 'max-content' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
