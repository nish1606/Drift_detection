export default function TooltipTerm({ label, tip, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1 border-b border-dotted border-slate-300 text-inherit ${className}`} title={tip}>
      {label}
      <span className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-slate-400">i</span>
    </span>
  )
}