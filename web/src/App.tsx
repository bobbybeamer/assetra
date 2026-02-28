import { type FormEvent, useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { extractErrorMessage, getHealthUrl, pingHealth } from './lib/api'
import { AuthCard } from './components/AuthCard'
import { HealthCard } from './components/HealthCard'
import { ProtectedRoute } from './components/ProtectedRoute'
import { TopNav } from './components/TopNav'
import { ToastStack } from './components/ToastStack'
import { useAuthContext } from './context/AuthContext'
import { useAssets } from './hooks/useAssets'
import { useSync } from './hooks/useSync'
import { useToasts } from './hooks/useToasts'
import { AssetsPage } from './pages/AssetsPage'
import { SyncPage } from './pages/SyncPage'

function App() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [message, setMessage] = useState('Not checked yet')
  const {
    username,
    setUsername,
    password,
    setPassword,
    tenantId,
    setTenantId,
    accessToken,
    role,
    canWrite,
    authMessage,
    loginErrors,
    isSigningIn,
    setAuthMessage,
    signIn,
    signOut,
    runWithAuthRetry,
  } = useAuthContext()
  const { toasts, addToast, removeToast } = useToasts()
  const {
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
  } = useAssets({
    tenantId,
    runWithAuthRetry,
    onUnauthorized: (msg) => {
      setAuthMessage(msg)
      addToast(msg)
    },
    onError: addToast,
  })

  const { syncStatus, syncMessage, syncPayload, handleSyncNow, resetSyncState } = useSync({
    tenantId,
    runWithAuthRetry,
    onAfterSync: loadAssetsAuthed,
    onError: addToast,
  })

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      const token = await signIn()
      await loadAssets(token, tenantId)
    } catch (error) {
      const message = extractErrorMessage(error, 'Sign-in failed. Check credentials or API availability.')
      setAuthMessage(message)
      addToast(message)
    }
  }

  const handleSignOut = () => {
    signOut()
    resetAssetsState()
    resetSyncState()
  }

  const checkBackend = async () => {
    setStatus('loading')
    try {
      await pingHealth()
      setStatus('ok')
      setMessage('Backend is reachable')
    } catch {
      setStatus('error')
      setMessage('Backend is not reachable')
    }
  }

  useEffect(() => {
    void checkBackend()
  }, [])

  useEffect(() => {
    if (!accessToken) {
      return
    }
    void loadAssets(accessToken, tenantId)
  }, [accessToken, tenantId])

  return (
    <BrowserRouter>
      <main className="app-shell">
        <header className="app-header">
          <h1>Assetra Operations Console</h1>
          <p className="subtitle">Manage tenant assets, monitor API health, and run sync workflows from one secure workspace.</p>
        </header>

        <HealthCard status={status} message={message} endpoint={getHealthUrl()} onCheck={() => void checkBackend()} />

        <AuthCard
          username={username}
          password={password}
          tenantId={tenantId}
          accessToken={accessToken}
          assetsStatus={assetsStatus}
          authMessage={authMessage}
          loginErrors={loginErrors}
          isSigningIn={isSigningIn}
          role={role}
          canWrite={canWrite}
          onUsernameChange={setUsername}
          onPasswordChange={setPassword}
          onTenantIdChange={setTenantId}
          onSubmit={handleLogin}
          onSignOut={handleSignOut}
          onRefreshAssets={() => void loadAssetsAuthed()}
        />

        {!accessToken ? (
          <section className="status-card">
            <h2>Protected Routes</h2>
            <p>Sign in to access the Assets and Sync pages.</p>
          </section>
        ) : (
          <>
            <TopNav username={username} tenantId={tenantId} role={role} />

            <Routes>
              <Route path="/" element={<Navigate to="/assets" replace />} />
              <Route
                path="/assets"
                element={
                  <ProtectedRoute isAuthenticated={Boolean(accessToken)}>
                    <AssetsPage
                      newAssetTag={newAssetTag}
                      newAssetName={newAssetName}
                      newAssetStatus={newAssetStatus}
                      canWrite={canWrite}
                      createStatus={createStatus}
                      createMessage={createMessage}
                      createErrors={createErrors}
                      assets={assets}
                      assetsStatus={assetsStatus}
                      selectedAsset={selectedAsset}
                      detailStatus={detailStatus}
                      onNewAssetTagChange={setNewAssetTag}
                      onNewAssetNameChange={setNewAssetName}
                      onNewAssetStatusChange={setNewAssetStatus}
                      onCreateAsset={handleCreateAsset}
                      onViewAsset={(assetId) => void loadAssetDetailAuthed(assetId)}
                      onUpdateAsset={updateAssetAuthed}
                    />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/sync"
                element={
                  <ProtectedRoute isAuthenticated={Boolean(accessToken)}>
                    <SyncPage
                      syncStatus={syncStatus}
                      syncMessage={syncMessage}
                      syncPayload={syncPayload}
                      canWrite={canWrite}
                      onRunSync={() => void handleSyncNow()}
                    />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<Navigate to={accessToken ? '/assets' : '/'} replace />} />
            </Routes>
          </>
        )}
      </main>
      <ToastStack toasts={toasts} onDismiss={removeToast} />
    </BrowserRouter>
  )
}

export default App
