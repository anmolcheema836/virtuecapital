document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('network-form');
    const resultsAccordion = document.getElementById('results-accordion');
    const loadingIndicator = document.getElementById('loading');
    const errorDisplay = document.getElementById('error-display');
    const submitButton = document.getElementById('submit-button');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 1. Reset the UI
        resultsAccordion.innerHTML = '';
        errorDisplay.style.display = 'none';
        loadingIndicator.style.display = 'block';
        submitButton.disabled = true;

        // 2. Get user input
        const host = document.getElementById('host').value;
        const selectedTools = Array.from(document.querySelectorAll('input[type=checkbox]:checked')).map(cb => cb.value);

        if (selectedTools.length === 0) {
            displayError('Please select at least one diagnostic tool.');
            return;
        }

        try {
            // 3. Call the server's API
            const response = await fetch('/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, tools: selectedTools })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'An unknown server error occurred.');
            }

            // 4. Display the results
            displayResults(data);

        } catch (error) {
            displayError(error.message);
        } finally {
            // 5. Clean up the UI
            loadingIndicator.style.display = 'none';
            submitButton.disabled = false;
        }
    });

    function displayError(message) {
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
        loadingIndicator.style.display = 'none';
        submitButton.disabled = false;
    }

    function displayResults(data) {
        if (!data || data.length === 0) {
            resultsAccordion.innerHTML = '<p class="text-center">No results were returned from the server.</p>';
            return;
        }

        let accordionHTML = '';
        data.forEach((location, index) => {
            const collapseId = `collapse-${index}`;
            const headingId = `heading-${index}`;
            
            const resultsContent = Object.entries(location.results).map(([tool, result]) => `
                <strong>${escapeHtml(tool.charAt(0).toUpperCase() + tool.slice(1))}:</strong>
                <pre>${escapeHtml(result) || 'Command failed or produced no output.'}</pre>
            `).join('');

            accordionHTML += `
                <div class="accordion-item">
                    <h2 class="accordion-header" id="${headingId}">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}" aria-expanded="true" aria-controls="${collapseId}">
                            ${escapeHtml(location.name)}
                        </button>
                    </h2>
                    <div id="${collapseId}" class="accordion-collapse collapse show" aria-labelledby="${headingId}">
                        <div class="accordion-body">
                            ${resultsContent}
                        </div>
                    </div>
                </div>
            `;
        });
        resultsAccordion.innerHTML = accordionHTML;
    }
    
    // Simple function to prevent HTML injection in results
    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});