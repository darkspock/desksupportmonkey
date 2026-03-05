import { Link } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useI18n } from '../../lib/i18n';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{children}</p>
    </div>
  );
}

export default function ResellerTermsPage() {
  const { t } = useI18n();

  return (
    <AuthShell title={t('reseller.terms.title')} subtitle="" showBackToLogin={false}>
      <div className="space-y-6">
        <Section title={t('reseller.terms.section_overview')}>{t('reseller.terms.overview')}</Section>
        <Section title={t('reseller.terms.section_commission')}>{t('reseller.terms.commission')}</Section>
        <Section title={t('reseller.terms.section_payout')}>
          <span className="font-semibold text-foreground">{t('reseller.terms.payout')}</span>
        </Section>
        <Section title={t('reseller.terms.section_clawback')}>{t('reseller.terms.clawback')}</Section>
        <Section title={t('reseller.terms.section_demo')}>{t('reseller.terms.demo')}</Section>
        <Section title={t('reseller.terms.section_general')}>{t('reseller.terms.general')}</Section>

        <div className="pt-2 text-center">
          <Link to="/reseller/register" className="text-sm font-medium text-primary hover:underline">
            {t('common.back')}
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}
