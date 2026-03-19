import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { trends } from '../api/client'
import type { TrendPrediction, MovingAveragePoint } from '../api/client'
import StatCard from '../components/StatCard'
import TrendChart from '../components/TrendChart'
import PageLoader from '../components/PageLoader'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts'

export default function Trends() {
  const [showMA, setShowMA] = useState(false)
  const [predictionMetric, setPredictionMetric] = useState('commit_count')

  const { data: overview, isLoading } = useQuery({
    queryKey: ['trend-overview'],
    queryFn: () => trends.overview(30),
  })

  const { data: commitTrend } = useQuery({
    queryKey: ['trend-commits'],
    queryFn: () => trends.metric('commit_count', 30),
  })

  const { data: prediction } = useQuery({
    queryKey: ['trend-prediction', predictionMetric],
    queryFn: () => trends.predictions(predictionMetric, 90),
  })

  const { data: movingAvg } = useQuery({
    queryKey: ['trend-ma', predictionMetric],
    queryFn: () => trends.movingAverage(predictionMetric, 90, 7),
    enabled: showMA,
  })

  if (isLoading) return <PageLoader />

  // Combine historical + predictions for chart
  const predictionChartData = prediction ? [
    ...prediction.historical.map((h) => ({ date: h.date, value: h.value, predicted: null as number | null })),
    ...prediction.predictions.map((p) => ({ date: p.date.split('T')[0], value: null as number | null, predicted: p.value })),
  ] : []

  // Bridge the last historical point to first prediction
  if (predictionChartData.length > 0 && prediction && prediction.predictions.length > 0) {
    const lastHistorical = prediction.historical[prediction.historical.length - 1]
    if (lastHistorical) {
      const bridgeIdx = prediction.historical.length - 1
      predictionChartData[bridgeIdx] = {
        ...predictionChartData[bridgeIdx],
        predicted: lastHistorical.value,
      }
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Trends</h2>

      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard
            label="Velocity"
            value={overview.velocity.current_value}
            change={overview.velocity.change_percent}
            subtitle="commits + PRs"
          />
          <StatCard
            label="Quality Score"
            value={overview.quality.current_value}
            change={overview.quality.change_percent}
            subtitle="100 - security alerts"
          />
          <StatCard
            label="Engagement"
            value={overview.engagement.current_value}
            change={overview.engagement.change_percent}
            subtitle="active contributors"
          />
        </div>
      )}

      {Array.isArray(commitTrend) && commitTrend.length > 0 ? (
        <div className="bg-white rounded-lg border p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium">Commit Trend (30 days)</h3>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={showMA} onChange={(e) => setShowMA(e.target.checked)} />
              Moving Average
            </label>
          </div>
          {showMA && movingAvg && movingAvg.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={movingAvg}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="raw_value" stroke="#94a3b8" name="Raw" dot={false} />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" name="Moving Avg" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <TrendChart data={commitTrend as Array<{date: string; value: number}>} label="Commits" />
          )}
        </div>
      ) : null}

      {/* Predictions Section */}
      <div className="bg-white rounded-lg border p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium">Predictions</h3>
          <select
            value={predictionMetric}
            onChange={(e) => setPredictionMetric(e.target.value)}
            className="px-3 py-1.5 border rounded text-sm"
          >
            <option value="commit_count">Commits</option>
            <option value="pr_count">Pull Requests</option>
            <option value="open_issues">Issues</option>
          </select>
        </div>

        {prediction && (
          <div className="mb-3">
            <div className="flex gap-4 text-sm mb-2">
              <span className="px-2 py-1 bg-gray-100 rounded">
                Trend: <strong>{prediction.trend}</strong>
              </span>
              {prediction.slope !== null && (
                <span className="px-2 py-1 bg-gray-100 rounded">
                  Slope: {prediction.slope}
                </span>
              )}
              {prediction.confidence !== null && (
                <span className="px-2 py-1 bg-gray-100 rounded">
                  Confidence: {Math.round(prediction.confidence * 100)}%
                </span>
              )}
            </div>
          </div>
        )}

        {predictionChartData.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={predictionChartData}>
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" name="Historical" dot={false} />
              <Line
                type="monotone" dataKey="predicted" stroke="#3b82f6" name="Predicted"
                strokeDasharray="5 5" dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        {prediction && prediction.predictions.length > 0 && (
          <div className="mt-3 grid grid-cols-3 gap-3">
            {prediction.predictions.map((p) => (
              <div key={p.days_ahead} className="text-center p-2 bg-blue-50 rounded">
                <p className="text-xs text-gray-500">{p.days_ahead} days</p>
                <p className="text-lg font-semibold">{p.value}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
