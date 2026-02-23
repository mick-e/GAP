import { useQuery } from '@tanstack/react-query'
import { trends } from '../api/client'
import StatCard from '../components/StatCard'
import TrendChart from '../components/TrendChart'
import PageLoader from '../components/PageLoader'

export default function Trends() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['trend-overview'],
    queryFn: () => trends.overview(30),
  })

  const { data: commitTrend } = useQuery({
    queryKey: ['trend-commits'],
    queryFn: () => trends.metric('commit_count', 30),
  })

  if (isLoading) return <PageLoader />

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Trends</h2>

      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard
            label="Velocity"
            value={overview.velocity.current_value}
            change={overview.velocity.change_percent}
            subtitle="commits + PRs"
          />
          <StatCard
            label="Quality Score"
            value={overview.quality.current_value}
            change={overview.quality.change_percent}
            subtitle="100 - security alerts"
          />
          <StatCard
            label="Engagement"
            value={overview.engagement.current_value}
            change={overview.engagement.change_percent}
            subtitle="active contributors"
          />
        </div>
      )}

      {Array.isArray(commitTrend) && commitTrend.length > 0 ? (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-medium mb-3">Commit Trend (30 days)</h3>
          <TrendChart data={commitTrend as Array<{date: string; value: number}>} label="Commits" />
        </div>
      ) : null}
    </div>
  )
}
