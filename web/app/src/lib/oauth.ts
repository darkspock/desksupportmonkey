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

/**
 * Open a popup to Microsoft's OAuth authorize endpoint and poll for the
 * id_token in the hash fragment. No MSAL library needed.
 */
export function loginWithMicrosoftPopup(
  clientId: string,
  tenantId = 'common',
): Promise<string> {
  const redirectUri = `${window.location.origin}/auth-redirect.html`;
  const nonce = crypto.randomUUID();
  const params = new URLSearchParams({
    client_id: clientId,
    response_type: 'id_token',
    redirect_uri: redirectUri,
    scope: 'openid profile email',
    response_mode: 'fragment',
    nonce,
  });

  const url = `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize?${params}`;
  const popup = window.open(url, 'microsoft-login', 'width=500,height=700,left=200,top=100');

  return new Promise((resolve, reject) => {
    if (!popup) {
      reject(new Error('Popup blocked'));
      return;
    }
    const interval = setInterval(() => {
      try {
        if (popup.closed) {
          clearInterval(interval);
          reject(new Error('Popup closed by user'));
          return;
        }
        const popupUrl = popup.location.href;
        if (popupUrl.includes('#')) {
          const hash = new URLSearchParams(popupUrl.split('#')[1]);
          const idToken = hash.get('id_token');
          const error = hash.get('error');
          if (idToken) {
            clearInterval(interval);
            popup.close();
            resolve(idToken);
          } else if (error) {
            clearInterval(interval);
            popup.close();
            reject(new Error(hash.get('error_description') || error));
          }
        }
      } catch {
        // Cross-origin — popup still on Microsoft's domain, keep polling
      }
    }, 300);
  });
}

export async function loginWithMicrosoft(idToken: string): Promise<string> {
  const { data } = await api.post<{ data: { access_token: string } }>('/auth/oauth/microsoft', {
    id_token: idToken,
  });
  return data.data.access_token;
}
