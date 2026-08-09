import { useEffect, useMemo, useState } from 'react'
import PolicyCard from '../components/PolicyCard'
import LastUpdated from '../components/LastUpdated'
import { getPolicies, getPolicyHistory, savePolicyDraft } from '../api'
import { formatLongDateTime } from '../utils/formatters'

export default function Policies({ role }) {
  const canEdit = role === 'Compliance'
  const [policies, setPolicies] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [draft, setDraft] = useState(null)
  const [stage, setStage] = useState('edit')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true

    const load = async () => {
      try {
        setLoading(true)
        const [nextPolicies, nextHistory] = await Promise.all([getPolicies(role), getPolicyHistory(role)])

        if (!active) {
          return
        }

        setPolicies(nextPolicies)
        setHistory(nextHistory)
      } catch (error) {
        console.error('Policies load failed:', error)
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    load()

    return () => {
      active = false
    }
  }, [role])

  function beginEdit(policy) {
    setSelectedPolicy(policy)
    setDraft(policy)
    setStage('edit')
  }

  async function publishPolicy() {
    if (!draft) {
      return
    }

    setSaving(true)
    const updated = await savePolicyDraft({ ...draft, modifiedBy: role === 'Compliance' ? 'Current compliance user' : 'Risk engineer reviewer' }, role)
    setPolicies((current) => current.map((policy) => (policy.id === updated.id ? updated : policy)))
    const nextHistory = await getPolicyHistory(role)
    setHistory(nextHistory)
    setSaving(false)
    setSelectedPolicy(null)
    setDraft(null)
    setStage('edit')
  }

  const orderedPolicies = useMemo(() => [...policies].sort((left, right) => new Date(right.lastModified).getTime() - new Date(left.lastModified).getTime()), [policies])

  if (loading) {
    return <div className="h-80 animate-pulse rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Policies</h2>
        <LastUpdated />
      </div>
      {!canEdit ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300">
          Read-only access for this role. Policy changes require compliance approval.
        </div>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-2">
        {orderedPolicies.map((policy) => (
          <PolicyCard key={policy.id} policy={policy} canEdit={canEdit} onEdit={beginEdit} />
        ))}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Version history</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Past policy changes, who made them, and why.</p>
        <div className="mt-4 space-y-3">
          {history.map((entry) => (
            <article key={entry.id || entry.name} className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-50">{entry.policyName || entry.name}</p>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{entry.changeSummary || entry.policy_type}</p>
                </div>
                <div className="text-right text-sm text-slate-500 dark:text-slate-400">
                  <p>{entry.changedBy || entry.modifiedBy || 'system'}</p>
                  <p>{entry.changedAt ? formatLongDateTime(entry.changedAt) : entry.lastModified ? formatLongDateTime(entry.lastModified) : '-'}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      {selectedPolicy ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/30 px-4">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Policy editor</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">{selectedPolicy.name}</h3>
              </div>
              <button type="button" onClick={() => setSelectedPolicy(null)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
                Close
              </button>
            </div>

            {stage === 'edit' ? (
              <div className="mt-5 grid gap-4">
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Condition
                  <textarea value={draft.condition} onChange={(event) => setDraft({ ...draft, condition: event.target.value })} disabled={!canEdit} className="min-h-24 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-70" />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Action
                  <input value={draft.action} onChange={(event) => setDraft({ ...draft, action: event.target.value })} disabled={!canEdit} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-70" />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-700">
                  Escalation target
                  <input value={draft.escalation} onChange={(event) => setDraft({ ...draft, escalation: event.target.value })} disabled={!canEdit} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-70" />
                </label>

                <div className="flex flex-wrap gap-3">
                  <button type="button" disabled={!canEdit} onClick={() => setStage('review')} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">
                    Save as draft
                  </button>
                  {!canEdit ? <span className="self-center text-sm text-slate-500">Editing disabled for this role.</span> : null}
                </div>
              </div>
            ) : (
              <div className="mt-5 space-y-4">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                  <p className="font-semibold text-slate-900 dark:text-slate-50">Draft review</p>
                  <ul className="mt-3 space-y-2">
                    <li>Condition: {draft.condition}</li>
                    <li>Action: {draft.action}</li>
                    <li>Escalation: {draft.escalation}</li>
                  </ul>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={() => setStage('edit')} className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700">
                    Back to edit
                  </button>
                  <button type="button" disabled={saving || !canEdit} onClick={publishPolicy} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">
                    Publish
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}