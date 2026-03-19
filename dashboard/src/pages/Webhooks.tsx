import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { webhooks } from '../api/client'
import type { WebhookEvent, WebhookEventDetail } from '../api/client'
import DataTable from '../components/DataTable'
import PageLoader from '../components/PageLoader'

export default function Webhooks() {
  const queryClient = useQueryClient()
  const [eventType, setEventType] = useState('')
  const [repoName, setRepoName] = useState('')
  const [processedFilter, setProcessedFilter] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [detailEvent, setDetailEvent] = useState<WebhookEventDetail | null>(null)

  const params: Record<string, string> = {}
  if (eventType) params.event_type = eventType
  if (repoName) params.repo_name = repoName
  if (processedFilter) params.processed = processedFilter

  const { data, isLoading } = useQuery({
    queryKey: ['webhookEvents', params],
    queryFn: () => webhooks.events(Object.keys(params).length ? params : undefined),
  })

  const replayMutation = useMutation({
    mutationFn: (id: string) => webhooks.replay(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['webhookEvents'] }),
  })

  const batchReplayMutation = useMutation({
    mutationFn: (ids: string[]) => webhooks.replayBatch(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhookEvents'] })
      setSelected(new Set())
    },
  })

  const detailQuery = useMutation({
    mutationFn: (id: string) => webhooks.event(id),
    onSuccess: (data) => setDetailEvent(data),
  })

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (isLoading) return <PageLoader />

  const columns = [
    {
      key: 'select',
      header: '',
      render: (row: WebhookEvent) => (
        <input
          type="checkbox"
          checked={selected.has(row.id)}
          onChange={() => toggleSelect(row.id)}
          onClick={(e) => e.stopPropagation()}
        />
      ),
    },
    { key: 'event_type', header: 'Event Type' },
    { key: 'action', header: 'Action' },
    { key: 'repo_name', header: 'Repository' },
    { key: 'sender', header: 'Sender' },
    {
      key: 'processed',
      header: 'Status',
      render: (row: WebhookEvent) => (
        <span className={`text-xs px-2 py-0.5 rounded ${row.processed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
          {row.processed ? 'Processed' : 'Pending'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      render: (row: WebhookEvent) => new Date(row.created_at).toLocaleString(),
    },
    {
      key: 'actions',
      header: '',
      render: (row: WebhookEvent) => (
        <div className="flex gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); replayMutation.mutate(row.id) }}
            className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
          >
            Replay
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); detailQuery.mutate(row.id) }}
            className="px-2 py-1 text-xs bg-gray-50 text-gray-700 rounded hover:bg-gray-100"
          >
            Detail
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Webhook Events</h2>
        {selected.size > 0 && (
          <button
            onClick={() => batchReplayMutation.mutate([...selected])}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Replay Selected ({selected.size})
          </button>
        )}
      </div>

      <div className="flex gap-3 mb-4">
        <select
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
          className="px-3 py-2 border rounded text-sm"
        >
          <option value="">All Events</option>
          <option value="push">Push</option>
          <option value="pull_request">Pull Request</option>
          <option value="issues">Issues</option>
          <option value="release">Release</option>
          <option value="workflow_run">Workflow Run</option>
        </select>
        <input
          placeholder="Repository name"
          value={repoName}
          onChange={(e) => setRepoName(e.target.value)}
          className="px-3 py-2 border rounded text-sm"
        />
        <select
          value={processedFilter}
          onChange={(e) => setProcessedFilter(e.target.value)}
          className="px-3 py-2 border rounded text-sm"
        >
          <option value="">All Status</option>
          <option value="true">Processed</option>
          <option value="false">Pending</option>
        </select>
      </div>

      <div className="bg-white rounded-lg border">
        <DataTable
          data={(data || []) as unknown as Record<string, unknown>[]}
          columns={columns as { key: string; header: string; render?: (row: Record<string, unknown>) => React.ReactNode }[]}
          pageSize={20}
          searchable
        />
      </div>

      {detailEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold">
                Event: {detailEvent.event_type}/{detailEvent.action}
              </h3>
              <button
                onClick={() => setDetailEvent(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                Close
              </button>
            </div>
            <div className="p-4 space-y-2 text-sm">
              <p><span className="font-medium">ID:</span> {detailEvent.id}</p>
              <p><span className="font-medium">Repository:</span> {detailEvent.repo_name}</p>
              <p><span className="font-medium">Sender:</span> {detailEvent.sender}</p>
              <p><span className="font-medium">Processed:</span> {detailEvent.processed ? 'Yes' : 'No'}</p>
              {detailEvent.error && (
                <p><span className="font-medium">Error:</span> {detailEvent.error}</p>
              )}
              <div>
                <p className="font-medium mb-1">Payload:</p>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-96">
                  {JSON.stringify(detailEvent.payload, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
