import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://comex-backend-gecp.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 min — Render cold start + BigQuery podem exceder 60s
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token em todas as requisições
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => {
    // Verificar se a resposta é HTML ao invés de JSON
    const contentType = response.headers['content-type'] || '';
    if (contentType.includes('text/html')) {
      console.error('❌ Erro: API retornou HTML ao invés de JSON. Possível erro do servidor.');
      return Promise.reject(new Error('Servidor retornou HTML ao invés de JSON. Verifique se o backend está rodando corretamente.'));
    }
    
    // Verificar se o body parece ser HTML
    if (typeof response.data === 'string' && response.data.trim().startsWith('<!')) {
      console.error('❌ Erro: Resposta parece ser HTML:', response.data.substring(0, 200));
      return Promise.reject(new Error('Servidor retornou HTML ao invés de JSON. Verifique a URL da API e se o backend está rodando.'));
    }
    
    return response;
  },
  (error) => {
    if (error.response) {
      // Verificar se o erro é HTML
      const contentType = error.response.headers['content-type'] || '';
      if (contentType.includes('text/html') || 
          (typeof error.response.data === 'string' && error.response.data.trim().startsWith('<!'))) {
        console.error('❌ Erro: API retornou HTML de erro:', error.response.data.substring(0, 200));
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        return Promise.reject(new Error(`Servidor retornou HTML ao invés de JSON. Verifique se o backend está rodando em ${apiUrl}`));
      }
      
      // Se receber 401 (não autorizado), redirecionar para login
      if (error.response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      console.error('Erro da API:', error.response.data);
    } else if (error.request) {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      console.error('❌ Erro de conexão: Não foi possível conectar ao backend em', apiUrl);
      console.error('Verifique se o backend está rodando e acessível.');
    } else {
      console.error('Erro:', error.message);
    }
    return Promise.reject(error);
  }
);

// API de Sinergias e Sugestões
export const sinergiasAPI = {
  getSinergiasEstado: async (uf = null) => {
    const params = uf ? { uf } : {};
    const response = await api.get('/dashboard/sinergias-estado', { params });
    return response.data;
  },
  
  getSugestoesEmpresas: async (limite = 20, tipo = null, uf = null) => {
    const params = { limite };
    if (tipo) params.tipo = tipo;
    if (uf) params.uf = uf;
    const response = await api.get('/dashboard/sugestoes-empresas', { params });
    return response.data;
  },
  
  atualizarDadosCompletos: async () => {
    const response = await api.post('/atualizar-dados-completos');
    return response.data;
  },
};

export default api;

// Função auxiliar para verificar se backend está acessível
const checkBackendHealth = async (timeoutMs = 15000) => {
  try {
    const healthResponse = await api.get('/health', { timeout: timeoutMs });
    return healthResponse.data?.status === 'healthy' || healthResponse.status === 200;
  } catch (error) {
    console.warn('⚠️ Backend health check falhou:', error.message);
    return false;
  }
};

