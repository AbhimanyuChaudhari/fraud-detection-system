import { useState } from 'react'

export default function KafkaProducer({ onTransaction }) {
  const [running, setRunning]   = useState(false)
  const [count, setCount]       = useState(0)
  const [interval, setIntervalRef] = useState(null)

  const SAMPLE_TRANSACTIONS = [
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 250.00,   TransactionDT: 86400,  ProductCD: 'W', card4: 'visa',       card6: 'debit',  P_emaildomain: 'gmail.com',     R_emaildomain: 'gmail.com',  DeviceType: 'desktop', isFraud: 0 },
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 15000.00, TransactionDT: 7200,   ProductCD: 'C', card4: 'mastercard', card6: 'credit', P_emaildomain: 'protonmail.com', R_emaildomain: 'yahoo.com',  DeviceType: 'mobile',  isFraud: 1 },
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 49.99,    TransactionDT: 43200,  ProductCD: 'H', card4: 'visa',       card6: 'debit',  P_emaildomain: 'outlook.com',   R_emaildomain: 'gmail.com',  DeviceType: 'desktop', isFraud: 0 },
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 8750.00,  TransactionDT: 3600,   ProductCD: 'S', card4: 'discover',   card6: 'credit', P_emaildomain: 'temp.com',      R_emaildomain: 'hotmail.com',DeviceType: 'mobile',  isFraud: 1 },
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 120.50,   TransactionDT: 64800,  ProductCD: 'W', card4: 'visa',       card6: 'debit',  P_emaildomain: 'gmail.com',     R_emaildomain: 'gmail.com',  DeviceType: 'desktop', isFraud: 0 },
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 3200.00,  TransactionDT: 10800,  ProductCD: 'C', card4: 'amex',       card6: 'credit', P_emaildomain: 'icloud.com',    R_emaildomain: 'yahoo.com',  DeviceType: 'desktop', isFraud: 0 },
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 22000.00, TransactionDT: 1800,   ProductCD: 'R', card4: 'mastercard', card6: 'credit', P_emaildomain: 'guerrilla.com', R_emaildomain: 'temp.org',   DeviceType: 'mobile',  isFraud: 1 },
    { TransactionID: `TX${Date.now()}`, TransactionAmt: 75.00,    TransactionDT: 54000,  ProductCD: 'W', card4: 'visa',       card6: 'debit',  P_emaildomain: 'gmail.com',     R_emaildomain: 'gmail.com',  DeviceType: 'desktop', isFraud: 0 },
  ]

  let idx = 0

  async function sendNext() {
    const tx = { ...SAMPLE_TRANSACTIONS[idx % SAMPLE_TRANSACTIONS.length], TransactionID: `TX${Date.now()}_${idx}` }
    idx++
    try {
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tx)
      })
      if (res.ok) {
        setCount(c => c + 1)
        onTransaction()
      }
    } catch (e) {}
  }

  function startStream() {
    setRunning(true)
    const id = setInterval(sendNext, 1500)
    setIntervalRef(id)
  }

  function stopStream() {
    setRunning(false)
    clearInterval(interval)
  }

  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border2)',
      borderRadius: 12, padding: '14px 20px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: running ? 'rgba(0,214,143,0.1)' : 'rgba(108,99,255,0.1)',
          border: `1px solid ${running ? 'rgba(0,214,143,0.3)' : 'rgba(108,99,255,0.3)'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16
        }}>
          {running ? '📡' : '⬡'}
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>
            Transaction Stream Simulator
          </div>
          <div style={{ fontSize: 11, color: 'var(--text3)' }}>
            {running ? `Streaming... ${count} transactions sent` : 'Simulates IEEE-CIS transaction patterns'}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {running && (
          <div style={{ display: 'flex', gap: 3, alignItems: 'center' }}>
            {[0, 1, 2].map(i => (
              <div key={i} style={{
                width: 3, height: 12, background: 'var(--green)', borderRadius: 2,
                animation: `pulse 1s ease-in-out ${i * 0.2}s infinite`
              }} />
            ))}
          </div>
        )}
        <button
          onClick={running ? stopStream : startStream}
          style={{
            padding: '8px 20px', borderRadius: 8, border: 'none',
            background: running ? 'rgba(255,77,109,0.15)' : 'var(--accent)',
            color: running ? 'var(--red)' : 'white',
            fontSize: 13, fontWeight: 500, cursor: 'pointer',
            border: running ? '1px solid rgba(255,77,109,0.3)' : 'none',
            transition: 'all 0.15s'
          }}
        >
          {running ? 'Stop Stream' : 'Start Stream'}
        </button>
      </div>
    </div>
  )
}
