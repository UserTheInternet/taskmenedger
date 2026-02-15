import { getIsoWeekKey, toIsoDate, getWeekDates, getMonthDates, fromIsoDate } from '../utils/date.js';
import { generateTaskId, parseWeekMarkdown, parseSomedayMarkdown, serializeSomedayMarkdown, serializeWeekMarkdown } from '../utils/md.js';
import { vaultFs } from './vaultFs.js';

function emptyIndex() {
  return {
    tasks: [],
    someday: [],
    employees: [],
    weekMaps: {},
    weekFiles: {}
  };
}

function uniq(arr) {
  return [...new Set(arr.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'ru'));
}

function personFileContent(name) {
  return `---\nname: ${name}\nrole: ''\n---\n# ${name}\n`;
}

export async function loadVaultIndex(rootHandle) {
  const index = emptyIndex();

  const weekFiles = (await vaultFs.listFiles(rootHandle, 'weeks')).filter((x) => x.endsWith('.md'));
  for (const fileName of weekFiles) {
    const weekKey = fileName.replace('.md', '');
    const content = await vaultFs.readText(rootHandle, `weeks/${fileName}`);
    const byDate = parseWeekMarkdown(content, weekKey);
    index.weekMaps[weekKey] = byDate;
    index.weekFiles[weekKey] = `weeks/${fileName}`;

    Object.keys(byDate).forEach((date) => {
      byDate[date].forEach((task) => index.tasks.push(task));
    });
  }

  const somedayContent = await vaultFs.readText(rootHandle, 'someday.md');
  index.someday = parseSomedayMarkdown(somedayContent);

  const peopleFiles = (await vaultFs.listFiles(rootHandle, 'people')).filter((x) => x.endsWith('.md'));
  index.employees = uniq(peopleFiles.map((x) => x.replace('.md', '')));

  const taskEmployees = uniq([...index.tasks.map((t) => t.assignee), ...index.someday.map((t) => t.assignee)]);
  index.employees = uniq([...index.employees, ...taskEmployees]);

  return index;
}

async function ensureWeekMap(index, rootHandle, weekKey) {
  if (!index.weekMaps[weekKey]) {
    index.weekMaps[weekKey] = {};
    const weekDates = getWeekDates(`${weekKey.slice(0, 4)}-01-01`);
    weekDates.forEach((d) => {
      index.weekMaps[weekKey][toIsoDate(d)] = [];
    });
    index.weekFiles[weekKey] = `weeks/${weekKey}.md`;
  }

  if (!index.weekFiles[weekKey]) {
    index.weekFiles[weekKey] = `weeks/${weekKey}.md`;
  }

  await saveWeek(index, rootHandle, weekKey);
}

async function saveWeek(index, rootHandle, weekKey) {
  const content = serializeWeekMarkdown(weekKey, index.weekMaps[weekKey] || {});
  await vaultFs.writeText(rootHandle, index.weekFiles[weekKey] || `weeks/${weekKey}.md`, content);
}

async function saveSomeday(index, rootHandle) {
  await vaultFs.writeText(rootHandle, 'someday.md', serializeSomedayMarkdown(index.someday));
}

export async function ensureEmployee(index, rootHandle, employeeName) {
  const name = (employeeName || '').trim();
  if (!name) return null;
  if (!index.employees.includes(name)) {
    index.employees.push(name);
    index.employees = uniq(index.employees);
    await vaultFs.writeText(rootHandle, `people/${name}.md`, personFileContent(name));
  }
  return name;
}

export async function addTask(index, rootHandle, { title, dueDate, assignee = '', someday = false }) {
  const task = {
    id: generateTaskId(),
    title: title.trim(),
    done: false,
    assignee: assignee.trim(),
    dueDate: someday ? '' : dueDate,
    weekKey: someday ? '' : getIsoWeekKey(dueDate),
    someday
  };

  if (task.assignee) await ensureEmployee(index, rootHandle, task.assignee);

  if (someday) {
    index.someday.push(task);
    await saveSomeday(index, rootHandle);
    return task;
  }

  await ensureWeekMap(index, rootHandle, task.weekKey);
  if (!index.weekMaps[task.weekKey][dueDate]) index.weekMaps[task.weekKey][dueDate] = [];
  index.weekMaps[task.weekKey][dueDate].push(task);
  await saveWeek(index, rootHandle, task.weekKey);
  return task;
}

function removeTaskFromWeekMap(index, task) {
  const map = index.weekMaps[task.weekKey];
  if (!map || !map[task.dueDate]) return;
  map[task.dueDate] = map[task.dueDate].filter((t) => t.id !== task.id);
}

export async function toggleTask(index, rootHandle, taskId) {
  const inSomeday = index.someday.find((t) => t.id === taskId);
  if (inSomeday) {
    inSomeday.done = !inSomeday.done;
    await saveSomeday(index, rootHandle);
    return;
  }

  for (const weekKey of Object.keys(index.weekMaps)) {
    for (const date of Object.keys(index.weekMaps[weekKey])) {
      const task = index.weekMaps[weekKey][date].find((t) => t.id === taskId);
      if (task) {
        task.done = !task.done;
        await saveWeek(index, rootHandle, weekKey);
        return;
      }
    }
  }
}

