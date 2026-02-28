import { useMemo, useState } from 'react'
import { type SyncResponse } from '../lib/api'

type SyncPageProps = {
  syncStatus: 'idle' | 'loading' | 'ok' | 'error'
  syncMessage: string
  syncPayload: SyncResponse | null
  canWrite: boolean
  onRunSync: () => void
}

export function SyncPage({ syncStatus, syncMessage, syncPayload, canWrite, onRunSync }: SyncPageProps) {
  const [showRawPayload, setShowRawPayload] = useState(false)
  const assetChanges = Array.isArray(syncPayload?.asset_changes) ? syncPayload.asset_changes.length : 0
  const acceptedEvents = Array.isArray(syncPayload?.accepted_scan_event_ids)
    ? syncPayload.accepted_scan_event_ids.length
    : 0
  const statusClassName = useMemo(() => {
    if (syncStatus === 'ok') {
      return 'status-ok'
    }
    if (syncStatus === 'error') {
      return 'status-error'
    }
    if (syncStatus === 'loading') {
      return 'status-loading'
    }
    return 'status-idle'
  }, [syncStatus])
  const syncMessageClass =
    syncStatus === 'ok'
      ? 'inline-message message-success'
      : syncStatus === 'error'
        ? 'inline-message message-error'
        : syncStatus === 'loading'
          ? 'inline-message message-info'
          : 'inline-message message-muted'

  return (
    <section className="status-card">
      <h2>Sync</h2>
      <p className="hint-text">Run a sync to exchange recent device and asset updates with the backend.</p>
      {!canWrite ? <p className="inline-message message-muted">Your role is read-only. Sync execution is disabled.</p> : null}
      <p className="status-line">
        Sync status: <span className={`status-pill ${statusClassName}`}>{syncStatus.toUpperCase()}</span>
      </p>
      <p className={syncMessageClass} role={syncStatus === 'error' ? 'alert' : 'status'} aria-live="polite">
        {syncMessage}
      </p>
      <div className="sync-actions">
        <button className="primary-button" onClick={onRunSync} disabled={syncStatus === 'loading' || !canWrite}>
          {syncStatus === 'loading' ? 'Running sync…' : 'Run Sync Now'}
        </button>
        {syncPayload ? (
          <button type="button" className="secondary-button" onClick={() => setShowRawPayload((current) => !current)}>
            {showRawPayload ? 'Hide raw payload' : 'Show raw payload'}
          </button>
        ) : null}
      </div>
      {syncPayload ? (
        <p className="pagination-meta">Last sync response captured from server at {syncPayload.server_time ?? '-'}</p>
      ) : null}
      {syncPayload ? (
        <div className="sync-summary">
          <p>
            Asset changes: <strong>{assetChanges}</strong>
          </p>
          <p>
            Accepted scan events: <strong>{acceptedEvents}</strong>
          </p>
          <p>
            Server time: <strong>{syncPayload.server_time ?? '-'}</strong>
          </p>
        </div>
      ) : (
        <div className="sync-summary">
          <p>No sync payload yet. Run sync to view reconciliation details.</p>
        </div>
      )}
      {syncPayload && showRawPayload ? <pre className="json-block">{JSON.stringify(syncPayload, null, 2)}</pre> : null}
    </section>
  )
}
