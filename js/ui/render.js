import { getPeriodColumns, weekRangeLabel } from '../utils/date.js';
import { getTasksForPeriod } from '../storage/vaultIndex.js';

function esc(text) {
  return String(text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

export function renderApp(state, index) {
  document.body.setAttribute('data-theme', state.ui.theme);
  document.querySelector('meta[name="theme-color"]').setAttribute('content', state.ui.theme === 'dark' ? '#101214' : '#ffffff');
  document.getElementById('themeBtn').textContent = state.ui.theme === 'dark' ? 'Светлая тема' : 'Тёмная тема';

  document.querySelectorAll('.tab').forEach((btn) => btn.classList.toggle('active', btn.dataset.tab === state.ui.tab));
  document.querySelectorAll('.mode-btn').forEach((btn) => btn.classList.toggle('active', btn.dataset.mode === state.ui.mode));
  document.getElementById('datePicker').value = state.ui.selectedDate;
  document.getElementById('rangeLabel').textContent = `Неделя: ${weekRangeLabel(state.ui.selectedDate)}`;

  const teamTab = state.ui.tab === 'team';
  document.getElementById('addEmployeeBtn').classList.toggle('hidden', !teamTab);
  document.getElementById('quickAddInput').placeholder = teamTab
    ? 'Иван / Подготовить отчёт'
    : 'Новая задача для выбранной даты';

  renderBoard(state, index);
  renderSomeday(index.someday);
  renderPomodoro(state);
}

function renderBoard(state, index) {
  const board = document.getElementById('board');
  board.innerHTML = '';

  if (state.ui.tab === 'my') {
    const columns = getPeriodColumns(state.ui.mode, state.ui.selectedDate);
    board.style.gridTemplateColumns = `repeat(${columns.length}, minmax(180px, 1fr))`;
    const tasks = getTasksForPeriod(index, state.ui.mode, state.ui.selectedDate);

    columns.forEach((column) => {
      const el = document.createElement('section');
      el.className = 'column';
      el.dataset.dropZone = 'date';
      el.dataset.date = column.key;
      el.innerHTML = `<h3>${esc(column.label)}</h3><div class="task-list"></div><input class="inline-input" data-add-date="${column.key}" type="text" placeholder="+ Задача" />`;
      const list = el.querySelector('.task-list');
      tasks.filter((t) => t.dueDate === column.key).forEach((task) => list.appendChild(taskNode(task)));
      board.appendChild(el);
    });
  } else {
    const employees = index.employees.length ? index.employees : ['Без сотрудника'];
    board.style.gridTemplateColumns = `repeat(${employees.length}, minmax(220px, 1fr))`;
    const tasks = getTasksForPeriod(index, state.ui.mode, state.ui.selectedDate);

    employees.forEach((name) => {
      const el = document.createElement('section');
      el.className = 'column';
      el.dataset.dropZone = 'employee';
      el.dataset.employee = name;
      el.innerHTML = `<h3>${esc(name)}</h3><div class="task-list"></div><input class="inline-input" data-add-employee="${esc(name)}" type="text" placeholder="+ Задача" />`;
      const list = el.querySelector('.task-list');
      tasks.filter((t) => (t.assignee || 'Без сотрудника') === name).forEach((task) => list.appendChild(taskNode(task)));
      board.appendChild(el);
    });
  }
}

function taskNode(task) {
  const item = document.createElement('div');
  item.className = `task${task.done ? ' done' : ''}`;
  item.draggable = true;
  item.dataset.taskId = task.id;
  item.innerHTML = `<input type="checkbox" ${task.done ? 'checked' : ''} /><span class="task-title">${esc(task.title)}</span>`;
  return item;
}

function renderSomeday(tasks) {
  const list = document.getElementById('somedayList');
  list.innerHTML = '';
  tasks.forEach((task) => list.appendChild(taskNode(task)));
}

function renderPomodoro(state) {
  const p = state.pomodoro;
  const mm = String(Math.floor(p.secondsLeft / 60)).padStart(2, '0');
  const ss = String(p.secondsLeft % 60).padStart(2, '0');
  document.getElementById('pomodoroTime').textContent = `${mm}:${ss}`;
  document.getElementById('pomodoroToggleBtn').textContent = p.running ? 'Стоп' : 'Старт';
  document.getElementById('pomodoroModeLabel').textContent = p.mode === 'focus' ? 'Фокус' : p.mode === 'short' ? 'Короткий перерыв' : 'Длинный перерыв';
  document.getElementById('pomodoroSoundBtn').textContent = p.settings.sound ? '🔔' : '🔕';

  document.getElementById('focusInput').value = p.settings.focus;
  document.getElementById('shortInput').value = p.settings.short;
  document.getElementById('longInput').value = p.settings.long;
  document.getElementById('cyclesInput').value = p.settings.cycles;
}
