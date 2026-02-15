import { shiftDateByMode } from '../utils/date.js';

export function bindEvents(ctx) {
  const {
    state,
    persistUi,
    rerender,
    pickVault,
    addTask,
    addSomeday,
    addEmployee,
    toggleTask,
    moveTaskToDate,
    moveTaskToSomeday,
    moveTaskAssignee,
    importLegacy,
    togglePomodoro,
    savePomodoro,
    togglePomodoroSettings,
    togglePomodoroSound
  } = ctx;

  document.getElementById('tabs').addEventListener('click', (e) => {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    state.ui.tab = btn.dataset.tab;
    persistUi();
    rerender();
  });

  document.getElementById('modeSwitch').addEventListener('click', (e) => {
    const btn = e.target.closest('.mode-btn');
    if (!btn) return;
    state.ui.mode = btn.dataset.mode;
    persistUi();
    rerender();
  });

  document.getElementById('datePicker').addEventListener('change', (e) => {
    state.ui.selectedDate = e.target.value;
    persistUi();
    rerender();
  });

  document.getElementById('prevBtn').addEventListener('click', () => {
    state.ui.selectedDate = shiftDateByMode(state.ui.selectedDate, state.ui.mode, -1);
    persistUi();
    rerender();
  });

  document.getElementById('nextBtn').addEventListener('click', () => {
    state.ui.selectedDate = shiftDateByMode(state.ui.selectedDate, state.ui.mode, 1);
    persistUi();
    rerender();
  });

  document.getElementById('themeBtn').addEventListener('click', () => {
    state.ui.theme = state.ui.theme === 'dark' ? 'light' : 'dark';
    persistUi();
    rerender();
  });

  document.getElementById('pickVaultBtn').addEventListener('click', async () => {
    await pickVault();
    rerender();
  });

  document.getElementById('importLegacyBtn').addEventListener('click', async () => {
    await importLegacy();
    rerender();
  });

  document.getElementById('addEmployeeBtn').addEventListener('click', async () => {
    const name = prompt('Имя сотрудника');
    if (!name || !name.trim()) return;
    await addEmployee(name.trim());
    rerender();
  });

  document.getElementById('quickAddInput').addEventListener('keydown', async (e) => {
    if (e.key !== 'Enter') return;
    const value = e.target.value.trim();
    if (!value) return;

    if (state.ui.tab === 'team') {
      const [employee, ...rest] = value.split('/');
      if (!employee || rest.length === 0) return;
      await addTask(rest.join('/').trim(), state.ui.selectedDate, employee.trim());
    } else {
      await addTask(value, state.ui.selectedDate, '');
    }

    e.target.value = '';
    rerender();
  });

  document.getElementById('somedayInput').addEventListener('keydown', async (e) => {
    if (e.key !== 'Enter') return;
    const title = e.target.value.trim();
    if (!title) return;
    await addSomeday(title);
    e.target.value = '';
    rerender();
  });

  document.getElementById('board').addEventListener('keydown', async (e) => {
    if (e.key !== 'Enter') return;
    const date = e.target.dataset.addDate;
    const employee = e.target.dataset.addEmployee;
    if (!date && !employee) return;
    const title = e.target.value.trim();
    if (!title) return;
    await addTask(title, date || state.ui.selectedDate, employee || '');
    e.target.value = '';
    rerender();
  });

  document.body.addEventListener('click', async (e) => {
    const task = e.target.closest('.task');
    if (!task) return;
    await toggleTask(task.dataset.taskId);
    rerender();
  });

  let dragId = null;
  document.body.addEventListener('dragstart', (e) => {
    const task = e.target.closest('.task');
    if (!task) return;
    dragId = task.dataset.taskId;
  });

  document.body.addEventListener('dragover', (e) => {
    const zone = e.target.closest('[data-drop-zone]');
    if (!zone) return;
    e.preventDefault();
  });

  document.body.addEventListener('drop', async (e) => {
    const zone = e.target.closest('[data-drop-zone]');
    if (!zone || !dragId) return;
    e.preventDefault();

    if (zone.dataset.dropZone === 'someday') {
      await moveTaskToSomeday(dragId);
    } else if (zone.dataset.dropZone === 'date') {
      await moveTaskToDate(dragId, zone.dataset.date);
    } else if (zone.dataset.dropZone === 'employee') {
      await moveTaskAssignee(dragId, zone.dataset.employee);
    }

    dragId = null;
    rerender();
  });

  document.getElementById('pomodoroToggleBtn').addEventListener('click', () => {
    togglePomodoro();
    rerender();
  });
  document.getElementById('pomodoroSettingsBtn').addEventListener('click', () => {
    togglePomodoroSettings();
  });
  document.getElementById('pomodoroSoundBtn').addEventListener('click', () => {
    togglePomodoroSound();
    rerender();
  });
  document.getElementById('savePomodoroBtn').addEventListener('click', () => {
    savePomodoro(
      Number(document.getElementById('focusInput').value),
      Number(document.getElementById('shortInput').value),
      Number(document.getElementById('longInput').value),
      Number(document.getElementById('cyclesInput').value)
    );
    rerender();
  });
}
