import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { auth, org } from '../api/client'

export default function Settings() {
  const queryClient = useQueryClient()
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: () => auth.me() })
  const { data: keys } = useQuery({ queryKey: ['api-keys'], queryFn: () => auth.listApiKeys() })
  const { data: repos } = useQuery({ queryKey: ['repos'], queryFn: () => org.repos() })

  const [keyName, setKeyName] = useState('')
  const [newKey, setNewKey] = useState<string | null>(null)
  const [selectedRepos, setSelectedRepos] = useState<string[]>([])
  const [showRepoSelect, setShowRepoSelect] = useState(false)

  const createKey = useMutation({
    mutationFn: ({ name, repos }: { name: string; repos: string[] }) =>
      auth.createApiKeyWithRepos(name, repos),
    onSuccess: (data) => {
      setNewKey(data.key)
      setKeyName('')
      setSelectedRepos([])
      setShowRepoSelect(false)
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  const deleteKey = useMutation({
    mutationFn: (id: string) => auth.deleteApiKey(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
  })

  function toggleRepo(repoName: string) {
    setSelectedRepos((prev) =>
      prev.includes(repoName) ? prev.filter((r) => r !== repoName) : [...prev, repoName]
    )
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Settings</h2>

      {user && (
        <div className="bg-white rounded-lg border p-4 mb-6">
          <h3 className="font-medium mb-2">Account</h3>
          <p className="text-sm">Email: {user.email}</p>
          <p className="text-sm">Name: {user.name || '-'}</p>
          <p className="text-sm">Role: {user.role}</p>
        </div>
      )}

      <div className="bg-white rounded-lg border p-4">
        <h3 className="font-medium mb-3">API Keys</h3>

        <div className="space-y-3 mb-4">
          <div className="flex gap-2">
            <input
              placeholder="Key name"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              className="px-3 py-2 border rounded text-sm flex-1"
            />
            <button
              onClick={() => keyName && createKey.mutate({ name: keyName, repos: selectedRepos })}
              className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Create
            </button>
          </div>

          <div>
            <button
              onClick={() => setShowRepoSelect(!showRepoSelect)}
              className="text-sm text-blue-600 hover:underline"
            >
              {showRepoSelect ? 'Hide' : 'Set'} repo permissions
              {selectedRepos.length > 0 && ` (${selectedRepos.length} selected)`}
            </button>

            {showRepoSelect && (
              <div className="mt-2 border rounded p-3 max-h-48 overflow-y-auto">
                <p className="text-xs text-gray-500 mb-2">
                  Select repos this key can access (none = all repos):
                </p>
                {(repos || []).map((r) => (
                  <label key={r.name} className="flex items-center gap-2 text-sm py-0.5">
                    <input
                      type="checkbox"
                      checked={selectedRepos.includes(r.name)}
                      onChange={() => toggleRepo(r.name)}
                      className="rounded"
                    />
                    {r.name}
                  </label>
                ))}
                {(!repos || repos.length === 0) && (
                  <p className="text-xs text-gray-400">No repos available</p>
                )}
              </div>
            )}
          </div>
        </div>

        {newKey && (
          <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
            <p className="text-sm text-green-800 font-medium">New API Key (copy now, won't be shown again):</p>
            <code className="text-xs break-all">{newKey}</code>
          </div>
        )}

        <div className="space-y-2">
          {(keys || []).map((k) => (
            <div key={k.id} className="flex items-center justify-between border rounded p-2">
              <div>
                <p className="text-sm font-medium">{k.name}</p>
                <p className="text-xs text-gray-400">{k.prefix}...</p>
              </div>
              <button
                onClick={() => deleteKey.mutate(k.id)}
                className="text-xs text-red-600 hover:underline"
              >
                Revoke
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
