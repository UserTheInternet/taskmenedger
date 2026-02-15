export function createTask({ id, title, assignee = '', dueDate = '', done = false, weekKey = '', someday = false }) {
  return { id, title, assignee, dueDate, done, weekKey, someday };
}
