const TASK_RE = /^- \[( |x)\] (.*?)(?: \[\[(.*?)\]\])?\s*<!--id:(.*?)-->\s*$/;

export function generateTaskId() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  const rand = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  return `task_${y}${m}${d}_${rand}`;
}

export function parseWeekMarkdown(content, weekKey) {
  const lines = content.split(/\r?\n/);
  const map = {};
  let currentDate = null;

  lines.forEach((line) => {
    if (line.startsWith('## ')) {
      currentDate = line.replace('## ', '').trim();
      if (!map[currentDate]) map[currentDate] = [];
      return;
    }

    const m = line.match(TASK_RE);
    if (!m || !currentDate) return;

    map[currentDate].push({
      id: m[4],
      title: m[2].trim(),
      assignee: m[3] ? m[3].trim() : '',
      done: m[1] === 'x',
      dueDate: currentDate,
      weekKey,
      someday: false
    });
  });

  return map;
}

export function serializeWeekMarkdown(weekKey, byDate) {
  const dates = Object.keys(byDate).sort();
  const lines = [`# Week ${weekKey}`, ''];

  dates.forEach((date) => {
    lines.push(`## ${date}`);
    const tasks = byDate[date] || [];
    tasks.forEach((task) => {
      const assignee = task.assignee ? ` [[${task.assignee}]]` : '';
      lines.push(`- [${task.done ? 'x' : ' '}] ${task.title}${assignee} <!--id:${task.id}-->`);
    });
    lines.push('');
  });

  return lines.join('\n').trimEnd() + '\n';
}

export function parseSomedayMarkdown(content) {
  return content
    .split(/\r?\n/)
    .map((line) => line.match(TASK_RE))
    .filter(Boolean)
    .map((m) => ({
      id: m[4],
      title: m[2].trim(),
      assignee: m[3] ? m[3].trim() : '',
      done: m[1] === 'x',
      dueDate: '',
      weekKey: '',
      someday: true
    }));
}

export function serializeSomedayMarkdown(tasks) {
  const lines = ['# Someday', ''];
  tasks.forEach((task) => {
    const assignee = task.assignee ? ` [[${task.assignee}]]` : '';
    lines.push(`- [${task.done ? 'x' : ' '}] ${task.title}${assignee} <!--id:${task.id}-->`);
  });
  return lines.join('\n').trimEnd() + '\n';
}
