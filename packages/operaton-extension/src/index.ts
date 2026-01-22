/**
 * @operaton/operaton-extension
 * 
 * JupyterLab extension that provides a communication bridge between
 * the main window and Pyodide workers using BroadcastChannel.
 * 
 * This allows Python code running in Web Workers to access:
 * - The bpmn-moddle library bundle
 * - localStorage data (not accessible from workers directly)
 * - Other main window resources
 * 
 * Usage from Python:
 *     from bpmn_moddle import load_bpmn_moddle, parse_bpmn
 *     await load_bpmn_moddle()
 *     result = await parse_bpmn(bpmn_xml)
 */

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from '@jupyterlab/application';

import { PageConfig } from '@jupyterlab/coreutils';

import { DEBUG_BUILD } from './debug-config';

/**
 * Debug flag - set to true to enable verbose logging.
 * Can be enabled at build time via: DEBUG_BUILD=true npm run build
 * Or at runtime via: localStorage.setItem('operaton-debug', 'true')
 */
const DEBUG = (): boolean => {
  if (DEBUG_BUILD) {
    return true;
  }
  try {
    return localStorage.getItem('operaton-debug') === 'true';
  } catch {
    return false;
  }
};

const CHANNEL_NAME = 'operaton-bridge';

// Cache for the bpmn-moddle bundle
let bpmnModdleBundleCache: string | null = null;

// Cache for the dmn-moddle bundle
let dmnModdleBundleCache: string | null = null;

// Cache for the bpmn-js-differ bundle
let bpmnJsDifferBundleCache: string | null = null;

/**
 * Get the base URL for extension static assets.
 * Uses PageConfig.getBaseUrl() to handle JupyterLite served from sub-paths.
 */
function getExtensionStaticUrl(filename: string): string {
  const baseUrl = PageConfig.getBaseUrl();
  // Remove trailing slash if present, then add extensions path
  const base = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  return `${base}/extensions/@operaton/operaton-extension/static/${filename}`;
}

/**
 * Fetch the bpmn-moddle UMD bundle and cache it
 */
async function getBpmnModdleBundle(): Promise<string> {
  if (bpmnModdleBundleCache) {
    return bpmnModdleBundleCache;
  }
  
  // The bundle is served as a static asset of this extension
  // Use PageConfig.getBaseUrl() to handle sub-path deployments
  const bundleUrl = getExtensionStaticUrl('bpmn-moddle.umd.js');
  if (DEBUG()) console.log('operaton-bridge: Fetching bpmn-moddle bundle from', bundleUrl);
  
  const response = await fetch(bundleUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch bpmn-moddle bundle: ${response.status} ${response.statusText}`);
  }
  
  bpmnModdleBundleCache = await response.text();
  if (DEBUG()) console.log('operaton-bridge: bpmn-moddle bundle cached', bpmnModdleBundleCache.length, 'bytes');
  return bpmnModdleBundleCache;
}

/**
 * Fetch the dmn-moddle UMD bundle and cache it
 */
async function getDmnModdleBundle(): Promise<string> {
  if (dmnModdleBundleCache) {
    return dmnModdleBundleCache;
  }
  
  // The bundle is served as a static asset of this extension
  // Use PageConfig.getBaseUrl() to handle sub-path deployments
  const bundleUrl = getExtensionStaticUrl('dmn-moddle.umd.js');
  if (DEBUG()) console.log('operaton-bridge: Fetching dmn-moddle bundle from', bundleUrl);
  
  const response = await fetch(bundleUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch dmn-moddle bundle: ${response.status} ${response.statusText}`);
  }
  
  dmnModdleBundleCache = await response.text();
  if (DEBUG()) console.log('operaton-bridge: dmn-moddle bundle cached', dmnModdleBundleCache.length, 'bytes');
  return dmnModdleBundleCache;
}

/**
 * Fetch the bpmn-js-differ UMD bundle and cache it
 */
