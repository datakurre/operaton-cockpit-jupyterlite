# bpmn-moddle JupyterLab Extension

JupyterLab extension that provides bpmn-moddle JavaScript library to Python via globalThis.

## Usage

In a Python notebook cell:

```python
from js import BpmnModdle

moddle = BpmnModdle.new()
result = await moddle.fromXML(bpmn_xml)
print(result.rootElement.id)
```
