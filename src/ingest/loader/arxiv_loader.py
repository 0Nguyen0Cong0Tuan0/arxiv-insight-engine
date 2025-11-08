import sys
import arxiv
import urllib3
import requests
from pathlib import Path
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))
from config import settings

def search_arxiv_papers(query: str, max_results: int = settings.MAX_PAPERS):
    """
    Search ArXiv and return metadata without downloading PDFs.
    
    Args:
        query (str): The search query for arXiv papers.
        max_results (int): Maximum number of results to return.
    
    Returns:
        List of paper metadata dictionaries.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending,
    )
    
    results = []

    for result in client.results(search):
        paper_id_full = result.entry_id.split('/')[-1]

        if 'v' in paper_id_full:
            paper_id_base = paper_id_full.split('v')[0]
        else:
            paper_id_base = paper_id_full
        
        results.append({
            "id": paper_id_full, 
            "id_base": paper_id_base,
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "abstract": result.summary[:300] + "..." if len(result.summary) > 300 else result.summary,
            "published": result.published.strftime("%Y-%m-%d"),
            "pdf_url": result.pdf_url,
            "entry_id": result.entry_id
        })
    
    return results

def download_single_arxiv_paper(paper_id: str, save_dir: Path = settings.RAW_PAPERS_DIR):
    """
    Download a single ArXiv paper by ID.
    
    Args:
        paper_id (str): The ArXiv paper ID (with or without version).
        save_dir (Path): Directory to save the downloaded paper.
    
    Returns:
        str: Path to downloaded PDF, or None if failed.
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    
    if 'v' in paper_id:
        paper_id_base = paper_id.split('v')[0]
    else:
        paper_id_base = paper_id
    
    client = arxiv.Client()
    search = arxiv.Search(
        query=f"id:{paper_id_base}",
        max_results=1,
    )
    
    try:
        result = next(client.results(search))
        filename = f"{paper_id}.pdf"
        pdf_path = save_dir / filename
        
        if not pdf_path.exists():
            print(f"Downloading {paper_id} from {result.pdf_url}...")
            response = requests.get(result.pdf_url, verify=False, timeout=30)
            response.raise_for_status()
            pdf_path.write_bytes(response.content)
            print(f"Downloaded: {pdf_path}")
        else:
            print(f"Already exists: {pdf_path}")
        
        return str(pdf_path)
        
    except StopIteration:
        print(f"Paper not found: {paper_id}")
        return None
    except Exception as e:
        print(f"Error downloading {paper_id}: {e}")
        return None
    
def download_arxiv_papers(query: str, max_docs: int = settings.MAX_PAPERS, save_dir: Path = settings.RAW_PAPERS_DIR):
    """
    Downloads arXiv papers as PDF + metadata. Saves them to the specified directory.
    
    Args:
        query (str): The search query for arXiv papers.
        max_docs (int): Maximum number of documents to download.
        save_dir (Path): Directory to save the downloaded papers.
    
    Returns:
        List of file paths to the downloaded papers.
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_docs,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    
    pdf_paths = []
    
    for result in client.results(search):
        paper_id = result.entry_id.split('/')[-1]
        if 'v' in paper_id:
            paper_id_base = paper_id.split('v')[0]
        else:
            paper_id_base = paper_id
            
        filename = f"{paper_id}.pdf"
        pdf_url = result.pdf_url
        pdf_path = str(save_dir / filename)
        
        pdf_paths.append(pdf_path)
        
        if pdf_url and not Path(pdf_path).exists():
            try:
                print(f"Downloading {paper_id} from {pdf_url}...")
                response = requests.get(pdf_url, verify=False, timeout=30)
                response.raise_for_status()
                Path(pdf_path).write_bytes(response.content)
                print(f"Downloaded: {pdf_path}")
            except requests.RequestException as e:
                print(f"Failed to download {pdf_url}: {e}")
                continue
        else:
            print(f"Already exists: {pdf_path}")
    
    return pdf_paths
