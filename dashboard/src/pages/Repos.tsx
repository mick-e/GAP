import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { org } from '../api/client'
import type { Repo } from '../api/client'
import DataTable from '../components/DataTable'
import PageLoader from '../components/PageLoader'

export default function Repos() {
  const navigate = useNavigate()
  const { data: repos, isLoading } = useQuery({
    queryKey: ['repos'],
    queryFn: () => org.repos(),
  })

  if (isLoading) return <PageLoader />

  const columns = [
    { key: 'name', header: 'Name', render: (r: Repo) => (
      <span className="font-medium text-blue-600">{r.name}</span>
    )},
    { key: 'language', header: 'Language' },
    { key: 'stars', header: 'Stars' },
    { key: 'forks', header: 'Forks' },
    { key: 'open_issues', header: 'Issues' },
    { key: 'updated_at', header: 'Updated', render: (r: Repo) => (
      <span className="text-gray-500">{new Date(r.updated_at).toLocaleDateString()}</span>
    )},
  ]

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Repositories</h2>
      <div className="bg-white rounded-lg border">
        <DataTable
          data={(repos || []) as (Repo & Record<string, unknown>)[]}
          columns={columns}
          onRowClick={(r) => navigate(`/repos/${(r as Repo).name}`)}
          searchable
        />
      </div>
    </div>
  )
}
