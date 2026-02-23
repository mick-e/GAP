import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { schedules } from '../api/client'
import type { Schedule } from '../api/client'
import PageLoader from '../components/PageLoader'

export default function Reports() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['schedules'], queryFn: () => schedules.list() })

  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [reportType, setReportType] = useState('activity')
  const [schedule, setSchedule] = useState('weekly')
  const [recipients, setRecipients] = useState('')

  const createMutation = useMutation({
    mutationFn: () => schedules.create({
      name, report_type: reportType, schedule,
      recipients: recipients.split(',').map((r) => r.trim()).filter(Boolean),
      config: {},
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      setShowForm(false)
      setName('')
      setRecipients('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => schedules.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schedules'] }),
  })

  const runMutation = useMutation({
    mutationFn: (id: string) => schedules.run(id),
  })

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Scheduled Reports</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'New Schedule'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border p-4 mb-4 space-y-3">
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm" />
          <div className="flex gap-3">
            <select value={reportType} onChange={(e) => setReportType(e.target.value)}
              className="px-3 py-2 border rounded text-sm">
              <option value="activity">Activity</option>
              <option value="quality">Quality</option>
              <option value="releases">Releases</option>
            </select>
            <select value={schedule} onChange={(e) => setSchedule(e.target.value)}
              className="px-3 py-2 border rounded text-sm">
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          <input placeholder="Recipients (comma-separated emails)" value={recipients}
            onChange={(e) => setRecipients(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm" />
          <button onClick={() => createMutation.mutate()}
            className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">
            Create
          </button>
        </div>
      )}

      <div className="space-y-3">
        {(data || []).map((s: Schedule) => (
          <div key={s.id} className="bg-white rounded-lg border p-4 flex items-center justify-between">
            <div>
              <p className="font-medium">{s.name}</p>
              <p className="text-xs text-gray-500">
                {s.report_type} / {s.schedule} / {s.is_active ? 'Active' : 'Paused'}
              </p>
              {s.next_run_at && (
                <p className="text-xs text-gray-400">Next: {new Date(s.next_run_at).toLocaleString()}</p>
              )}
            </div>
            <div className="flex gap-2">
              <button onClick={() => runMutation.mutate(s.id)}
                className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                Run Now
              </button>
              <button onClick={() => deleteMutation.mutate(s.id)}
                className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100">
                Delete
              </button>
            </div>
          </div>
        ))}
        {data?.length === 0 && (
          <p className="text-gray-500 text-sm">No scheduled reports yet.</p>
        )}
      </div>
    </div>
  )
}
