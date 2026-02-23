import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { repo } from '../api/client'
import StatCard from '../components/StatCard'
import PageLoader from '../components/PageLoader'

export default function RepoDetail() {
  const { name } = useParams<{ name: string }>()

  const { data: commits, isLoading: loadingCommits } = useQuery({
    queryKey: ['repo-commits', name],
    queryFn: () => repo.commits(name!),
    enabled: !!name,
  })

  const { data: pulls } = useQuery({
    queryKey: ['repo-pulls', name],
    queryFn: () => repo.pulls(name!),
    enabled: !!name,
  })

  const { data: issues } = useQuery({
    queryKey: ['repo-issues', name],
    queryFn: () => repo.issues(name!),
    enabled: !!name,
  })

  const { data: security } = useQuery({
    queryKey: ['repo-security', name],
    queryFn: () => repo.security(name!),
    enabled: !!name,
  })

  if (loadingCommits) return <PageLoader />

  const c = commits as Record<string, unknown> | undefined
  const p = pulls as Record<string, unknown> | undefined
  const iss = issues as Record<string, unknown> | undefined
  const sec = security as Record<string, unknown> | undefined

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">{name}</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Commits" value={c?.count as number ?? 0} subtitle="This month" />
        <StatCard label="Pull Requests" value={p?.count as number ?? 0} />
        <StatCard label="Issues" value={iss?.count as number ?? 0} />
        <StatCard
          label="Security Alerts"
          value={
            ((sec?.code_scanning as Record<string, number>)?.count ?? 0) +
            ((sec?.dependabot as Record<string, number>)?.count ?? 0) +
            ((sec?.secret_scanning as Record<string, number>)?.count ?? 0)
          }
        />
      </div>

      {sec && (
        <div className="bg-white rounded-lg border p-4 mb-4">
          <h3 className="font-medium mb-2">Security</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>Code Scanning: {(sec.code_scanning as Record<string, number>)?.count ?? 0}</div>
            <div>Dependabot: {(sec.dependabot as Record<string, number>)?.count ?? 0}</div>
            <div>Secret Scanning: {(sec.secret_scanning as Record<string, number>)?.count ?? 0}</div>
          </div>
        </div>
      )}
    </div>
  )
}
