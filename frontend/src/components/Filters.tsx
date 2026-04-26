import React from "react";

interface FiltersProps {
  empresa: string;
  ano?: number;
  mes?: number;
  uf?: string;
  ncm: string;
  anos: number[];
  meses: number[];
  ufs: string[];
  onChange: (field: string, value: string | number | undefined) => void;
  onApply: () => void;
  onClear: () => void;
}

const Filters: React.FC<FiltersProps> = ({
  empresa,
  ano,
  mes,
  uf,
  ncm,
  anos,
  meses,
  ufs,
  onChange,
  onApply,
  onClear,
}) => {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-5">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="Buscar CNPJ ou Razão Social"
          value={empresa}
          onChange={(event) => onChange("empresa", event.target.value)}
        />
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={ano ?? ""}
          onChange={(event) => onChange("ano", event.target.value ? Number(event.target.value) : undefined)}
        >
          <option value="">Todos os anos</option>
          {anos.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={mes ?? ""}
          onChange={(event) => onChange("mes", event.target.value ? Number(event.target.value) : undefined)}
        >
          <option value="">Todos os meses</option>
          {meses.map((item) => (
            <option key={item} value={item}>
              {String(item).padStart(2, "0")}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={uf ?? ""}
          onChange={(event) => onChange("uf", event.target.value || undefined)}
        >
          <option value="">Todas as UFs</option>
          {ufs.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="Buscar NCM"
          value={ncm}
          onChange={(event) => onChange("ncm", event.target.value)}
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          onClick={onApply}
        >
          Aplicar filtros
        </button>
        <button
          type="button"
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          onClick={onClear}
        >
          Limpar
        </button>
      </div>
    </div>
  );
};

export default Filters;
