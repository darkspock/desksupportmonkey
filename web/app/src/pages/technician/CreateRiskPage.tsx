import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import toast from 'react-hot-toast';

export default function CreateRiskPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('cyber');

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/risks', { title, description, category });
      return data.data;
    },
    onSuccess: (data) => {
      toast.success(t('page.risks.created'));
      navigate(`/risks/${data.id}`);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Error');
    },
  });

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
          <Link to="/risks" className="hover:text-foreground">{t('page.risks.title')}</Link>
          <span>/</span>
          <span>{t('page.risks.create')}</span>
        </div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.risks.create')}</h2>
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
            placeholder={t('page.risks.title_placeholder')}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('risk.field.description')}</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={4}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            placeholder={t('page.risks.description_placeholder')}
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
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => mutation.mutate()}
            disabled={!title.trim() || !description.trim() || mutation.isPending}
            className="h-9 rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? t('common.saving') : t('page.risks.create')}
          </button>
          <Link
            to="/risks"
            className="inline-flex h-9 items-center rounded-md border border-border bg-card px-4 text-sm font-medium text-foreground hover:bg-muted/50"
          >
            {t('common.cancel')}
          </Link>
        </div>
      </div>
    </div>
  );
}
