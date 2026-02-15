export function createEmployee(name, role = '') {
  return { name: String(name || '').trim(), role: String(role || '').trim() };
}
