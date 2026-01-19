// @ts-check

/**
 * @typedef {import('../types').Comment} Comment
 */

export class CommentRenderer {
    /**
     * Render the comments feed.
     * @param {string} containerId 
     * @param {Comment[]} comments 
     */
    renderComments(containerId, comments) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!comments || comments.length === 0) {
            container.innerHTML = '<p class="text-muted">No additional comments found.</p>';
            return;
        }

        // Create feed structure
        const feedHtml = `
            <div class="comments-controls">
                <input type="text" id="comment-search" placeholder="Search comments..." class="form-control mb-3">
            </div>
            <div class="comments-list" style="max-height: 400px; overflow-y: auto;">
                ${comments.map(c => this.createCommentCard(c)).join('')}
            </div>
            <p class="text-end text-muted mt-2"><small>Total comments: ${comments.length}</small></p>
        `;

        container.innerHTML = feedHtml;

        // Add search functionality
        const searchInput = document.getElementById('comment-search');
        if (searchInput) {
            searchInput.addEventListener('keyup', (e) => {
                // @ts-ignore
                const term = e.target.value.toLowerCase();
                this.filterComments(container, term);
            });
        }
    }

    /**
     * Create HTML for a single comment card.
     * @param {Comment} comment 
     */
    createCommentCard(comment) {
        return `
            <div class="card mb-2 comment-card">
                <div class="card-body py-2">
                    <h6 class="card-subtitle mb-2 text-muted d-flex justify-content-between">
                        <span>${comment.newscast}</span>
                        <small>${comment.date}</small>
                    </h6>
                    <p class="card-text mb-0">${comment.text}</p>
                </div>
            </div>
        `;
    }

    /**
     * Filter comments based on search term.
     * @param {HTMLElement} container 
     * @param {string} term 
     */
    filterComments(container, term) {
        const cards = container.querySelectorAll('.comment-card');
        cards.forEach(card => {
            // @ts-ignore
            const text = card.textContent.toLowerCase();
            // @ts-ignore
            card.style.display = text.includes(term) ? '' : 'none';
        });
    }
}
