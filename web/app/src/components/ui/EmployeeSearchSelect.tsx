import { useEffect, useMemo, useState } from 'react';
import { cn } from '../../lib/cn';
import type { AssignableUser } from '../../types';

interface EmployeeSearchSelectProps {
  users: AssignableUser[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  allLabel: string;
  noResultsLabel: string;
  className?: string;
}

export function EmployeeSearchSelect({
  users,
  value,
  onChange,
  placeholder,
  allLabel,
  noResultsLabel,
  className,
}: EmployeeSearchSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');

  const selectedUser = useMemo(
    () => users.find((user) => user.id === value),
    [users, value],
  );

  useEffect(() => {
    setQuery(selectedUser?.email ?? '');
  }, [selectedUser?.email]);

  const filteredUsers = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return users;
    return users.filter((user) => {
      const haystack = `${user.email} ${user.name ?? ''}`.toLowerCase();
      return haystack.includes(normalized);
    });
  }, [query, users]);

  return (
    <div className={cn('relative min-w-48', className)}>
      <input
        value={query}
        onFocus={() => setIsOpen(true)}
        onBlur={() => {
          setTimeout(() => setIsOpen(false), 120);
          if (!query.trim()) onChange('');
          if (!value && query.trim()) setQuery('');
        }}
        onChange={(e) => {
          const next = e.target.value;
          setQuery(next);
          setIsOpen(true);
          if (!next.trim()) onChange('');
        }}
        placeholder={placeholder}
        className="w-full rounded-lg border border-input bg-card px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
      />

      {isOpen && (
        <div className="absolute z-30 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-border bg-card py-1 shadow-lg">
          <button
            type="button"
            onMouseDown={(e) => {
              e.preventDefault();
              onChange('');
              setQuery('');
              setIsOpen(false);
            }}
            className="block w-full px-3 py-2 text-left text-sm text-foreground hover:bg-accent"
          >
            {allLabel}
          </button>

          {filteredUsers.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">{noResultsLabel}</p>
          ) : (
            filteredUsers.map((user) => (
              <button
                key={user.id}
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault();
                  onChange(user.id);
                  setQuery(user.email);
                  setIsOpen(false);
                }}
                className={cn(
                  'block w-full px-3 py-2 text-left text-sm hover:bg-accent',
                  value === user.id ? 'bg-primary/10 text-primary' : 'text-foreground',
                )}
              >
                {user.email}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
