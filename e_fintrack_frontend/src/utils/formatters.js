export function money(value) {
  return `BDT ${Number(value || 0).toLocaleString('en-BD', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function statusColor(status) {
  const colors = {
    ACTIVE: 'green',
    SUCCESS: 'green',
    PAID: 'green',
    PENDING: 'gold',
    OVERDUE: 'red',
    FAILED: 'red',
    REJECTED: 'red',
    FROZEN: 'orange',
    DEFAULTED: 'volcano',
  };

  return colors[status] || 'default';
}

function valueText(value) {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.map(valueText).join(' ');
  if (typeof value === 'object') return Object.values(value).map(valueText).join(' ');
  return String(value).toLowerCase();
}

export function matchesSearch(item, search, fields) {
  const query = search.trim().toLowerCase();
  if (!query) return true;

  return fields.some((field) => {
    const value = typeof field === 'function' ? field(item) : item?.[field];
    return valueText(value).includes(query);
  });
}
