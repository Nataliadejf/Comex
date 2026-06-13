import api from '../services/api';

export const contatosApi = {
  /** Autocomplete por razão social ou CNPJ (retorna lista de sugestões) */
  autocomplete: (q, limit = 20) =>
    api.get('/api/contatos/autocomplete', { params: { q, limit } }),

  /** Perfil completo: dados RF + estabelecimentos + CNAE enriquecido + comex */
  empresa: (cnpj) =>
    api.get(`/api/contatos/empresa/${encodeURIComponent(cnpj)}`),

  /** Lista de empresas filtrada por CNAE / setor / segmento */
  listar: (params = {}) =>
    api.get('/api/contatos/empresas', { params }),

  /** Busca estabelecimentos ativos de um CNPJ raiz */
  estabelecimentos: (cnpjRaiz, params = {}) =>
    api.get(`/api/contatos/estabelecimentos/${encodeURIComponent(cnpjRaiz)}`, { params }),
};