export async function moveTaskToDate(index, rootHandle, taskId, targetDate) {
  const srcSomedayIdx = index.someday.findIndex((t) => t.id === taskId);
  let task = null;

  if (srcSomedayIdx >= 0) {
    task = index.someday.splice(srcSomedayIdx, 1)[0];
    await saveSomeday(index, rootHandle);
  } else {
    for (const weekKey of Object.keys(index.weekMaps)) {
      for (const date of Object.keys(index.weekMaps[weekKey])) {
        const idx = index.weekMaps[weekKey][date].findIndex((t) => t.id === taskId);
        if (idx >= 0) {
          task = index.weekMaps[weekKey][date].splice(idx, 1)[0];
          await saveWeek(index, rootHandle, weekKey);
          break;
        }
      }
      if (task) break;
    }
  }

  if (!task) return;

  task.someday = false;
  task.dueDate = targetDate;
  task.weekKey = getIsoWeekKey(targetDate);
  await ensureWeekMap(index, rootHandle, task.weekKey);
  if (!index.weekMaps[task.weekKey][task.dueDate]) index.weekMaps[task.weekKey][task.dueDate] = [];
  index.weekMaps[task.weekKey][task.dueDate].push(task);
  await saveWeek(index, rootHandle, task.weekKey);
}

export async function moveTaskToSomeday(index, rootHandle, taskId) {
  let task = null;
  for (const weekKey of Object.keys(index.weekMaps)) {
    for (const date of Object.keys(index.weekMaps[weekKey])) {
      const idx = index.weekMaps[weekKey][date].findIndex((t) => t.id === taskId);
      if (idx >= 0) {
        task = index.weekMaps[weekKey][date].splice(idx, 1)[0];
        await saveWeek(index, rootHandle, weekKey);
        break;
      }
    }
    if (task) break;
  }
  if (!task) return;
  task.someday = true;
  task.weekKey = '';
  task.dueDate = '';
  index.someday.push(task);
  await saveSomeday(index, rootHandle);
}

export async function moveTaskAssignee(index, rootHandle, taskId, assignee) {
  await ensureEmployee(index, rootHandle, assignee);

  for (const weekKey of Object.keys(index.weekMaps)) {
    for (const date of Object.keys(index.weekMaps[weekKey])) {
      const task = index.weekMaps[weekKey][date].find((t) => t.id === taskId);
      if (task) {
        task.assignee = assignee;
        await saveWeek(index, rootHandle, weekKey);
        return;
      }
    }
  }

  const s = index.someday.find((t) => t.id === taskId);
  if (s) {
    s.assignee = assignee;
    await saveSomeday(index, rootHandle);
  }
}

export function getTasksForPeriod(index, mode, selectedDate) {
  const all = [];
  const weekMaps = index && index.weekMaps ? index.weekMaps : {};
  Object.values(weekMaps).forEach((byDate) => {
    Object.values(byDate).forEach((arr) => all.push(...arr));
  });

  const selected = fromIsoDate(selectedDate);
  if (mode === 'day') {
    return all.filter((t) => t.dueDate === selectedDate);
  }
  if (mode === 'week') {
    const keys = getWeekDates(selectedDate).map((d) => toIsoDate(d));
    return all.filter((t) => keys.includes(t.dueDate));
  }

  const y = selected.getFullYear();
  const m = selected.getMonth();
  return all.filter((t) => {
    const d = fromIsoDate(t.dueDate);
    return d.getFullYear() === y && d.getMonth() === m;
  });
}

export async function importLegacyLocalStorage(index, rootHandle, selectedDate) {
  const raw = localStorage.getItem('weekly-planner-russian-v2');
  if (!raw) throw new Error('Старые данные не найдены');
  const parsed = JSON.parse(raw);

  const my = Array.isArray(parsed.my) ? parsed.my : [];
  for (const t of my) {
    const dueDate = t.date || selectedDate;
    await addTask(index, rootHandle, {
      title: t.title || 'Без названия',
      dueDate,
      assignee: t.assignee || '',
      someday: t.day === 'Когда-нибудь'
    });
  }

  const teamRaw = Array.isArray(parsed.team) ? parsed.team : [];
  if (teamRaw.length && teamRaw[0] && Array.isArray(teamRaw[0].tasks)) {
    for (const group of teamRaw) {
      const assignee = (group.employee || '').trim();
      if (assignee) await ensureEmployee(index, rootHandle, assignee);
      for (const t of group.tasks || []) {
        await addTask(index, rootHandle, {
          title: t.title || 'Без названия',
          dueDate: t.date || selectedDate,
          assignee,
          someday: false
        });
      }
    }
  }
}
