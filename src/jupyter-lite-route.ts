import { API, RoutePluginParams } from './types';

export const headers = (api: API) => {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    'X-XSRF-TOKEN': api.CSRFToken,
  };
};

export default [
  {
    id: 'jupyterLiteNavigation',
    pluginPoint: 'cockpit.navigation',
    properties: {
      pagePath: '#/jupyter',
      label: 'Jupyter Lite',
      priority: 1,
      checkActive: function (path: string) {
        return path.indexOf('#/jupyter') > -1;
      },
    },
  },
  {
    id: 'jupyterLiteRoute',
    pluginPoint: 'cockpit.route',
    properties: {
      path: '/jupyter',
      label: '/jupyter',
    },

    render: async (node: Element, { api }: RoutePluginParams) => {
      const iframe = document.createElement('iframe');
      try {
        const userId = (
          await (
            await fetch(`${api.adminApi}/auth/user/default`, {
              method: 'get',
              headers: headers(api),
            })
          ).json()
        )['userId'];
        const profile = await (
          await fetch(`${api.engineApi}/user/${userId}/profile`, {
            method: 'get',
            headers: headers(api),
          })
        ).json();
        const displayName = `${profile['firstName']}`;
        iframe.src = `../scripts/jupyter/lab/index.html?room=default&username=${displayName}`;
      } catch (e) {
        iframe.src = '../scripts/jupyter/lab/index.html';
      }
      iframe.style.setProperty('position', 'absolute');
      iframe.style.setProperty('top', '0px');
      iframe.style.setProperty('right', '0px');
      iframe.style.setProperty('bottom', '0px');
      iframe.style.setProperty('left', '0px');
      iframe.style.setProperty('width', '100%');
      iframe.style.setProperty('height', '100%');
      iframe.setAttribute('frameBorder', '0');
      iframe.setAttribute('width', '100%');
      iframe.setAttribute('height', '100%');
      node.appendChild(iframe);
      window.addEventListener('message', (ev: MessageEvent) => {
        if (iframe.contentWindow?.location.toString().startsWith(ev.origin)) {
          iframe.contentWindow?.postMessage(api, ev.origin);
        }
      });
    },
  },
];
