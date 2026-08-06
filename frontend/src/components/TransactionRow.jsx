import { formatCurrency, formatDateTime, formatPercent } from '../utils/formatters'

const statusTone = {
  Pending: 'border-amber-200 bg-amber-50 text-amber-700',
  Approved: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  Declined: 'border-rose-200 bg-rose-50 text-rose-700',
  Escalated: 'border-slate-200 bg-slate-100 text-slate-700',
}

export default function TransactionRow({ transaction, onSelect, isNew = false }) {
  return (
    <tr onClick={() => onSelect(transaction)} className={`cursor-pointer border-b border-slate-100 transition hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900/60 ${isNew ? 'bg-amber-50/70 dark:bg-amber-950/30' : ''}`}>
      <td className="px-4 py-3 text-sm font-medium text-slate-900 dark:text-slate-50">{transaction.id}</td>
      <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">{formatCurrency(transaction.amount)}</td>
      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">{formatDateTime(transaction.timestamp)}</td>
      <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">{formatPercent(transaction.confidence, 0)}</td>
      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">{transaction.topFactor}</td>
      <td className="px-4 py-3 text-sm">
        <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold animate-badge-pop ${statusTone[transaction.status] ?? statusTone.Pending}`}>
          {transaction.status}
        </span>
      </td>
    </tr>
  )
}