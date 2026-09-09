// Centralized API configuration for QuickDrop
// Points to the Azure App Service backend when hosted on Vercel or external origins.
const API_BASE_URL = (() => {
  if (window.QUICKDROP_API_URL) {
    return window.QUICKDROP_API_URL.replace(/\/+$/, '');
  }
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return '';
  }
  return 'https://quick-drop-fjcteaaaezccctc7.centralindia-01.azurewebsites.net';
})();

window.API_BASE_URL = API_BASE_URL;
