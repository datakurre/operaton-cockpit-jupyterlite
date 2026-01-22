"""
Operaton library for Pyodide.

This module provides:
1. BroadcastChannel bridge for communicating with the JupyterLab extension
2. BPMN moddle support for parsing/serializing BPMN 2.0 XML
3. DMN moddle support for parsing/serializing DMN 1.3 XML
4. BPMN-JS-Differ for comparing BPMN diagrams
5. REST API client for interacting with the Operaton engine

The module communicates with the JupyterLab extension via BroadcastChannel to:
- Load JavaScript library bundles (bpmn-moddle, dmn-moddle, bpmn-js-differ)
- Access localStorage (not available directly in Web Workers)

Usage:
    import operaton
    
    # Load environment variables from localStorage (required for REST API)
    await operaton.load_env()
    
    # REST API
    from operaton import Operaton
    definitions = Operaton.get('/process-definition')
    
    # BPMN Moddle
    await operaton.load_bpmn_moddle()
    result = await operaton.parse_bpmn(bpmn_xml)
    
    # DMN Moddle
    await operaton.load_dmn_moddle()
    result = await operaton.parse_dmn(dmn_xml)
    
    # BPMN Differ
    diff = await operaton.compare_bpmn(old_xml, new_xml)
"""

import asyncio
import js
import json
import os

from pyodide.ffi import create_proxy, to_js


# =============================================================================
# BroadcastChannel Bridge
# =============================================================================

# BroadcastChannel name (must match the extension)
CHANNEL_NAME = 'operaton-bridge'


class OperatonBridge:
    """
    Bridge for communicating with the JupyterLab extension.
    Uses BroadcastChannel API to access main window resources.
    """
    
    def __init__(self):
        print(f"[OperatonBridge] Creating BroadcastChannel '{CHANNEL_NAME}'")
        self._channel = js.BroadcastChannel.new(CHANNEL_NAME)
        self._pending_responses = {}
        self._request_id = 0
        # Set up message handler
        self._on_message_proxy = create_proxy(self._on_message)
        self._channel.onmessage = self._on_message_proxy
        print(f"[OperatonBridge] BroadcastChannel created and message handler attached")
    
    def _on_message(self, event):
        """Handle messages from the extension."""
        print(f"[OperatonBridge] Received message event: {event}")
        try:
            data = event.data.to_py()
            print(f"[OperatonBridge] Parsed message data: {data}")
            request_id = data.get('request_id')
            print(f"[OperatonBridge] Request ID from response: {request_id}, pending: {list(self._pending_responses.keys())}")
            
            if request_id and request_id in self._pending_responses:
                future = self._pending_responses[request_id]
                if not future.done():
                    print(f"[OperatonBridge] Resolving future for request {request_id}")
                    future.set_result(data)
                else:
                    print(f"[OperatonBridge] Future already done for request {request_id}")
            else:
                print(f"[OperatonBridge] No pending request for ID {request_id}")
        except Exception as e:
            print(f"[OperatonBridge] Error handling message: {e}")
            import traceback
            traceback.print_exc()
    
    async def request(self, action: str, **kwargs) -> dict:
        """Send a request to the extension and wait for response."""
        self._request_id += 1
        request_id = str(self._request_id)
        
        loop = asyncio.get_event_loop()
        response_future = loop.create_future()
        self._pending_responses[request_id] = response_future
        
        # Send request via BroadcastChannel
        message = {
            'action': action,
            'request_id': request_id,
            **kwargs
        }
        print(f"[OperatonBridge] Sending message: {message}")
        js_message = to_js(message, dict_converter=js.Object.fromEntries)
        print(f"[OperatonBridge] JS message object: {js_message}")
        self._channel.postMessage(js_message)
        print(f"[OperatonBridge] Message posted, waiting for response...")
        
        try:
            response = await asyncio.wait_for(response_future, timeout=30.0)
            print(f"[OperatonBridge] Got response: {response}")
            if response.get('action') == 'error':
                raise RuntimeError(response.get('error', 'Unknown error'))
            return response
        except asyncio.TimeoutError:
            print(f"[OperatonBridge] TIMEOUT waiting for response to {action}")
            del self._pending_responses[request_id]
            raise RuntimeError(f"Timeout waiting for response to {action}")
        finally:
            if request_id in self._pending_responses:
                del self._pending_responses[request_id]
    
    async def get_bpmn_moddle_bundle(self) -> str:
        """Get the bpmn-moddle UMD bundle code."""
        response = await self.request('get_bpmn_moddle_bundle')
        return response.get('bundle', '')
    
    async def get_localstorage(self, key: str) -> str | None:
        """Get a value from localStorage."""
        response = await self.request('get_localstorage', key=key)
        return response.get('value')
    
    async def set_localstorage(self, key: str, value: str) -> bool:
        """Set a value in localStorage."""
        response = await self.request('set_localstorage', key=key, value=value)
        return response.get('success', False)
    
    async def remove_localstorage(self, key: str) -> bool:
        """Remove a value from localStorage."""
        response = await self.request('remove_localstorage', key=key)
        return response.get('success', False)
    
    async def get_localstorage_keys(self) -> list[str]:
        """Get all keys in localStorage."""
        response = await self.request('get_localstorage_keys')
        return response.get('keys', [])
    
    def close(self):
        """Close the BroadcastChannel."""
        self._channel.close()
        self._on_message_proxy.destroy()


