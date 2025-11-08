const Search = {
    init() {
        const searchInput = document.getElementById('arxivSearch');
        const searchBtn = document.getElementById('searchButton');
        const ingestBtn = document.getElementById('ingestBtn');
        
        // Search button click
        searchBtn.addEventListener('click', () => this.searchArxiv());
        
        // Enter key to search
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.searchArxiv();
            }
        });
        
        // Ingest button click
        ingestBtn.addEventListener('click', () => this.ingestSelected());
    },
    
    async searchArxiv() {
        const query = document.getElementById('arxivSearch').value.trim();
        if (!query) return;
        
        const resultsDiv = document.getElementById('arxivResults');
        resultsDiv.innerHTML = '<div style="text-align: center; padding: 40px;"><div class="loading"></div></div>';
        
        try {
            const data = await API.searchArxiv(query);
            const results = data.results || [];
            AppState.setArxivResults(results);
            
            if (results.length === 0) {
                resultsDiv.innerHTML = '<div style="text-align: center; padding: 40px 20px; color: var(--text-secondary);"><p>No papers found</p></div>';
                return;
            }
            
            this.displayResults(results);
            UI.showToast(`Found ${results.length} papers`, 'success');
        } catch (error) {
            console.error('Search error:', error);
            UI.showToast('Error searching ArXiv', 'error');
            resultsDiv.innerHTML = '<div style="text-align: center; padding: 40px 20px; color: var(--text-secondary);"><p>Error searching papers</p></div>';
        }
    },
    
    displayResults(results) {
        const resultsDiv = document.getElementById('arxivResults');
        
        resultsDiv.innerHTML = results.map((paper, idx) => `
            <div class="arxiv-paper" data-index="${idx}">
                <div class="paper-title">${paper.title}</div>
                <div class="paper-authors">${paper.authors.join(', ')}</div>
                <div class="paper-date">${paper.published}</div>
            </div>
        `).join('');
        
        // Add click handlers
        document.querySelectorAll('.arxiv-paper').forEach((el, idx) => {
            el.addEventListener('click', () => this.togglePaper(idx));
        });
    },
    
    togglePaper(idx) {
        const paper = AppState.arxivResults[idx];
        const paperEl = document.querySelectorAll('.arxiv-paper')[idx];
        const ingestBtn = document.getElementById('ingestBtn');
        
        if (AppState.selectedPapers.includes(paper.id)) {
            AppState.removeSelectedPaper(paper.id);
            paperEl.classList.remove('selected');
        } else {
            AppState.addSelectedPaper(paper.id);
            paperEl.classList.add('selected');
        }
        
        ingestBtn.disabled = AppState.selectedPapers.length === 0;
    },
    
    async ingestSelected() {
        if (AppState.selectedPapers.length === 0) return;
        
        const btn = document.getElementById('ingestBtn');
        btn.innerHTML = '<div class="loading"></div> Ingesting...';
        btn.disabled = true;
        
        try {
            const result = await API.ingestPapers(AppState.selectedPapers);
            
            if (result.success) {
                UI.showToast(`${AppState.selectedPapers.length} papers ingested successfully!`, 'success');
                await Upload.loadStats();
            } else {
                UI.showToast('Error ingesting papers', 'error');
            }
        } catch (error) {
            console.error('Ingest error:', error);
            UI.showToast('Error ingesting papers', 'error');
        }
        
        btn.innerHTML = '<i data-lucide="database" size="20"></i> Ingest Selected Papers';
        btn.disabled = false;
        AppState.clearSelectedPapers();
        
        document.querySelectorAll('.arxiv-paper').forEach(el => el.classList.remove('selected'));
        lucide.createIcons();
    }
};