import { useQuery } from '@tanstack/react-query'
import { teams } from '../api/client'
import type { TeamComparison } from '../api/client'
import StatCard from '../components/StatCard'
import DataTable from '../components/DataTable'
import PageLoader from '../components/PageLoader'
import clsx from 'clsx'

const ratingColors: Record<string, string> = {
  elite: 'bg-green-100 text-green-800',
  high: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-red-100 text-red-800',
}

export default function Teams() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['team-metrics'],
    queryFn: () => teams.metrics(30),
  })

  const { data: dora } = useQuery({
    queryKey: ['dora'],
    queryFn: () => teams.dora(30),
  })

  const { data: comparison } = useQuery({
    queryKey: ['team-compare'],
    queryFn: () => teams.compare(30),
  })

  if (isLoading) return <PageLoader />

  const columns = [
    { key: 'repo_name', header: 'Repo', render: (r: TeamComparison) => (
      <span className="font-medium">{r.repo_name}</span>
    )},
    { key: 'commits', header: 'Commits' },
    { key: 'prs', header: 'PRs' },
    { key: 'releases', header: 'Releases' },
    { key: 'contributors', header: 'Contributors' },
    { key: 'avg_pr_merge_hours', header: 'Avg Merge (hrs)', render: (r: TeamComparison) => (
      <span>{r.avg_pr_merge_hours?.toFixed(1) ?? '-'}</span>
    )},
  ]

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Teams & DORA</h2>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Commits" value={metrics.total_commits} />
          <StatCard label="Total PRs" value={metrics.total_prs} />
          <StatCard label="Releases" value={metrics.total_releases} />
          <StatCard label="Contributors" value={metrics.contributors_count} />
        </div>
      )}

      {dora && (
        <div className="bg-white rounded-lg border p-4 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">DORA Metrics</h3>
            <span className={clsx('px-2 py-1 rounded text-xs font-medium', ratingColors[dora.rating] || 'bg-gray-100')}>
              {dora.rating.toUpperCase()}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Deploy Frequency</p>
              <p className="text-lg font-semibold">{dora.deployment_frequency}/wk</p>
            </div>
            <div>
              <p className="text-gray-500">Lead Time</p>
              <p className="text-lg font-semibold">{dora.lead_time_hours}h</p>
            </div>
            <div>
              <p className="text-gray-500">MTTR</p>
              <p className="text-lg font-semibold">{dora.mttr_hours}h</p>
            </div>
            <div>
              <p className="text-gray-500">Change Failure Rate</p>
              <p className="text-lg font-semibold">{dora.change_failure_rate}%</p>
            </div>
          </div>
        </div>
      )}

      {comparison && comparison.length > 0 && (
        <div className="bg-white rounded-lg border">
          <h3 className="font-medium p-4 border-b">Repo Comparison</h3>
          <DataTable data={comparison as (TeamComparison & Record<string, unknown>)[]} columns={columns} />
        </div>
      )}
    </div>
  )
}
