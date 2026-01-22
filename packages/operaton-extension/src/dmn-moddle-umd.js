/**
 * Entry point for the DMN moddle standalone IIFE bundle.
 * This exports DmnModdle as a global that can be loaded
 * in a Web Worker via fetch + eval.
 * 
 * Includes camunda-dmn-moddle extensions for Camunda namespace support.
 * 
 * esbuild will bundle this and expose it as: var DmnModdle = ...
 * Then we assign it to self.DmnModdle at the end.
 */

import { DmnModdle } from 'dmn-moddle';
import camundaModdle from 'camunda-dmn-moddle/resources/camunda.json';

/**
 * Create a DmnModdle instance with Camunda extensions pre-configured.
 * @param {object} additionalPackages - Additional moddle packages to include
 * @returns {DmnModdle} Configured DmnModdle instance
 */
function createDmnModdle(additionalPackages = {}) {
  return new DmnModdle({
    camunda: camundaModdle,
    ...additionalPackages
  });
}

// Export the factory function and the raw class
const exports = {
  DmnModdle,
  camundaModdle,
  createDmnModdle
};

// Assign to self for worker access
if (typeof self !== 'undefined') {
  self.DmnModdle = DmnModdle;
  self.camundaDmnModdle = camundaModdle;
  self.createDmnModdle = createDmnModdle;
}

export default exports;