// Função de retry com backoff exponencial
const retryWithBackoff = async (fn, maxRetries = 3, baseDelay = 1000) => {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      // Se não for erro de conexão ou timeout, não fazer retry
      const msg = String(error.message || '').toLowerCase();
      const isConnectionError =
        error.code === 'ERR_NETWORK' ||
        error.code === 'ECONNREFUSED' ||
        error.code === 'ETIMEDOUT' ||
        error.code === 'ECONNABORTED' || // timeout do axios no browser
        msg.includes('network error') ||
        msg.includes('timeout') ||
        msg.includes('aborted') ||
        msg.includes('não foi possível conectar');
      
      if (!isConnectionError || attempt === maxRetries) {
        throw error;
      }
      
      // Calcular delay exponencial: 1s, 2s, 4s
      const delay = baseDelay * Math.pow(2, attempt);
      console.log(`⚠️ Tentativa ${attempt + 1}/${maxRetries + 1} falhou. Tentando novamente em ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};

/** Parâmetros de filtro alinhados ao dashboard principal (BigQuery empresas_ncm_import_export_uf). */
function buildComexDashboardBqQueryParams(paramsObj = {}) {
  const params = paramsObj || {};
  const urlParams = new URLSearchParams();
  const mesesVal = Math.min(120, Math.max(1, parseInt(params.meses, 10) || 24));
  urlParams.append('meses', String(mesesVal));
  if (params.tipoOperacao && String(params.tipoOperacao).trim()) {
    urlParams.append('tipo_operacao', String(params.tipoOperacao).trim());
  }
  if (params.ncm && String(params.ncm).trim()) urlParams.append('ncm', String(params.ncm).trim());
  if (params.ncms && Array.isArray(params.ncms)) {
    params.ncms.forEach((ncm) => {
      if (ncm != null && String(ncm).trim()) urlParams.append('ncms', String(ncm).trim());
    });
  }
  if (params.data_inicio && /^\d{4}-\d{2}-\d{2}$/.test(String(params.data_inicio))) {
    urlParams.append('data_inicio', params.data_inicio);
  }
  if (params.data_fim && /^\d{4}-\d{2}-\d{2}$/.test(String(params.data_fim))) {
    urlParams.append('data_fim', params.data_fim);
  }
  const empImp = params.empresa_importadora != null ? String(params.empresa_importadora).trim() : '';
  const empExp = params.empresa_exportadora != null ? String(params.empresa_exportadora).trim() : '';
  if (empImp) urlParams.append('empresa_importadora', empImp);
  if (empExp) urlParams.append('empresa_exportadora', empExp);
  return urlParams;
}

// Endpoints
export const dashboardAPI = {
  getStats: async (paramsObj = {}) => {
    // Sempre usar objeto de parâmetros
    const params = paramsObj || {};

    const urlParams = new URLSearchParams();
    // Backend aceita até 120 meses (10 anos); cap para evitar 422
    const mesesVal = Math.min(120, Math.max(1, parseInt(params.meses, 10) || 24));
    urlParams.append('meses', String(mesesVal));
    if (params.tipoOperacao && String(params.tipoOperacao).trim()) {
      urlParams.append('tipo_operacao', String(params.tipoOperacao).trim());
    }
    if (params.ncm && String(params.ncm).trim()) urlParams.append('ncm', String(params.ncm).trim());
    if (params.ncms && Array.isArray(params.ncms)) {
      params.ncms.forEach(ncm => {
        if (ncm != null && String(ncm).trim()) urlParams.append('ncms', String(ncm).trim());
      });
    }
    if (params.data_inicio && /^\d{4}-\d{2}-\d{2}$/.test(String(params.data_inicio))) {
      urlParams.append('data_inicio', params.data_inicio);
    }
    if (params.data_fim && /^\d{4}-\d{2}-\d{2}$/.test(String(params.data_fim))) {
      urlParams.append('data_fim', params.data_fim);
    }
    const empImp = params.empresa_importadora != null ? String(params.empresa_importadora).trim() : '';
    const empExp = params.empresa_exportadora != null ? String(params.empresa_exportadora).trim() : '';
    if (empImp) {
      urlParams.append('empresa_importadora', empImp);
    }
    if (empExp) {
      urlParams.append('empresa_exportadora', empExp);
    }
    if (empImp || empExp) {
      urlParams.append('_', String(Date.now()));
      console.log('🔗 URL da API (verifique se é o backend local):', API_BASE_URL);
      console.log('🔗 Filtro na URL:', empImp ? `empresa_importadora=${encodeURIComponent(empImp)}` : '', empExp ? `empresa_exportadora=${encodeURIComponent(empExp)}` : '');
    }
    
    const url = `/dashboard/stats?${urlParams.toString()}`;
    console.log('🔗 Fazendo requisição para:', `${API_BASE_URL}${url}`);
    
    // Usar retry com backoff exponencial
    return await retryWithBackoff(async () => {
      // Verificar saúde do backend primeiro (não bloqueante)
      try {
        const isHealthy = await checkBackendHealth();
        if (!isHealthy) {
          console.warn('⚠️ Backend health check falhou, mas tentando requisição mesmo assim...');
        }
      } catch (healthError) {
        console.warn('⚠️ Erro no health check, mas continuando:', healthError.message);
      }

      const response = await api.get(url, {
        timeout: 45000, // 45 segundos (reduzido de 60s para evitar timeouts muito longos)
        validateStatus: (status) => status < 500, // Aceitar até 499 sem lançar erro
      });
      
      // Verificar status HTTP
      if (response.status >= 400) {
        // Se retornou HTML em caso de erro
        if (typeof response.data === 'string' && response.data.trim().startsWith('<!')) {
          throw new Error(`Erro ${response.status}: Servidor retornou HTML. Verifique os logs do backend.`);
        }
        const detail = response.data?.detail;
        const detailStr = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail.map(d => d?.msg || JSON.stringify(d)).join(', ') : (detail && typeof detail === 'object' ? JSON.stringify(detail) : response.data?.detail || response.data || response.statusText));
        throw new Error(`Erro ${response.status}: ${detailStr}`);
      }
      
      // Validar resposta
      if (!response || !response.data) {
        throw new Error('Resposta vazia do servidor');
      }
      
      // Verificar se não é HTML
      if (typeof response.data === 'string' && response.data.trim().startsWith('<!')) {
        console.error('❌ Resposta HTML recebida:', response.data.substring(0, 300));
        throw new Error('Servidor retornou HTML ao invés de JSON. Verifique se o backend está rodando corretamente.');
      }
      
      console.log('✅ Resposta válida recebida');
      return response;
    }, 3, 1000); // 3 retries, começando com 1 segundo
  },
};

export const buscaAPI = {
  buscar: (filtros) => {
    // Converter NCM único para lista se necessário
    const filtrosProcessados = { ...filtros };
    if (filtrosProcessados.ncm && !filtrosProcessados.ncms) {
      filtrosProcessados.ncms = [filtrosProcessados.ncm];
      delete filtrosProcessados.ncm;
    }
    return api.post('/buscar', filtrosProcessados);
  },
};

export const empresasAPI = {
  /** Fallback: usa endpoint de debug quando autocomplete falha (ex.: 404 em produção). */
  debugEmpresas: (tipo, limite = 30, busca = '') => {
    const params = new URLSearchParams({ limite: String(limite) });
    if (tipo) params.set('tipo', tipo);
    if (busca) params.set('busca', busca);
    return api.get(`/dashboard/debug/empresas?${params.toString()}`);
  },
};

export const ncmAPI = {
  getAnalise: (ncm, anoInicio = 2022, anoFim = 2025) =>
    api.get('/api/empresa-intel/ncm-analise', { params: { ncm, ano_inicio: anoInicio, ano_fim: anoFim } }),
  panoramaGlobal: (ncm, ano = null) =>
    api.get('/api/empresa-intel/panorama-global', { params: ano ? { ncm, ano } : { ncm } }),
};

// API de Empresas Recomendadas
export const empresasRecomendadasAPI = {
  getEmpresasRecomendadas: async (limite = 100, tipo = null, uf = null, ncm = null) => {
    try {
      const params = { limite };
      if (tipo) params.tipo = tipo;
      if (uf) params.uf = uf;
      if (ncm) params.ncm = ncm;
      const response = await api.get('/dashboard/empresas-recomendadas', { params });
      return response.data || { success: false, data: [] };
    } catch (error) {
      console.warn('⚠️ Erro ao buscar empresas recomendadas:', error.message);
      return { success: false, data: [], message: 'Arquivo não encontrado ou vazio' };
    }
  },
  
  getEmpresasImportadoras: async (limite = 10) => {
    try {
      const response = await api.get('/dashboard/empresas-importadoras', { params: { limite } });
      return response.data || { success: false, data: [] };
    } catch (error) {
      console.warn('⚠️ Erro ao buscar empresas importadoras:', error.message);
      return { success: false, data: [] };
    }
  },
  
  getEmpresasExportadoras: async (limite = 10) => {
    try {
      const response = await api.get('/dashboard/empresas-exportadoras', { params: { limite } });
      return response.data || { success: false, data: [] };
    } catch (error) {
      console.warn('⚠️ Erro ao buscar empresas exportadoras:', error.message);
      return { success: false, data: [] };
    }
  },
};

// API de Dados ComexStat
export const comexstatAPI = {
  getDadosComexstat: async () => {
    try {
      const response = await api.get('/dashboard/dados-comexstat');
      return response.data || { success: false, data: null };
    } catch (error) {
      console.warn('⚠️ Erro ao buscar dados ComexStat:', error.message);
      return { success: false, data: null, message: 'Arquivo não encontrado' };
    }
  },
  
  getDadosNCM: async (limite = 100, uf = null, tipo = null) => {
    try {
      const params = { limite };
      if (uf) params.uf = uf;
      if (tipo) params.tipo = tipo;
      const response = await api.get('/dashboard/dados-ncm-comexstat', { params });
      return response.data || { success: false, data: [] };
    } catch (error) {
      console.warn('⚠️ Erro ao buscar dados NCM ComexStat:', error.message);
      return { success: false, data: [] };
    }
  },
};

/** BigQuery Base dos Dados + relatório estado/NCM + DOU */
export const dadosReaisAPI = {
  getExportadoras: (ano = 2021, limit = 100) =>
    api.get('/api/empresas/exportadoras', { params: { ano, limit } }),
  getImportadoras: (ano = 2021, limit = 100) =>
    api.get('/api/empresas/importadoras', { params: { ano, limit } }),
  getNcmsPorCnpj: (cnpj) => api.get(`/api/empresas/${encodeURIComponent(cnpj)}/ncms`),
  getRelatorioEstadoNcm: (ano) =>
    api.get('/api/relatorio/estado-ncm-empresa', { params: ano != null ? { ano } : {} }),
  popularEstadoNcmBq: (ano = 2021) =>
    api.post('/api/relatorio/popular-estado-ncm-bq', null, { params: { ano } }),
  getDouNcms: (q) => api.get('/api/diario-oficial/ncms', { params: { q } }),
};

/** Sincronização BigQuery → PostgreSQL (admin) */
export const adminSyncAPI = {
  sincronizarTudo: (ano = 2021, adminToken) =>
    api.post('/admin/sincronizar/tudo', null, {
      params: { ano },
      headers: adminToken ? { 'X-Admin-Token': adminToken } : {},
    }),
};

/** Dashboard apenas PostgreSQL (pós-sync) */
export const dashboardLocalAPI = {
  buscar: (params = {}) => api.get('/api/dashboard/buscar', { params }),
};

/** Dashboard principal + autocomplete a partir da tabela BigQuery empresas_ncm_import_export_uf */
export const comexDashboardBqAPI = {
  autocompleteEmpresa: (q, tipo = '', limit = 25) =>
    api.get('/api/comex-dashboard/autocomplete/empresa', {
      params: { q: q || '', tipo: tipo || '', limit },
    }),
  getDashboardStats: async (paramsObj = {}) => {
    const urlParams = buildComexDashboardBqQueryParams(paramsObj);
    const url = `/api/comex-dashboard/dashboard-stats?${urlParams.toString()}`;
    return await retryWithBackoff(async () => {
      // Acorda instância free do Render antes da query pesada do BigQuery
      await checkBackendHealth(120000);
      const response = await api.get(url, {
        timeout: 240000, // 4 min — várias queries BQ em sequência / paralelo
        validateStatus: (status) => status < 500,
      });
      if (response.status >= 400) {
        const detail = response.data?.detail;
        const detailStr =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d?.msg || JSON.stringify(d)).join(', ')
              : JSON.stringify(detail || response.data || response.statusText);
        throw new Error(`Erro ${response.status}: ${detailStr}`);
      }
      if (!response || !response.data) {
        throw new Error('Resposta vazia do servidor');
      }
      if (typeof response.data === 'string' && response.data.trim().startsWith('<!')) {
        throw new Error('Servidor retornou HTML ao invés de JSON.');
      }
      return response;
    }, 4, 2500);
  },
  getTabelaDetalhada: (paramsObj = {}) => {
    const urlParams = buildComexDashboardBqQueryParams(paramsObj);
    urlParams.append('page', String(Math.max(1, parseInt(paramsObj.page, 10) || 1)));
    urlParams.append(
      'page_size',
      String(Math.min(100, Math.max(1, parseInt(paramsObj.page_size, 10) || 10)))
    );
    return api.get(`/api/comex-dashboard/tabela-detalhada?${urlParams.toString()}`, {
      timeout: 240000,
    });
  },
};

export const coletaAPI = {
  coletarDados: () => api.post('/coletar-dados'),
};

export const healthAPI = {
  check: () => api.get('/health'),
};

// Administração de usuários (aprovação de cadastros) — requer admin
export const adminUsuariosAPI = {
  me: () => api.get('/admin/usuarios/me'),
  pendentes: () => api.get('/admin/usuarios/pendentes'),
  aprovar: (email) => api.post('/admin/usuarios/aprovar', { email }),
  recusar: (email) => api.post('/admin/usuarios/recusar', { email }),
};

