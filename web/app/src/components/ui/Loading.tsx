export function Loading() {
  return (
    <div className="flex items-center justify-center p-12" role="status" aria-live="polite" aria-label="Loading">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" aria-hidden="true" />
    </div>
  );
}

export function PageLoading() {
  return (
    <div className="flex items-center justify-center min-h-screen" role="status" aria-live="polite" aria-label="Loading page">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" aria-hidden="true" />
    </div>
  );
}
