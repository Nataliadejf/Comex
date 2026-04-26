import React from "react";
import { formatCurrencyUSD } from "../utils/formatters";

type HeatMapRow = {
  sigla_uf: string;
  total_importacao_fob: number;
  total_exportacao_fob: number;
};

type Mode = "importacao" | "exportacao";

const UF_ORDER = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
  "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
  "RS", "RO", "RR", "SC", "SP", "SE", "TO",
];

const HeatMapUF: React.FC<{
  data: HeatMapRow[];
  mode: Mode;
  onModeChange: (mode: Mode) => void;
}> = ({ data, mode, onModeChange }) => {
  const byUf = new Map(data.map((item) => [item.sigla_uf, item]));
  const values = data.map((item) =>
    mode === "importacao" ? Number(item.total_importacao_fob || 0) : Number(item.total_exportacao_fob || 0)
  );
  const maxValue = values.length ? Math.max(...values) : 0;

  const getColor = (value: number) => {
    if (maxValue <= 0) return "#f1f5f9";
    const intensity = Math.max(0.15, value / maxValue);
    if (mode === "importacao") return `rgba(37, 99, 235, ${intensity})`;
    return `rgba(22, 163, 74, ${intensity})`;
  };

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-900">Mapa de calor por UF</h3>
        <div className="flex gap-2">
          <button
            type="button"
            className={`rounded-lg px-3 py-1 text-sm ${mode === "importacao" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700"}`}
            onClick={() => onModeChange("importacao")}
          >
            Importação
          </button>
          <button
            type="button"
            className={`rounded-lg px-3 py-1 text-sm ${mode === "exportacao" ? "bg-green-600 text-white" : "bg-slate-100 text-slate-700"}`}
            onClick={() => onModeChange("exportacao")}
          >
            Exportação
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 lg:grid-cols-9">
        {UF_ORDER.map((uf) => {
          const row = byUf.get(uf);
          const value =
            mode === "importacao"
              ? Number(row?.total_importacao_fob || 0)
              : Number(row?.total_exportacao_fob || 0);
          return (
            <div
              key={uf}
              className="rounded-lg p-3 text-center text-xs font-semibold text-slate-900"
              style={{ backgroundColor: getColor(value) }}
              title={`${uf} - ${formatCurrencyUSD(value)}`}
            >
              <div>{uf}</div>
              <div className="mt-1 text-[10px] font-normal">{formatCurrencyUSD(value)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default HeatMapUF;
