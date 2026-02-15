import { renderApp } from './ui/render.js';
import { bindEvents } from './ui/events.js';
import { pickVaultDirectory, restoreVaultDirectory, vaultFs } from './storage/vaultFs.js';
import {
  loadVaultIndex,
  addTask,
  ensureEmployee,
  toggleTask,
  moveTaskToDate,
  moveTaskToSomeday,
  moveTaskAssignee,
  importLegacyLocalStorage
} from './storage/vaultIndex.js';

const UI_KEY = 'planner-ui-settings-v3';
const POMODORO_KEY = 'planner-pomodoro-v3';

const state = {
  vaultHandle: null,
  vaultIndex: null,
  ui: loadUi(),
  pomodoro: loadPomodoro(),
  pomodoroSettingsOpen: false
};

let timerId = null;
let deferredInstallPrompt = null;

function loadUi() {
  const fallback = { tab: 'my', mode: 'week', selectedDate: new Date().toISOString().slice(0, 10), theme: 'light' };
  try {
    const parsed = JSON.parse(localStorage.getItem(UI_KEY) || '{}');
    return {
      tab: parsed.tab === 'team' ? 'team' : 'my',
      mode: ['day', 'week', 'month'].includes(parsed.mode) ? parsed.mode : 'week',
      selectedDate: parsed.selectedDate || fallback.selectedDate,
      theme: parsed.theme === 'dark' ? 'dark' : 'light'
    };
  } catch {
    return fallback;
  }
}

function persistUi() {
  localStorage.setItem(UI_KEY, JSON.stringify(state.ui));
}

function defaultPomodoro() {
  return {
    mode: 'focus',
    running: false,
    secondsLeft: 25 * 60,
    cyclesDone: 0,
    settings: { focus: 25, short: 5, long: 15, cycles: 4, sound: true }
  };
}

function loadPomodoro() {
  const fallback = defaultPomodoro();
  try {
    const parsed = JSON.parse(localStorage.getItem(POMODORO_KEY) || '{}');
    return {
      mode: ['focus', 'short', 'long'].includes(parsed.mode) ? parsed.mode : fallback.mode,
      running: false,
      secondsLeft: Number(parsed.secondsLeft) > 0 ? Number(parsed.secondsLeft) : fallback.secondsLeft,
      cyclesDone: Number(parsed.cyclesDone) >= 0 ? Number(parsed.cyclesDone) : 0,
      settings: {
        focus: Math.max(1, Number(parsed.settings?.focus) || fallback.settings.focus),
        short: Math.max(1, Number(parsed.settings?.short) || fallback.settings.short),
        long: Math.max(1, Number(parsed.settings?.long) || fallback.settings.long),
        cycles: Math.max(1, Number(parsed.settings?.cycles) || fallback.settings.cycles),
        sound: typeof parsed.settings?.sound === 'boolean' ? parsed.settings.sound : fallback.settings.sound
      }
    };
  } catch {
    return fallback;
  }
}

function persistPomodoro() {
  localStorage.setItem(POMODORO_KEY, JSON.stringify(state.pomodoro));
}

function setStatus(text) {
  document.getElementById('statusText').textContent = text;
}

function rerender() {
  renderApp(state, state.vaultIndex || { tasks: [], someday: [], employees: [] });
  document.getElementById('pomodoroSettings').classList.toggle('hidden', !state.pomodoroSettingsOpen);
}

function durationByMode(mode) {
  if (mode === 'short') return state.pomodoro.settings.short * 60;
  if (mode === 'long') return state.pomodoro.settings.long * 60;
  return state.pomodoro.settings.focus * 60;
}

function playTone(freq, duration = 160, type = 'sine') {
  if (!state.pomodoro.settings.sound) return;
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return;
  const ctx = new Ctx();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.value = 0.0001;
  osc.connect(gain);
  gain.connect(ctx.destination);
  const now = ctx.currentTime;
  gain.gain.exponentialRampToValueAtTime(0.06, now + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration / 1000);
  osc.start(now);
  osc.stop(now + duration / 1000 + 0.03);
  osc.onended = () => ctx.close();
}

function playFinishSound() {
  playTone(523, 120, 'triangle');
  setTimeout(() => playTone(659, 140, 'triangle'), 130);
  setTimeout(() => playTone(783, 220, 'triangle'), 300);
}

function nextPomodoroSession() {
  if (state.pomodoro.mode === 'focus') {
    state.pomodoro.cyclesDone += 1;
    state.pomodoro.mode = (state.pomodoro.cyclesDone % state.pomodoro.settings.cycles === 0) ? 'long' : 'short';
  } else {
    state.pomodoro.mode = 'focus';
  }
  state.pomodoro.secondsLeft = durationByMode(state.pomodoro.mode);
}

