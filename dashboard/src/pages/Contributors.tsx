import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { contributors } from '../api/client'
import type { ContributorProfile } from '../api/client'
import PageLoader from '../components/PageLoader'

export default function Contributors() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')

  const minCommits = searchParams.get('min_commits') || ''
  const sortBy = searchParams.get('sort_by') || ''
  const sortOrder = searchParams.get('sort_order') || 'desc'

  const queryString = [
    minCommits ? `min_commits=${minCommits}` : '',
    sortBy ? `sort_by=${sortBy}` : '',
    sortOrder !== 'desc' ? `sort_order=${sortOrder}` : '',
  ]
    .filter(Boolean)
    .join('&')

  const { data, isLoading } = useQuery({
    queryKey: ['contributors', queryString],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (minCommits) params.set('min_commits', minCommits)
      if (sortBy) params.set('sort_by', sortBy)
      if (sortOrder) params.set('sort_order', sortOrder)
      const qs = params.toString()
      const res = await fetch(`/api/v1/contributors${qs ? `?${qs}` : ''}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      })
      return res.json()
    },
  })

  if (isLoading) return <PageLoader />

  const items: ContributorProfile[] = data?.items || data || []
  const filtered = items.filter(
    (c: ContributorProfile) =>
      !search.trim() || c.login.toLowerCase().includes(search.toLowerCase())
  )

  function updateFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams)
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    setSearchParams(params)
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Contributors</h2>
      <div className="flex flex-wrap items-end gap-3 mb-4 bg-white border rounded-lg p-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Search</label>
          <input
            type="text"
            placeholder="Search contributors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Min Commits
          </label>
          <input
            type="number"
            min={0}
            placeholder="0"
            value={minCommits}
            onChange={(e) => updateFilter('min_commits', e.target.value)}
            className="w-24 px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Sort By</label>
          <select
            value={sortBy}
            onChange={(e) => updateFilter('sort_by', e.target.value)}
            className="px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
          >
            <option value="">Default</option>
            <option value="commits">Commits</option>
            <option value="prs">PRs</option>
            <option value="issues">Issues</option>
            <option value="reviews">Reviews</option>
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((c: ContributorProfile) => (
          <div
            key={c.login}
            onClick={() => navigate(`/contributors/${c.login}`)}
            className="bg-white rounded-lg border p-4 cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-3">
              {c.avatar_url && (
                <img
                  src={c.avatar_url}
                  alt={c.login}
                  className="w-10 h-10 rounded-full"
                />
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
