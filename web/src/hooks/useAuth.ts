import { useEffect, useState } from 'react'
import { ApiError, extractFieldErrors, getAuthContext, login, refreshAccessToken } from '../lib/api'

const ACCESS_TOKEN_KEY = 'assetra.accessToken'
const REFRESH_TOKEN_KEY = 'assetra.refreshToken'
const TENANT_ID_KEY = 'assetra.tenantId'
const USERNAME_KEY = 'assetra.username'

export function useAuth() {
  const [username, setUsername] = useState(localStorage.getItem(USERNAME_KEY) ?? 'smoke_admin')
  const [password, setPassword] = useState('')
  const [tenantId, setTenantId] = useState(localStorage.getItem(TENANT_ID_KEY) ?? '1')
  const [accessToken, setAccessToken] = useState(localStorage.getItem(ACCESS_TOKEN_KEY) ?? '')
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem(REFRESH_TOKEN_KEY) ?? '')
  const [authMessage, setAuthMessage] = useState('Not signed in')
  const [loginErrors, setLoginErrors] = useState<Record<string, string>>({})
  const [isSigningIn, setIsSigningIn] = useState(false)
  const [role, setRole] = useState<string>('unknown')
  const [canWrite, setCanWrite] = useState(false)

  const saveTokens = (newAccess: string, newRefresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, newAccess)
    localStorage.setItem(REFRESH_TOKEN_KEY, newRefresh)
    setAccessToken(newAccess)
    setRefreshToken(newRefresh)
  }

  const signIn = async (): Promise<string> => {
    setIsSigningIn(true)
    setAuthMessage('Signing in...')
    setLoginErrors({})
    try {
      const tokens = await login(username, password)
      saveTokens(tokens.access, tokens.refresh)
      const context = await getAuthContext(tokens.access, tenantId)
      setRole(context.role)
      setCanWrite(context.can_write)
      localStorage.setItem(TENANT_ID_KEY, tenantId)
      localStorage.setItem(USERNAME_KEY, username)
      setAuthMessage('Signed in')
      return tokens.access
    } catch (error) {
      if (error instanceof ApiError) {
        setLoginErrors(extractFieldErrors(error.data))
      }
      throw error
    } finally {
      setIsSigningIn(false)
    }
  }

  const signOut = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    setAccessToken('')
    setRefreshToken('')
    setAuthMessage('Signed out')
    setLoginErrors({})
    setRole('unknown')
    setCanWrite(false)
  }

  useEffect(() => {
    if (!accessToken || !tenantId) {
      return
    }

    let isCancelled = false
    const loadContext = async () => {
      try {
        const context = await getAuthContext(accessToken, tenantId)
        if (isCancelled) {
          return
        }
        setRole(context.role)
        setCanWrite(context.can_write)
      } catch {
        if (isCancelled) {
          return
        }
        setRole('unknown')
        setCanWrite(false)
      }
    }

    void loadContext()
    return () => {
      isCancelled = true
    }
  }, [accessToken, tenantId])

  const runWithAuthRetry = async <T,>(operation: (token: string) => Promise<T>): Promise<T> => {
    try {
      return await operation(accessToken)
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401 || !refreshToken) {
        throw error
      }

      const refreshed = await refreshAccessToken(refreshToken)
      const nextRefresh = refreshed.refresh ?? refreshToken
      saveTokens(refreshed.access, nextRefresh)
      return operation(refreshed.access)
    }
  }

  return {
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
  }
}
