"""Projeção simples de série temporal (média móvel + tendência linear)."""
from __future__ import annotations

import statistics
from datetime import date
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta


def projetar_serie(serie: List[Dict[str, Any]], n_meses: int = 6) -> List[Dict[str, Any]]:
    """
    Projeta os próximos n_meses com base na média dos últimos 12 pontos e tendência linear.
    Cada item de entrada: {ano, mes, valor_usd} ou {periodo, valor_usd}.
    """
    parsed: List[Dict[str, Any]] = []
    for s in serie:
        if s.get("ano") and s.get("mes"):
            y, m = int(s["ano"]), int(s["mes"])
        elif s.get("periodo"):
            parts = str(s["periodo"]).split("-")
            if len(parts) >= 2:
                y, m = int(parts[0]), int(parts[1])
            else:
                continue
        else:
            continue
        parsed.append({"ano": y, "mes": m, "valor_usd": float(s.get("valor_usd") or 0)})

    if len(parsed) < 3:
        return []

    parsed.sort(key=lambda x: (x["ano"], x["mes"]))
    valores = [p["valor_usd"] for p in parsed]
    janela = valores[-12:]
    media = statistics.mean(janela)
    desvio = statistics.stdev(janela) if len(janela) > 1 else 0.0
    n = len(janela)
    x_vals = list(range(n))
    x_mean = statistics.mean(x_vals)
    y_mean = media
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, janela))
    den = sum((x - x_mean) ** 2 for x in x_vals) or 1.0
    slope = num / den

    ultimo = parsed[-1]
    base_date = date(int(ultimo["ano"]), int(ultimo["mes"]), 1)
    projecoes: List[Dict[str, Any]] = []
    for i in range(1, n_meses + 1):
        proj_date = base_date + relativedelta(months=i)
        valor_proj = max(0.0, media + slope * i)
        confianca = max(0.0, 1.0 - (desvio / media if media else 1.0))
        projecoes.append(
            {
                "periodo": proj_date.strftime("%Y-%m"),
                "ano": proj_date.year,
                "mes": proj_date.month,
                "valor_usd_projetado": round(valor_proj, 2),
                "confianca": round(confianca, 2),
                "projetado": True,
            }
        )
    return projecoes
