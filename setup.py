from vector_store import setup_chromadb
from chunking import chunk_per_page
import argparse
import subprocess
from pathlib import Path
from pypdf import PdfReader

def get_all_pdf_files(directory :Path) -> list[Path]:
    files = []
    for path in directory.iterdir():
        if path.is_file() and path.suffix.lower() == ".pdf":
            files.append(path)
    return files
def convert_to_pdf(file_path: Path) -> Path:
    if file_path.suffix.lower() != ".docx":
        raise ValueError("Only DOCX files are supported")
    output_path = file_path.with_suffix(".pdf")
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(file_path.parent),
            str(file_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if not output_path.is_file():
        raise RuntimeError(f"PDF conversion failed: {file_path}")
    return output_path

def read_pdf(file_path: Path) -> list[str]:
    reader = PdfReader(file_path)
    return [page.extract_text() for page in reader.pages]

def index_documents(convert_pdf: bool = False):
    directory = Path("data")
    if convert_pdf:
        for path in directory.iterdir():
            if path.is_file() and path.suffix.lower() == ".docx":
                convert_to_pdf(path)

    collection = setup_chromadb()
    files = get_all_pdf_files(directory)
    files_text_dir: dict[Path, list[str]] = {
        path: read_pdf(path)
        for path in files
    }
    for path, pages in files_text_dir.items():
        print(f"{path.name}: {len(pages)} Pages")

    for path, pages in files_text_dir.items():
        chunks_per_page = chunk_per_page(pages)

        ids = []
        documents = []
        metadatas = []

        for page_number, chunks in enumerate(chunks_per_page, start=1):
            for chunk_number, chunk in enumerate(chunks, start=1):
                ids.append(f"{path.name}_p{page_number}_c{chunk_number}")
                documents.append(chunk)
                metadatas.append({
                    "source": path.name,
                    "page": page_number,
                    "chunk": chunk_number
                })

        if documents:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        print(f"{path.name}: {len(documents)} chunks saved")

    return collection


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF-Dokumente aus data/ indexieren.")
    parser.add_argument("--convert-pdf", action="store_true", help="DOCX-Dateien vor dem Indexieren mit LibreOffice in PDF konvertieren.")
    args = parser.parse_args()
    index_documents(convert_pdf=args.convert_pdf)


if __name__ == "__main__":
    main()
