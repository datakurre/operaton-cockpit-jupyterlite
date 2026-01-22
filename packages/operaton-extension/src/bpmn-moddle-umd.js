/**
 * Entry point for the standalone IIFE bundle.
 * This exports BpmnModdle as a global that can be loaded
 * in a Web Worker via fetch + eval.
 * 
 * Includes camunda-bpmn-moddle extensions for Camunda namespace support.
 * 
 * esbuild will bundle this and expose it as: var BpmnModdle = ...
 * Then we assign it to self.BpmnModdle at the end.
 */

import { BpmnModdle } from 'bpmn-moddle';
import camundaModdle from 'camunda-bpmn-moddle/resources/camunda.json';

/**
 * Create a BpmnModdle instance with Camunda extensions pre-configured.
 * @param {object} additionalPackages - Additional moddle packages to include
 * @returns {BpmnModdle} Configured BpmnModdle instance
 */
function createBpmnModdle(additionalPackages = {}) {
  return new BpmnModdle({
    camunda: camundaModdle,
    ...additionalPackages
  });
}

// Export the factory function and the raw class
const exports = {
  BpmnModdle,
  camundaModdle,
  createBpmnModdle
};

// Assign to self for worker access
if (typeof self !== 'undefined') {
  self.BpmnModdle = BpmnModdle;
  self.camundaModdle = camundaModdle;
  self.createBpmnModdle = createBpmnModdle;
}

export default exports;
