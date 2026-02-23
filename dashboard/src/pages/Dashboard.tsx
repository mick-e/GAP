import { useQuery } from '@tanstack/react-query'
import { org, trends } from '../api/client'
import StatCard from '../components/StatCard'
import SparklineChart from '../components/SparklineChart'
import PageLoader from '../components/PageLoader'

export default function Dashboard() {
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['org-summary'],
    queryFn: () => org.summary(),
  })

  const { data: sparklines } = useQuery({
    queryKey: ['sparklines'],
    queryFn: () => trends.sparklines(14),
  })

  if (loadingSummary) return <PageLoader />

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Dashboard</h2>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard label="Repositories" value={summary.total_repos} subtitle={`${summary.total_private_repos} private`} />
          <StatCard label="Stars" value={summary.total_stars} />
          <StatCard label="Forks" value={summary.total_forks} />
          <StatCard label="Open Issues" value={summary.total_open_issues} />
        </div>
      )}

      {sparklines && sparklines.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {sparklines.map((s) => (
            <div key={s.metric} className="bg-white rounded-lg border p-4">
              <p className="text-sm text-gray-500 mb-1">{s.metric.replace('_', ' ')}</p>
              <div className="flex items-end gap-2">
                <span className="text-lg font-semibold">{s.current}</span>
                <span className={`text-xs ${s.change_percent > 0 ? 'text-green-600' : 'text-gray-400'}`}>
                  {s.change_percent > 0 ? '+' : ''}{s.change_percent}%
                </span>
              </div>
              <SparklineChart data={s.data} />
            </div>
          ))}
        </div>
      )}

      {summary && Object.keys(summary.languages).length > 0 && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-medium text-gray-600 mb-3">Languages</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.languages)
              .sort(([, a], [, b]) => b - a)
              .map(([lang, count]) => (
                <span key={lang} className="px-2 py-1 bg-gray-100 rounded text-xs">
                  {lang}: {count}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
