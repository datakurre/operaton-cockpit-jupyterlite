declare module 'bpmn-moddle' {
  export interface Point {
    x: number;
    y: number;
    width?: number;
    height?: number;
  }
  
  export interface Activity {
    activityId: string;
    id?: string;
    [key: string]: any;
  }
  
  export class BpmnModdle {
    constructor(options?: any);
    fromXML(xml: string): Promise<any>;
    toXML(element: any, options?: any): Promise<any>;
    create(type: string, attrs?: any): any;
  }
}
