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
     * Load Python files from the manifest.
     */
    private async loadPythonFiles(): Promise<void> {
        if (!this.pyodide) {
            throw new Error('Pyodide not initialized');
        }

        // Create directory structure
        this.pyodide.FS.mkdir('/lib');
        this.pyodide.FS.mkdir('/py');
        this.pyodide.FS.mkdir('/py/pipeline');
        this.pyodide.FS.mkdir('/py/pipeline/steps');

        // Fetch manifest
        let manifest: string[];
        try {
            const response = await fetch('py-files.json', { cache: 'no-store' });
            manifest = await response.json();
        } catch (error) {
            console.warn('[PyodideService] Failed to load manifest, using fallback');
            manifest = this.getFallbackManifest();
        }

        // Load each file
        for (const filepath of manifest) {
            try {
                const response = await fetch(filepath, { cache: 'no-store' });
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

    /**
     * Fallback file list if manifest fails to load.
     */
    private getFallbackManifest(): string[] {
        return [
            'lib/__init__.py',
            'lib/config_dynamic.py',
            'lib/cleaners.py',
            'lib/builders.py',
            'lib/utils.py',
            'lib/exceptions.py',
            'lib/quality.py',
            'lib/schemas/__init__.py',
            'lib/schemas/output.py',
            'lib/schemas/errors.py',
            'py/pipeline/__init__.py',
            'py/pipeline/base.py',
            'py/pipeline/orchestrator.py',
            'py/pipeline/steps/__init__.py',
            'py/pipeline/steps/validate.py',
            'py/pipeline/steps/clean.py',
            'py/pipeline/steps/aggregate.py',
            'py/pipeline/steps/charts.py',
            'py/pipeline/steps/export.py',
        ];
    }
}
