import { type FormEvent, useState } from 'react'
import {
  ApiError,
  createAsset,
  extractErrorMessage,
  extractFieldErrors,
  listAssets,
  getAssetDetail,
  updateAsset,
  type UpdateAssetInput,
  type AssetRecord,
} from '../lib/api'

type AuthRunner = <T>(operation: (token: string) => Promise<T>) => Promise<T>

type UseAssetsArgs = {
  tenantId: string
  runWithAuthRetry: AuthRunner
  onUnauthorized: (message: string) => void
  onError: (message: string) => void
}

export function useAssets({ tenantId, runWithAuthRetry, onUnauthorized, onError }: UseAssetsArgs) {
  const [assets, setAssets] = useState<AssetRecord[]>([])
  const [assetsStatus, setAssetsStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [selectedAsset, setSelectedAsset] = useState<AssetRecord | null>(null)
  const [detailStatus, setDetailStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [newAssetTag, setNewAssetTag] = useState('')
  const [newAssetName, setNewAssetName] = useState('')
  const [newAssetStatus, setNewAssetStatus] = useState('active')
  const [createStatus, setCreateStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [createMessage, setCreateMessage] = useState('')
  const [createErrors, setCreateErrors] = useState<Record<string, string>>({})

  const loadAssets = async (tokenValue: string, tenantValue: string) => {
    setAssetsStatus('loading')
    try {
      const records = await listAssets(tokenValue, tenantValue)
      setAssets(records)
      setAssetsStatus('ok')
    } catch (error) {
      setAssetsStatus('error')
      onError(extractErrorMessage(error, 'Failed to load assets.'))
    }
  }

  const loadAssetsAuthed = async () => {
    setAssetsStatus('loading')
    try {
      const records = await runWithAuthRetry((token) => listAssets(token, tenantId))
      setAssets(records)
      setAssetsStatus('ok')
    } catch (error) {
      setAssetsStatus('error')
      const message = extractErrorMessage(error, 'Unable to refresh assets with current session.')
      if (error instanceof ApiError && error.status === 401) {
        onUnauthorized('Session expired or unauthorized. Please sign in again.')
      }
      onError(message)
    }
  }

  const loadAssetDetailAuthed = async (assetId: number) => {
    setDetailStatus('loading')
    try {
      const detail = await runWithAuthRetry((token) => getAssetDetail(assetId, token, tenantId))
      setSelectedAsset(detail)
      setDetailStatus('ok')
    } catch (error) {
      setDetailStatus('error')
      onError(extractErrorMessage(error, 'Failed to load asset detail.'))
    }
  }

  const handleCreateAsset = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setCreateStatus('loading')
    setCreateMessage('Creating asset...')
    setCreateErrors({})
    try {
      const created = await runWithAuthRetry((token) =>
        createAsset(
          {
            asset_tag: newAssetTag,
            name: newAssetName,
            status: newAssetStatus,
          },
          token,
          tenantId,
        ),
      )
      setCreateStatus('ok')
      setCreateMessage(`Created asset #${created.id}`)
      setNewAssetTag('')
      setNewAssetName('')
      await loadAssetsAuthed()
      await loadAssetDetailAuthed(created.id)
    } catch (error) {
      setCreateStatus('error')
      if (error instanceof ApiError) {
        setCreateErrors(extractFieldErrors(error.data))
      }
      setCreateMessage(extractErrorMessage(error, 'Asset create failed. Verify required fields and tenant access.'))
      onError(extractErrorMessage(error, 'Asset create failed.'))
    }
  }

  const updateAssetAuthed = async (assetId: number, input: UpdateAssetInput) => {
    try {
      const updated = await runWithAuthRetry((token) => updateAsset(assetId, input, token, tenantId))
      setAssets((current) => current.map((asset) => (asset.id === assetId ? updated : asset)))
      setSelectedAsset((current) => (current?.id === assetId ? updated : current))
      return updated
    } catch (error) {
      onError(extractErrorMessage(error, 'Asset update failed.'))
      throw error
    }
  }

  const resetAssetsState = () => {
    setAssets([])
    setSelectedAsset(null)
    setCreateMessage('')
    setCreateErrors({})
    setCreateStatus('idle')
    setAssetsStatus('idle')
    setDetailStatus('idle')
  }

  return {
    assets,
    assetsStatus,
    selectedAsset,
    detailStatus,
    newAssetTag,
    newAssetName,
    newAssetStatus,
    createStatus,
    createMessage,
    createErrors,
    setNewAssetTag,
    setNewAssetName,
    setNewAssetStatus,
    loadAssets,
    loadAssetsAuthed,
    loadAssetDetailAuthed,
    handleCreateAsset,
    updateAssetAuthed,
    resetAssetsState,
  }
}
