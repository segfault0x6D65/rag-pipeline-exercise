from langchain_text_splitters import RecursiveCharacterTextSplitter
def setup_splitter () -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        length_function=len
    )
def chunk_per_page(pages: list[str]) -> list[list[str]]:
    splitter = setup_splitter()
    return [splitter.split_text(page or "") for page in pages]