# Global bridge instance
_bridge = None


def get_bridge() -> OperatonBridge:
    """Get or create the global bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = OperatonBridge()
    return _bridge


# =============================================================================
# Environment Loading
# =============================================================================

# Track if environment has been loaded
_env_loaded = False


async def _load_env_async():
    """
    Load environment variables from localStorage into os.environ.
    
    The Operaton Cockpit addon stores API configuration in localStorage
    under the 'env' key as a JSON object with keys like:
    - OPERATON_ENGINE_API
    - OPERATON_CSRF_TOKEN
    - OPERATON_ADMIN_API
    - etc.
    
    This function reads that data and updates os.environ.
    """
    global _env_loaded
    
    if _env_loaded:
        return
    
    bridge = get_bridge()
    env_json = await bridge.get_localstorage('env')
    
    if env_json:
        try:
            env_data = json.loads(env_json)
            for key, value in env_data.items():
                os.environ[key] = str(value)
            print(f"[operaton] Loaded {len(env_data)} environment variables from localStorage")
            _env_loaded = True
        except json.JSONDecodeError as e:
            print(f"[operaton] Error parsing env from localStorage: {e}")
    else:
        print("[operaton] No 'env' key found in localStorage")


async def _ensure_env_async():
    """Ensure environment is loaded (async version)."""
    if not _env_loaded:
        await _load_env_async()


async def load_env():
    """
    Explicitly load environment variables from localStorage.
    
    Call this before using Operaton API methods:
        await operaton.load_env()
    """
    await _load_env_async()


# =============================================================================
# REST API Client
# =============================================================================

class Operaton:
    """
    REST API client for Operaton (Camunda 7) engine.
    
    Provides static methods for common REST operations.
    Environment variables must be loaded first via `await operaton.load_env()`.
    """
    
    @staticmethod
    def _check_env():
        """Check that environment has been loaded."""
        if not _env_loaded:
            raise RuntimeError(
                "Environment not loaded. Call 'await operaton.load_env()' first."
            )
    
    @staticmethod
    def _get_base_url():
        """Get the base API URL."""
        Operaton._check_env()
        return os.environ["OPERATON_ENGINE_API"].rstrip("/")
    
    @staticmethod
    def _get_csrf_token():
        """Get the CSRF token."""
        Operaton._check_env()
        return os.environ.get("OPERATON_CSRF_TOKEN", "")

    @staticmethod
    def get(path, raw=False):
        """
        Make a GET request to the Operaton REST API.
        
        Args:
            path: API path (e.g., '/process-definition')
            raw: If True, return raw response text instead of parsing JSON
            
        Returns:
            Parsed JSON response or raw text if raw=True
        """
        url = Operaton._get_base_url() + "/" + path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.open("GET", url, False)
        request.send(None)
        assert request.status in [200], request.responseText
        return request.responseText if raw else json.loads(request.responseText or 'null')

    @staticmethod
    def post(path, data):
        """
        Make a POST request to the Operaton REST API.
        
        Args:
            path: API path
            data: Data to send as JSON
            
        Returns:
            Parsed JSON response
        """
        url = Operaton._get_base_url() + "/" + path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.open("POST", url, False)
        request.setRequestHeader("Content-Type", "application/json")
        request.setRequestHeader("X-XSRF-TOKEN", Operaton._get_csrf_token())
        request.send(json.dumps(data))
        assert request.status in [200, 204], request.responseText
        return json.loads(request.responseText or 'null')
        
    @staticmethod
    def put(path, data):
        """
        Make a PUT request to the Operaton REST API.
        
        Args:
            path: API path
            data: Data to send as JSON
            
        Returns:
            Parsed JSON response
        """
        url = Operaton._get_base_url() + "/" + path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.open("PUT", url, False)
        request.setRequestHeader("Content-Type", "application/json")
        request.setRequestHeader("X-XSRF-TOKEN", Operaton._get_csrf_token())
        request.send(json.dumps(data))
        assert request.status in [200, 204], request.responseText
        return json.loads(request.responseText or 'null')

    @staticmethod
    def delete(path, raw=False):
        """
        Make a DELETE request to the Operaton REST API.
        
        Args:
            path: API path
            raw: If True, return raw response text instead of parsing JSON
            
        Returns:
            Parsed JSON response or raw text if raw=True
        """
        url = Operaton._get_base_url() + "/" + path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.open("DELETE", url, False)
        request.setRequestHeader("X-XSRF-TOKEN", Operaton._get_csrf_token())
        request.send(None)
        assert request.status in [204], request.responseText
        return request.responseText if raw else json.loads(request.responseText or 'null')


# =============================================================================
# BPMN Moddle
# =============================================================================

# Track if bpmn-moddle has been loaded
_bpmn_moddle_loaded = False


async def load_bpmn_moddle():
    """
    Load bpmn-moddle into the Pyodide worker context.
    
    This function requests the bpmn-moddle UMD bundle from the extension
    via BroadcastChannel and evaluates it in the worker context.
    
    The bundle includes camunda-bpmn-moddle extensions for Camunda namespace support.
    
    Returns:
        The BpmnModdle constructor function
    """
    global _bpmn_moddle_loaded
    
    if _bpmn_moddle_loaded:
        return getattr(js, 'BpmnModdle', None)
    
    # Check if already loaded
    if hasattr(js, 'BpmnModdle'):
        _bpmn_moddle_loaded = True
        return js.BpmnModdle
    
    # Get the bundle via BroadcastChannel
    bridge = get_bridge()
    bundle_code = await bridge.get_bpmn_moddle_bundle()
    
    if not bundle_code:
        raise ImportError("Failed to get bpmn-moddle bundle from extension")
    
    # The webpack bundle uses an internal module system that expects 'exports' to exist.
    # We need to wrap the bundle in a function that provides these globals.
    # The bundle ends with: self.BpmnModdle = ...
    wrapper_code = f"""
