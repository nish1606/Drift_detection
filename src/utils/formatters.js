export function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatNumber(value, digits = 2) {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

export function formatPercent(value, digits = 0) {
  return `${formatNumber(value * 100, digits)}%`
}

export function formatDateTime(value) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

export function formatLongDateTime(value) {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatRelativeLabel(value) {
  const diff = Date.now() - new Date(value).getTime()
  const hours = Math.max(0, Math.round(diff / 3600000))

  if (hours === 0) {
    return 'Just now'
  }

  if (hours === 1) {
    return '1h ago'
  }

  return `${hours}h ago`
}

export function createCsv(rows, columns) {
  const header = columns.map((column) => column.label).join(',')
  const body = rows.map((row) => columns.map((column) => JSON.stringify(column.getValue(row) ?? '')).join(','))
  return [header, ...body].join('\n')
}