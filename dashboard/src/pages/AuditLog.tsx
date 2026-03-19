import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { audit, AuditLogEntry } from '../api/client'
import DataTable from '../components/DataTable'

const ACTION_OPTIONS = [
  '',
  'auth.login',
  'auth.register',
  'api_key.create',
  'api_key.delete',
  'schedule.create',
  'schedule.update',
  'schedule.delete',
  'schedule.run',
  'webhook.received',
]

const STATUS_OPTIONS = ['', 'success', 'failure']

export default function AuditLog() {
  const [action, setAction] = useState('')
  const [status, setStatus] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const params: Record<string, string> = {}
  if (action) params.action = action
  if (status) params.status = status
  if (startDate) params.start_date = new Date(startDate).toISOString()
  if (endDate) params.end_date = new Date(endDate).toISOString()

  const { data: logs, isLoading, error } = useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => audit.logs(params),
  })

  const { data: stats } = useQuery({
    queryKey: ['audit-stats'],
    queryFn: () => audit.stats(),
  })

  const columns = [
    {
      key: 'created_at',
      header: 'Timestamp',
      render: (row: AuditLogEntry) =>
        new Date(row.created_at).toLocaleString(),
    },
    { key: 'user_id', header: 'User' },
    { key: 'action', header: 'Action' },
    {
      key: 'resource_type',
      header: 'Resource',
      render: (row: AuditLogEntry) =>
        row.resource_type
          ? `${row.resource_type}${row.resource_id ? ` (${row.resource_id.slice(0, 8)}...)` : ''}`
          : '-',
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: AuditLogEntry) => (
        <span
          className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
            row.status === 'success'
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }`}
        >
          {row.status}
        </span>
      ),
    },
  ]

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Audit Log</h2>

      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg border p-4">
            <p className="text-sm text-gray-500">Total Events</p>
            <p className="text-2xl font-bold">{stats.total}</p>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <p className="text-sm text-gray-500">Action Types</p>
            <p className="text-2xl font-bold">
              {Object.keys(stats.by_action).length}
            </p>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <p className="text-sm text-gray-500">Days Tracked</p>
            <p className="text-2xl font-bold">
              {Object.keys(stats.by_day).length}
            </p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border p-4 mb-4">
        <div className="flex gap-3 flex-wrap">
          <select
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded"
          >
            <option value="">All Actions</option>
            {ACTION_OPTIONS.filter(Boolean).map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded"
          >
            <option value="">All Statuses</option>
            {STATUS_OPTIONS.filter(Boolean).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded"
            placeholder="Start date"
          />
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded"
            placeholder="End date"
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-sm text-red-700">
          {error instanceof Error ? error.message : 'Failed to load audit logs'}
        </div>
      )}

      <div className="bg-white rounded-lg border">
        {isLoading ? (
          <p className="p-4 text-sm text-gray-500">Loading...</p>
        ) : (
          <DataTable
            data={(logs || []) as Array<AuditLogEntry & Record<string, unknown>>}
            columns={columns}
            pageSize={20}
            searchable
          />
        )}
      </div>
    </div>
  )
}
