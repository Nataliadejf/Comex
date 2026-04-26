import api from "./api";

export interface DashboardFilters {
  empresa?: string;
  ano?: number;
  mes?: number;
  uf?: string;
  ncm?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export interface DashboardDataResponse {
  kpis: {
    total_importado: number;
    total_exportado: number;
    saldo_comercial: number;
    empresas_unicas: number;
  };
  timeline: Array<{
    ano: number;
    mes: number;
    total_importacao_fob: number;
    total_exportacao_fob: number;
  }>;
  top_import: Array<{
    cnpj: string;
    razao_social: string;
    total_importacao_fob: number;
  }>;
  top_export: Array<{
    cnpj: string;
    razao_social: string;
    total_exportacao_fob: number;
  }>;
  heatmap: Array<{
    sigla_uf: string;
    total_importacao_fob: number;
    total_exportacao_fob: number;
  }>;
  table: Array<{
    cnpj: string;
    razao_social: string;
    sigla_uf: string;
    id_ncm: string;
    ano: number;
    mes: number;
    total_importacao_fob: number;
    total_exportacao_fob: number;
    saldo: number;
  }>;
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

const normalizeParams = (filters: DashboardFilters): Record<string, string | number> => {
  const params: Record<string, string | number> = {};
  if (filters.empresa) params.empresa = filters.empresa.trim();
  if (filters.ano) params.ano = filters.ano;
  if (filters.mes) params.mes = filters.mes;
  if (filters.uf) params.uf = filters.uf;
  if (filters.ncm) params.ncm = filters.ncm.trim();
  if (filters.page) params.page = filters.page;
  if (filters.pageSize) params.page_size = filters.pageSize;
  if (filters.sortBy) params.sort_by = filters.sortBy;
  if (filters.sortOrder) params.sort_order = filters.sortOrder;
  return params;
};

export const comexDashboardAPI = {
  getFilterOptions: async () => {
    const response = await api.get("/api/comex-dashboard/options");
    return response.data as { anos: number[]; meses: number[]; ufs: string[] };
  },

  getDashboardData: async (filters: DashboardFilters) => {
    const response = await api.get("/api/comex-dashboard/data", {
      params: normalizeParams(filters),
    });
    return response.data as DashboardDataResponse;
  },

  getCsvExportUrl: (filters: DashboardFilters) => {
    const search = new URLSearchParams();
    const params = normalizeParams(filters);
    Object.entries(params).forEach(([key, value]) => {
      if (["page", "page_size", "sort_by", "sort_order"].includes(key)) return;
      search.set(key, String(value));
    });
    return `${api.defaults.baseURL}/api/comex-dashboard/export-csv?${search.toString()}`;
  },
};
