import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { ApiError, extractFieldErrors, type AssetRecord, type UpdateAssetInput } from '../lib/api'

type AssetsPageProps = {
  newAssetTag: string
  newAssetName: string
  newAssetStatus: string
  canWrite: boolean
  createStatus: 'idle' | 'loading' | 'ok' | 'error'
  createMessage: string
  createErrors: Record<string, string>
  assets: AssetRecord[]
  assetsStatus: 'idle' | 'loading' | 'ok' | 'error'
  selectedAsset: AssetRecord | null
  detailStatus: 'idle' | 'loading' | 'ok' | 'error'
  onNewAssetTagChange: (value: string) => void
  onNewAssetNameChange: (value: string) => void
  onNewAssetStatusChange: (value: string) => void
  onCreateAsset: (event: FormEvent<HTMLFormElement>) => void
  onViewAsset: (assetId: number) => void
  onUpdateAsset: (assetId: number, input: UpdateAssetInput) => Promise<AssetRecord>
}

export function AssetsPage({
  newAssetTag,
  newAssetName,
  newAssetStatus,
  canWrite,
  createStatus,
  createMessage,
  createErrors,
  assets,
  assetsStatus,
  selectedAsset,
  detailStatus,
  onNewAssetTagChange,
  onNewAssetNameChange,
  onNewAssetStatusChange,
  onCreateAsset,
  onViewAsset,
  onUpdateAsset,
}: AssetsPageProps) {
  type AssetActivityItem = {
    id: string
    assetId: number
    action: 'edit' | 'bulk'
    status: string
    at: number
  }

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [editingAssetId, setEditingAssetId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editStatus, setEditStatus] = useState('active')
  const [editMessageStatus, setEditMessageStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [editMessage, setEditMessage] = useState('')
  const [editErrors, setEditErrors] = useState<Record<string, string>>({})
  const [sortColumn, setSortColumn] = useState<'id' | 'asset_tag' | 'name' | 'status'>('id')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [pageSize, setPageSize] = useState(10)
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedAssetIds, setSelectedAssetIds] = useState<number[]>([])
  const [bulkStatus, setBulkStatus] = useState('active')
  const [bulkMessageStatus, setBulkMessageStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [bulkMessage, setBulkMessage] = useState('')
  const [bulkRunning, setBulkRunning] = useState(false)
  const [rowUpdateTimes, setRowUpdateTimes] = useState<Record<number, number>>({})
  const [currentTime, setCurrentTime] = useState(Date.now())
  const [activityItems, setActivityItems] = useState<AssetActivityItem[]>([])
  const [exportMessageStatus, setExportMessageStatus] = useState<'idle' | 'ok' | 'error'>('idle')
  const [exportMessage, setExportMessage] = useState('')
  const createAssetTagInputRef = useRef<HTMLInputElement | null>(null)
  const searchInputRef = useRef<HTMLInputElement | null>(null)
  const inlineEditNameInputRef = useRef<HTMLInputElement | null>(null)

  const statusOptions = useMemo(() => {
    const values = assets
      .map((asset) => (typeof asset.status === 'string' ? asset.status : ''))
      .filter((value) => value.length > 0)
    return ['all', ...new Set(values)]
  }, [assets])

  const filteredAssets = useMemo(() => {
    const normalizedQuery = searchTerm.trim().toLowerCase()
    return assets.filter((asset) => {
      const matchesStatus =
        statusFilter === 'all' || (typeof asset.status === 'string' && asset.status === statusFilter)
      if (!matchesStatus) {
        return false
      }

      if (!normalizedQuery) {
        return true
      }

      const inTag = typeof asset.asset_tag === 'string' && asset.asset_tag.toLowerCase().includes(normalizedQuery)
      const inName = typeof asset.name === 'string' && asset.name.toLowerCase().includes(normalizedQuery)
      const inId = String(asset.id).includes(normalizedQuery)
      return inTag || inName || inId
    })
  }, [assets, searchTerm, statusFilter])

  const sortedAssets = useMemo(() => {
    const toComparable = (asset: AssetRecord): string | number => {
      if (sortColumn === 'id') {
        return asset.id
      }
      const value = asset[sortColumn]
      return typeof value === 'string' ? value.toLowerCase() : ''
    }

    return [...filteredAssets].sort((left, right) => {
      const leftValue = toComparable(left)
      const rightValue = toComparable(right)
      let result = 0

      if (typeof leftValue === 'number' && typeof rightValue === 'number') {
        result = leftValue - rightValue
      } else {
        result = String(leftValue).localeCompare(String(rightValue))
      }

      return sortDirection === 'asc' ? result : -result
    })
  }, [filteredAssets, sortColumn, sortDirection])

  const assetSummary = useMemo(() => {
    const summary = {
      total: assets.length,
      active: 0,
      in_maintenance: 0,
      retired: 0,
      lost: 0,
    }

    for (const asset of assets) {
      if (asset.status === 'active') {
        summary.active += 1
      } else if (asset.status === 'in_maintenance') {
        summary.in_maintenance += 1
      } else if (asset.status === 'retired') {
        summary.retired += 1
      } else if (asset.status === 'lost') {
        summary.lost += 1
      }
    }

    return summary
  }, [assets])

  const totalPages = Math.max(1, Math.ceil(sortedAssets.length / pageSize))
  const startIndex = (currentPage - 1) * pageSize
  const endIndexExclusive = startIndex + pageSize
  const paginatedAssets = sortedAssets.slice(startIndex, endIndexExclusive)
  const hasActiveViewChanges =
    searchTerm.trim().length > 0 ||
    statusFilter !== 'all' ||
    sortColumn !== 'id' ||
    sortDirection !== 'asc' ||
    pageSize !== 10

  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, statusFilter, sortColumn, sortDirection, pageSize])

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages)
    }
  }, [currentPage, totalPages])

  useEffect(() => {
    const visibleIds = new Set(sortedAssets.map((asset) => asset.id))
    setSelectedAssetIds((current) => current.filter((id) => visibleIds.has(id)))
  }, [sortedAssets])

  useEffect(() => {
    if (!canWrite) {
      setSelectedAssetIds([])
      setEditingAssetId(null)
    }
  }, [canWrite])

  useEffect(() => {
    const timer = window.setInterval(() => {
      setCurrentTime(Date.now())
    }, 1000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (createStatus === 'ok') {
      createAssetTagInputRef.current?.focus()
    }
  }, [createStatus])

  useEffect(() => {
    if (editingAssetId !== null) {
      inlineEditNameInputRef.current?.focus()
    }
  }, [editingAssetId])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      const isTypingTarget =
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.tagName === 'SELECT' ||
        target?.isContentEditable

      if (isTypingTarget) {
        return
      }

      const isMetaK = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k'
      const isSlash = event.key === '/'
      if (!isMetaK && !isSlash) {
        return
      }

      event.preventDefault()
      searchInputRef.current?.focus()
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const toggleSort = (column: 'id' | 'asset_tag' | 'name' | 'status') => {
    if (sortColumn === column) {
      setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortColumn(column)
    setSortDirection('asc')
  }

  const getSortLabel = (column: 'id' | 'asset_tag' | 'name' | 'status') => {
    if (sortColumn !== column) {
      return ''
    }
    return sortDirection === 'asc' ? ' ▲' : ' ▼'
  }

  const isCurrentPageFullySelected =
    paginatedAssets.length > 0 && paginatedAssets.every((asset) => selectedAssetIds.includes(asset.id))

  const toggleRowSelection = (assetId: number) => {
    setSelectedAssetIds((current) =>
      current.includes(assetId) ? current.filter((id) => id !== assetId) : [...current, assetId],
    )
  }

  const toggleSelectCurrentPage = () => {
    const pageIds = paginatedAssets.map((asset) => asset.id)
    setSelectedAssetIds((current) => {
      if (isCurrentPageFullySelected) {
        return current.filter((id) => !pageIds.includes(id))
      }
      const merged = new Set([...current, ...pageIds])
      return [...merged]
    })
  }

  const runBulkStatusUpdate = async () => {
    if (!canWrite || selectedAssetIds.length === 0 || bulkRunning) {
      return
    }

    setBulkRunning(true)
    setBulkMessageStatus('loading')
    setBulkMessage('Applying bulk status update...')

    const results = await Promise.allSettled(
      selectedAssetIds.map((assetId) => onUpdateAsset(assetId, { status: bulkStatus })),
    )

    const succeeded = results.filter((result) => result.status === 'fulfilled').length
    const failed = results.length - succeeded

    if (failed > 0) {
      setBulkMessageStatus('error')
      setBulkMessage(`Bulk update completed with partial failures. Updated: ${succeeded}, failed: ${failed}.`)
    } else {
      setBulkMessageStatus('ok')
      setBulkMessage(`Bulk update succeeded for ${succeeded} assets.`)
    }

    const now = Date.now()
    const successfulIds = selectedAssetIds.filter((_, index) => results[index]?.status === 'fulfilled')
    if (successfulIds.length > 0) {
      setRowUpdateTimes((current) => {
        const next = { ...current }
        for (const id of successfulIds) {
          next[id] = now
        }
        return next
      })
      addActivityItems(successfulIds, 'bulk', bulkStatus)
    }

    setBulkRunning(false)
    setSelectedAssetIds([])
  }

  const getRowUpdatedLabel = (assetId: number) => {
    const timestamp = rowUpdateTimes[assetId]
    if (!timestamp) {
      return ''
    }
    const secondsAgo = Math.max(0, Math.floor((currentTime - timestamp) / 1000))
    if (secondsAgo < 1) {
      return 'Updated just now'
    }
    if (secondsAgo === 1) {
      return 'Updated 1s ago'
    }
    return `Updated ${secondsAgo}s ago`
  }

  const getActivityTimeLabel = (timestamp: number) => {
    const secondsAgo = Math.max(0, Math.floor((currentTime - timestamp) / 1000))
    if (secondsAgo < 1) {
      return 'just now'
    }
    if (secondsAgo === 1) {
      return '1s ago'
    }
    if (secondsAgo < 60) {
      return `${secondsAgo}s ago`
    }
    const minutesAgo = Math.floor(secondsAgo / 60)
    if (minutesAgo === 1) {
      return '1m ago'
    }
    return `${minutesAgo}m ago`
  }

  const addActivityItems = (assetIds: number[], action: 'edit' | 'bulk', status: string) => {
    if (assetIds.length === 0) {
      return
    }
    const now = Date.now()
    const newItems = assetIds.map((assetId) => ({
      id: `${action}-${assetId}-${now}-${Math.random().toString(36).slice(2, 8)}`,
      assetId,
      action,
      status,
      at: now,
    }))
    setActivityItems((current) => [...newItems, ...current].slice(0, 20))
  }

  const getMessageClass = (status: 'idle' | 'loading' | 'ok' | 'error') => {
    if (status === 'ok') {
      return 'inline-message message-success'
    }
    if (status === 'error') {
      return 'inline-message message-error'
    }
    if (status === 'loading') {
      return 'inline-message message-info'
    }
    return 'inline-message message-muted'
  }

  const resetAssetsView = () => {
    setSearchTerm('')
    setStatusFilter('all')
    setSortColumn('id')
    setSortDirection('asc')
    setPageSize(10)
    setCurrentPage(1)
    setSelectedAssetIds([])
    setBulkMessage('')
    setBulkMessageStatus('idle')
    setExportMessageStatus('ok')
    setExportMessage('View reset to defaults.')
  }

  const toCsvCell = (value: unknown) => {
    const text = String(value ?? '')
    return `"${text.replace(/"/g, '""')}"`
  }

  const exportCurrentViewCsv = () => {
    if (sortedAssets.length === 0) {
      setExportMessageStatus('error')
      setExportMessage('No rows to export for the current filters.')
      return
    }

    const header = ['id', 'asset_tag', 'name', 'status']
    const rows = sortedAssets.map((asset) => [
      toCsvCell(asset.id),
      toCsvCell(asset.asset_tag ?? ''),
      toCsvCell(typeof asset.name === 'string' ? asset.name : ''),
      toCsvCell(typeof asset.status === 'string' ? asset.status : ''),
    ])

    const csv = [header.join(','), ...rows.map((row) => row.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `assetra-assets-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    setExportMessageStatus('ok')
    setExportMessage(`Exported ${sortedAssets.length} rows to CSV.`)
  }

  const startEdit = (asset: AssetRecord) => {
    setEditingAssetId(asset.id)
    setEditName(typeof asset.name === 'string' ? asset.name : '')
    setEditStatus(typeof asset.status === 'string' ? asset.status : 'active')
    setEditMessage('')
    setEditMessageStatus('idle')
    setEditErrors({})
  }

  const cancelEdit = () => {
    setEditingAssetId(null)
    setEditName('')
    setEditStatus('active')
    setEditMessage('')
    setEditMessageStatus('idle')
    setEditErrors({})
  }

  const saveEdit = async () => {
    if (!editingAssetId) {
      return
    }
    setEditMessageStatus('loading')
    setEditMessage('Saving changes...')
    setEditErrors({})
    try {
      await onUpdateAsset(editingAssetId, { name: editName, status: editStatus })
      setEditMessageStatus('ok')
      setEditMessage(`Asset #${editingAssetId} updated.`)
      setRowUpdateTimes((current) => ({ ...current, [editingAssetId]: Date.now() }))
      addActivityItems([editingAssetId], 'edit', editStatus)
      setEditingAssetId(null)
    } catch (error) {
      setEditMessageStatus('error')
      if (error instanceof ApiError) {
        setEditErrors(extractFieldErrors(error.data))
      }
      setEditMessage('Failed to update asset.')
    }
  }

  return (
    <>
      <section className="status-card">
        <h2>Create Asset</h2>
        {canWrite ? (
          <form className="login-form" onSubmit={onCreateAsset}>
            <label>
              Asset Tag
              <input
                ref={createAssetTagInputRef}
                value={newAssetTag}
                onChange={(event) => onNewAssetTagChange(event.target.value)}
                required
              />
              {createErrors.asset_tag ? <span className="field-error">{createErrors.asset_tag}</span> : null}
            </label>
            <label>
              Name
              <input value={newAssetName} onChange={(event) => onNewAssetNameChange(event.target.value)} required />
              {createErrors.name ? <span className="field-error">{createErrors.name}</span> : null}
            </label>
            <label>
              Status
              <select value={newAssetStatus} onChange={(event) => onNewAssetStatusChange(event.target.value)}>
                <option value="active">active</option>
                <option value="in_maintenance">in_maintenance</option>
                <option value="retired">retired</option>
                <option value="lost">lost</option>
              </select>
              {createErrors.status ? <span className="field-error">{createErrors.status}</span> : null}
              {createErrors.non_field_errors ? <span className="field-error">{createErrors.non_field_errors}</span> : null}
            </label>
            <div className="row-actions">
              <button type="submit">Create asset</button>
            </div>
          </form>
        ) : (
          <p className="inline-message message-muted">Your role is read-only. Asset creation is disabled.</p>
        )}
        {createMessage ? (
          <p className={getMessageClass(createStatus)} role={createStatus === 'error' ? 'alert' : 'status'} aria-live="polite">
            {createMessage}
          </p>
        ) : null}
      </section>

      <section className="status-card">
        <h2>Assets</h2>
        <p className="status-line">
          Request status: <strong>{assetsStatus.toUpperCase()}</strong>
        </p>
        <p className="hint-text">Search, filter, sort, and bulk-manage assets from this workspace view.</p>
        <div className="summary-grid">
          <p className="summary-item">
            <span>Total</span>
            <strong>{assetSummary.total}</strong>
          </p>
          <p className="summary-item">
            <span>Active</span>
            <strong>{assetSummary.active}</strong>
          </p>
          <p className="summary-item">
            <span>Maintenance</span>
            <strong>{assetSummary.in_maintenance}</strong>
          </p>
          <p className="summary-item">
            <span>Retired</span>
            <strong>{assetSummary.retired}</strong>
          </p>
          <p className="summary-item">
            <span>Lost</span>
            <strong>{assetSummary.lost}</strong>
          </p>
          <p className="summary-item">
            <span>Selected</span>
            <strong>{selectedAssetIds.length}</strong>
          </p>
        </div>
        <div className="filters-row">
          <label>
            Search
            <input
              ref={searchInputRef}
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="ID, tag, or name"
            />
            <span className="hint-inline">
              Shortcut: <span className="kbd">/</span> or <span className="kbd">Ctrl/⌘ + K</span>
            </span>
          </label>
          <label>
            Status Filter
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              {statusOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p>
          Showing {sortedAssets.length} of {assets.length} assets.
        </p>
        {hasActiveViewChanges ? <p className="active-view-indicator">Filters or sort are currently applied.</p> : null}
        <div className="view-actions">
          <button type="button" className="secondary-button" onClick={resetAssetsView} disabled={!hasActiveViewChanges}>
            Reset view
          </button>
          <button type="button" className="secondary-button" onClick={exportCurrentViewCsv} disabled={sortedAssets.length === 0}>
            Export current view (CSV)
          </button>
          {exportMessage ? (
            <p
              className={getMessageClass(exportMessageStatus === 'idle' ? 'ok' : exportMessageStatus)}
              role={exportMessageStatus === 'error' ? 'alert' : 'status'}
              aria-live="polite"
            >
              {exportMessage}
            </p>
          ) : null}
        </div>
        <div className="bulk-row">
          {canWrite ? (
            <>
              <label>
                Bulk Status
                <select value={bulkStatus} onChange={(event) => setBulkStatus(event.target.value)}>
                  <option value="active">active</option>
                  <option value="in_maintenance">in_maintenance</option>
                  <option value="retired">retired</option>
                  <option value="lost">lost</option>
                </select>
              </label>
              <button type="button" onClick={() => void runBulkStatusUpdate()} disabled={selectedAssetIds.length === 0 || bulkRunning}>
                {bulkRunning ? 'Applying...' : `Apply to ${selectedAssetIds.length} selected`}
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setSelectedAssetIds([])}
                disabled={selectedAssetIds.length === 0 || bulkRunning}
              >
                Clear selection
              </button>
            </>
          ) : (
            <p className="inline-message message-muted">Your role is read-only. Bulk updates are disabled.</p>
          )}
          {bulkMessage ? (
            <p className={getMessageClass(bulkMessageStatus)} role={bulkMessageStatus === 'error' ? 'alert' : 'status'} aria-live="polite">
              {bulkMessage}
            </p>
          ) : null}
        </div>
        <div className="pagination-row">
          <label>
            Page Size
            <select value={String(pageSize)} onChange={(event) => setPageSize(Number(event.target.value))}>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
            </select>
          </label>
          <p className="pagination-meta">
            Page {currentPage} of {totalPages}
          </p>
          <p className="pagination-meta">
            Rows {sortedAssets.length === 0 ? 0 : startIndex + 1}-{Math.min(endIndexExclusive, sortedAssets.length)}
          </p>
          <div className="pagination-actions">
            <button type="button" onClick={() => setCurrentPage((page) => Math.max(1, page - 1))} disabled={currentPage <= 1}>
              Previous
            </button>
            <button
              type="button"
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
              disabled={currentPage >= totalPages}
            >
              Next
            </button>
          </div>
        </div>
        {assets.length === 0 ? (
          <p>No assets available yet. Create your first asset above to get started.</p>
        ) : sortedAssets.length === 0 ? (
          <p>No assets match the current filters. Adjust search/filter or reset view.</p>
        ) : (
          <div className="table-wrapper">
            <table className="asset-table">
            <thead>
              <tr>
                {canWrite ? (
                  <th>
                    <input
                      type="checkbox"
                      aria-label="Select all assets on this page"
                      checked={isCurrentPageFullySelected}
                      onChange={toggleSelectCurrentPage}
                    />
                  </th>
                ) : null}
                <th>
                  <button
                    type="button"
                    className="sort-button"
                    aria-label={`Sort by ID${sortColumn === 'id' ? ` (${sortDirection})` : ''}`}
                    onClick={() => toggleSort('id')}
                  >
                    ID{getSortLabel('id')}
                  </button>
                </th>
                <th>
                  <button
                    type="button"
                    className="sort-button"
                    aria-label={`Sort by asset tag${sortColumn === 'asset_tag' ? ` (${sortDirection})` : ''}`}
                    onClick={() => toggleSort('asset_tag')}
                  >
                    Asset Tag{getSortLabel('asset_tag')}
                  </button>
                </th>
                <th>
                  <button
                    type="button"
                    className="sort-button"
                    aria-label={`Sort by name${sortColumn === 'name' ? ` (${sortDirection})` : ''}`}
                    onClick={() => toggleSort('name')}
                  >
                    Name{getSortLabel('name')}
                  </button>
                </th>
                <th>
                  <button
                    type="button"
                    className="sort-button"
                    aria-label={`Sort by status${sortColumn === 'status' ? ` (${sortDirection})` : ''}`}
                    onClick={() => toggleSort('status')}
                  >
                    Status{getSortLabel('status')}
                  </button>
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedAssets.map((asset) => (
                <tr key={asset.id}>
                  {canWrite ? (
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Select asset ${asset.id}`}
                        checked={selectedAssetIds.includes(asset.id)}
                        onChange={() => toggleRowSelection(asset.id)}
                      />
                    </td>
                  ) : null}
                  <td>{asset.id}</td>
                  <td>{asset.asset_tag ?? '-'}</td>
                  <td>
                    {canWrite && editingAssetId === asset.id ? (
                      <input
                        ref={inlineEditNameInputRef}
                        value={editName}
                        onChange={(event) => setEditName(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === 'Escape') {
                            event.preventDefault()
                            cancelEdit()
                          }
                          if (event.key === 'Enter') {
                            event.preventDefault()
                            void saveEdit()
                          }
                        }}
                      />
                    ) : typeof asset.name === 'string' ? (
                      asset.name
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>
                    {canWrite && editingAssetId === asset.id ? (
                      <select
                        value={editStatus}
                        onChange={(event) => setEditStatus(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === 'Escape') {
                            event.preventDefault()
                            cancelEdit()
                          }
                        }}
                      >
                        <option value="active">active</option>
                        <option value="in_maintenance">in_maintenance</option>
                        <option value="retired">retired</option>
                        <option value="lost">lost</option>
                      </select>
                    ) : typeof asset.status === 'string' ? (
                      asset.status
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>
                    <div className="table-actions">
                      <button type="button" className="secondary-button" onClick={() => onViewAsset(asset.id)}>
                        View
                      </button>
                      {canWrite && editingAssetId === asset.id ? (
                        <>
                          <button type="button" className="primary-button" onClick={() => void saveEdit()}>
                            Save
                          </button>
                          <button type="button" className="secondary-button" onClick={cancelEdit}>
                            Cancel
                          </button>
                        </>
                      ) : canWrite ? (
                        <button type="button" className="secondary-button" onClick={() => startEdit(asset)}>
                          Edit
                        </button>
                      ) : null}
                    </div>
                    {getRowUpdatedLabel(asset.id) ? <p className="row-meta">{getRowUpdatedLabel(asset.id)}</p> : null}
                  </td>
                </tr>
              ))}
            </tbody>
            </table>
          </div>
        )}
        {editErrors.name ? <p className="field-error">name: {editErrors.name}</p> : null}
        {editErrors.status ? <p className="field-error">status: {editErrors.status}</p> : null}
        {editErrors.non_field_errors ? <p className="field-error">{editErrors.non_field_errors}</p> : null}
        {editMessage ? (
          <p className={getMessageClass(editMessageStatus)} role={editMessageStatus === 'error' ? 'alert' : 'status'} aria-live="polite">
            {editMessage}
          </p>
        ) : null}
      </section>

      <section className="status-card">
        <h2>Asset Detail</h2>
        <p className="status-line">
          Detail status: <strong>{detailStatus.toUpperCase()}</strong>
        </p>
        {!selectedAsset ? (
          <p>Select an asset from the list to load details.</p>
        ) : (
          <pre className="json-block">{JSON.stringify(selectedAsset, null, 2)}</pre>
        )}
      </section>

      <section className="status-card">
        <h2>Recent Asset Activity</h2>
        {activityItems.length === 0 ? (
          <p>No updates yet. Edit assets or run a bulk update to populate activity.</p>
        ) : (
          <ul className="activity-list">
            {activityItems.map((item) => (
              <li key={item.id} className="activity-item">
                <span>
                  Asset #{item.assetId} • {item.action === 'bulk' ? 'bulk status set' : 'edited'} • {item.status}
                </span>
                <span className="activity-time">{getActivityTimeLabel(item.at)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
