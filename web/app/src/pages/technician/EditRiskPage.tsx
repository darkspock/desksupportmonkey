import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import toast from 'react-hot-toast';
import type { RiskDetail } from '../../types';

export default function EditRiskPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [reviewCadence, setReviewCadence] = useState('');

  const { data: risk, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['risk', id],
    queryFn: async () => {
      const { data } = await api.get(`/risks/${id}`);
      return data.data as RiskDetail;
    },
  });

  useEffect(() => {
    if (risk) {
      setTitle(risk.title);
      setDescription(risk.description);
      setCategory(risk.category);
      setReviewCadence(risk.review_cadence || '');
    }
  }, [risk]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, string> = {};
      if (title !== risk?.title) payload.title = title;
      if (description !== risk?.description) payload.description = description;
      if (category !== risk?.category) payload.category = category;
      if (reviewCadence && reviewCadence !== risk?.review_cadence) payload.review_cadence = reviewCadence;
      await api.put(`/risks/${id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] });
      toast.success(t('page.risks.updated'));
      navigate(`/risks/${id}`);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Error');
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error).message} onRetry={refetch} />;
  if (!risk) return null;

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
          <Link to="/risks" className="hover:text-foreground">{t('page.risks.title')}</Link>
          <span>/</span>
          <Link to={`/risks/${id}`} className="hover:text-foreground">{risk.title.slice(0, 30)}</Link>
          <span>/</span>
          <span>{t('common.edit')}</span>
        </div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.risks.edit')}</h2>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('risk.field.title')}</label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            maxLength={200}
            className="h-9 w-full rounded-md border border-border bg-background px-3 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('risk.field.description')}</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={4}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('risk.field.category')}</label>
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="h-9 w-full rounded-md border border-border bg-background px-3 text-sm"
          >
            <option value="cyber">{t('risk.category.cyber')}</option>
            <option value="operational">{t('risk.category.operational')}</option>
            <option value="compliance">{t('risk.category.compliance')}</option>
            <option value="third_party">{t('risk.category.third_party')}</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('risk.field.review_cadence')}</label>
          <select
            value={reviewCadence}
            onChange={e => setReviewCadence(e.target.value)}
            className="h-9 w-full rounded-md border border-border bg-background px-3 text-sm"
          >
            <option value="">{t('common.none')}</option>
            <option value="monthly">{t('risk.cadence.monthly')}</option>
            <option value="quarterly">{t('risk.cadence.quarterly')}</option>
            <option value="annually">{t('risk.cadence.annually')}</option>
          </select>
        </div>
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => mutation.mutate()}
            disabled={!title.trim() || !description.trim() || mutation.isPending}
            className="h-9 rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? t('common.saving') : t('common.save')}
          </button>
          <Link
            to={`/risks/${id}`}
            className="inline-flex h-9 items-center rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground hover:bg-muted/50"
          >
            {t('common.cancel')}
          </Link>
        </div>
      </div>
    </div>
  );
}
