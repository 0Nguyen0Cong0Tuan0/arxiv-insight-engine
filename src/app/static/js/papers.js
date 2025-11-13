// Papers Management System

class PapersManager {
    constructor() {
        this.papers = [];
        this.selectedPapers = new Set();
        this.isModalOpen = false;
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }
    
    setupUI() {
        // Create papers management button in header
        this.addManagementButton();
        
        // Create modal
        this.createModal();
    }
    
    addManagementButton() {
        const headerStats = document.querySelector('.header-stats');
        if (headerStats && !document.getElementById('papers-manage-btn')) {
            const manageBtn = document.createElement('div');
            manageBtn.id = 'papers-manage-btn';
            manageBtn.className = 'voice-toggle';
            manageBtn.style.cursor = 'pointer';
            manageBtn.innerHTML = `
                <i data-lucide="database"></i>
                <span>Manage Papers</span>
            `;
            manageBtn.addEventListener('click', () => this.openModal());
            headerStats.appendChild(manageBtn);
            
            // Initialize icon
            if (window.lucide) {
                lucide.createIcons();
            }
        }
    }
    
    createModal() {
        // Create modal HTML
        const modal = document.createElement('div');
        modal.id = 'papers-modal';
        modal.className = 'papers-modal';
        modal.style.display = 'none';
        modal.innerHTML = `
            <div class="papers-modal-overlay" onclick="window.papersManager.closeModal()"></div>
            <div class="papers-modal-content">
                <div class="papers-modal-header">
                    <h2>
                        <i data-lucide="database"></i>
                        Manage Papers
                    </h2>
                    <button class="papers-modal-close" onclick="window.papersManager.closeModal()">
                        <i data-lucide="x"></i>
                    </button>
                </div>
                
                <div class="papers-modal-toolbar">
                    <div class="papers-toolbar-left">
                        <span class="papers-count">Loading...</span>
                    </div>
                    <div class="papers-toolbar-right">
                        <button class="btn btn-primary" id="selectAllBtn" onclick="window.papersManager.selectAll()">
                            <i data-lucide="check-square"></i>
                            Select All
                        </button>
                        <button class="btn btn-primary" id="deleteSelectedBtn" onclick="window.papersManager.deleteSelected()" 
                                style="background: linear-gradient(135deg, var(--error), #dc2626);" disabled>
                            <i data-lucide="trash-2"></i>
                            Delete Selected
                        </button>
                    </div>
                </div>
                
                <div class="papers-list" id="papersList">
                    <div class="papers-loading">
                        <div class="loading"></div>
                        <p>Loading papers...</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Initialize icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }
    
    async openModal() {
        this.isModalOpen = true;
        const modal = document.getElementById('papers-modal');
        modal.style.display = 'flex';
        
        // Load papers
        await this.loadPapers();
        
        // Reinitialize icons after content load
        if (window.lucide) {
            lucide.createIcons();
        }
    }
    
    closeModal() {
        this.isModalOpen = false;
        const modal = document.getElementById('papers-modal');
        modal.style.display = 'none';
        this.selectedPapers.clear();
    }
    
    async loadPapers() {
        try {
            const response = await fetch('/api/papers/list');
            const data = await response.json();
            
            if (data.success) {
                this.papers = data.papers;
                this.renderPapers();
                
                // Update count
                document.querySelector('.papers-count').textContent = 
                    `${data.total_papers} papers (${data.total_chunks} chunks)`;
            }
        } catch (error) {
            console.error('Error loading papers:', error);
            document.getElementById('papersList').innerHTML = `
                <div class="papers-error">
                    <i data-lucide="alert-circle"></i>
                    <p>Error loading papers. Please try again.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
        }
    }
    
    renderPapers() {
        const papersList = document.getElementById('papersList');
        
        if (this.papers.length === 0) {
            papersList.innerHTML = `
                <div class="papers-empty">
                    <i data-lucide="inbox" size="64"></i>
                    <h3>No papers found</h3>
                    <p>Upload PDFs or search ArXiv to add papers</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }
        
        papersList.innerHTML = this.papers.map(paper => `
            <div class="paper-item" data-paper-id="${paper.paper_id}">
                <div class="paper-checkbox">
                    <input type="checkbox" 
                           id="paper-${paper.paper_id}" 
                           onchange="window.papersManager.togglePaper('${paper.paper_id}')">
                </div>
                <div class="paper-info" onclick="window.papersManager.viewPaper('${paper.paper_id}')">
                    <div class="paper-title">
                        <i data-lucide="file-text"></i>
                        <strong>${paper.title}</strong>
                    </div>
                    <div class="paper-meta">
                        <span class="paper-meta-item">
                            <i data-lucide="hash"></i>
                            ID: ${paper.paper_id}
                        </span>
                        <span class="paper-meta-item">
                            <i data-lucide="layers"></i>
                            ${paper.chunk_count} chunks
                        </span>
                        <span class="paper-meta-item">
                            <i data-lucide="file"></i>
                            ${this.formatBytes(paper.total_size)}
                        </span>
                    </div>
                </div>
                <div class="paper-actions">
                    <button class="paper-action-btn" 
                            onclick="window.papersManager.viewPaper('${paper.paper_id}')"
                            title="View details">
                        <i data-lucide="eye"></i>
                    </button>
                    <button class="paper-action-btn paper-action-delete" 
                            onclick="window.papersManager.deleteSingle('${paper.paper_id}')"
                            title="Delete paper">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        if (window.lucide) lucide.createIcons();
    }
    
    togglePaper(paperId) {
        const checkbox = document.getElementById(`paper-${paperId}`);
        if (checkbox.checked) {
            this.selectedPapers.add(paperId);
        } else {
            this.selectedPapers.delete(paperId);
        }
        
        // Update delete button state
        const deleteBtn = document.getElementById('deleteSelectedBtn');
        deleteBtn.disabled = this.selectedPapers.size === 0;
        
        // Update select all button text
        const selectAllBtn = document.getElementById('selectAllBtn');
        if (this.selectedPapers.size === this.papers.length) {
            selectAllBtn.innerHTML = `
                <i data-lucide="square"></i>
                Deselect All
            `;
        } else {
            selectAllBtn.innerHTML = `
                <i data-lucide="check-square"></i>
                Select All
            `;
        }
        if (window.lucide) lucide.createIcons();
    }
    
    selectAll() {
        const allSelected = this.selectedPapers.size === this.papers.length;
        
        if (allSelected) {
            // Deselect all
            this.selectedPapers.clear();
            document.querySelectorAll('.paper-item input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
        } else {
            // Select all
            this.papers.forEach(paper => {
                this.selectedPapers.add(paper.paper_id);
                const checkbox = document.getElementById(`paper-${paper.paper_id}`);
                if (checkbox) checkbox.checked = true;
            });
        }
        
        // Update buttons
        const deleteBtn = document.getElementById('deleteSelectedBtn');
        deleteBtn.disabled = this.selectedPapers.size === 0;
        
        const selectAllBtn = document.getElementById('selectAllBtn');
        if (this.selectedPapers.size === this.papers.length) {
            selectAllBtn.innerHTML = `
                <i data-lucide="square"></i>
                Deselect All
            `;
        } else {
            selectAllBtn.innerHTML = `
                <i data-lucide="check-square"></i>
                Select All
            `;
        }
        if (window.lucide) lucide.createIcons();
    }
    
    async deleteSelected() {
        if (this.selectedPapers.size === 0) return;
        
        const paperIds = Array.from(this.selectedPapers);
        const confirmed = confirm(
            `Are you sure you want to delete ${paperIds.length} paper(s)?\n` +
            `This will remove all chunks and cannot be undone.`
        );
        
        if (!confirmed) return;
        
        try {
            const response = await fetch('/api/papers/delete', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(paperIds)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(
                    `Successfully deleted ${data.chunks_deleted} chunks from ${data.papers_deleted.length} papers`,
                    'success'
                );
                
                // Reload papers
                this.selectedPapers.clear();
                await this.loadPapers();
                
                // Update stats in header
                if (window.updateStats) {
                    updateStats();
                }
            }
        } catch (error) {
            console.error('Error deleting papers:', error);
            this.showNotification('Error deleting papers. Please try again.', 'error');
        }
    }
    
    async deleteSingle(paperId) {
        const paper = this.papers.find(p => p.paper_id === paperId);
        const confirmed = confirm(
            `Delete paper "${paper?.title || paperId}"?\n` +
            `This will remove ${paper?.chunk_count || 0} chunks and cannot be undone.`
        );
        
        if (!confirmed) return;
        
        try {
            const response = await fetch('/api/papers/delete', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify([paperId])
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Successfully deleted paper`, 'success');
                
                // Reload papers
                await this.loadPapers();
                
                // Update stats in header
                if (window.updateStats) {
                    updateStats();
                }
            }
        } catch (error) {
            console.error('Error deleting paper:', error);
            this.showNotification('Error deleting paper. Please try again.', 'error');
        }
    }
    
    async viewPaper(paperId) {
        try {
            const response = await fetch(`/api/papers/${paperId}`);
            const data = await response.json();
            
            if (data.success) {
                this.showPaperDetails(data);
            }
        } catch (error) {
            console.error('Error loading paper details:', error);
            this.showNotification('Error loading paper details', 'error');
        }
    }
    
    showPaperDetails(data) {
        const modal = document.createElement('div');
        modal.className = 'paper-details-modal';
        modal.innerHTML = `
            <div class="papers-modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="paper-details-content">
                <div class="paper-details-header">
                    <h2>
                        <i data-lucide="file-text"></i>
                        ${data.paper.title}
                    </h2>
                    <button class="papers-modal-close" onclick="this.parentElement.parentElement.remove()">
                        <i data-lucide="x"></i>
                    </button>
                </div>
                <div class="paper-details-body">
                    <div class="paper-details-info">
                        <strong>Paper ID:</strong> ${data.paper.paper_id}<br>
                        <strong>Total Chunks:</strong> ${data.total_chunks}
                    </div>
                    <div class="paper-chunks-list">
                        <h3>Chunks Preview</h3>
                        ${data.chunks.slice(0, 10).map((chunk, idx) => `
                            <div class="chunk-preview">
                                <div class="chunk-header">
                                    <strong>Chunk ${idx + 1}</strong>
                                    <span class="chunk-type">${chunk.type}</span>
                                </div>
                                <div class="chunk-content">${chunk.content.substring(0, 300)}...</div>
                            </div>
                        `).join('')}
                        ${data.chunks.length > 10 ? `
                            <p style="text-align: center; color: var(--text-secondary); margin-top: 16px;">
                                And ${data.chunks.length - 10} more chunks...
                            </p>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        if (window.lucide) lucide.createIcons();
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    showNotification(message, type = 'info') {
        // Reuse voice assistant notification if available
        if (window.voiceAssistant && window.voiceAssistant.showNotification) {
            window.voiceAssistant.showNotification(message, type);
        } else {
            alert(message);
        }
    }
}

// Initialize papers manager
window.papersManager = new PapersManager();