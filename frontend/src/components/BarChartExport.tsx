import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrencyUSD } from "../utils/formatters";

type Row = { cnpj: string; razao_social: string; total_exportacao_fob: number };

const BarChartExport: React.FC<{ data: Row[] }> = ({ data }) => {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-base font-semibold text-slate-900">Top 10 empresas por exportação</h3>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 12 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tickFormatter={(v) => formatCurrencyUSD(Number(v))} />
            <YAxis dataKey="razao_social" type="category" width={180} />
            <Tooltip
              formatter={(value) => formatCurrencyUSD(Number(value))}
              labelFormatter={(_, payload) => {
                const item = payload?.[0]?.payload as Row | undefined;
                return item ? `${item.razao_social} (${item.cnpj})` : "";
              }}
            />
            <Bar dataKey="total_exportacao_fob" fill="#16a34a" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default BarChartExport;