(function() {{
    {bundle_code}
}})();
"""
    js.eval(wrapper_code)
    
    if hasattr(js, 'BpmnModdle'):
        _bpmn_moddle_loaded = True
        print("bpmn-moddle: Loaded successfully via BroadcastChannel (with Camunda extensions)")
        return js.BpmnModdle
    else:
        raise ImportError("BpmnModdle not found after evaluating bundle")


async def parse_bpmn(xml_string: str):
    """
    Parse a BPMN 2.0 XML string.
    
    The BpmnModdle instance is automatically configured with Camunda extensions.
    
    Args:
        xml_string: The BPMN XML content to parse
        
    Returns:
        A JavaScript object containing:
        - rootElement: The parsed BPMN definitions element
        - elementsById: Dictionary of elements by ID
        - references: Array of references
        - warnings: Array of parsing warnings
    """
    # Use createBpmnModdle which includes Camunda extensions
    if not hasattr(js, 'createBpmnModdle'):
        await load_bpmn_moddle()
    
    moddle = js.createBpmnModdle()
    result = await moddle.fromXML(xml_string)
    return result


async def to_bpmn_xml(element, format_output=True):
    """
    Convert a BPMN element to XML string.
    
    Args:
        element: The BPMN element to serialize
        format_output: Whether to format the output with indentation
        
    Returns:
        The BPMN XML string
    """
    if not hasattr(js, 'createBpmnModdle'):
        await load_bpmn_moddle()
    
    moddle = js.createBpmnModdle()
    options = js.Object.new()
    options.format = format_output
    result = await moddle.toXML(element, options)
    return result.xml


async def create_bpmn_element(element_type: str, **attrs):
    """
    Create a new BPMN element.
    
    Args:
        element_type: The BPMN type (e.g., 'bpmn:Process', 'bpmn:Task')
        **attrs: Attributes for the element
        
    Returns:
        A new BPMN element
    """
    if not hasattr(js, 'createBpmnModdle'):
        await load_bpmn_moddle()
    
    moddle = js.createBpmnModdle()
    js_attrs = js.Object.new()
    for key, value in attrs.items():
        setattr(js_attrs, key, value)
    return moddle.create(element_type, js_attrs)


# =============================================================================
# DMN Moddle
# =============================================================================

# Track if dmn-moddle has been loaded
_dmn_moddle_loaded = False


async def load_dmn_moddle():
    """
    Load dmn-moddle into the Pyodide worker context.
    
    This function requests the dmn-moddle UMD bundle from the extension
    via BroadcastChannel and evaluates it in the worker context.
    
    The bundle includes camunda-dmn-moddle extensions for Camunda namespace support.
    
    Returns:
        The DmnModdle constructor function
    """
    global _dmn_moddle_loaded
    
    if _dmn_moddle_loaded:
        return getattr(js, 'DmnModdle', None)
    
    # Check if already loaded
    if hasattr(js, 'DmnModdle'):
        _dmn_moddle_loaded = True
        return js.DmnModdle
    
    # Get the bundle via BroadcastChannel
    bridge = get_bridge()
    
    # Request DMN moddle bundle
    response = await bridge.request('get_dmn_moddle_bundle')
    bundle_code = response.get('bundle', '')
    
    if not bundle_code:
        raise ImportError("Failed to get dmn-moddle bundle from extension")
    
    # The webpack bundle uses an internal module system that expects 'exports' to exist.
    # We need to wrap the bundle in a function that provides these globals.
    # The bundle ends with: self.DmnModdle = ...
    wrapper_code = f"""
