import React from "react";
import { formatCurrencyUSD } from "../utils/formatters";

type SortOrder = "asc" | "desc";

type DataRow = {
  cnpj: string;
  razao_social: string;
  sigla_uf: string;
  id_ncm: string;
  ano: number;
  mes: number;
  total_importacao_fob: number;
  total_exportacao_fob: number;
  saldo: number;
};

interface DataTableProps {
  rows: DataRow[];
  page: number;
  pageSize: number;
  total: number;
  sortBy: string;
  sortOrder: SortOrder;
  onSort: (column: string) => void;
  onPageChange: (page: number) => void;
  onExportCsv: () => void;
}

const columns: Array<{ key: string; label: string }> = [
  { key: "cnpj", label: "CNPJ" },
  { key: "razao_social", label: "Razão Social" },
  { key: "sigla_uf", label: "UF" },
  { key: "id_ncm", label: "NCM" },
  { key: "ano", label: "Ano" },
  { key: "mes", label: "Mês" },
  { key: "total_importacao_fob", label: "Total Importação" },
  { key: "total_exportacao_fob", label: "Total Exportação" },
  { key: "saldo", label: "Saldo" },
];

const DataTable: React.FC<DataTableProps> = ({
  rows,
  page,
  pageSize,
  total,
  sortBy,
  sortOrder,
  onSort,
  onPageChange,
  onExportCsv,
}) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(total, page * pageSize);

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-900">Tabela detalhada</h3>
        <button
          type="button"
          className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-700"
          onClick={onExportCsv}
        >
          Exportar CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left">
              {columns.map((column) => (
                <th key={column.key} className="cursor-pointer px-3 py-2" onClick={() => onSort(column.key)}>
                  {column.label}
                  {sortBy === column.key ? (sortOrder === "asc" ? " ↑" : " ↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={`${row.cnpj}-${row.id_ncm}-${idx}`} className="border-b border-slate-100">
                <td className="px-3 py-2">{row.cnpj}</td>
                <td className="px-3 py-2">{row.razao_social}</td>
                <td className="px-3 py-2">{row.sigla_uf}</td>
                <td className="px-3 py-2">{row.id_ncm}</td>
                <td className="px-3 py-2">{row.ano}</td>
                <td className="px-3 py-2">{String(row.mes).padStart(2, "0")}</td>
                <td className="px-3 py-2">{formatCurrencyUSD(row.total_importacao_fob)}</td>
                <td className="px-3 py-2">{formatCurrencyUSD(row.total_exportacao_fob)}</td>
                <td className="px-3 py-2">{formatCurrencyUSD(row.saldo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
        <span>
          Mostrando {start}-{end} de {total}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded border border-slate-300 px-2 py-1 disabled:opacity-50"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Anterior
          </button>
          <span>
            Página {page} de {totalPages}
          </span>
          <button
            type="button"
            className="rounded border border-slate-300 px-2 py-1 disabled:opacity-50"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Próxima
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataTable;