async function getBpmnJsDifferBundle(): Promise<string> {
  if (bpmnJsDifferBundleCache) {
    return bpmnJsDifferBundleCache;
  }
  
  // The bundle is served as a static asset of this extension
  // Use PageConfig.getBaseUrl() to handle sub-path deployments
  const bundleUrl = getExtensionStaticUrl('bpmn-js-differ.umd.js');
  if (DEBUG()) console.log('operaton-bridge: Fetching bpmn-js-differ bundle from', bundleUrl);
  
  const response = await fetch(bundleUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch bpmn-js-differ bundle: ${response.status} ${response.statusText}`);
  }
  
  bpmnJsDifferBundleCache = await response.text();
  if (DEBUG()) console.log('operaton-bridge: bpmn-js-differ bundle cached', bpmnJsDifferBundleCache.length, 'bytes');
  return bpmnJsDifferBundleCache;
}

/**
 * Handle messages from workers via BroadcastChannel
 */
async function handleMessage(
  data: Record<string, unknown>,
  channel: BroadcastChannel
): Promise<void> {
  const action = data.action as string;
  const requestId = data.request_id as string;
  
  if (DEBUG()) console.log('operaton-bridge: Received:', action, requestId);
  
  let response: Record<string, unknown>;
  
  try {
    switch (action) {
      case 'get_bpmn_moddle_bundle': {
        const bundle = await getBpmnModdleBundle();
        response = { action: 'bpmn_moddle_bundle', request_id: requestId, bundle };
        break;
      }
      
      case 'get_dmn_moddle_bundle': {
        const bundle = await getDmnModdleBundle();
        response = { action: 'dmn_moddle_bundle', request_id: requestId, bundle };
        break;
      }
      
      case 'get_bpmn_js_differ_bundle': {
        const bundle = await getBpmnJsDifferBundle();
        response = { action: 'bpmn_js_differ_bundle', request_id: requestId, bundle };
        break;
      }
      
      case 'get_localstorage': {
        const key = data.key as string;
        const value = localStorage.getItem(key);
        response = { action: 'localstorage_value', request_id: requestId, key, value };
        break;
      }
      
      case 'set_localstorage': {
        const key = data.key as string;
        const value = data.value as string;
        localStorage.setItem(key, value);
        response = { action: 'localstorage_set', request_id: requestId, key, success: true };
        break;
      }
      
      case 'remove_localstorage': {
        const key = data.key as string;
        localStorage.removeItem(key);
        response = { action: 'localstorage_removed', request_id: requestId, key, success: true };
        break;
      }
      
      case 'get_localstorage_keys': {
        const keys: string[] = [];
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key) keys.push(key);
        }
        response = { action: 'localstorage_keys', request_id: requestId, keys };
        break;
      }
      
      case 'ping': {
        response = { action: 'pong', request_id: requestId };
        break;
      }
      
      default:
        console.warn('operaton-bridge: Unknown action:', action);
        response = { action: 'error', request_id: requestId, error: `Unknown action: ${action}` };
    }
  } catch (error) {
    console.error('operaton-bridge: Error handling message:', error);
    response = { 
      action: 'error', 
      request_id: requestId,
      error: error instanceof Error ? error.message : String(error) 
    };
  }
  
  if (DEBUG()) console.log('operaton-bridge: Sending response:', { action: response.action, request_id: response.request_id, hasBundle: 'bundle' in response });
  channel.postMessage(response);
  if (DEBUG()) console.log('operaton-bridge: Response sent');
}

/**
 * Plugin that provides a communication bridge to Pyodide workers via BroadcastChannel
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: '@operaton/operaton-extension:plugin',
  autoStart: true,
  activate: (app: JupyterFrontEnd): void => {
    console.log('@operaton/operaton-extension: Activated');
    if (DEBUG()) console.log('operaton-bridge: Creating BroadcastChannel:', CHANNEL_NAME);
    
    // Create BroadcastChannel for communication with workers
    const channel = new BroadcastChannel(CHANNEL_NAME);
    if (DEBUG()) console.log('operaton-bridge: BroadcastChannel created:', channel);
    
    // Expose channel on window for debugging
    (window as any).__operatonBridgeChannel = channel;
    if (DEBUG()) console.log('operaton-bridge: Channel exposed as window.__operatonBridgeChannel for debugging');
    
    channel.onmessage = (event) => {
      if (DEBUG()) {
        console.log('operaton-bridge: onmessage event received:', event);
        console.log('operaton-bridge: event.data:', event.data);
      }
      const data = event.data as Record<string, unknown>;
      if (data && data.action) {
        if (DEBUG()) console.log('operaton-bridge: Processing action:', data.action, 'request_id:', data.request_id);
        handleMessage(data, channel);
      } else {
        if (DEBUG()) console.log('operaton-bridge: Ignoring message without action:', data);
      }
    };
    
    channel.onmessageerror = (event) => {
      console.error('operaton-bridge: Message error:', event);
    };
    
    if (DEBUG()) console.log('operaton-bridge: Listening for messages');
    
    // Self-test: only run when debugging is enabled
    if (DEBUG()) {
      const testChannel = new BroadcastChannel(CHANNEL_NAME);
      testChannel.onmessage = (event) => {
        console.log('operaton-bridge: Self-test channel received:', event.data);
      };
      // Send a test message
      setTimeout(() => {
        console.log('operaton-bridge: Sending self-test message...');
        testChannel.postMessage({ action: 'ping', request_id: 'self-test' });
      }, 1000);
    }
  },
};

export default plugin;
