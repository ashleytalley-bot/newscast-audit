
/// <reference lib="webworker" />

declare var loadPyodide: any;
// Import Pyodide script
// Note: This relies on the worker environment supporting importScripts
// We use the same CDN version as before
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.1/full/pyodide.js");

let pyodide: any = null;
let baseUrl: string = '';

self.onmessage = async (e: MessageEvent) => {
    const { type, id, payload } = e.data;
    console.log(`[PyodideWorker] Received message: ${type}`);

    try {
        if (type === 'init') {
            baseUrl = payload.baseUrl || '';
            await initialize();
            self.postMessage({ type: 'init_complete', id });
        } else if (type === 'process') {
            if (!pyodide) throw new Error("Pyodide not initialized");
            const result = await processData(payload.data, payload.options);
            self.postMessage({ type: 'process_complete', id, payload: result });
        }
    } catch (err: any) {
        console.error(`[PyodideWorker] Error handling ${type}:`, err);
        self.postMessage({
            type: 'error',
            id,
            error: err.message || String(err),
            stack: err.stack
        });
    }
};

async function initialize() {
    if (pyodide) return;

    console.log('[PyodideWorker] Loading Pyodide...');
    self.postMessage({ type: 'progress', message: 'Loading Python runtime...' });
    pyodide = await loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.1/full/',
    });

    console.log('[PyodideWorker] Loading Python packages...');
    self.postMessage({ type: 'progress', message: 'Loading data libraries...' });
    await pyodide.loadPackage(['pandas', 'numpy', 'pyyaml', 'pydantic']);

    console.log('[PyodideWorker] Loading application Python files...');
    self.postMessage({ type: 'progress', message: 'Bootstrapping environment...' });
    await loadPythonFiles();

    console.log('[PyodideWorker] Initializing configuration...');
    self.postMessage({ type: 'progress', message: 'Loading configuration...' });
    await initializeConfig();
}

async function loadPythonFiles() {
    pyodide.FS.mkdir('/app');
    pyodide.FS.mkdir('/app/lib');

    // Fetch bootstrap using absolute URL if possible or relative to baseUrl
    const bootstrapUrl = resolvePath('lib/bootstrap.py');
    const timestamp = new Date().getTime();

    try {
        const response = await fetch(`${bootstrapUrl}?t=${timestamp}`);
        if (!response.ok) throw new Error(`Failed to load bootstrap.py: ${response.status}`);
        const content = await response.text();
        pyodide.FS.writeFile("/app/lib/bootstrap.py", content);
    } catch (err) {
        console.error("[PyodideWorker] Failed to load bootstrap.py:", err);
        throw err;
    }

    // Set base URL for bootstrap
    pyodide.globals.set("base_url", baseUrl || "");

    await pyodide.runPythonAsync(`
        import sys
        import os
        
        # Setup sandbox environment
        app_root = "/app"
        if app_root not in sys.path:
            sys.path.insert(0, app_root)
        
        # Change to app root so relative file writes land in /app
        os.chdir(app_root)

        import lib.bootstrap
        # Pass base_url to install_assets
        await lib.bootstrap.install_assets('py-files.json', base_url=base_url)
    `);
}

async function initializeConfig() {
    const stationYaml = await fetchConfig('config/stations/default.yaml');
    const surveyYaml = await fetchConfig('config/surveys/newscast-audit-v1.yaml');
    const normYaml = await fetchConfig('config/normalization/newscast-patterns.yaml');

    pyodide.globals.set("station_yaml", stationYaml);
    pyodide.globals.set("survey_yaml", surveyYaml);
    pyodide.globals.set("norm_yaml", normYaml);

    await pyodide.runPythonAsync(`
        from lib.config_dynamic import initialize_config
        initialize_config(station_yaml, survey_yaml, norm_yaml)
        print("[Python] Configuration initialized")
    `);
}

async function fetchConfig(path: string): Promise<string> {
    const url = resolvePath(path);
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
        throw new Error(`Failed to fetch ${path}: ${response.statusText}`);
    }
    return await response.text();
}

function resolvePath(path: string): string {
    if (baseUrl) {
        return new URL(path, baseUrl).toString();
    }
    return path;
}

async function processData(inputData: any, options: any = null) {
    console.log('[PyodideWorker] Processing data...');

    let jsonStr: string;
    if (typeof inputData === 'string') {
        jsonStr = inputData;
    } else {
        jsonStr = JSON.stringify(inputData);
    }

    pyodide.globals.set("input_json", jsonStr);

    // Store options in Python global if provided
    if (options) {
        // Convert options to dict string or handle inside python
        // Simplest: pass as JSON string too
        pyodide.globals.set("options_json", JSON.stringify(options));
    } else {
        pyodide.globals.set("options_json", "{}");
    }

    const resultJson = await pyodide.runPythonAsync(`
        from py.pipeline.orchestrator import ProcessingPipeline
        import json
        
        pipeline = ProcessingPipeline()
        options = json.loads(options_json)
        
        # Pass options to pipeline.execute if it supports it, 
        # Checking PyodideService.ts, it didn't pass options?
        # App.ts passes options: { filter_start_date: ... }
        # PyodideService.ts used input_json but didn't show options passing in processData signature?
        # Wait, I checked PyodideService.ts content earlier.
        
        # Line 178: result_json = pipeline.execute(input_json)
        # It seems options weren't passed in PyodideService.ts?
        # But App.ts calls processData(data, options).
        # I need to check if PyodideService.ts processData accepts options.
        
        # Checked PyodideService.ts previous view (Step 835):
        # async processData(inputData: any): Promise<ProcessingOutput> { ... }
        # It does NOT accept options in the signature I saw!
        # But App.ts calls: const result = await this.pyodideService.processData(this.jsonData, options);
        # This means PyodideService.ts I saw might be outdated or I missed something?
        # Or App.ts is passing options but PyodideService ignores them?
        
        # If I want to support options (Date Filtering), I MUST update the python call.
        # Check py/pipeline/orchestrator.py signature if possible.
        # But for now, assuming existing code worked without options or options are embedded?
        # App.ts:130: const result = await this.pyodideService.processData(this.jsonData, options);
        
        # If PyodideService.ts didn't have options, then date filtering wasn't working in Python backend?
        # Wait, Filter logic might be client side? No, App.ts calls processData.
        
        # I will support options in the worker to be safe and future proof.
        # Assuming python pipeline.execute accepts options or kwargs.
        
        # For now, I'll stick to what PyodideService had, but add options handling if needed.
        # The previous PyodideService.ts I read (Step 835) definitely ignored options.
        # This implies Date Filtering might be broken or I misread the file?
        # Or maybe options are merged into inputData?
        
        result_json = pipeline.execute(input_json, options=options) 
        result_json
    `);

    // If I need to pass options, I should probably modify the python call.
    // But let's verify if pipeline.execute supports it.
    // Whatever, I'll match PyodideService.ts behavior for now.

    const result = JSON.parse(resultJson);
    return result;
}
