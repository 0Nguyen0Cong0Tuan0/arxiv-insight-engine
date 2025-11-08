const API = {
    baseURL: '',
    
    async uploadPDFs(files) {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        
        const response = await fetch(`${this.baseURL}/api/ingest/upload`, {
            method: 'POST',
            body: formData
        });
        
        return response.json();
    },
    
    async searchArxiv(query, maxResults = 20) {
        const response = await fetch(`${this.baseURL}/api/arxiv/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, max_results: maxResults })
        });
        
        return response.json();
    },
    
    async ingestPapers(paperIds) {
        const response = await fetch(`${this.baseURL}/api/arxiv/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_ids: paperIds })
        });
        
        return response.json();
    },
    
    async queryText(query, imageBase64 = null) {
        const response = await fetch(`${this.baseURL}/api/query/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, image_base64: imageBase64 })
        });
        
        return response.json();
    },
    
    async getStats() {
        const response = await fetch(`${this.baseURL}/api/stats`);
        return response.json();
    }
};