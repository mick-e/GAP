import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { contributors } from '../api/client'
import StatCard from '../components/StatCard'
import PageLoader from '../components/PageLoader'

export default function ContributorDetail() {
  const { username } = useParams<{ username: string }>()

  const { data: profile, isLoading } = useQuery({
    queryKey: ['contributor', username],
    queryFn: () => contributors.get(username!),
    enabled: !!username,
  })

  const { data: activity } = useQuery({
    queryKey: ['contributor-activity', username],
    queryFn: () => contributors.activity(username!, 30),
    enabled: !!username,
  })

  if (isLoading) return <PageLoader />
  if (!profile) return <p className="text-gray-500">Contributor not found</p>

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        {profile.avatar_url && (
          <img src={profile.avatar_url} alt={profile.login} className="w-16 h-16 rounded-full" />
        )}
        <div>
          <h2 className="text-xl font-semibold">{profile.login}</h2>
          <p className="text-sm text-gray-500">{profile.repos.join(', ')}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Commits" value={profile.total_commits} />
        <StatCard label="Pull Requests" value={profile.total_prs} />
        <StatCard label="Issues" value={profile.total_issues} />
        <StatCard label="Reviews" value={profile.total_reviews} />
      </div>

      {Array.isArray(activity) && activity.length > 0 ? (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="font-medium mb-3">Recent Activity</h3>
          <div className="space-y-2">
            {(activity as Array<{date: string; commits: number}>).slice(0, 10).map((a) => (
              <div key={a.date} className="flex justify-between text-sm">
                <span className="text-gray-600">{a.date}</span>
                <span className="font-medium">{a.commits} commits</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
