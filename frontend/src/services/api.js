import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('Erro da API:', error.response.data);
    } else if (error.request) {
      console.error('Erro de conexão:', error.request);
    } else {
      console.error('Erro:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

// Endpoints
export const dashboardAPI = {
  getStats: (meses = 3, tipoOperacao = null, ncm = null, empresa = null, ncms = null) => {
    const params = new URLSearchParams({ meses: meses.toString() });
    if (tipoOperacao) params.append('tipo_operacao', tipoOperacao);
    if (ncm) params.append('ncm', ncm);
    if (empresa) params.append('empresa', empresa);
    if (ncms) params.append('ncms', ncms); // Múltiplos NCMs separados por vírgula
    return api.get(`/dashboard/stats?${params.toString()}`);
  },
  exportRelatorio: (meses = 3, tipoOperacao = null, ncm = null, empresa = null, formato = 'excel') => {
    const params = new URLSearchParams({ meses: meses.toString(), formato });
    if (tipoOperacao) params.append('tipo_operacao', tipoOperacao);
    if (ncm) params.append('ncm', ncm);
    if (empresa) params.append('empresa', empresa);
    return api.get(`/dashboard/export?${params.toString()}`, { responseType: 'blob' });
  },
};

export const buscaAPI = {
  buscar: (filtros) => api.post('/buscar', filtros),
};

export const ncmAPI = {
  getAnalise: (ncm) => api.get(`/ncm/${ncm}/analise`),
};

export const coletaAPI = {
  coletarDados: () => api.post('/coletar-dados'),
};

export const healthAPI = {
  check: () => api.get('/health'),
};

export const empresasAPI = {
  autocomplete: (q, limit = 10) => api.get(`/empresas/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`),
};

export const ncmsAPI = {
  verificar: (ncms) => api.get(`/ncms/verificar?ncms=${encodeURIComponent(ncms)}`),
};

