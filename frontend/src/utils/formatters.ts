export const formatCurrencyUSD = (value: number): string => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
};

export const formatMonthYear = (year: number, month: number): string => {
  const mm = String(month).padStart(2, "0");
  return `${mm}/${year}`;
};

export const formatInteger = (value: number): string => {
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(
    Number(value || 0)
  );
};
