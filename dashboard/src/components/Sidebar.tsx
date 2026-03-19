import { NavLink } from 'react-router-dom'
import clsx from 'clsx'

const links = [
  { to: '/', label: 'Dashboard', icon: '~' },
  { to: '/repos', label: 'Repos', icon: '>' },
  { to: '/contributors', label: 'Contributors', icon: '@' },
  { to: '/trends', label: 'Trends', icon: '^' },
  { to: '/teams', label: 'Teams', icon: '#' },
  { to: '/metrics', label: 'Metrics', icon: '%' },
  { to: '/reports', label: 'Reports', icon: '=' },
  { to: '/webhooks', label: 'Webhooks', icon: '&' },
  { to: '/audit', label: 'Audit Log', icon: '!' },
  { to: '/settings', label: 'Settings', icon: '*' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 text-gray-300 min-h-screen flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold text-white">GAP</h1>
        <p className="text-xs text-gray-500">GitHub Analytics</p>
      </div>
      <nav className="flex-1 py-4">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-4 py-2 text-sm transition-colors',
                isActive ? 'bg-blue-600/20 text-blue-400 border-r-2 border-blue-400' : 'hover:bg-gray-800'
              )
            }
          >
            <span className="font-mono text-xs w-4 text-center">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
