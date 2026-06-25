export function isTradingHours(now: Date): boolean {
  const day = now.getDay();
  if (day === 0 || day === 6) return false;
  const m = now.getHours() * 60 + now.getMinutes();
  const am = m >= 9 * 60 + 30 && m <= 11 * 60 + 30;
  const pm = m >= 13 * 60 && m <= 15 * 60;
  return am || pm;
}

export function refetchIntervalMs(now: Date): number | false {
  return isTradingHours(now) ? 60000 : false;
}
