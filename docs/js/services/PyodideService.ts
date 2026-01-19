
/**
 * Pyodide Service - Manages Python runtime in a Web Worker.
 *
 * Handles initialization, file loading, and Python function calls via message passing.
 */

import type { ProcessingOutput } from '../types';

export class PyodideService {
    private worker: Worker | null = null;
    private initPromise: Promise<void> | null = null;
    private messageIdCounter = 0;
    private pendingMessages = new Map<number, { resolve: (val: any) => void, reject: (err: any) => void }>();

    /**
     * Initialize Pyodide Web Worker.
     */
    async initialize(): Promise<void> {
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = this._doInitialize();
        return this.initPromise;
    }

    private _doInitialize(): Promise<void> {
        return new Promise((resolve, reject) => {
            if (this.worker) {
                resolve();
                return;
            }

            console.log('[PyodideService] Initializing Worker...');
            // Path is relative to the directory containing the HTML file
            this.worker = new Worker('js/workers/PyodideWorker.js');

            this.worker.onmessage = (e) => {
                const { type, id, payload, error } = e.data;
                const pending = this.pendingMessages.get(id);

                if (pending) {
                    if (type === 'error') {
                        pending.reject(new Error(error));
                    } else if (type === 'init_complete') {
                        pending.resolve(null);
                    } else if (type === 'process_complete') {
                        pending.resolve(payload);
                    }
                    this.pendingMessages.delete(id);
                } else if (type === 'error') {
                    console.error('[PyodideService] Unhandled Worker Error:', error);
                }
            };

            this.worker.onerror = (err) => {
                console.error('Worker Script Error:', err);
                const initPending = this.pendingMessages.get(0) || this.pendingMessages.get(1); // Heuristic
                if (initPending && this.pendingMessages.size === 1) {
                    initPending.reject(err);
                }
            };

            const id = this.nextId();
            this.pendingMessages.set(id, { resolve: () => resolve(), reject });

            // Pass baseUrl so worker knows where to fetch files from
            // window.location.href includes index.html, we want the directory
            const baseUrl = window.location.href.substring(0, window.location.href.lastIndexOf('/') + 1);

            this.worker.postMessage({
                type: 'init',
                id,
                payload: { baseUrl }
            });
        });
    }

    /**
     * Process survey data using the Python pipeline in the worker.
     */
    async processData(inputData: any, options: any = null): Promise<ProcessingOutput> {
        if (!this.worker) {
            throw new Error('Pyodide not initialized. Call initialize() first.');
        }

        return new Promise((resolve, reject) => {
            const id = this.nextId();
            this.pendingMessages.set(id, { resolve, reject });

            this.worker!.postMessage({
                type: 'process',
                id,
                payload: { data: inputData, options }
            });
        });
    }

    /**
     * Check if Pyodide is initialized.
     */
    isInitialized(): boolean {
        return this.worker !== null;
    }

    private nextId() {
        return ++this.messageIdCounter;
    }
}