function togglePomodoro() {
  if (state.pomodoro.running) {
    clearInterval(timerId);
    timerId = null;
    state.pomodoro.running = false;
    persistPomodoro();
    return;
  }

  state.pomodoro.running = true;
  playTone(523, 140, 'sine');
  persistPomodoro();

  timerId = setInterval(() => {
    state.pomodoro.secondsLeft -= 1;
    if (state.pomodoro.secondsLeft <= 0) {
      playFinishSound();
      alert('Pomodoro finished!');
      nextPomodoroSession();
    }
    persistPomodoro();
    rerender();
  }, 1000);
}

function savePomodoro(focus, short, long, cycles) {
  state.pomodoro.settings.focus = Math.max(1, focus || 25);
  state.pomodoro.settings.short = Math.max(1, short || 5);
  state.pomodoro.settings.long = Math.max(1, long || 15);
  state.pomodoro.settings.cycles = Math.max(1, cycles || 4);
  if (!state.pomodoro.running) state.pomodoro.secondsLeft = durationByMode(state.pomodoro.mode);
  persistPomodoro();
}

function togglePomodoroSettings() {
  state.pomodoroSettingsOpen = !state.pomodoroSettingsOpen;
}

function togglePomodoroSound() {
  state.pomodoro.settings.sound = !state.pomodoro.settings.sound;
  persistPomodoro();
  if (state.pomodoro.settings.sound) playTone(660, 120);
}

async function pickVault() {
  if (!window.showDirectoryPicker) {
    setStatus('Нужен Chromium/Яндекс/Edge с File System Access API.');
    return;
  }
  state.vaultHandle = await pickVaultDirectory();
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
  setStatus('Vault подключён и индекс загружен.');
}

async function restoreVault() {
  state.vaultHandle = await restoreVaultDirectory();
  if (!state.vaultHandle) return false;
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
  setStatus('Vault восстановлен.');
  return true;
}

async function ensureVaultReady() {
  if (state.vaultHandle) return true;
  const restored = await restoreVault();
  if (restored) return true;
  setStatus('Vault не выбран. Нажмите «Выбрать Vault».');
  return false;
}

async function addTaskWrapper(title, dueDate, assignee) {
  if (!(await ensureVaultReady())) return;
  await addTask(state.vaultIndex, state.vaultHandle, { title, dueDate, assignee, someday: false });
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
}

async function addSomeday(title) {
  if (!(await ensureVaultReady())) return;
  await addTask(state.vaultIndex, state.vaultHandle, { title, dueDate: '', assignee: '', someday: true });
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
}

async function addEmployee(name) {
  if (!(await ensureVaultReady())) return;
  await ensureEmployee(state.vaultIndex, state.vaultHandle, name);
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
}

async function toggleTaskWrapper(id) {
  if (!(await ensureVaultReady())) return;
  await toggleTask(state.vaultIndex, state.vaultHandle, id);
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
}

async function moveTaskToDateWrapper(id, date) {
  if (!(await ensureVaultReady())) return;
  await moveTaskToDate(state.vaultIndex, state.vaultHandle, id, date);
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
}

async function moveTaskToSomedayWrapper(id) {
  if (!(await ensureVaultReady())) return;
  await moveTaskToSomeday(state.vaultIndex, state.vaultHandle, id);
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
}

async function moveTaskAssigneeWrapper(id, assignee) {
  if (!(await ensureVaultReady())) return;
  await moveTaskAssignee(state.vaultIndex, state.vaultHandle, id, assignee);
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
}

async function importLegacy() {
  if (!(await ensureVaultReady())) return;
  await importLegacyLocalStorage(state.vaultIndex, state.vaultHandle, state.ui.selectedDate);
  state.vaultIndex = await loadVaultIndex(state.vaultHandle);
  setStatus('Импорт из старого localStorage завершён.');
}

function setupPwaInstall() {
  const btn = document.getElementById('installBtn');
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    btn.classList.remove('hidden');
  });
  btn.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    btn.classList.add('hidden');
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }
}

async function init() {
  await restoreVault();
  rerender();
  setupPwaInstall();

  bindEvents({
    state,
    persistUi,
    rerender,
    pickVault,
    addTask: addTaskWrapper,
    addSomeday,
    addEmployee,
    toggleTask: toggleTaskWrapper,
    moveTaskToDate: moveTaskToDateWrapper,
    moveTaskToSomeday: moveTaskToSomedayWrapper,
    moveTaskAssignee: moveTaskAssigneeWrapper,
    importLegacy,
    togglePomodoro,
    savePomodoro,
    togglePomodoroSettings,
    togglePomodoroSound
  });
}

init();
