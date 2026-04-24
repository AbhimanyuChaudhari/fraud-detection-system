import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts'

export function SparklineChart({ data }) {
  const chartData = (data || []).map((v, i) => ({ i, v }))
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border2)',
      borderRadius: 12, padding: '16px 20px'
    }}>
      <div style={{ fontSize: 11, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
        Fraud Probability — Last 60 Transactions
      </div>
      <ResponsiveContainer width="100%" height={80}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#6c63ff" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6c63ff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis domain={[0, 1]} hide />
          <XAxis dataKey="i" hide />
          <Tooltip
            contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 6, fontSize: 11 }}
            formatter={(v) => [`${(v * 100).toFixed(1)}%`, 'Fraud Prob']}
            labelFormatter={() => ''}
          />
          <Area
            type="monotone" dataKey="v"
            stroke="#6c63ff" strokeWidth={2}
            fill="url(#sparkGrad)"
            dot={false} isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RiskDistChart({ counts }) {
  const data = [
    { label: 'LOW',    value: counts?.LOW    || 0, color: '#00d68f' },
    { label: 'MEDIUM', value: counts?.MEDIUM || 0, color: '#ffb703' },
    { label: 'HIGH',   value: counts?.HIGH   || 0, color: '#ff4d6d' },
  ]

  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border2)',
      borderRadius: 12, padding: '16px 20px'
    }}>
      <div style={{ fontSize: 11, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
        Risk Distribution
      </div>
      <ResponsiveContainer width="100%" height={80}>
        <BarChart data={data} barSize={28}>
          <XAxis dataKey="label" tick={{ fontSize: 10, fill: 'var(--text3)' }} axisLine={false} tickLine={false} />
          <YAxis hide />
          <Tooltip
            contentStyle={{ background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 6, fontSize: 11 }}
            formatter={(v) => [v, 'Transactions']}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.color} fillOpacity={0.8} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
