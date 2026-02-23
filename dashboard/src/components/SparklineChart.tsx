import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface Props {
  data: number[]
  color?: string
}

export default function SparklineChart({ data, color = '#3b82f6' }: Props) {
  const chartData = data.map((v, i) => ({ v, i }))

  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={chartData}>
        <Line type="monotone" dataKey="v" stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
