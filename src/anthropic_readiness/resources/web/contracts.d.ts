/** JSON values shared by JSDoc modules; runtime documents are schema checked by the server. */
export type JsonValue = null | boolean | number | string | JsonValue[] | JsonObject;
export interface JsonObject {
  [key: string]: JsonValue;
}
