import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { customMetrics } from '../api/client'
import type { CustomMetricResponse, VariableInfo } from '../api/client'
import PageLoader from '../components/PageLoader'

export default function Metrics() {
  const queryClient = useQueryClient()
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['custom-metrics'],
    queryFn: () => customMetrics.list(),
  })
  const { data: variables } = useQuery({
    queryKey: ['metric-variables'],
    queryFn: () => customMetrics.variables(),
  })

  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [formula, setFormula] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [evalResults, setEvalResults] = useState<Record<string, { result: number; variables: Record<string, number> }>>({})

  const createMutation = useMutation({
    mutationFn: () => customMetrics.create({ name, description: description || undefined, formula, is_public: isPublic }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom-metrics'] })
      setShowForm(false)
      setName('')
      setDescription('')
      setFormula('')
      setIsPublic(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => customMetrics.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['custom-metrics'] }),
  })

  const evaluateMutation = useMutation({
    mutationFn: (id: string) => customMetrics.evaluate(id, 30),
    onSuccess: (data) => {
      setEvalResults((prev) => ({ ...prev, [data.metric_id]: { result: data.result, variables: data.variables } }))
    },
  })

  const insertVariable = (varName: string) => {
    setFormula((prev) => (prev ? `${prev} ${varName}` : varName))
  }

  const insertOperator = (op: string) => {
    setFormula((prev) => `${prev} ${op} `)
  }

  if (isLoading) return <PageLoader />

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Custom Metrics</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'New Metric'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border p-4 mb-4 space-y-3">
          <input placeholder="Metric name" value={name} onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm" />
          <input placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border rounded text-sm" />

          {/* Formula builder */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Formula</label>
            <div className="flex flex-wrap gap-1 mb-2">
              {(variables || []).map((v: VariableInfo) => (
                <button key={v.name} onClick={() => insertVariable(v.name)}
                  className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
                  title={v.description}>
                  {v.name}
                </button>
              ))}
            </div>
            <div className="flex gap-1 mb-2">
              {['+', '-', '*', '/', '(', ')'].map((op) => (
                <button key={op} onClick={() => insertOperator(op)}
                  className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200 font-mono">
                  {op}
                </button>
              ))}
            </div>
            <input value={formula} onChange={(e) => setFormula(e.target.value)}
              placeholder="e.g., commits + prs * 2"
              className="w-full px-3 py-2 border rounded text-sm font-mono" />
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />
            Make public
          </label>

          <button onClick={() => createMutation.mutate()}
            disabled={!name || !formula}
            className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50">
            Create
          </button>
          {createMutation.error && (
            <p className="text-red-500 text-sm">{(createMutation.error as Error).message}</p>
          )}
        </div>
      )}

      <div className="space-y-3">
        {(metrics || []).map((m: CustomMetricResponse) => (
          <div key={m.id} className="bg-white rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{m.name}</p>
                <p className="text-xs text-gray-500 font-mono">{m.formula}</p>
                {m.description && <p className="text-xs text-gray-400 mt-1">{m.description}</p>}
                {m.is_public && <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded mt-1 inline-block">Public</span>}
              </div>
              <div className="flex gap-2">
                <button onClick={() => evaluateMutation.mutate(m.id)}
                  className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                  Evaluate
                </button>
                <button onClick={() => deleteMutation.mutate(m.id)}
                  className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100">
                  Delete
                </button>
              </div>
            </div>
            {evalResults[m.id] && (
              <div className="mt-3 p-3 bg-gray-50 rounded">
                <p className="text-lg font-semibold">{evalResults[m.id].result}</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {Object.entries(evalResults[m.id].variables).map(([k, v]) => (
                    <span key={k} className="text-xs text-gray-500">{k}={v}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        {metrics?.length === 0 && (
          <p className="text-gray-500 text-sm">No custom metrics yet. Create one to get started.</p>
        )}
      </div>
    </div>
  )
}
