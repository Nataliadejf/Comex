import React from "react";
import {
  Bar,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
} from "recharts";
import { formatCurrencyUSD, formatMonthYear } from "../utils/formatters";

type TimelineRow = {
  ano: number;
  mes: number;
  total_importacao_fob: number;
  total_exportacao_fob: number;
};

const MonthlyChart: React.FC<{ data: TimelineRow[] }> = ({ data }) => {
  const chartData = data.map((item) => ({
    ...item,
    periodo: formatMonthYear(item.ano, item.mes),
  }));

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-base font-semibold text-slate-900">Evolução mensal</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="periodo" />
            <YAxis tickFormatter={(v) => formatCurrencyUSD(Number(v))} />
            <Tooltip formatter={(value) => formatCurrencyUSD(Number(value))} />
            <Legend />
            <Bar dataKey="total_importacao_fob" name="Importação" fill="#2563eb" />
            <Bar dataKey="total_exportacao_fob" name="Exportação" fill="#16a34a" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MonthlyChart;
