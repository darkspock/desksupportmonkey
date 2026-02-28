export interface BrandMetric {
  value: string;
  label: string;
  description: string;
}

export interface BrandMessages {
  caption: string;
  tagline: string;
  subtitle: string;
  metrics: BrandMetric[];
  card: { title: string; description: string };
  login: { title: string; subtitle: string };
  register: { title: string; subtitle: string };
  termsUrl: string;
  privacyUrl: string;
}

export interface BrandConfig {
  name: string;
  shortName: string;
  slug: string;
  logoPath: string;
  faviconPath: string;
  loginImagePath: string;
  themePath: string;
  openSourceMode: boolean;
  upgradeUrl: string;
}

// Mutable singleton — updated in-place by loadBrand() so every importer
// sees the same object reference with the live values.
export const brand: BrandConfig = {
  name: 'DeskSupportMonkey',
  shortName: 'DS Monkey',
  slug: 'dsm',
  logoPath: '/brands/dsm/logo.png',
  faviconPath: '/brands/dsm/favicon.png',
  loginImagePath: '/brands/dsm/brand-login.png',
  themePath: '/brands/dsm/theme.css',
  openSourceMode: false,
  upgradeUrl: '',
};

// Brand messages loaded per locale. Stored separately so they can be
// locale-aware without duplicating the brand config.
let _messages: Record<string, BrandMessages> | null = null;

const DEFAULT_MESSAGES: BrandMessages = {
  caption: '',
  tagline: '',
  subtitle: '',
  metrics: [],
  card: { title: '', description: '' },
  login: { title: 'Sign in', subtitle: '' },
  register: { title: 'Register', subtitle: '' },
  termsUrl: '#',
  privacyUrl: '#',
};

export function getBrandMessages(locale: string): BrandMessages {
  if (!_messages) return DEFAULT_MESSAGES;
  return _messages[locale] ?? _messages['en'] ?? DEFAULT_MESSAGES;
}

export async function loadBrand(): Promise<BrandConfig> {
  try {
    const res = await fetch('/api/v1/brand');
    if (res.ok) {
      const json = await res.json();
      Object.assign(brand, json.data);
    }
  } catch {
    // Keep defaults on failure
  }

  // Load brand messages JSON
  try {
    const msgRes = await fetch(`/api/v1/brand/assets/messages.json`);
    if (msgRes.ok) {
      _messages = await msgRes.json();
    }
  } catch {
    // Messages will use defaults
  }

  return brand;
}
