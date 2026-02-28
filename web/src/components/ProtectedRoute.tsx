import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

type ProtectedRouteProps = {
  isAuthenticated: boolean
  children: ReactNode
}

export function ProtectedRoute({ isAuthenticated, children }: ProtectedRouteProps) {
  if (!isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
