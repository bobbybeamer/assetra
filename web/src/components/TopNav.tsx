import { NavLink, useLocation } from 'react-router-dom'

type TopNavProps = {
  username: string
  tenantId: string
  role: string
}

export function TopNav({ username, tenantId, role }: TopNavProps) {
  const location = useLocation()
  const currentPage = location.pathname.startsWith('/sync') ? 'Sync Operations' : 'Asset Workspace'

  return (
    <section className="status-card nav-shell">
      <div className="nav-header">
        <div>
          <h2>{currentPage}</h2>
          <p className="hint-text">Use the tabs to switch between inventory management and synchronization.</p>
        </div>
        <p className="nav-context">
          User: <strong>{username || '-'}</strong> • Tenant: <strong>{tenantId || '-'}</strong> • Role:{' '}
          <strong>{role || '-'}</strong>
        </p>
      </div>

      <nav className="top-nav">
        <NavLink to="/assets" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          Assets
        </NavLink>
        <NavLink to="/sync" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          Sync
        </NavLink>
      </nav>
    </section>
  )
}
