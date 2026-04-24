import { useEffect, useRef } from 'react'

function RiskBadge({ level }) {
  const config = {
    HIGH:   { color: 'var(--red)',    bg: 'rgba(255,77,109,0.12)',   dot: '#ff4d6d' },
    MEDIUM: { color: 'var(--amber)',  bg: 'rgba(255,183,3,0.12)',    dot: '#ffb703' },
    LOW:    { color: 'var(--green)',  bg: 'rgba(0,214,143,0.12)',    dot: '#00d68f' },
  }
  const c = config[level] || config.LOW
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: c.bg, border: `1px solid ${c.color}22`,
      borderRadius: 6, padding: '3px 8px', fontSize: 11, color: c.color, fontWeight: 500
    }}>
      <div style={{ position: 'relative', width: 6, height: 6 }}>
        <div style={{ width: 6, height: 6, borderRadius: '50%', background: c.dot }} />
        {level === 'HIGH' && (
          <div style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            background: c.dot, animation: 'ping 1.5s ease-out infinite'
          }} />
        )}
      </div>
      {level}
    </div>
  )
}

function ScoreBar({ value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{
        flex: 1, height: 4, background: 'var(--bg4)',
        borderRadius: 2, overflow: 'hidden'
      }}>
        <div style={{
          width: `${Math.min(value * 100, 100)}%`,
          height: '100%', background: color, borderRadius: 2,
          transition: 'width 0.4s ease'
        }} />
      </div>
      <span style={{ fontSize: 10, color: 'var(--text3)', width: 32, textAlign: 'right' }}>
        {(value * 100).toFixed(0)}%
      </span>
    </div>
  )
}

export default function TransactionFeed({ transactions }) {
  const listRef = useRef()

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0
    }
  }, [transactions.length])

  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border2)',
      borderRadius: 12, display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 20px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ position: 'relative' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)' }} />
            <div style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              background: 'var(--green)', animation: 'ping 2s ease-out infinite'
            }} />
          </div>
          <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>Live Transaction Feed</span>
        </div>
        <span style={{ fontSize: 11, color: 'var(--text3)' }}>
          {transactions.length} transactions
        </span>
      </div>

      {/* Column headers */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '120px 90px 70px 80px 1fr 80px',
        gap: 8, padding: '8px 20px',
        borderBottom: '1px solid var(--border)',
        fontSize: 10, color: 'var(--text3)',
        textTransform: 'uppercase', letterSpacing: '0.06em'
      }}>
        <span>TX ID</span>
        <span>Amount</span>
        <span>Risk</span>
        <span>Score</span>
        <span>Model Breakdown</span>
        <span>Latency</span>
      </div>

      {/* Rows */}
      <div ref={listRef} style={{ overflowY: 'auto', flex: 1 }}>
        {transactions.length === 0 ? (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            height: 120, color: 'var(--text3)', fontSize: 13
          }}>
            Waiting for transactions...
          </div>
        ) : (
          transactions.map((tx, i) => (
            <div key={tx.id || i} style={{
              display: 'grid',
              gridTemplateColumns: '120px 90px 70px 80px 1fr 80px',
              gap: 8, padding: '10px 20px',
              borderBottom: '1px solid var(--border)',
              animation: i === 0 ? 'slideIn 0.3s ease' : 'none',
              background: tx.risk_level === 'HIGH' ? 'rgba(255,77,109,0.03)' : 'transparent',
              transition: 'background 0.2s'
            }}>
              <span style={{ fontSize: 12, color: 'var(--text2)', fontFamily: 'monospace' }}>
                {tx.transaction_id?.slice(0, 10)}...
              </span>
              <span style={{ fontSize: 12, color: 'var(--text)', fontWeight: 500 }}>
                ${tx.amount?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span><RiskBadge level={tx.risk_level} /></span>
              <span style={{
                fontSize: 13, fontWeight: 600,
                color: tx.fraud_probability > 0.7 ? 'var(--red)' :
                       tx.fraud_probability > 0.4 ? 'var(--amber)' : 'var(--green)'
              }}>
                {(tx.fraud_probability * 100).toFixed(1)}%
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3, justifyContent: 'center' }}>
                <ScoreBar value={tx.xgb_score || 0}  color="var(--accent2)" />
                <ScoreBar value={tx.iso_score || 0}  color="var(--amber)" />
                <ScoreBar value={tx.lstm_score || 0} color="var(--blue)" />
              </div>
              <span style={{ fontSize: 11, color: 'var(--text3)' }}>
                {tx.latency_ms?.toFixed(0)}ms
              </span>
            </div>
          ))
        )}
      </div>

      {/* Legend */}
      <div style={{
        padding: '8px 20px', borderTop: '1px solid var(--border)',
        display: 'flex', gap: 16, fontSize: 10, color: 'var(--text3)'
      }}>
        {[['XGBoost', 'var(--accent2)'], ['Isolation Forest', 'var(--amber)'], ['LSTM', 'var(--blue)']].map(([label, color]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 8, height: 3, background: color, borderRadius: 2 }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}
