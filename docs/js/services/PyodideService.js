var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => {
  __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
  return value;
};
class PyodideService {
  constructor() {
    __publicField(this, "pyodide", null);
    __publicField(this, "initPromise", null);
  }
  /**
   * Initialize Pyodide and load required packages.
   */
  async initialize() {
    if (this.initPromise) {
      return this.initPromise;
    }
    this.initPromise = this._doInitialize();
    return this.initPromise;
  }
  async _doInitialize() {
    if (this.pyodide) {
      return;
    }
    console.log("[PyodideService] Loading Pyodide...");
    this.pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/"
    });
    console.log("[PyodideService] Loading Python packages...");
    await this.pyodide.loadPackage(["pandas", "numpy", "pyyaml", "pydantic"]);
    console.log("[PyodideService] Loading application Python files...");
    await this.loadPythonFiles();
    console.log("[PyodideService] Initializing configuration...");
    await this.initializeConfig();
  }
  /**
   * Load Python files from the manifest using the bootstrap module.
   */
  async loadPythonFiles() {
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized");
    }
    console.log("[PyodideService] Bootstrapping Python environment...");
    this.pyodide.FS.mkdir("/app");
    this.pyodide.FS.mkdir("/app/lib");
    try {
      const timestamp = (/* @__PURE__ */ new Date()).getTime();
      const response = await fetch(`lib/bootstrap.py?t=${timestamp}`);
      if (!response.ok)
        throw new Error(`Failed to load bootstrap.py: ${response.status}`);
      const content = await response.text();
      this.pyodide.FS.writeFile("/app/lib/bootstrap.py", content);
    } catch (err) {
      console.error("[PyodideService] Failed to load bootstrap.py:", err);
      throw err;
    }
    try {
      await this.pyodide.runPythonAsync(`
                import sys
                import os
                
                # Setup sandbox environment
                app_root = "/app"
                if app_root not in sys.path:
                    sys.path.insert(0, app_root)
                
                # Change to app root so relative file writes land in /app
                os.chdir(app_root)

                import lib.bootstrap
                await lib.bootstrap.install_assets('py-files.json')
            `);
      console.log("[PyodideService] Python environment finished bootstrapping.");
    } catch (err) {
      console.error("[PyodideService] Bootstrap execution failed:", err);
      throw err;
    }
  }
  /**
   * Initialize Python configuration from YAML files.
   */
  async initializeConfig() {
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized");
    }
    const stationYaml = await this.fetchConfig("config/stations/default.yaml");
    const surveyYaml = await this.fetchConfig("config/surveys/newscast-audit-v1.yaml");
    const normYaml = await this.fetchConfig("config/normalization/newscast-patterns.yaml");
    this.pyodide.globals.set("station_yaml", stationYaml);
    this.pyodide.globals.set("survey_yaml", surveyYaml);
    this.pyodide.globals.set("norm_yaml", normYaml);
    await this.pyodide.runPythonAsync(`
            from lib.config_dynamic import initialize_config
            initialize_config(station_yaml, survey_yaml, norm_yaml)
            print("[Python] Configuration initialized")
        `);
  }
  /**
   * Fetch a configuration file.
   */
  async fetchConfig(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to fetch ${path}: ${response.statusText}`);
    }
    return await response.text();
  }
  /**
   * Process survey data using the Python pipeline.
   */
  async processData(inputData) {
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized. Call initialize() first.");
    }
    console.log("[PyodideService] Processing data...");
    let jsonStr;
    if (typeof inputData === "string") {
      jsonStr = inputData;
    } else {
      jsonStr = JSON.stringify(inputData);
    }
    this.pyodide.globals.set("input_json", jsonStr);
    const resultJson = await this.pyodide.runPythonAsync(`
            from py.pipeline.orchestrator import ProcessingPipeline
            
            pipeline = ProcessingPipeline()
            # input_json is populated via globals.set()
            result_json = pipeline.execute(input_json) 
            result_json
        `);
    return JSON.parse(resultJson);
  }
  /**
   * Check if Pyodide is initialized.
   */
  isInitialized() {
    return this.pyodide !== null;
  }
}
export {
  PyodideService
};
//# sourceMappingURL=PyodideService.js.map
