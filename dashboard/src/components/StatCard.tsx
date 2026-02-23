import clsx from 'clsx'

interface Props {
  label: string
  value: string | number
  change?: number
  subtitle?: string
}

export default function StatCard({ label, value, change, subtitle }: Props) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
      {change !== undefined && (
        <p className={clsx('text-xs mt-1', change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-400')}>
          {change > 0 ? '+' : ''}{change.toFixed(1)}%
        </p>
      )}
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  )
}
