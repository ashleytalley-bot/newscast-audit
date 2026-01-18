/**
 * Enhanced Error UI Components
 *
 * Provides rich, user-friendly error messages with actionable guidance.
 */

class ErrorUI {
    constructor() {
        this.errorContainer = document.getElementById('error-message');
        this.warningsContainer = this.createWarningsContainer();
    }

    /**
     * Create warnings container if it doesn't exist
     */
    createWarningsContainer() {
        let container = document.getElementById('warnings-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'warnings-container';
            container.className = 'warnings-container hidden';
            // Insert after results section title
            const resultsSection = document.getElementById('results-section');
            if (resultsSection) {
                resultsSection.insertBefore(container, resultsSection.firstChild);
            }
        }
        return container;
    }

    /**
     * Show structured error with detailed information
     */
    showError(error) {
        if (typeof error === 'string') {
            // Simple string error
            this.showSimpleError(error);
            return;
        }

        if (error.error) {
            // Structured error from Python
            this.showStructuredError(error.error);
        } else {
            // JavaScript error or unknown format
            this.showSimpleError(error.message || String(error));
        }
    }

    /**
     * Show simple error message
     */
    showSimpleError(message) {
        this.errorContainer.innerHTML = this.createErrorHTML({
            error_type: 'Error',
            message: message,
            user_action: 'Please try again or contact support if the issue persists.'
        });
        this.errorContainer.classList.remove('hidden');
        this.scrollToError();
    }

    /**
     * Show structured error with full details
     */
    showStructuredError(errorData) {
        this.errorContainer.innerHTML = this.createStructuredErrorHTML(errorData);
        this.errorContainer.classList.remove('hidden');
        this.scrollToError();
    }

    /**
     * Create HTML for basic error
     */
    createErrorHTML(errorData) {
        return `
            <div class="error-card">
                <div class="error-header">
                    <svg class="error-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <h3 class="error-title">${this.escapeHtml(errorData.error_type || 'Error')}</h3>
                </div>
                <p class="error-message">${this.escapeHtml(errorData.message)}</p>
                ${errorData.user_action ? `
                    <div class="error-action">
                        <strong>What to do:</strong> ${this.escapeHtml(errorData.user_action)}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Create HTML for structured error with details
     */
    createStructuredErrorHTML(errorData) {
        let html = `
            <div class="error-card">
                <div class="error-header">
                    <svg class="error-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <h3 class="error-title">${this.escapeHtml(errorData.error_type || 'Error')}</h3>
                </div>
                <p class="error-message">${this.escapeHtml(errorData.message)}</p>
        `;

        // Show user action if available
        if (errorData.user_action) {
            html += `
                <div class="error-action">
                    <strong>What to do:</strong> ${this.escapeHtml(errorData.user_action)}
                </div>
            `;
        }

        // Show details if available
        if (errorData.details && Object.keys(errorData.details).length > 0) {
            html += `<div class="error-details">`;
            html += `<button class="error-details-toggle" onclick="this.nextElementSibling.classList.toggle('hidden')">
                Show technical details ▼
            </button>`;
            html += `<div class="error-details-content hidden">`;

            // Missing columns
            if (errorData.details.missing_columns) {
                html += `
                    <div class="error-detail-item">
                        <strong>Missing columns:</strong>
                        <ul>
                            ${errorData.details.missing_columns.map(col => `<li>${this.escapeHtml(col)}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            // Found columns
            if (errorData.details.found_columns && errorData.details.found_columns.length > 0) {
                html += `
                    <div class="error-detail-item">
                        <strong>Columns found in file:</strong>
                        <ul>
                            ${errorData.details.found_columns.slice(0, 10).map(col => `<li>${this.escapeHtml(col)}</li>`).join('')}
                            ${errorData.details.found_columns.length > 10 ? '<li>... and more</li>' : ''}
                        </ul>
                    </div>
                `;
            }

            // Issue count
            if (errorData.details.issue_count !== undefined) {
                html += `
                    <div class="error-detail-item">
                        <strong>Issues found:</strong> ${errorData.details.issue_count}
                    </div>
                `;
            }

            // Examples
            if (errorData.details.examples && errorData.details.examples.length > 0) {
                html += `
                    <div class="error-detail-item">
                        <strong>Examples:</strong>
                        <ul>
                            ${errorData.details.examples.map(ex => `<li>${this.escapeHtml(String(ex))}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            // Row counts for InsufficientDataError
            if (errorData.details.initial_count) {
                html += `
                    <div class="error-detail-item">
                        <strong>Data summary:</strong>
                        <ul>
                            <li>Initial rows: ${errorData.details.initial_count}</li>
                            <li>Valid rows: ${errorData.details.final_count || 0}</li>
                            <li>Dropped rows: ${errorData.details.dropped_count || 0}</li>
                        </ul>
                    </div>
                `;
            }

            html += `</div></div>`;
        }

        html += `</div>`;
        return html;
    }

    /**
     * Show data quality messages (warnings and info)
     */
    showWarnings(qualityData) {
        if (!qualityData ||
            ((!qualityData.warnings || qualityData.warnings.length === 0) &&
                (!qualityData.info || qualityData.info.length === 0))) {
            this.hideWarnings();
            return;
        }

        let html = '<div class="warnings-card">';

        // Render Warnings
        if (qualityData.warnings && qualityData.warnings.length > 0) {
            html += `
                <div class="warnings-header">
                    <svg class="warning-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                        <line x1="12" y1="9" x2="12" y2="13"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    <h4>Data Quality Warnings</h4>
                </div>
                <p class="warnings-intro">The data was processed successfully, but some quality issues were detected:</p>
            `;

            qualityData.warnings.forEach(warning => {
                html += this.createQualityMessageHTML(warning, 'warning');
            });
        }

        // Render Info
        if (qualityData.info && qualityData.info.length > 0) {
            html += `
                <div class="info-header ${qualityData.warnings && qualityData.warnings.length > 0 ? 'mt-4' : ''}">
                    <svg class="info-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <h4>Information</h4>
                </div>
            `;

            qualityData.info.forEach(info => {
                html += this.createQualityMessageHTML(info, 'info');
            });
        }

        html += '</div>';
        this.warningsContainer.innerHTML = html;
        this.warningsContainer.classList.remove('hidden');
    }

    /**
     * Create HTML for a single quality message
     */
    createQualityMessageHTML(data, type) {
        return `
            <div class="quality-item ${type}-item">
                <p class="quality-message">${this.escapeHtml(data.message)}</p>
                ${data.examples && data.examples.length > 0 ? `
                    <details class="quality-examples">
                        <summary>Show examples (${data.examples.length})</summary>
                        <ul>
                            ${data.examples.map(ex => `<li>${this.escapeHtml(String(ex))}</li>`).join('')}
                        </ul>
                    </details>
                ` : ''}
            </div>
        `;
    }

    /**
     * Hide error message
     */
    hideError() {
        this.errorContainer.classList.add('hidden');
        this.errorContainer.innerHTML = '';
    }

    /**
     * Hide warnings
     */
    hideWarnings() {
        this.warningsContainer.classList.add('hidden');
        this.warningsContainer.innerHTML = '';
    }

    /**
     * Scroll to error message
     */
    scrollToError() {
        setTimeout(() => {
            this.errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Clear all error and warning UI
     */
    clearAll() {
        this.hideError();
        this.hideWarnings();
    }
}

// Singleton instance
const errorUI = new ErrorUI();
