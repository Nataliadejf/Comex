import React, { useMemo, useState } from 'react';
import { Alert, Radio, Spin } from 'antd';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const fmtUsd = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(
    v || 0
  );

function pivotarSerie(serie) {
  const map = {};
  (serie || []).forEach(({ periodo, tipo, valor_usd, valor_usd_projetado, projetado }) => {
    if (!periodo) return;
    if (!map[periodo]) {
      map[periodo] = { periodo, projetado: false };
    }
    const key = tipo === 'EXP' ? 'EXP' : 'IMP';
    if (projetado) {
      map[periodo][`${key}_proj`] = valor_usd_projetado ?? valor_usd;
      map[periodo].projetado = true;
    } else {
      map[periodo][key] = (map[periodo][key] || 0) + (valor_usd || 0);
    }
  });
  return Object.values(map).sort((a, b) => a.periodo.localeCompare(b.periodo));
}

export default function EmpresaTimeline({
  serie = [],
  projecao = [],
  loading = false,
  aviso = null,
  height = 300,
}) {
  const [janela, setJanela] = useState('36');

  const chartData = useMemo(() => {
    const merged = [
      ...serie.map((s) => ({ ...s, projetado: false })),
      ...projecao.flatMap((p) => [
        { periodo: p.periodo, tipo: 'IMP', valor_usd_projetado: p.valor_usd_projetado, projetado: true },
        { periodo: p.periodo, tipo: 'EXP', valor_usd_projetado: p.valor_usd_projetado, projetado: true },
      ]),
    ];
    let pivoted = pivotarSerie(merged);
    const n = parseInt(janela, 10);
    if (n > 0 && n < 900 && pivoted.length > n) {
      pivoted = pivoted.slice(-n);
    }
    return pivoted;
  }, [serie, projecao, janela]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin />
      </div>
    );
  }

  return (
    <div>
      {aviso && <Alert type="warning" showIcon message={aviso} style={{ marginBottom: 12 }} />}
      <div style={{ marginBottom: 12, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Radio.Group value={janela} onChange={(e) => setJanela(e.target.value)} size="small">
          <Radio.Button value="12">12m</Radio.Button>
          <Radio.Button value="24">24m</Radio.Button>
          <Radio.Button value="36">36m</Radio.Button>
          <Radio.Button value="999">Todos</Radio.Button>
        </Radio.Group>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="periodo" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} />
          <Tooltip formatter={(v) => fmtUsd(v)} />
          <Legend />
          <Line type="monotone" dataKey="IMP" name="Importação" stroke="#2563EB" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="EXP" name="Exportação" stroke="#16A34A" strokeWidth={2} dot={false} />
          <Line
            type="monotone"
            dataKey="IMP_proj"
            name="Importação (proj.)"
            stroke="#2563EB"
            strokeDasharray="6 3"
            strokeWidth={1.5}
            dot={false}
            opacity={0.55}
          />
          <Line
            type="monotone"
            dataKey="EXP_proj"
            name="Exportação (proj.)"
            stroke="#16A34A"
            strokeDasharray="6 3"
            strokeWidth={1.5}
            dot={false}
            opacity={0.55}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
