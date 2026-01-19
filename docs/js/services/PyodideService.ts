/**
 * Pyodide Service - Manages Python runtime in the browser.
 *
 * Handles initialization, file loading, and Python function calls.
 */

import type { ProcessingOutput } from '../types';

/**
 * Pyodide instance type (from external library).
 */
declare const loadPyodide: any;

interface PyodideInstance {
    loadPackage(packages: string[]): Promise<void>;
    FS: {
        mkdir(path: string): void;
        writeFile(path: string, content: string): void;
    };
    runPythonAsync(code: string): Promise<any>;
}

export class PyodideService {
    private pyodide: PyodideInstance | null = null;
    private initPromise: Promise<void> | null = null;

    /**
     * Initialize Pyodide and load required packages.
     */
    async initialize(): Promise<void> {
        // Return existing initialization if in progress
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = this._doInitialize();
        return this.initPromise;
    }

    private async _doInitialize(): Promise<void> {
        if (this.pyodide) {
            return; // Already initialized
        }

        console.log('[PyodideService] Loading Pyodide...');
        this.pyodide = await loadPyodide({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.1/full/',
        });

        console.log('[PyodideService] Loading Python packages...');
        await this.pyodide.loadPackage(['pandas', 'numpy']);

        console.log('[PyodideService] Loading application Python files...');
        await this.loadPythonFiles();

        console.log('[PyodideService] Initializing configuration...');
        await this.initializeConfig();
    }

    /**
     * Load Python files from the manifest using the bootstrap module.
     */
    private async loadPythonFiles(): Promise<void> {
        if (!this.pyodide) {
            throw new Error('Pyodide not initialized');
        }

        console.log('[PyodideService] Bootstrapping Python environment...');

        // 1. Ensure lib directory exists
        this.pyodide.FS.mkdir('/lib');

        // 2. Fetch and write bootstrap.py manually (it's the seed)
        try {
            const timestamp = new Date().getTime();
            const response = await fetch(`lib/bootstrap.py?t=${timestamp}`);
            if (!response.ok) throw new Error(`Failed to load bootstrap.py: ${response.status}`);
            const content = await response.text();
            this.pyodide.FS.writeFile("/lib/bootstrap.py", content);
        } catch (err) {
            console.error("[PyodideService] Failed to load bootstrap.py:", err);
            throw err;
        }

        // 3. Run bootstrap to install everything else from manifest
        try {
            await this.pyodide.runPythonAsync(`
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
    private async initializeConfig(): Promise<void> {
        if (!this.pyodide) {
            throw new Error('Pyodide not initialized');
        }

        // Load YAML configuration files
        const stationYaml = await this.fetchConfig('config/stations/default.yaml');
        const surveyYaml = await this.fetchConfig('config/surveys/newscast-audit-v1.yaml');
        const normYaml = await this.fetchConfig('config/normalization/newscast-patterns.yaml');

        // Initialize config in Python
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
    private async fetchConfig(path: string): Promise<string> {
        const response = await fetch(path, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`Failed to fetch ${path}: ${response.statusText}`);
        }
        return await response.text();
    }

    /**
     * Process survey data using the Python pipeline.
     */
    async processData(jsonData: string): Promise<ProcessingOutput> {
        if (!this.pyodide) {
            throw new Error('Pyodide not initialized. Call initialize() first.');
        }

        console.log('[PyodideService] Processing data...');

        const resultJson = await this.pyodide.runPythonAsync(`
from pipeline.orchestrator import ProcessingPipeline

pipeline = ProcessingPipeline()
result_json = pipeline.execute('''${jsonData.replace(/'/g, "\\'")}''')
result_json
        `);

        return JSON.parse(resultJson) as ProcessingOutput;
    }

    /**
     * Check if Pyodide is initialized.
     */
    isInitialized(): boolean {
        return this.pyodide !== null;
    }


}
