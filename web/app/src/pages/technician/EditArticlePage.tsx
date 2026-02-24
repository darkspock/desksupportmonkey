import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import TipTapEditor from '../../components/editor/TipTapEditor';
import type { ArticleCategory, ArticleDetail } from '../../types';

export default function EditArticlePage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const navigate = useNavigate();
  const toast = useToast();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [excerpt, setExcerpt] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [initialized, setInitialized] = useState(false);

  const { data: article, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['kb-article', id],
    queryFn: async () => {
      const { data } = await api.get(`/kb/articles/${id}`);
      return data.data as ArticleDetail;
    },
  });

  const { data: categories } = useQuery({
    queryKey: ['kb-categories'],
    queryFn: async () => {
      const { data } = await api.get('/kb/categories');
      return data.data as ArticleCategory[];
    },
  });

  useEffect(() => {
    if (article && !initialized) {
      setTitle(article.title);
      setContent(article.content);
      setExcerpt(article.excerpt || '');
      setCategoryId(article.category_id || '');
      setInitialized(true);
    }
  }, [article, initialized]);

  const mutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, string | null> = {};
      if (title.trim() !== article?.title) body.title = title.trim();
      if (content.trim() !== article?.content) body.content = content.trim();
      body.excerpt = excerpt.trim() || null;
      body.category_id = categoryId || null;
      const { data } = await api.put(`/kb/articles/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      toast.success(t('page.kb.article_updated'));
      navigate(`/kb/articles/${id}`);
    },
    onError: () => {
      toast.error(t('common.error'));
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    mutation.mutate();
  };

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />;
  if (!article || !initialized) return <Loading />;

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('page.kb.edit_article')}</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('common.title')} *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            maxLength={300}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.kb.excerpt')}</label>
          <textarea
            value={excerpt}
            onChange={(e) => setExcerpt(e.target.value)}
            maxLength={500}
            rows={2}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.kb.category')}</label>
          <select
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
          >
            <option value="">{t('common.none')}</option>
            {categories?.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.kb.content')} *</label>
          <TipTapEditor content={content} onChange={setContent} />
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={mutation.isPending || !title.trim() || !content.trim()}
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {mutation.isPending ? t('common.saving') : t('common.save')}
          </button>
          <button type="button" onClick={() => navigate(`/kb/articles/${id}`)} className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
            {t('common.cancel')}
          </button>
        </div>
      </form>
    </div>
  );
}