(function() {{
    {bundle_code}
}})();
"""
    js.eval(wrapper_code)
    
    if hasattr(js, 'DmnModdle'):
        _dmn_moddle_loaded = True
        print("dmn-moddle: Loaded successfully via BroadcastChannel")
        return js.DmnModdle
    else:
        raise ImportError("DmnModdle not found after evaluating bundle")


async def parse_dmn(xml_string: str):
    """
    Parse a DMN 1.3 XML string.
    
    The DmnModdle instance is automatically configured with Camunda extensions.
    
    Args:
        xml_string: The DMN XML content to parse
        
    Returns:
        A JavaScript object containing:
        - rootElement: The parsed DMN definitions element
        - elementsById: Dictionary of elements by ID
        - references: Array of references
        - warnings: Array of parsing warnings
    """
    # Use createDmnModdle which includes Camunda extensions
    if not hasattr(js, 'createDmnModdle'):
        await load_dmn_moddle()
    
    moddle = js.createDmnModdle()
    result = await moddle.fromXML(xml_string)
    return result


async def to_dmn_xml(element, format_output=True):
    """
    Convert a DMN element to XML string.
    
    Args:
        element: The DMN element to serialize
        format_output: Whether to format the output with indentation
        
    Returns:
        The DMN XML string
    """
    if not hasattr(js, 'createDmnModdle'):
        await load_dmn_moddle()
    
    moddle = js.createDmnModdle()
    options = js.Object.new()
    options.format = format_output
    result = await moddle.toXML(element, options)
    return result.xml


async def create_dmn_element(element_type: str, **attrs):
    """
    Create a new DMN element.
    
    Args:
        element_type: The DMN type (e.g., 'dmn:Decision', 'dmn:DecisionTable')
        **attrs: Attributes for the element
        
    Returns:
        A new DMN element
    """
    if not hasattr(js, 'createDmnModdle'):
        await load_dmn_moddle()
    
    moddle = js.createDmnModdle()
    js_attrs = js.Object.new()
    for key, value in attrs.items():
        setattr(js_attrs, key, value)
    return moddle.create(element_type, js_attrs)


# =============================================================================
# BPMN-JS-Differ
# =============================================================================

# Track if bpmn-js-differ has been loaded
_bpmn_js_differ_loaded = False


async def load_bpmn_js_differ():
    """
    Load bpmn-js-differ into the Pyodide worker context.
    
    This function requests the bpmn-js-differ UMD bundle from the extension
    via BroadcastChannel and evaluates it in the worker context.
    
    Returns:
        The bpmnDiff function
    """
    global _bpmn_js_differ_loaded
    
    if _bpmn_js_differ_loaded:
        return getattr(js, 'bpmnDiff', None)
    
    # Check if already loaded
    if hasattr(js, 'bpmnDiff'):
        _bpmn_js_differ_loaded = True
        return js.bpmnDiff
    
    # Get the bundle via BroadcastChannel
    bridge = get_bridge()
    response = await bridge.request('get_bpmn_js_differ_bundle')
    bundle_code = response.get('bundle', '')
    
    if not bundle_code:
        raise ImportError("Failed to get bpmn-js-differ bundle from extension")
    
    # The webpack bundle uses an internal module system that expects 'exports' to exist.
    # We need to wrap the bundle in a function that provides these globals.
    # The bundle ends with: self.bpmnDiff = ...
    wrapper_code = f"""
