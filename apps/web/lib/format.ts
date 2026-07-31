const isoDatePattern = /^(\d{4})-(\d{2})-(\d{2})/;

export function formatIsoDate(value: string): string {
  const match = isoDatePattern.exec(value);
  if (!match) return value;
  const [, year, month, day] = match;
  return `${day}/${month}/${year}`;
}

export function formatInteger(value: number | undefined): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
    useGrouping: true,
  }).format(Math.round(value ?? 0));
}
