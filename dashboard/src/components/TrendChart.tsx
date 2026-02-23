import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface DataPoint {
  date: string
  value: number
}

interface Props {
  data: DataPoint[]
  color?: string
  label?: string
}

export default function TrendChart({ data, color = '#3b82f6', label = 'Value' }: Props) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Area type="monotone" dataKey="value" stroke={color} fill={color} fillOpacity={0.1} name={label} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
