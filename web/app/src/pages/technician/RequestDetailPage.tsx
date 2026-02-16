import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import type { ServiceRequest, Comment, Note } from '../../types';

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isRole } = useAuth();
  const queryClient = useQueryClient();
  const isTech = isRole('technician', 'admin', 'super_admin');

  const { data: request, isLoading } = useQuery({
    queryKey: ['request', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}`);
      return data.data as ServiceRequest;
    },
  });

  const { data: comments } = useQuery({
    queryKey: ['request-comments', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/comments`);
      return data.data as Comment[];
    },
  });

  const { data: notes } = useQuery({
    queryKey: ['request-notes', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/notes`);
      return data.data as Note[];
    },
    enabled: isTech,
  });

  const [commentBody, setCommentBody] = useState('');
  const [noteBody, setNoteBody] = useState('');

  const addComment = useMutation({
    mutationFn: () => api.post(`/requests/${id}/comments`, { body: commentBody }),
    onSuccess: () => { setCommentBody(''); queryClient.invalidateQueries({ queryKey: ['request-comments', id] }); },
  });

  const addNote = useMutation({
    mutationFn: () => api.post(`/requests/${id}/notes`, { body: noteBody }),
    onSuccess: () => { setNoteBody(''); queryClient.invalidateQueries({ queryKey: ['request-notes', id] }); },
  });

  const changeStatus = useMutation({
    mutationFn: (status: string) => api.patch(`/requests/${id}/status`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['request', id] }),
  });

  const assign = useMutation({
    mutationFn: () => api.patch(`/requests/${id}/assign`, { assigned_to: user?.id }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['request', id] }),
  });

  if (isLoading) return <Loading />;
  if (!request) return <p className="text-red-600">Request not found</p>;

  const statusActions: Record<string, string[]> = {
    submitted: ['in_review', 'rejected'],
    in_review: ['in_progress', 'rejected'],
    in_progress: ['resolved'],
    rejected: ['submitted'],
  };
  const nextStatuses = statusActions[request.status] || [];

  return (
    <div className="max-w-3xl space-y-6">
      <Card>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{request.title}</h2>
            <div className="flex gap-2 mt-2">
              <StatusBadge status={request.status} />
              <StatusBadge status={request.priority} />
              <StatusBadge status={request.type} />
            </div>
          </div>
        </div>
        <p className="text-sm text-gray-700 whitespace-pre-wrap mb-4">{request.description}</p>
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
          <div>Created: {new Date(request.created_at).toLocaleString()}</div>
          <div>Assigned: {request.assigned_to || 'Unassigned'}</div>
        </div>

        {isTech && (
          <div className="flex gap-2 mt-4 flex-wrap">
            {!request.assigned_to && (
              <button onClick={() => assign.mutate()} className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700">
                Assign to me
              </button>
            )}
            {nextStatuses.map((s) => (
              <button key={s} onClick={() => changeStatus.mutate(s)} className="border px-3 py-1.5 rounded text-sm hover:bg-gray-50">
                {s.replace('_', ' ')}
              </button>
            ))}
          </div>
        )}
      </Card>

      {/* Comments */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Comments</h3>
        <div className="space-y-3 mb-4">
          {comments?.map((c) => (
            <div key={c.id} className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500 mb-1">{c.author_email} &middot; {new Date(c.created_at).toLocaleString()}</p>
              <p className="text-sm text-gray-700">{c.body}</p>
            </div>
          ))}
          {!comments?.length && <p className="text-sm text-gray-400">No comments yet.</p>}
        </div>
        <div className="flex gap-2">
          <input
            value={commentBody}
            onChange={(e) => setCommentBody(e.target.value)}
            placeholder="Add a comment..."
            className="flex-1 border rounded px-3 py-1.5 text-sm"
          />
          <button onClick={() => addComment.mutate()} disabled={!commentBody.trim()} className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm disabled:opacity-50">
            Send
          </button>
        </div>
      </Card>

      {/* Internal Notes (tech only) */}
      {isTech && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Internal Notes</h3>
          <div className="space-y-3 mb-4">
            {notes?.map((n) => (
              <div key={n.id} className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-xs text-gray-500 mb-1">{n.author_id} &middot; {new Date(n.created_at).toLocaleString()}</p>
                <p className="text-sm text-gray-700">{n.body}</p>
              </div>
            ))}
            {!notes?.length && <p className="text-sm text-gray-400">No internal notes.</p>}
          </div>
          <div className="flex gap-2">
            <input
              value={noteBody}
              onChange={(e) => setNoteBody(e.target.value)}
              placeholder="Add an internal note..."
              className="flex-1 border rounded px-3 py-1.5 text-sm"
            />
            <button onClick={() => addNote.mutate()} disabled={!noteBody.trim()} className="bg-yellow-600 text-white px-3 py-1.5 rounded text-sm disabled:opacity-50">
              Add Note
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
