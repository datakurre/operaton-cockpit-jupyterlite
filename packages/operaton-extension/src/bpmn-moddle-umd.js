/**
 * Entry point for the standalone IIFE bundle.
 * This exports BpmnModdle as a global that can be loaded
 * in a Web Worker via fetch + eval.
 * 
 * esbuild will bundle this and expose it as: var BpmnModdle = ...
 * Then we assign it to self.BpmnModdle at the end.
 */

import { BpmnModdle } from 'bpmn-moddle';

// Export for esbuild's IIFE format
export { BpmnModdle as default };

// Also assign to self for worker access
if (typeof self !== 'undefined') {
  self.BpmnModdle = BpmnModdle;
}
