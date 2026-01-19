import esbuild from 'esbuild';
// glob removed
// Actually, let's just list the files or use a simple directory scan since we don't want to add too many dependencies if possible.
// Or just use fs.readdir.
import fs from 'fs';
import path from 'path';

// Simple directory scan for .ts files in specific directories
function findTsFiles(dir) {
    if (!fs.existsSync(dir)) return [];
    return fs.readdirSync(dir)
        .filter(file => file.endsWith('.ts') && !file.endsWith('.d.ts'))
        .map(file => path.join(dir, file));
}

const serviceFiles = findTsFiles('docs/js/services');
const typeFiles = findTsFiles('docs/js/types'); // Types usually don't need compilation unless they have enums or runtime code.
// For now, let's verify if types have runtime code. Usually interfaces don't emit code.
// docs/js/types/index.ts usually exports things, so it might need compilation if used as a module.

const entryPoints = [
    ...serviceFiles,
    ...typeFiles
];

console.log('Compiling TypeScript files:', entryPoints);

async function build() {
    try {
        await esbuild.build({
            entryPoints: entryPoints,
            outdir: '.', // Output to same directories (e.g. docs/js/services)
            outbase: '.', // Preserve full path from root
            allowOverwrite: true, // Allow writing next to source
            bundle: false, // Don't bundle, keep individual files suitable for ESM import
            format: 'esm',
            platform: 'browser',
            target: ['es2020'],
            sourcemap: true,
        });
        console.log('⚡ Build complete!');
    } catch (error) {
        console.error('Build failed:', error);
        process.exit(1);
    }
}

build();
