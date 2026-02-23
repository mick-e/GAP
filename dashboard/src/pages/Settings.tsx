import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { auth } from '../api/client'

export default function Settings() {
  const queryClient = useQueryClient()
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: () => auth.me() })
  const { data: keys } = useQuery({ queryKey: ['api-keys'], queryFn: () => auth.listApiKeys() })

  const [keyName, setKeyName] = useState('')
  const [newKey, setNewKey] = useState<string | null>(null)

  const createKey = useMutation({
    mutationFn: (name: string) => auth.createApiKey(name),
    onSuccess: (data) => {
      setNewKey(data.key)
      setKeyName('')
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  const deleteKey = useMutation({
    mutationFn: (id: string) => auth.deleteApiKey(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
  })

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

        <div className="flex gap-2 mb-4">
          <input
            placeholder="Key name"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            className="px-3 py-2 border rounded text-sm flex-1"
          />
          <button
            onClick={() => keyName && createKey.mutate(keyName)}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Create
          </button>
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
