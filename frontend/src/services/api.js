import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://comex-backend-gecp.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 segundos (aumentado de 30s)
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
const checkBackendHealth = async () => {
  try {
    const healthResponse = await api.get('/health', { timeout: 5000 });
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
      const isConnectionError = 
        error.code === 'ERR_NETWORK' || 
        error.code === 'ECONNREFUSED' ||
        error.code === 'ETIMEDOUT' ||
        error.message?.includes('Network Error') ||
        error.message?.includes('timeout') ||
        error.message?.includes('Não foi possível conectar');
      
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

// Endpoints
export const dashboardAPI = {
  getStats: async (paramsObj = {}) => {
    // Sempre usar objeto de parâmetros
    const params = paramsObj || {};

    const urlParams = new URLSearchParams();
    urlParams.append('meses', params.meses || 24);
    if (params.tipoOperacao) urlParams.append('tipo_operacao', params.tipoOperacao);
    if (params.ncm) urlParams.append('ncm', params.ncm);
    if (params.ncms && Array.isArray(params.ncms)) {
      params.ncms.forEach(ncm => urlParams.append('ncms', ncm));
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
        throw new Error(`Erro ${response.status}: ${response.data?.detail || response.data || response.statusText}`);
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
  autocompleteImportadoras: (query, limit = 20) => 
    api.get(`/empresas/autocomplete/importadoras?q=${encodeURIComponent(query)}&limit=${limit}`),
  autocompleteExportadoras: (query, limit = 20) => 
    api.get(`/empresas/autocomplete/exportadoras?q=${encodeURIComponent(query)}&limit=${limit}`),
};

export const ncmAPI = {
  getAnalise: (ncm) => api.get(`/ncm/${ncm}/analise`),
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

export const coletaAPI = {
  coletarDados: () => api.post('/coletar-dados'),
};

export const healthAPI = {
  check: () => api.get('/health'),
};

