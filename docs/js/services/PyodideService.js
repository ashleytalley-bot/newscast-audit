var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => {
  __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
  return value;
};
class PyodideService {
  constructor() {
    __publicField(this, "worker", null);
    __publicField(this, "initPromise", null);
    __publicField(this, "messageIdCounter", 0);
    __publicField(this, "pendingMessages", /* @__PURE__ */ new Map());
    __publicField(this, "onProgressCallback", null);
  }
  /**
   * Register a callback for progress updates.
   */
  setOnProgress(callback) {
    this.onProgressCallback = callback;
  }
  /**
   * Initialize Pyodide Web Worker.
   */
  async initialize() {
    if (this.initPromise) {
      return this.initPromise;
    }
    this.initPromise = this._doInitialize();
    return this.initPromise;
  }
  _doInitialize() {
    return new Promise((resolve, reject) => {
      if (this.worker) {
        resolve();
        return;
      }
      console.log("[PyodideService] Initializing Worker...");
      this.worker = new Worker("js/workers/PyodideWorker.js");
      this.worker.onmessage = (e) => {
        const { type, id: id2, payload, error, message } = e.data;
        const pending = this.pendingMessages.get(id2);
        if (type === "progress") {
          if (this.onProgressCallback) {
            this.onProgressCallback(message);
          }
          return;
        }
        if (pending) {
          if (type === "error") {
            pending.reject(new Error(error));
          } else if (type === "init_complete") {
            pending.resolve(null);
          } else if (type === "process_complete") {
            pending.resolve(payload);
          }
          this.pendingMessages.delete(id2);
        } else if (type === "error") {
          console.error("[PyodideService] Unhandled Worker Error:", error);
        }
      };
      this.worker.onerror = (err) => {
        console.error("Worker Script Error:", err);
        const initPending = this.pendingMessages.get(0) || this.pendingMessages.get(1);
        if (initPending && this.pendingMessages.size === 1) {
          initPending.reject(err);
        }
      };
      const id = this.nextId();
      this.pendingMessages.set(id, { resolve: () => resolve(), reject });
      const baseUrl = window.location.href.substring(0, window.location.href.lastIndexOf("/") + 1);
      this.worker.postMessage({
        type: "init",
        id,
        payload: { baseUrl }
      });
    });
  }
  /**
   * Process survey data using the Python pipeline in the worker.
   */
  async processData(inputData, options = null) {
    if (!this.worker) {
      throw new Error("Pyodide not initialized. Call initialize() first.");
    }
    return new Promise((resolve, reject) => {
      const id = this.nextId();
      this.pendingMessages.set(id, { resolve, reject });
      this.worker.postMessage({
        type: "process",
        id,
        payload: { data: inputData, options }
      });
    });
  }
  /**
   * Check if Pyodide is initialized.
   */
  isInitialized() {
    return this.worker !== null;
  }
  nextId() {
    return ++this.messageIdCounter;
  }
}
export {
  PyodideService
};
//# sourceMappingURL=PyodideService.js.map
