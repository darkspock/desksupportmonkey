export interface BrandConfig {
  name: string;
  shortName: string;
  slug: string;
  logoPath: string;
  faviconPath: string;
  loginImagePath: string;
  themePath: string;
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
};

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
  return brand;
}
