import sys
import arxiv
import requests
import urllib3
from pathlib import Path
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))
from config import settings

def download_arxiv_papers(query: str, max_docs: int = settings.MAX_PAPERS, save_dir: Path = settings.RAW_PAPERS_DIR):
    """
    Downloads arXiv papers as PDF + metadata using the ArxivLoader. Saves them to the specified directory.

    Args:
        query (str): The search query for arXiv papers.
        max_docs (int): Maximum number of documents to download.
        save_dir (str): Directory to save the downloaded papers.
    
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
        filename = f"{result.entry_id.split('/')[-1]}.pdf"
        pdf_url = result.pdf_url
        pdf_path = str(save_dir / filename)
        
        pdf_paths.append(pdf_path)

        if pdf_url and not Path(pdf_path).exists():
            try:
                response = requests.get(pdf_url, verify=False)
                response.raise_for_status()
                Path(pdf_path).write_bytes(response.content)
                print(f"Downloaded: {pdf_path}")
            except requests.RequestException as e:
                print(f"Failed to download {pdf_url}: {e}")
                continue

    return pdf_paths