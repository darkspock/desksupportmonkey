import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/cn';

interface NavItem {
  to: string;
  label: string;
  roles?: string[];
}

const nav: NavItem[] = [
  { to: '/my/equipment', label: 'My Equipment' },
  { to: '/my/requests', label: 'My Requests' },
  { to: '/requests', label: 'Request Queue', roles: ['technician', 'admin', 'super_admin'] },
  { to: '/assets', label: 'Asset Inventory', roles: ['technician', 'admin', 'super_admin'] },
  { to: '/dashboard', label: 'Dashboard', roles: ['admin', 'super_admin'] },
  { to: '/users', label: 'Users', roles: ['admin', 'super_admin'] },
  { to: '/departments', label: 'Departments', roles: ['admin', 'super_admin'] },
  { to: '/reports', label: 'Reports', roles: ['admin', 'super_admin'] },
  { to: '/companies', label: 'Companies', roles: ['super_admin'] },
];

export function Sidebar() {
  const { user } = useAuth();
  const role = user?.role;

  const visible = nav.filter((item) => !item.roles || (role && item.roles.includes(role)));

  return (
    <aside className="w-56 shrink-0 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-4 border-b border-gray-700 flex items-center gap-3">
        <img src="/logo.png" alt="DeskSupportMonkey" className="w-9 h-9 rounded" />
        <div>
          <h1 className="text-lg font-bold tracking-tight leading-tight">DSM</h1>
          <p className="text-xs text-gray-400">DeskSupportMonkey</p>
        </div>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {visible.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'block px-3 py-2 rounded text-sm transition-colors',
                isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white',
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
