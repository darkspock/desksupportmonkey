import { useI18n } from '../../lib/i18n';
import { Card } from '../../components/ui/Card';
import { ExternalLink } from 'lucide-react';

const UPGRADE_URL = 'https://dsmcontrol.com';

export default function BillingPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">
          {t('page.billing.community_title')}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t('page.billing.community_subtitle')}
        </p>
      </div>

      <Card>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
              Community Edition
            </span>
          </div>

          <p className="text-sm text-muted-foreground">
            {t('page.billing.community_desc')}
          </p>

          <div className="pt-2 border-t border-border">
            <h3 className="text-sm font-medium text-foreground mb-2">
              {t('page.billing.community_features')}
            </h3>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              <li className="flex items-start gap-1.5">
                <span className="mt-0.5 text-green-600">&#10003;</span>
                {t('page.billing.community_feat_1')}
              </li>
              <li className="flex items-start gap-1.5">
                <span className="mt-0.5 text-green-600">&#10003;</span>
                {t('page.billing.community_feat_2')}
              </li>
              <li className="flex items-start gap-1.5">
                <span className="mt-0.5 text-green-600">&#10003;</span>
                {t('page.billing.community_feat_3')}
              </li>
            </ul>
          </div>

          <div className="pt-2 border-t border-border">
            <p className="text-sm text-muted-foreground mb-3">
              {t('page.billing.community_upgrade_prompt')}
            </p>
            <a
              href={UPGRADE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-md h-9 px-4 text-sm font-medium shadow-xs transition-all bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {t('page.billing.community_upgrade_cta')}
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
}
