import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { schedules, exportSchedules } from '../api/client'
import type { Schedule, ScheduleTemplate, ExportScheduleResponse } from '../api/client'
import PageLoader from '../components/PageLoader'

export default function Reports() {
  const [tab, setTab] = useState<'reports' | 'templates' | 'exports'>('reports')

  return (
    <div>
      <div className="flex items-center gap-4 mb-4 border-b">
        <button
          onClick={() => setTab('reports')}
          className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'reports' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Scheduled Reports
        </button>
        <button
          onClick={() => setTab('templates')}
          className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'templates' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Templates
        </button>
        <button
          onClick={() => setTab('exports')}
          className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'exports' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Scheduled Exports
        </button>
      </div>

      {tab === 'reports' && <ScheduledReports />}
      {tab === 'templates' && <TemplatesTab />}
      {tab === 'exports' && <ScheduledExports />}
    </div>
  )
}

function ScheduledReports() {
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

function TemplatesTab() {
  const queryClient = useQueryClient()
  const { data: templates } = useQuery({ queryKey: ['scheduleTemplates'], queryFn: () => schedules.templates() })

  const [selectedTemplate, setSelectedTemplate] = useState<ScheduleTemplate | null>(null)
  const [templateRecipients, setTemplateRecipients] = useState('')
  const [templateNameOverride, setTemplateNameOverride] = useState('')

  const createFromTemplateMutation = useMutation({
    mutationFn: (data: { template_id: string; recipients: string[]; name?: string }) =>
      schedules.createFromTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      setSelectedTemplate(null)
      setTemplateRecipients('')
      setTemplateNameOverride('')
    },
  })

  function handleUseTemplate(tpl: ScheduleTemplate) {
    setSelectedTemplate(tpl)
    setTemplateNameOverride('')
    setTemplateRecipients('')
  }

  function handleCreateFromTemplate() {
    if (!selectedTemplate) return
    const recips = templateRecipients.split(',').map((r) => r.trim()).filter(Boolean)
    createFromTemplateMutation.mutate({
      template_id: selectedTemplate.id,
      recipients: recips,
      name: templateNameOverride || undefined,
    })
  }

  return (
    <div className="space-y-3">
      {selectedTemplate && (
        <div className="bg-white rounded-lg border p-4 mb-4 space-y-3">
          <p className="font-medium">Create from: {selectedTemplate.name}</p>
          <input
            placeholder="Name override (optional)"
            value={templateNameOverride}
            onChange={(e) => setTemplateNameOverride(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm"
          />
          <input
            placeholder="Recipients (comma-separated emails)"
            value={templateRecipients}
            onChange={(e) => setTemplateRecipients(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm"
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreateFromTemplate}
              className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700"
            >
              Create Schedule
            </button>
            <button
              onClick={() => setSelectedTemplate(null)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {(templates || []).map((tpl: ScheduleTemplate) => (
        <div key={tpl.id} className="bg-white rounded-lg border p-4 flex items-center justify-between">
          <div>
            <p className="font-medium">{tpl.name}</p>
            <p className="text-xs text-gray-500">{tpl.description}</p>
            <p className="text-xs text-gray-400 mt-1">
              {tpl.report_type} / {tpl.schedule}
            </p>
          </div>
          <button
            onClick={() => handleUseTemplate(tpl)}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Use Template
          </button>
        </div>
      ))}
      {templates?.length === 0 && (
        <p className="text-gray-500 text-sm">No templates available.</p>
      )}
    </div>
  )
}

function ScheduledExports() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['export-schedules'],
    queryFn: () => exportSchedules.list(),
  })

  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [exportType, setExportType] = useState('pdf')
  const [dataSource, setDataSource] = useState('contributors')
  const [schedule, setSchedule] = useState('weekly')
  const [recipients, setRecipients] = useState('')

  const createMutation = useMutation({
    mutationFn: () => exportSchedules.create({
      name, export_type: exportType, data_source: dataSource, schedule,
      recipients: recipients.split(',').map((r) => r.trim()).filter(Boolean),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['export-schedules'] })
      setShowForm(false)
      setName('')
      setRecipients('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => exportSchedules.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['export-schedules'] }),
  })

  const runMutation = useMutation({
    mutationFn: (id: string) => exportSchedules.run(id),
  })

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Scheduled Exports</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'New Export'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border p-4 mb-4 space-y-3">
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm" />
          <div className="flex gap-3">
            <select value={dataSource} onChange={(e) => setDataSource(e.target.value)}
              className="px-3 py-2 border rounded text-sm">
              <option value="contributors">Contributors</option>
              <option value="teams">Teams</option>
              <option value="trends">Trends</option>
            </select>
            <select value={exportType} onChange={(e) => setExportType(e.target.value)}
              className="px-3 py-2 border rounded text-sm">
              <option value="pdf">PDF</option>
              <option value="csv">CSV</option>
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
        {(data || []).map((e: ExportScheduleResponse) => (
          <div key={e.id} className="bg-white rounded-lg border p-4 flex items-center justify-between">
            <div>
              <p className="font-medium">{e.name}</p>
              <p className="text-xs text-gray-500">
                {e.data_source} / {e.export_type.toUpperCase()} / {e.schedule} / {e.is_active ? 'Active' : 'Paused'}
              </p>
              {e.next_run_at && (
                <p className="text-xs text-gray-400">Next: {new Date(e.next_run_at).toLocaleString()}</p>
              )}
              {e.last_run_at && (
                <p className="text-xs text-gray-400">Last: {new Date(e.last_run_at).toLocaleString()}</p>
              )}
            </div>
            <div className="flex gap-2">
              <button onClick={() => runMutation.mutate(e.id)}
                className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                Run Now
              </button>
              <button onClick={() => deleteMutation.mutate(e.id)}
                className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100">
                Delete
              </button>
            </div>
          </div>
        ))}
        {data?.length === 0 && (
          <p className="text-gray-500 text-sm">No scheduled exports yet.</p>
        )}
      </div>
    </div>
  )
}
