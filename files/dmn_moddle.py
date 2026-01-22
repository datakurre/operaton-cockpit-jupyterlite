"""
DMN Moddle support for Pyodide.

This module provides a way to load and use dmn-moddle in Pyodide.
dmn-moddle is a JavaScript library for parsing DMN 1.3 XML.

The module communicates with the JupyterLab extension via BroadcastChannel to:
- Load the dmn-moddle library bundle
- Access localStorage (not available directly in Web Workers)

Usage:
    from dmn_moddle import load_dmn_moddle, parse_dmn
    
    # Initialize dmn-moddle (loads the library)
    await load_dmn_moddle()
    
    # Parse DMN XML
    result = await parse_dmn(dmn_xml)
    print(result.rootElement.id)
"""

import asyncio
import js
from pyodide.ffi import create_proxy, to_js

# Track if dmn-moddle has been loaded
_dmn_moddle_loaded = False

# Import the bridge from bpmn_moddle (shared infrastructure)
from bpmn_moddle import get_bridge


async def load_dmn_moddle():
    """
    Load dmn-moddle into the Pyodide worker context.
    
    This function requests the dmn-moddle UMD bundle from the extension
    via BroadcastChannel and evaluates it in the worker context.
    
    The bundle includes camunda-dmn-moddle extensions for Camunda namespace support.
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


async def create_element(element_type: str, **attrs):
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
