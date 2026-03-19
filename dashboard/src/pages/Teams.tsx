import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
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
  const [searchParams, setSearchParams] = useSearchParams()
  const [days, setDays] = useState(30)
  const sortBy = searchParams.get('sort_by') || ''
  const sortOrder = searchParams.get('sort_order') || 'desc'

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['team-metrics', days],
    queryFn: () => teams.metrics(days),
  })

  const { data: dora } = useQuery({
    queryKey: ['dora', days],
    queryFn: () => teams.dora(days),
  })

  const compareParams = new URLSearchParams()
  compareParams.set('days', String(days))
  if (sortBy) compareParams.set('sort_by', sortBy)
  if (sortOrder !== 'desc') compareParams.set('sort_order', sortOrder)

  const { data: comparison } = useQuery({
    queryKey: ['team-compare', days, sortBy, sortOrder],
    queryFn: async () => {
      const res = await fetch(
        `/api/v1/teams/compare?${compareParams.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      )
      return res.json()
    },
  })

  function updateFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams)
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    setSearchParams(params)
  }

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

      <div className="flex flex-wrap items-end gap-3 mb-4 bg-white border rounded-lg p-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Date Range (days)
          </label>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
            <option value={365}>365 days</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Sort By Metric
          </label>
          <select
            value={sortBy}
            onChange={(e) => updateFilter('sort_by', e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
          >
            <option value="">Default</option>
            <option value="commits">Commits</option>
            <option value="prs">PRs</option>
            <option value="releases">Releases</option>
            <option value="contributors">Contributors</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Order</label>
          <select
            value={sortOrder}
            onChange={(e) => updateFilter('sort_order', e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
          >
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </select>
        </div>
      </div>

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
