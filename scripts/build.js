import esbuild from 'esbuild';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

// Compute MD5 hash of file contents for cache-busting
function computeFileHash(filepath) {
    if (!fs.existsSync(filepath)) {
        return 'missing';
    }
    const content = fs.readFileSync(filepath);
    return crypto.createHash('md5').update(content).digest('hex').substring(0, 8);
}

// Simple directory scan for .ts files in specific directories
function findTsFiles(dir) {
    if (!fs.existsSync(dir)) return [];
    return fs.readdirSync(dir)
        .filter(file => file.endsWith('.ts') && !file.endsWith('.d.ts'))
        .map(file => path.join(dir, file));
}

const serviceFiles = findTsFiles('docs/js/services');
const moduleFiles = findTsFiles('docs/js/modules');
const typeFiles = findTsFiles('docs/js/types'); // Types usually don't need compilation unless they have enums or runtime code.
// For now, let's verify if types have runtime code. Usually interfaces don't emit code.
// docs/js/types/index.ts usually exports things, so it might need compilation if used as a module.

const entryPoints = [
    'docs/js/app.ts',
    'docs/js/workers/PyodideWorker.ts',
    ...serviceFiles,
    ...moduleFiles,
    ...typeFiles
];

console.log('Compiling TypeScript files:', entryPoints);

// Helper to get all files in a directory matching a pattern
function getFilesRecursive(dir, pattern, baseDir) {
    let results = [];
    if (!fs.existsSync(dir)) return results;

    const list = fs.readdirSync(dir);
    list.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        if (stat && stat.isDirectory()) {
            if (file !== '__pycache__') {
                results = results.concat(getFilesRecursive(filePath, pattern, baseDir));
            }
        } else if (file.match(pattern)) {
            const relPath = path.relative(baseDir, filePath);
            results.push(relPath.split(path.sep).join('/'));
        }
    });
    return results;
}

async function build() {
    try {
        console.log('Building TypeScript...');
        await esbuild.build({
            entryPoints: entryPoints,
            outdir: '.',
            outbase: '.',
            allowOverwrite: true,
            bundle: false,
            format: 'esm',
            platform: 'browser',
            target: ['es2020'],
            sourcemap: true,
        });

        // Generate Python manifests (replacing build.py)
        console.log('Generating manifests...');
        const docsDir = 'docs';

        // Python files
        const pyFiles = [
            ...getFilesRecursive(path.join(docsDir, 'lib'), /\.py$/, docsDir),
            ...getFilesRecursive(path.join(docsDir, 'py'), /\.py$/, docsDir)
        ].sort();
        fs.writeFileSync(path.join(docsDir, 'py-files.json'), JSON.stringify(pyFiles, null, 2));
        console.log(`✓ Generated py-files.json (${pyFiles.length} files)`);

        // Config files
        const configFiles = getFilesRecursive(path.join(docsDir, 'config'), /\.yaml$/, docsDir).sort();
        fs.writeFileSync(path.join(docsDir, 'config-files.json'), JSON.stringify(configFiles, null, 2));
        console.log(`✓ Generated config-files.json (${configFiles.length} files)`);

        // Generate asset manifest with content hashes for cache-busting
        console.log('Generating asset manifest with content hashes...');
        const assetManifest = {
            // JavaScript files
            'js/app.js': computeFileHash('docs/js/app.js'),

            // Python manifests (dynamic)
            'py-files.json': computeFileHash('docs/py-files.json'),
            'config-files.json': computeFileHash('docs/config-files.json'),

            // Config YAML files (add hashes for all configs)
            ...configFiles.reduce((acc, file) => {
                acc[file] = computeFileHash(path.join(docsDir, file));
                return acc;
            }, {})
        };

        fs.writeFileSync(
            path.join(docsDir, 'asset-manifest.json'),
            JSON.stringify(assetManifest, null, 2)
        );
        console.log(`✓ Generated asset-manifest.json (${Object.keys(assetManifest).length} assets)`);

        console.log('⚡ Build complete!');
    } catch (error) {
        console.error('Build failed:', error);
        process.exit(1);
    }
}

build();
