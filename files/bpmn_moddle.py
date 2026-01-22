"""
BPMN Moddle support for Pyodide.

This module provides a way to load and use bpmn-moddle in Pyodide.
bpmn-moddle is a JavaScript library for parsing BPMN 2.0 XML.

The module communicates with the JupyterLab extension via BroadcastChannel to:
- Load the bpmn-moddle library bundle
- Access localStorage (not available directly in Web Workers)

Usage:
    from bpmn_moddle import load_bpmn_moddle, parse_bpmn
    
    # Initialize bpmn-moddle (loads the library)
    await load_bpmn_moddle()
    
    # Parse BPMN XML
    result = await parse_bpmn(bpmn_xml)
    print(result.rootElement.id)
"""

import asyncio
import js
from pyodide.ffi import create_proxy, to_js

# Track if bpmn-moddle has been loaded
_bpmn_moddle_loaded = False

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


async def load_bpmn_moddle():
    """
    Load bpmn-moddle into the Pyodide worker context.
    
    This function requests the bpmn-moddle UMD bundle from the extension
    via BroadcastChannel and evaluates it in the worker context.
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
        print("bpmn-moddle: Loaded successfully via BroadcastChannel")
        return js.BpmnModdle
    else:
        raise ImportError("BpmnModdle not found after evaluating bundle")


async def parse_bpmn(xml_string: str):
    """
    Parse a BPMN 2.0 XML string.
    
    Args:
        xml_string: The BPMN XML content to parse
        
    Returns:
        A JavaScript object containing:
        - rootElement: The parsed BPMN definitions element
        - elementsById: Dictionary of elements by ID
        - references: Array of references
        - warnings: Array of parsing warnings
    """
    BpmnModdle = await load_bpmn_moddle()
    moddle = BpmnModdle.new()
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
    BpmnModdle = await load_bpmn_moddle()
    moddle = BpmnModdle.new()
    options = js.Object.new()
    options.format = format_output
    result = await moddle.toXML(element, options)
    return result.xml


async def create_element(element_type: str, **attrs):
    """
    Create a new BPMN element.
    
    Args:
        element_type: The BPMN type (e.g., 'bpmn:Process', 'bpmn:Task')
        **attrs: Attributes for the element
        
    Returns:
        A new BPMN element
    """
    BpmnModdle = await load_bpmn_moddle()
    moddle = BpmnModdle.new()
    js_attrs = js.Object.new()
    for key, value in attrs.items():
        setattr(js_attrs, key, value)
    return moddle.create(element_type, js_attrs)
