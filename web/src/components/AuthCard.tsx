import { type FormEvent } from 'react'

type AuthCardProps = {
  username: string
  password: string
  tenantId: string
  accessToken: string
  assetsStatus: 'idle' | 'loading' | 'ok' | 'error'
  authMessage: string
  loginErrors: Record<string, string>
  isSigningIn: boolean
  role: string
  canWrite: boolean
  onUsernameChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onTenantIdChange: (value: string) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onSignOut: () => void
  onRefreshAssets: () => void
}

export function AuthCard({
  username,
  password,
  tenantId,
  accessToken,
  assetsStatus,
  authMessage,
  loginErrors,
  isSigningIn,
  role,
  canWrite,
  onUsernameChange,
  onPasswordChange,
  onTenantIdChange,
  onSubmit,
  onSignOut,
  onRefreshAssets,
}: AuthCardProps) {
  const authMessageClass = isSigningIn
    ? 'inline-message message-info'
    : loginErrors.detail || loginErrors.non_field_errors
      ? 'inline-message message-error'
      : accessToken
        ? 'inline-message message-success'
        : 'inline-message message-muted'

  return (
    <section className="status-card">
      <h2>Login</h2>
      <p className="hint-text">Use your account and tenant context to access protected operational views.</p>
      <p className="auth-meta">
        Session:{' '}
        <span className={`status-pill ${accessToken ? 'status-ok' : 'status-idle'}`}>{accessToken ? 'Active' : 'Signed out'}</span>
        {accessToken ? (
          <>
            {' '}
            • Role: <strong>{role}</strong> • Access: <strong>{canWrite ? 'Write' : 'Read only'}</strong>
          </>
        ) : null}
      </p>
      <form className="login-form" onSubmit={onSubmit}>
        <label>
          Username
          <input
            value={username}
            onChange={(event) => onUsernameChange(event.target.value)}
            placeholder="Enter username"
            autoComplete="username"
            disabled={isSigningIn}
            required
          />
          {loginErrors.username ? <span className="field-error">{loginErrors.username}</span> : null}
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => onPasswordChange(event.target.value)}
            placeholder="Enter password"
            autoComplete="current-password"
            disabled={isSigningIn}
            required
          />
          {loginErrors.password ? <span className="field-error">{loginErrors.password}</span> : null}
        </label>
        <label>
          Tenant ID
          <input
            value={tenantId}
            onChange={(event) => onTenantIdChange(event.target.value)}
            placeholder="e.g. 1"
            disabled={isSigningIn}
            required
          />
          {loginErrors['non_field_errors'] ? <span className="field-error">{loginErrors['non_field_errors']}</span> : null}
          {loginErrors.detail ? <span className="field-error">{loginErrors.detail}</span> : null}
        </label>
        <div className="row-actions">
          <button type="submit" className="primary-button" disabled={isSigningIn}>
            {isSigningIn ? 'Signing in…' : 'Sign in'}
          </button>
          <button type="button" onClick={onSignOut} disabled={!accessToken || isSigningIn}>
            Sign out
          </button>
          <button
            type="button"
            onClick={onRefreshAssets}
            disabled={!accessToken || assetsStatus === 'loading' || isSigningIn}
          >
            Refresh assets
          </button>
        </div>
      </form>
      <p className={authMessageClass} role={authMessageClass.includes('message-error') ? 'alert' : 'status'} aria-live="polite">
        {authMessage}
      </p>
    </section>
  )
}
