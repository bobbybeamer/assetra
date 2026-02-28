type HealthCardProps = {
  status: 'idle' | 'loading' | 'ok' | 'error'
  message: string
  endpoint: string
  onCheck: () => void
}

export function HealthCard({ status, message, endpoint, onCheck }: HealthCardProps) {
  const statusClassName =
    status === 'ok' ? 'status-ok' : status === 'error' ? 'status-error' : status === 'loading' ? 'status-loading' : 'status-idle'

  return (
    <section className="status-card">
      <h2>Backend Health</h2>
      <p className="hint-text">Connectivity check for API availability before performing secure operations.</p>
      <p className="status-line">
        Status: <span className={`status-pill ${statusClassName}`}>{status.toUpperCase()}</span>
      </p>
      <p>{message}</p>
      <p className="endpoint">Endpoint: {endpoint}</p>
      <button className="primary-button" onClick={onCheck} disabled={status === 'loading'}>
        {status === 'loading' ? 'Checking…' : 'Re-check backend'}
      </button>
    </section>
  )
}