(function() {{
    {bundle_code}
}})();
"""
    js.eval(wrapper_code)
    
    if hasattr(js, 'bpmnDiff'):
        _bpmn_js_differ_loaded = True
        print("bpmn-js-differ: Loaded successfully via BroadcastChannel")
        return js.bpmnDiff
    else:
        raise ImportError("bpmnDiff not found after evaluating bundle")


def diff_bpmn(old_definitions, new_definitions):
    """
    Compute the difference between two BPMN definitions.
    
    Args:
        old_definitions: The old BPMN definitions element (from parse_bpmn().rootElement)
        new_definitions: The new BPMN definitions element (from parse_bpmn().rootElement)
        
    Returns:
        A JavaScript object containing:
        - _added: Map of elements added in the new diagram
        - _removed: Map of elements removed from the old diagram  
        - _changed: Map of elements that were modified
        - _layoutChanged: Map of elements with layout changes only
        
        Helper properties:
        - added: Array of added element IDs
        - removed: Array of removed element IDs
        - changed: Array of changed element IDs
        - layoutChanged: Array of layout-changed element IDs
    """
    if not hasattr(js, 'bpmnDiff'):
        raise RuntimeError("bpmn-js-differ not loaded. Call await load_bpmn_js_differ() first.")
    
    return js.bpmnDiff(old_definitions, new_definitions)


class BpmnDiffResult:
    """
    Python wrapper for bpmn-js-differ results.
    
    Provides convenient access to diff results with Python-friendly data types.
    """
    
    def __init__(self, js_diff_result):
        """
        Initialize from a JavaScript diff result object.
        
        Args:
            js_diff_result: The result from diff_bpmn()
        """
        self._result = js_diff_result
    
    @property
    def added(self) -> dict:
        """Elements that were added in the new diagram."""
        return self._map_to_dict(self._result._added)
    
    @property
    def removed(self) -> dict:
        """Elements that were removed from the old diagram."""
        return self._map_to_dict(self._result._removed)
    
    @property
    def changed(self) -> dict:
        """Elements that were modified (attributes changed)."""
        return self._map_to_dict(self._result._changed)
    
    @property
    def layout_changed(self) -> dict:
        """Elements with layout changes only (position/size)."""
        return self._map_to_dict(self._result._layoutChanged)
    
    @property
    def added_ids(self) -> list:
        """List of IDs of added elements."""
        return list(self.added.keys())
    
    @property
    def removed_ids(self) -> list:
        """List of IDs of removed elements."""
        return list(self.removed.keys())
    
    @property
    def changed_ids(self) -> list:
        """List of IDs of changed elements."""
        return list(self.changed.keys())
    
    @property
    def layout_changed_ids(self) -> list:
        """List of IDs of elements with layout changes."""
        return list(self.layout_changed.keys())
    
    @property
    def has_changes(self) -> bool:
        """Whether there are any changes between the two diagrams."""
        return bool(self.added or self.removed or self.changed or self.layout_changed)
    
    def _map_to_dict(self, js_map) -> dict:
        """Convert a JavaScript Map-like object to a Python dict."""
        if js_map is None:
            return {}
        try:
            # The _added, _removed, etc. are JavaScript objects, not Maps
            result = {}
            keys = list(js.Object.keys(js_map))
            for key in keys:
                result[str(key)] = getattr(js_map, str(key))
            return result
        except Exception:
            return {}
    
    def __repr__(self):
        return (
            f"BpmnDiffResult(added={len(self.added)}, removed={len(self.removed)}, "
            f"changed={len(self.changed)}, layout_changed={len(self.layout_changed)})"
        )


async def compare_bpmn(old_xml: str, new_xml: str) -> BpmnDiffResult:
    """
    Compare two BPMN XML strings and return the differences.
    
    This is a convenience function that handles loading the required libraries
    and parsing the XML before computing the diff.
    
    Args:
        old_xml: The old BPMN XML string
        new_xml: The new BPMN XML string
        
    Returns:
        BpmnDiffResult object with the differences
        
    Example:
        result = await compare_bpmn(old_xml, new_xml)
        if result.has_changes:
            print(f"Added elements: {result.added_ids}")
            print(f"Removed elements: {result.removed_ids}")
            print(f"Changed elements: {result.changed_ids}")
    """
    # Ensure both libraries are loaded
    await load_bpmn_moddle()
    await load_bpmn_js_differ()
    
    # Parse both diagrams
    old_result = await parse_bpmn(old_xml)
    new_result = await parse_bpmn(new_xml)
    
    # Compute the diff
    js_diff = diff_bpmn(old_result.rootElement, new_result.rootElement)
    
    return BpmnDiffResult(js_diff)
