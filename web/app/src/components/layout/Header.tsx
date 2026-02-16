import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../hooks/useNotifications';

export function Header() {
  const { user, logout } = useAuth();
  const { unread } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <header className="h-14 border-b border-gray-200 bg-white flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-4">
        <Link to="/my/notifications" className="relative text-gray-500 hover:text-gray-700">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          {unread > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </Link>
        <div className="relative" ref={ref}>
          <button onClick={() => setOpen(!open)} className="text-sm text-gray-600 hover:text-gray-900">
            {user?.email}
          </button>
          {open && (
            <div className="absolute right-0 mt-2 w-44 bg-white border rounded-lg shadow-lg py-1 z-50">
              <div className="px-3 py-2 text-xs text-gray-400 border-b">{user?.role.replace('_', ' ')}</div>
              <button onClick={logout} className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50">
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
