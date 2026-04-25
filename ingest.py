"""
CLI Document Ingestion Script
Process documents from a folder and add them to the vector store.
"""
import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent))

from config import config
from src.document_processor import DocumentProcessor
from src.embeddings_manager import EmbeddingsManager

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Personal Knowledge Brain - Document Ingestion CLI"
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="./documents",
        help="Path to documents folder (default: ./documents)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing vectorstore before ingestion",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        help="Filter by file extension (e.g., pdf, docx)",
    )
    args = parser.parse_args()

    console.print(
        Panel.fit(
            "[bold magenta]🧠 Personal Knowledge Brain[/bold magenta]\n"
            "[cyan]Document Ingestion CLI[/cyan]",
            border_style="magenta",
        )
    )

    # Validate API key
    if not config.GOOGLE_API_KEY or config.GOOGLE_API_KEY == "your_google_api_key_here":
        console.print("[bold red]❌ GOOGLE_API_KEY not set![/bold red]")
        console.print("Set it in your .env file or environment variables.")
        sys.exit(1)

    # Initialize embeddings manager
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing embeddings...", total=None)
        try:
            embeddings_manager = EmbeddingsManager(
                google_api_key=config.GOOGLE_API_KEY,
                embedding_model=config.EMBEDDING_MODEL,
                vector_store_path=config.VECTOR_STORE_PATH,
            )
        except Exception as e:
            console.print(f"[red]Failed to initialize embeddings: {e}[/red]")
            sys.exit(1)
        progress.update(task, completed=True)

    # Reset if requested
    if args.reset:
        console.print("[yellow]🗑️ Resetting vectorstore...[/yellow]")
        embeddings_manager.reset_vectorstore()
        console.print("[green]✅ Vectorstore cleared[/green]")

    # Process documents
    console.print(f"\n[blue]📁 Scanning folder: {args.folder}[/blue]")

    processor = DocumentProcessor(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    if args.format:
        processor.supported_extensions = [f".{args.format.lstrip('.')}"]

    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Processing documents...", total=None)
        chunks = processor.process_all_documents(args.folder)
        progress.update(task, completed=True)

    if not chunks:
        console.print("[yellow]⚠️ No documents found or processed[/yellow]")
        sys.exit(0)

    console.print(f"[green]📄 Created {len(chunks)} chunks[/green]")

    # Add to vectorstore
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding chunks into vectorstore...", total=None)
        added = embeddings_manager.add_documents(chunks)
        progress.update(task, completed=True)

    # Stats
    stats = embeddings_manager.get_vectorstore_stats()
    table = Table(title="Knowledge Base Stats")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Documents Ingested", str(stats["total_documents"]))
    table.add_row("Total Chunks", str(stats["total_chunks"]))
    table.add_row("Storage Size", stats["storage_size"])
    table.add_row("Indexed Files", ", ".join(stats["indexed_files"]) or "None")

    console.print(table)
    console.print("\n[bold green]✅ Ingestion complete![/bold green]")


if __name__ == "__main__":
    main()
