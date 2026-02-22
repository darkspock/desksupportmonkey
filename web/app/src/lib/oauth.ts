import {
  PublicClientApplication,
  type Configuration,
  type AuthenticationResult,
} from '@azure/msal-browser';
import api from './api';

export interface OAuthProviders {
  google: boolean;
  microsoft: boolean;
}

export async function fetchOAuthProviders(): Promise<OAuthProviders> {
  const { data } = await api.get<{ data: OAuthProviders }>('/auth/oauth/providers');
  return data.data;
}

export async function loginWithGoogle(idToken: string): Promise<string> {
  const { data } = await api.post<{ data: { access_token: string } }>('/auth/oauth/google', {
    id_token: idToken,
  });
  return data.data.access_token;
}

let _msalInstance: PublicClientApplication | null = null;

export function getMsalInstance(clientId: string, tenantId = 'common'): PublicClientApplication {
  if (!_msalInstance) {
    const config: Configuration = {
      auth: {
        clientId,
        authority: `https://login.microsoftonline.com/${tenantId}`,
        redirectUri: window.location.origin,
      },
      cache: { cacheLocation: 'sessionStorage' },
    };
    _msalInstance = new PublicClientApplication(config);
  }
  return _msalInstance;
}

export async function loginWithMicrosoftPopup(
  clientId: string,
  tenantId = 'common',
): Promise<AuthenticationResult> {
  const msal = getMsalInstance(clientId, tenantId);
  await msal.initialize();
  return msal.loginPopup({ scopes: ['openid', 'profile', 'email'] });
}

export async function loginWithMicrosoft(idToken: string): Promise<string> {
  const { data } = await api.post<{ data: { access_token: string } }>('/auth/oauth/microsoft', {
    id_token: idToken,
  });
  return data.data.access_token;
}
