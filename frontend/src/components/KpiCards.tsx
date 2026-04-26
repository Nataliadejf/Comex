import React from "react";
import { formatCurrencyUSD, formatInteger } from "../utils/formatters";

interface Kpis {
  total_importado: number;
  total_exportado: number;
  saldo_comercial: number;
  empresas_unicas: number;
}

const KpiCards: React.FC<{ kpis: Kpis }> = ({ kpis }) => {
  const cards = [
    { label: "Total Importado", value: formatCurrencyUSD(kpis.total_importado) },
    { label: "Total Exportado", value: formatCurrencyUSD(kpis.total_exportado) },
    { label: "Saldo Comercial", value: formatCurrencyUSD(kpis.saldo_comercial) },
    { label: "Empresas Únicas", value: formatInteger(kpis.empresas_unicas) },
  ];

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <div key={card.label} className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">{card.label}</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{card.value}</p>
        </div>
      ))}
    </div>
  );
};

export default KpiCards;
