const DB_NAME = 'vault-fs-db';
const STORE = 'handles';
const KEY = 'vault-directory';

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function saveHandle(handle) {
  const db = await openDb();
  await new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(handle, KEY);
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

async function loadHandle() {
  const db = await openDb();
  const handle = await new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly');
    const req = tx.objectStore(STORE).get(KEY);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror = () => reject(req.error);
  });
  db.close();
  return handle;
}

async function ensurePermission(handle, mode = 'readwrite') {
  if (!handle) return false;
  const opts = { mode };
  if ((await handle.queryPermission(opts)) === 'granted') return true;
  return (await handle.requestPermission(opts)) === 'granted';
}

async function getOrCreateDir(parent, name) {
  return parent.getDirectoryHandle(name, { create: true });
}

async function getFileHandle(dirHandle, path, create = true) {
  const parts = path.split('/').filter(Boolean);
  let current = dirHandle;
  for (let i = 0; i < parts.length - 1; i += 1) {
    current = await current.getDirectoryHandle(parts[i], { create });
  }
  return current.getFileHandle(parts[parts.length - 1], { create });
}

async function readText(dirHandle, path) {
  try {
    const fileHandle = await getFileHandle(dirHandle, path, false);
    const file = await fileHandle.getFile();
    return await file.text();
  } catch {
    return '';
  }
}

async function writeText(dirHandle, path, content) {
  const fileHandle = await getFileHandle(dirHandle, path, true);
  const writable = await fileHandle.createWritable();
  await writable.write(content);
  await writable.close();
}

async function listFiles(dirHandle, path) {
  const parts = path.split('/').filter(Boolean);
  let dir = dirHandle;
  for (const part of parts) {
    try {
      dir = await dir.getDirectoryHandle(part, { create: false });
    } catch {
      return [];
    }
  }

  const files = [];
  // eslint-disable-next-line no-restricted-syntax
  for await (const [name, handle] of dir.entries()) {
    if (handle.kind === 'file') files.push(name);
  }
  return files.sort();
}

async function ensureVaultStructure(rootHandle) {
  await getOrCreateDir(rootHandle, 'weeks');
  await getOrCreateDir(rootHandle, 'people');

  const inbox = await readText(rootHandle, 'inbox.md');
  if (!inbox) await writeText(rootHandle, 'inbox.md', '# Inbox\n');

  const someday = await readText(rootHandle, 'someday.md');
  if (!someday) await writeText(rootHandle, 'someday.md', '# Someday\n');

  const config = await readText(rootHandle, 'config.json');
  if (!config) await writeText(rootHandle, 'config.json', JSON.stringify({ version: 1 }, null, 2));
}

export async function pickVaultDirectory() {
  const handle = await window.showDirectoryPicker();
  const granted = await ensurePermission(handle, 'readwrite');
  if (!granted) throw new Error('Нет доступа к папке');
  await ensureVaultStructure(handle);
  await saveHandle(handle);
  return handle;
}

export async function restoreVaultDirectory() {
  const handle = await loadHandle();
  if (!handle) return null;
  const granted = await ensurePermission(handle, 'readwrite');
  if (!granted) return null;
  await ensureVaultStructure(handle);
  return handle;
}

export const vaultFs = {
  ensurePermission,
  ensureVaultStructure,
  readText,
  writeText,
  listFiles
};
