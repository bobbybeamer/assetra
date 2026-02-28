import { useState } from 'react'
import { extractErrorMessage, runSync, type SyncResponse } from '../lib/api'

type AuthRunner = <T>(operation: (token: string) => Promise<T>) => Promise<T>

type UseSyncArgs = {
  tenantId: string
  runWithAuthRetry: AuthRunner
  onAfterSync: () => Promise<void>
  onError: (message: string) => void
}

export function useSync({ tenantId, runWithAuthRetry, onAfterSync, onError }: UseSyncArgs) {
  const [syncStatus, setSyncStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [syncMessage, setSyncMessage] = useState('No sync run yet')
  const [syncPayload, setSyncPayload] = useState<SyncResponse | null>(null)

  const handleSyncNow = async () => {
    setSyncStatus('loading')
    setSyncMessage('Running sync...')
    try {
      const payload = await runWithAuthRetry((token) => runSync(token, tenantId))
      setSyncPayload(payload)
      setSyncStatus('ok')
      const changes = Array.isArray(payload.asset_changes) ? payload.asset_changes.length : 0
      setSyncMessage(`Sync succeeded. Asset changes returned: ${changes}`)
      await onAfterSync()
    } catch (error) {
      setSyncStatus('error')
      const message = extractErrorMessage(error, 'Sync failed. Please verify auth and tenant access.')
      setSyncMessage(message)
      onError(message)
    }
  }

  const resetSyncState = () => {
    setSyncPayload(null)
    setSyncMessage('No sync run yet')
    setSyncStatus('idle')
  }

  return {
    syncStatus,
    syncMessage,
    syncPayload,
    handleSyncNow,
    resetSyncState,
  }
}
