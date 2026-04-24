export default function StatCards({ stats }) {
  const cards = [
    {
      label: 'Total Scored',
      value: stats?.total_scored?.toLocaleString() || '0',
      icon: '⬡',
      color: 'var(--accent2)',
      bg: 'rgba(108,99,255,0.08)'
    },
    {
      label: 'High Risk',
      value: stats?.high_risk?.toLocaleString() || '0',
      icon: '⚠',
      color: 'var(--red)',
      bg: 'rgba(255,77,109,0.08)'
    },
    {
      label: 'Fraud Rate',
      value: `${stats?.fraud_rate || 0}%`,
      icon: '◎',
      color: 'var(--amber)',
      bg: 'rgba(255,183,3,0.08)'
    },
    {
      label: 'Avg Latency',
      value: `${stats?.avg_latency_ms || 0}ms`,
      icon: '⚡',
      color: 'var(--green)',
      bg: 'rgba(0,214,143,0.08)'
    },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
      {cards.map((c, i) => (
        <div key={i} style={{
          background: 'var(--bg2)', border: '1px solid var(--border2)',
          borderRadius: 12, padding: '16px 20px',
          animation: `fadeUp 0.4s ease ${i * 0.08}s both`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ fontSize: 11, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {c.label}
            </div>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: c.bg, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 14, color: c.color
            }}>
              {c.icon}
            </div>
          </div>
          <div style={{ fontSize: 26, fontWeight: 600, color: c.color, letterSpacing: '-0.02em' }}>
            {c.value}
          </div>
        </div>
      ))}
    </div>
  )
}
