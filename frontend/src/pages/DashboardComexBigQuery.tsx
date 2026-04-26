import React, { useEffect, useMemo, useState } from "react";
import Filters from "../components/Filters";
import KpiCards from "../components/KpiCards";
import MonthlyChart from "../components/LineChart";
import BarChartImport from "../components/BarChartImport";
import BarChartExport from "../components/BarChartExport";
import HeatMapUF from "../components/HeatMapUF";
import DataTable from "../components/DataTable";
import { DashboardDataResponse, DashboardFilters, comexDashboardAPI } from "../services/bigquery";

type SortOrder = "asc" | "desc";
type HeatMode = "importacao" | "exportacao";

const initialData: DashboardDataResponse = {
  kpis: {
    total_importado: 0,
    total_exportado: 0,
    saldo_comercial: 0,
    empresas_unicas: 0,
  },
  timeline: [],
  top_import: [],
  top_export: [],
  heatmap: [],
  table: [],
  pagination: { page: 1, page_size: 25, total: 0, total_pages: 1 },
};

/** Dashboard focado na tabela BigQuery empresas_ncm_import_export_uf (rota separada). */
const DashboardComexBigQuery: React.FC = () => {
  const [filters, setFilters] = useState<DashboardFilters>({
    page: 1,
    pageSize: 25,
    sortBy: "total_importacao_fob",
    sortOrder: "desc",
  });
  const [draftFilters, setDraftFilters] = useState<DashboardFilters>(filters);
  const [data, setData] = useState<DashboardDataResponse>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [anos, setAnos] = useState<number[]>([]);
  const [meses, setMeses] = useState<number[]>([]);
  const [ufs, setUfs] = useState<string[]>([]);
  const [heatMode, setHeatMode] = useState<HeatMode>("importacao");

  const loadOptions = async () => {
    try {
      const options = await comexDashboardAPI.getFilterOptions();
      setAnos(options.anos || []);
      setMeses(options.meses || []);
      setUfs(options.ufs || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadDashboard = async (activeFilters: DashboardFilters) => {
    setLoading(true);
    setError(null);
    try {
      const response = await comexDashboardAPI.getDashboardData(activeFilters);
      setData(response);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Não foi possível carregar os dados do dashboard.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOptions();
  }, []);

  useEffect(() => {
    loadDashboard(filters);
  }, [filters]);

  const hasNoData = useMemo(() => !loading && data.table.length === 0, [loading, data.table.length]);

  const handleDraftChange = (field: string, value: string | number | undefined) => {
    setDraftFilters((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleApplyFilters = () => {
    setFilters((prev) => ({
      ...prev,
      ...draftFilters,
      page: 1,
    }));
  };

  const handleClear = () => {
    const cleared: DashboardFilters = {
      page: 1,
      pageSize: 25,
      sortBy: "total_importacao_fob",
      sortOrder: "desc",
    };
    setDraftFilters(cleared);
    setFilters(cleared);
  };

  const handleSort = (column: string) => {
    setFilters((prev) => {
      const same = prev.sortBy === column;
      const nextOrder: SortOrder = same && prev.sortOrder === "desc" ? "asc" : "desc";
      return { ...prev, sortBy: column, sortOrder: nextOrder, page: 1 };
    });
  };

  const handleExportCsv = () => {
    const url = comexDashboardAPI.getCsvExportUrl(filters);
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="space-y-4 bg-slate-100 p-4">
      <h1 className="text-2xl font-bold text-slate-900">Dashboard Comex (BigQuery)</h1>

      <Filters
        empresa={String(draftFilters.empresa || "")}
        ano={draftFilters.ano}
        mes={draftFilters.mes}
        uf={draftFilters.uf}
        ncm={String(draftFilters.ncm || "")}
        anos={anos}
        meses={meses}
        ufs={ufs}
        onChange={handleDraftChange}
        onApply={handleApplyFilters}
        onClear={handleClear}
      />

      {error && <div className="rounded-lg bg-red-100 p-3 text-sm text-red-700">{error}</div>}
      {loading && <div className="rounded-lg bg-white p-3 text-sm text-slate-600">Carregando dados...</div>}

      {!loading && (
        <>
          <KpiCards kpis={data.kpis} />
          {hasNoData ? (
            <div className="rounded-xl bg-white p-6 text-center text-slate-600">Nenhum dado encontrado</div>
          ) : (
            <>
              <MonthlyChart data={data.timeline} />
              <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                <BarChartImport data={data.top_import} />
                <BarChartExport data={data.top_export} />
              </div>
              <HeatMapUF data={data.heatmap} mode={heatMode} onModeChange={setHeatMode} />
              <DataTable
                rows={data.table}
                page={data.pagination.page}
                pageSize={data.pagination.page_size}
                total={data.pagination.total}
                sortBy={String(filters.sortBy || "total_importacao_fob")}
                sortOrder={(filters.sortOrder as SortOrder) || "desc"}
                onSort={handleSort}
                onPageChange={(page) => setFilters((prev) => ({ ...prev, page }))}
                onExportCsv={handleExportCsv}
              />
            </>
          )}
        </>
      )}
    </div>
  );
};

export default DashboardComexBigQuery;
