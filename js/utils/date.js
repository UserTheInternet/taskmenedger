export function toIsoDate(date) {
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-');
}

export function fromIsoDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay() === 0 ? 7 : d.getDay();
  d.setDate(d.getDate() - day + 1);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function getWeekDates(baseIso) {
  const base = fromIsoDate(baseIso);
  const monday = startOfWeek(base);
  return Array.from({ length: 7 }, (_, i) => {
    const x = new Date(monday);
    x.setDate(monday.getDate() + i);
    return x;
  });
}

export function getMonthDates(baseIso) {
  const base = fromIsoDate(baseIso);
  const first = new Date(base.getFullYear(), base.getMonth(), 1);
  const last = new Date(base.getFullYear(), base.getMonth() + 1, 0);
  const res = [];
  for (let d = 1; d <= last.getDate(); d += 1) {
    res.push(new Date(base.getFullYear(), base.getMonth(), d));
  }
  return res;
}

export function getIsoWeekKey(dateOrIso) {
  const date = typeof dateOrIso === 'string' ? fromIsoDate(dateOrIso) : new Date(dateOrIso);
  const target = new Date(date.valueOf());
  const dayNr = (date.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  const firstThursday = new Date(target.getFullYear(), 0, 4);
  const firstDayNr = (firstThursday.getDay() + 6) % 7;
  firstThursday.setDate(firstThursday.getDate() - firstDayNr + 3);
  const week = 1 + Math.round((target - firstThursday) / 604800000);
  return `${target.getFullYear()}-W${String(week).padStart(2, '0')}`;
}

export function formatDayLabel(date) {
  const names = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
  return `${names[date.getDay()]} ${String(date.getDate()).padStart(2, '0')}.${String(date.getMonth() + 1).padStart(2, '0')}`;
}

export function getPeriodColumns(mode, selectedDate) {
  if (mode === 'day') {
    const d = fromIsoDate(selectedDate);
    return [{ key: selectedDate, label: formatDayLabel(d) }];
  }

  const dates = mode === 'month' ? getMonthDates(selectedDate) : getWeekDates(selectedDate);
  return dates.map((d) => ({ key: toIsoDate(d), label: formatDayLabel(d) }));
}

export function shiftDateByMode(selectedDate, mode, dir) {
  const date = fromIsoDate(selectedDate);
  if (mode === 'month') {
    date.setMonth(date.getMonth() + dir);
  } else if (mode === 'week') {
    date.setDate(date.getDate() + dir * 7);
  } else {
    date.setDate(date.getDate() + dir);
  }
  return toIsoDate(date);
}

export function weekRangeLabel(selectedDate) {
  const week = getWeekDates(selectedDate);
  const fmt = (d) => `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`;
  return `${fmt(week[0])} — ${fmt(week[4])}`;
}
