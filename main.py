import argparse

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from setup import index_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Fragen zu den indexierten Dokumenten beantworten.")
    parser.add_argument("--manual", action="store_true", help="Eigene Fragen eingeben (beenden mit exit oder quit). Standard: vier Beispielfragen automatisch beantworten.")
    parser.add_argument("--convert-pdf", action="store_true", help="DOCX-Dateien vor dem Indexieren mit LibreOffice in PDF konvertieren.")
    args = parser.parse_args()

    load_dotenv()

    collection = index_documents(convert_pdf=args.convert_pdf)
    model = ChatOpenRouter(model="openrouter/free")
    questions = iter([
        "Was ist FastAPI, und wofür eignet es sich typischerweise?",
        "Welche drei RAG-Paradigmen werden unterschieden?",
        "Was ist Azure AI Foundry?",
        "Welche Dokumentformate kann Docling verarbeiten?",
    ])
    while True:
        if not args.manual:
            question = next(questions, None)
            if question is None:
                break
            print(f"\nFrage> {question}")
        else:
            question = input("Frage> ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        results = collection.query(
            query_texts=[question],
            n_results=3,
            include=["documents", "metadatas"],
        )
        sources = []
        context_parts = []
        metadatas = (results.get("metadatas") or [[]])[0]
        for index, document in enumerate(results["documents"][0]):
            if not document:
                continue
            metadata = (metadatas[index] if index < len(metadatas) else None) or {}
            source = metadata.get("source", "Unbekannte Quelle")
            if metadata.get("page") is not None:
                source = f"{source}, Seite {metadata['page']}"
            if source not in sources:
                sources.append(source)
            reference = sources.index(source) + 1
            context_parts.append(f"[{reference}] {source}\n{document}")
        context = "\n\n".join(context_parts)

        if not context:
            print("Keine Dokumente gefunden. Bitte PDFs in data/ ablegen oder --convert-pdf für DOCX-Dateien verwenden.")
            return

        answer = model.invoke([
            ("system", "Beantworte die Frage ausschließlich anhand des Kontexts. "
                       "Belege Aussagen mit den Quellenmarkierungen [1], [2] usw. aus dem Kontext. "
                       "Falls die Antwort nicht enthalten ist, sage das."),
            ("human", f"Kontext:\n{context}\n\nFrage: {question}")
        ])
        print(answer.content)
        print("\nQuellen (abgerufene Dokumentstellen):")
        for reference, source in enumerate(sources, start=1):
            print(f"[{reference}] {source}")

if __name__ == "__main__":
    main()
