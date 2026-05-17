import api from '../services/api';

export const empresasApi = {
  listar: (params) => api.get('/api/empresas', { params }),
  perfil: (cnpj) => api.get(`/api/empresas/${encodeURIComponent(cnpj)}`),
  ncms: (cnpj, params) => api.get(`/api/empresas/${encodeURIComponent(cnpj)}/ncm`, { params }),
  estados: (cnpj, params) => api.get(`/api/empresas/${encodeURIComponent(cnpj)}/estados`, { params }),
  timeline: (cnpj) => api.get(`/api/empresas/${encodeURIComponent(cnpj)}/timeline`),
  ranking: (params) => api.get('/api/empresas/ranking', { params }),
  dou: (params) => api.get('/api/dou', { params }),
  douEmpresa: (cnpj, params) => api.get(`/api/dou/${encodeURIComponent(cnpj)}`, { params }),
  ncmDetalhe: (codigo) => api.get(`/api/ncm/${encodeURIComponent(codigo)}`),
  serieTemporal: (cnpj, params) =>
    api.get(`/api/empresas/${encodeURIComponent(cnpj)}/serie-temporal`, { params }),
  projecao: (cnpj, params) =>
    api.get(`/api/empresas/${encodeURIComponent(cnpj)}/projecao`, { params }),
  rankingSerie: (params) => api.get('/api/empresas/ranking/serie', { params }),
};
