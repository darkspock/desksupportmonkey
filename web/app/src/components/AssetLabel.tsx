import { useEffect, useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import JsBarcode from 'jsbarcode';
import { Card } from './ui/Card';
import { useI18n } from '../lib/i18n';

interface AssetLabelProps {
  assetId: string;
  serialNumber: string;
  brand: string;
  model: string;
}

export function AssetLabel({ assetId, serialNumber, brand, model }: AssetLabelProps) {
  const { t } = useI18n();
  const barcodeRef = useRef<SVGSVGElement>(null);
  const assetUrl = `${window.location.origin}/assets/${assetId}`;

  useEffect(() => {
    if (barcodeRef.current) {
      JsBarcode(barcodeRef.current, assetId, {
        format: 'CODE128',
        width: 1.5,
        height: 50,
        displayValue: true,
        fontSize: 12,
        font: 'monospace',
        margin: 4,
      });
    }
  }, [assetId]);

  const handlePrint = () => {
    const printWindow = window.open('', '_blank', 'width=500,height=600');
    if (!printWindow) return;

    const qrSvg = document.getElementById('asset-qr-code')?.outerHTML ?? '';
    const barcodeSvg = barcodeRef.current?.outerHTML ?? '';

    printWindow.document.write(`<!DOCTYPE html>
<html>
<head>
  <title>${brand} ${model} - ${serialNumber}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px;
      gap: 20px;
    }
    .label-header {
      text-align: center;
      font-size: 14px;
      font-weight: 600;
      color: #111;
    }
    .label-sub {
      text-align: center;
      font-size: 11px;
      color: #666;
      margin-top: 2px;
    }
    .section {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }
    .section-title {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #999;
    }
    svg { max-width: 100%; height: auto; }
    @media print {
      body { padding: 12px; }
    }
  </style>
</head>
<body>
  <div class="label-header">${brand} ${model}</div>
  <div class="label-sub">S/N: ${serialNumber}</div>
  <div class="section">
    <div class="section-title">QR</div>
    ${qrSvg}
  </div>
  <div class="section">
    <div class="section-title">ID</div>
    ${barcodeSvg}
  </div>
  <script>window.onload = function() { window.print(); }</script>
</body>
</html>`);
    printWindow.document.close();
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground">{t('page.asset_detail.label_title')}</h3>
        <button
          type="button"
          onClick={handlePrint}
          className="inline-flex items-center justify-center gap-1.5 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18.25 7.034V3.375" />
          </svg>
          {t('page.asset_detail.print_label')}
        </button>
      </div>

      <div className="flex flex-wrap items-start gap-8">
        <div className="flex flex-col items-center gap-1">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{t('page.asset_detail.qr_code')}</p>
          <QRCodeSVG id="asset-qr-code" value={assetUrl} size={120} level="M" />
          <p className="mt-1 max-w-[140px] truncate text-[10px] text-muted-foreground" title={assetUrl}>
            {assetUrl.replace(/^https?:\/\//, '')}
          </p>
        </div>

        <div className="flex flex-col items-center gap-1">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{t('page.asset_detail.barcode')}</p>
          <svg ref={barcodeRef} />
        </div>
      </div>
    </Card>
  );
}
