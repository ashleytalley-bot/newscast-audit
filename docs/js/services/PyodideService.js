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
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
    });
    console.log("[PyodideService] Loading Python packages...");
    await this.pyodide.loadPackage(["pandas", "numpy"]);
    console.log("[PyodideService] Loading application Python files...");
    await this.loadPythonFiles();
    console.log("[PyodideService] Initializing configuration...");
    await this.initializeConfig();
  }
  /**
   * Load Python files from the manifest.
   */
  async loadPythonFiles() {
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized");
    }
    this.pyodide.FS.mkdir("/lib");
    this.pyodide.FS.mkdir("/py");
    this.pyodide.FS.mkdir("/py/pipeline");
    this.pyodide.FS.mkdir("/py/pipeline/steps");
    let manifest;
    try {
      const response = await fetch("py-files.json", { cache: "no-store" });
      manifest = await response.json();
    } catch (error) {
      console.warn("[PyodideService] Failed to load manifest, using fallback");
      manifest = this.getFallbackManifest();
    }
    for (const filepath of manifest) {
      try {
        const response = await fetch(filepath, { cache: "no-store" });
        const content = await response.text();
        this.pyodide.FS.writeFile(`/${filepath}`, content);
      } catch (error) {
        console.error(`[PyodideService] Failed to load ${filepath}:`, error);
      }
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
    await this.pyodide.runPythonAsync(`
from lib.config_dynamic import initialize_config

station_yaml = """${stationYaml}"""
survey_yaml = """${surveyYaml}"""
norm_yaml = """${normYaml}"""

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
  async processData(jsonData) {
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized. Call initialize() first.");
    }
    console.log("[PyodideService] Processing data...");
    const resultJson = await this.pyodide.runPythonAsync(`
from pipeline.orchestrator import ProcessingPipeline

pipeline = ProcessingPipeline()
result_json = pipeline.execute('''${jsonData.replace(/'/g, "\\'")}''')
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
  /**
   * Fallback file list if manifest fails to load.
   */
  getFallbackManifest() {
    return [
      "lib/__init__.py",
      "lib/config_dynamic.py",
      "lib/cleaners.py",
      "lib/builders.py",
      "lib/utils.py",
      "lib/exceptions.py",
      "lib/quality.py",
      "lib/schemas/__init__.py",
      "lib/schemas/output.py",
      "lib/schemas/errors.py",
      "py/pipeline/__init__.py",
      "py/pipeline/base.py",
      "py/pipeline/orchestrator.py",
      "py/pipeline/steps/__init__.py",
      "py/pipeline/steps/validate.py",
      "py/pipeline/steps/clean.py",
      "py/pipeline/steps/aggregate.py",
      "py/pipeline/steps/charts.py",
      "py/pipeline/steps/export.py"
    ];
  }
}
export {
  PyodideService
};
//# sourceMappingURL=PyodideService.js.map
