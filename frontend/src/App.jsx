import { useState, useEffect, useCallback } from 'react'
import StatCards from './components/StatCards'
import TransactionFeed from './components/TransactionFeed'
import { SparklineChart, RiskDistChart } from './components/Charts'
import KafkaProducer from './components/KafkaProducer'

const POLL_INTERVAL = 2000

export default function App() {
  const [transactions, setTransactions] = useState([])
  const [stats, setStats]               = useState(null)
  const [lastUpdate, setLastUpdate]     = useState(null)

  const fetchData = useCallback(async () => {
    try {
      const [txRes, statsRes] = await Promise.all([
        fetch('/api/transactions/recent?limit=50'),
        fetch('/api/stats')
      ])
      const txData    = await txRes.json()
      const statsData = await statsRes.json()
      setTransactions(txData)
      setStats(statsData)
      setLastUpdate(new Date())
    } catch (e) {}
  }, [])

  useEffect(() => {
    fetchData()
    const id = setInterval(fetchData, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [fetchData])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: 20, gap: 14, overflow: 'hidden' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #6c63ff, #9d97ff)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18
          }}>⬡</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.01em' }}>
              FraudSense
            </div>
            <div style={{ fontSize: 11, color: 'var(--text3)' }}>
              Real-Time Detection · XGBoost + Isolation Forest + LSTM
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {lastUpdate && (
            <div style={{ fontSize: 11, color: 'var(--text3)' }}>
              Updated {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(0,214,143,0.08)', border: '1px solid rgba(0,214,143,0.2)',
            borderRadius: 8, padding: '5px 12px'
          }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--green)', animation: 'pulse 2s infinite' }} />
            <span style={{ fontSize: 11, color: 'var(--green)', fontWeight: 500 }}>API Live</span>
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      <div style={{ flexShrink: 0 }}>
        <StatCards stats={stats} />
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 14, flexShrink: 0 }}>
        <SparklineChart data={stats?.sparkline} />
        <RiskDistChart counts={stats?.risk_counts} />
      </div>

      {/* Stream simulator */}
      <div style={{ flexShrink: 0 }}>
        <KafkaProducer onTransaction={fetchData} />
      </div>

      {/* Live feed */}
      <TransactionFeed transactions={transactions} />

    </div>
  )
}
