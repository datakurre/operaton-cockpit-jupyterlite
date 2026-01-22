/**
 * Entry point for the standalone IIFE bundle.
 * This exports bpmn-js-differ as a global that can be loaded
 * in a Web Worker via fetch + eval.
 * 
 * esbuild will bundle this and expose it as: var BpmnJsDiffer = ...
 * Then we assign it to self.BpmnJsDiffer at the end.
 */

import { diff } from 'bpmn-js-differ';

// Export the diff function and any other utilities
const exports = {
  diff
};

// Assign to self for worker access
if (typeof self !== 'undefined') {
  self.bpmnDiff = diff;
  self.BpmnJsDiffer = exports;
}

export default exports;
