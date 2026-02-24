import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { contributors } from '../api/client'
import type { ContributorProfile } from '../api/client'
import PageLoader from '../components/PageLoader'

export default function Contributors() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['contributors'],
    queryFn: () => contributors.list(),
  })

  if (isLoading) return <PageLoader />

  const filtered = (data || []).filter((c: ContributorProfile) =>
    !search.trim() || c.login.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Contributors</h2>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search contributors..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-md px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((c: ContributorProfile) => (
          <div
            key={c.login}
            onClick={() => navigate(`/contributors/${c.login}`)}
            className="bg-white rounded-lg border p-4 cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-3">
              {c.avatar_url && (
                <img src={c.avatar_url} alt={c.login} className="w-10 h-10 rounded-full" />
              )}
              <div>
                <p className="font-medium">{c.login}</p>
                <p className="text-xs text-gray-500">{c.repos.length} repos</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                <p className="font-semibold text-lg">{c.total_commits}</p>
                <p className="text-gray-500">Commits</p>
              </div>
              <div>
                <p className="font-semibold text-lg">{c.total_prs}</p>
                <p className="text-gray-500">PRs</p>
              </div>
              <div>
                <p className="font-semibold text-lg">{c.total_reviews}</p>
                <p className="text-gray-500">Reviews</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
