import { IRenderMime } from '@jupyterlab/rendermime-interfaces';

import { Widget } from '@lumino/widgets';

import DmnViewer from 'dmn-js/lib/NavigatedViewer';

import 'dmn-js/dist/assets/dmn-font/css/dmn.css';
import 'dmn-js/dist/assets/dmn-js-decision-table.css';
import 'dmn-js/dist/assets/dmn-js-drd.css';
import 'dmn-js/dist/assets/dmn-js-shared.css';

/**
 * The default mime type for the extension.
 */
const MIME_TYPE = 'application/dmn+xml';

/**
 * The class name added to the extension.
 */
const CLASS_NAME = 'mimerenderer-dmn';

/**
 * A widget for rendering dmn.
 */
export class OutputWidget extends Widget implements IRenderMime.IRenderer {
  /**
   * Construct a new output widget.
   */
  constructor(options: IRenderMime.IRendererOptions) {
    super();
    this._mimeType = options.mimeType;
    this.addClass(CLASS_NAME);
  }

  /**
   * Decode content if it's base64-encoded
   */
  private decodeContent(content: string): string {
    // Check if content looks like base64 (doesn't start with XML declaration or whitespace + XML)
    const trimmed = content.trim();
    if (trimmed.startsWith('<?xml') || trimmed.startsWith('<')) {
      return content;
    }
    // Try to decode as base64
    try {
      const decoded = atob(content);
      // Verify it looks like XML
      if (decoded.trim().startsWith('<?xml') || decoded.trim().startsWith('<')) {
        return decoded;
      }
    } catch (e) {
      // Not valid base64, return original
    }
    return content;
  }

  /**
   * Render dmn into this widget's node.
   */
  async renderModel(model: IRenderMime.IMimeModel): Promise<void> {
    try {
      let changed = false;
      if (!this._dmn) {
        this._dmn = new DmnViewer({
          additionalModules: [],
        });
        changed = true;
      }
      if (
        model.data[this._mimeType] &&
        model.data[this._mimeType] !== this._xml
      ) {
        this._xml = this.decodeContent(model.data[this._mimeType] as string);
        await this._dmn.importXML(this._xml);
        changed = true;
      }
      if (
        model.data['application/dmn+json'] &&
        model.data['application/dmn+json'] !== this._json
      ) {
        this._json = model.data['application/dmn+json'] as string;
        changed = true;
      }
      if (this._dmn) {
        this._dmn.attachTo(this.node);
        /* @ts-ignore */
        window.foo = this.node;
        /* @ts-ignore */
        window.bar = this._dmn;
      }
      const config = JSON.parse(
        (model.data['application/dmn+json'] as string) || '{}'
      );
      if (this._dmn && changed) {
        if (config.style) {
          for (const name of Object.keys(config.style)) {
            this.node.style.setProperty(name, config.style[name]);
          }
        }
        const view: string =
          this._dmn
            .getViews()
            .find((view: any) => view.id === config.decisionId) ||
          this._dmn
            .getViews()
            .find((view: any) => view.id.startsWith('Decision'));
        await this._dmn.open(view);
        for (const el of this.node.getElementsByClassName('view-drd')) {
          (el as any)?.style?.setProperty('display', 'none');
        }
        for (const rule of config.matchedRules || []) {
          if (rule && rule.ruleId) {
            const xpathResult = document.evaluate(
              `//td[@data-row-id="${rule.ruleId}" or @data-element-id="${rule.ruleId}"]`,
              document,
              null,
              XPathResult.ORDERED_NODE_ITERATOR_TYPE,
              null
            );
            const elements = [];
            let element = xpathResult.iterateNext();
            while (element) {
              elements.push(element);
              element = xpathResult.iterateNext();
            }
            for (const el of elements) {
              (el as any)?.style?.setProperty('background-color', '#add6eb');
            }
          }
        }
      }
    } catch (e) {
      console.warn(e);
    }
    return Promise.resolve();
  }

  private _dmn: any = '';
  private _xml: string = '';
  private _json: string = '';
  private _mimeType: string = '';
}

/**
 * A mime renderer factory for dmn data.
 */
export const rendererFactory: IRenderMime.IRendererFactory = {
  safe: true,
  mimeTypes: [MIME_TYPE],
  createRenderer: (options) => new OutputWidget(options),
};

/**
 * Extension definition.
 */
const extension: IRenderMime.IExtension = {
  id: 'jupyterlab-dmn:plugin',
  rendererFactory,
  rank: 70, // svg is 80, png 90
  dataType: 'string',
  fileTypes: [
    {
      name: 'dmn',
      mimeTypes: [MIME_TYPE],
      extensions: ['.dmn'],
    },
  ],
  documentWidgetFactoryOptions: {
    name: 'A JupyterLab extension for rendering DMN files',
    primaryFileType: 'dmn',
    fileTypes: ['dmn'],
    defaultFor: ['dmn'],
  },
};

export default extension;
