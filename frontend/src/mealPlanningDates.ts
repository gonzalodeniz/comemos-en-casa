export type CalendarDate = `${number}-${string}-${string}`;
export type CalendarView = "week" | "month";

export function parseCalendarDate(value: string): Date {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) throw new Error("Invalid calendar date");
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(year, month - 1, day, 12);
  if (
    parsed.getFullYear() !== year ||
    parsed.getMonth() !== month - 1 ||
    parsed.getDate() !== day
  ) {
    throw new Error("Invalid calendar date");
  }
  return parsed;
}

export function formatCalendarDate(value: Date): CalendarDate {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}` as CalendarDate;
}

export function localToday(): CalendarDate {
  return formatCalendarDate(new Date());
}

export function addCalendarDays(value: string, amount: number): CalendarDate {
  const result = parseCalendarDate(value);
  result.setDate(result.getDate() + amount);
  return formatCalendarDate(result);
}

export function startOfWeekMonday(value: string): CalendarDate {
  const parsed = parseCalendarDate(value);
  const daysSinceMonday = (parsed.getDay() + 6) % 7;
  return addCalendarDays(value, -daysSinceMonday);
}

export function shiftMonthClamped(value: string, monthOffset: number): CalendarDate {
  const source = parseCalendarDate(value);
  const originalDay = source.getDate();
  const destinationFirst = new Date(
    source.getFullYear(),
    source.getMonth() + monthOffset,
    1,
    12,
  );
  const lastDay = new Date(
    destinationFirst.getFullYear(),
    destinationFirst.getMonth() + 1,
    0,
    12,
  ).getDate();
  destinationFirst.setDate(Math.min(originalDay, lastDay));
  return formatCalendarDate(destinationFirst);
}

export function annualMaximumEndDate(value: string): CalendarDate {
  const start = parseCalendarDate(value);
  if (start.getMonth() === 1 && start.getDate() === 29) {
    return `${start.getFullYear() + 1}-02-28` as CalendarDate;
  }
  const anniversary = new Date(
    start.getFullYear() + 1,
    start.getMonth(),
    start.getDate(),
    12,
  );
  anniversary.setDate(anniversary.getDate() - 1);
  return formatCalendarDate(anniversary);
}

export function visibleDateRange(
  referenceDate: string,
  view: CalendarView,
): { start: CalendarDate; end: CalendarDate; dates: CalendarDate[] } {
  if (view === "week") {
    const start = startOfWeekMonday(referenceDate);
    const dates = Array.from({ length: 7 }, (_, index) => addCalendarDays(start, index));
    return { start, end: dates[6], dates };
  }

  const reference = parseCalendarDate(referenceDate);
  const firstOfMonth = formatCalendarDate(
    new Date(reference.getFullYear(), reference.getMonth(), 1, 12),
  );
  const lastOfMonth = formatCalendarDate(
    new Date(reference.getFullYear(), reference.getMonth() + 1, 0, 12),
  );
  const start = startOfWeekMonday(firstOfMonth);
  const last = parseCalendarDate(lastOfMonth);
  const end = addCalendarDays(lastOfMonth, 6 - ((last.getDay() + 6) % 7));
  const dates: CalendarDate[] = [];
  for (let current = start; current <= end; current = addCalendarDays(current, 1)) {
    dates.push(current);
  }
  return { start, end, dates };
}

export function formatDateLabel(value: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("es", options).format(parseCalendarDate(value));
}
