"""
Phantom CLI - Hide files inside other files.

Usage:
    phantom hide <carrier> <payload...> -o <output> [-p password]
    phantom extract <file> -o <output_dir> [-p password]
"""

import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich import print as rprint

from .banner import BANNER, BANNER_SMALL
from .core.engine import (
    hide as engine_hide,
    extract as engine_extract,
    PhantomError,
    PayloadNotFoundError,
    DecryptionError,
    IntegrityError,
)

console = Console()
app = typer.Typer(
    name="phantom",
    help="👻 Phantom - Hide files inside other files",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def show_banner():
    """Display the ASCII art banner."""
    console.print(BANNER)


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """👻 Phantom - Steganography & Polyglot CLI Tool"""
    if ctx.invoked_subcommand is None:
        show_banner()


@app.command()
def hide(
    carrier: str = typer.Argument(
        ..., help="Path to the carrier file (PDF, PNG, JPEG, etc.)"
    ),
    payloads: List[str] = typer.Argument(
        ..., help="Path(s) to file(s) to hide inside the carrier"
    ),
    output: str = typer.Option(
        ..., "--output", "-o", help="Output file path"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password for AES-256-GCM encryption"
    ),
    no_compress: bool = typer.Option(
        False, "--no-compress", help="Disable payload compression"
    ),
):
    """
    🔒 Hide file(s) inside a carrier file.

    Examples:
        phantom hide report.pdf secret.exe -o output.pdf -p "mypassword"
        phantom hide image.png file1.txt file2.zip -o steg_image.png
    """
    console.print(BANNER_SMALL)
    console.print()

    carrier_path = Path(carrier)
    payload_paths = [Path(p) for p in payloads]
    output_path = Path(output)

    # Validate
    if not carrier_path.exists():
        console.print(f"[red]❌ Carrier file not found:[/red] {carrier_path}")
        raise typer.Exit(1)

    for p in payload_paths:
        if not p.exists():
            console.print(f"[red]❌ Payload file not found:[/red] {p}")
            raise typer.Exit(1)

    # Show operation summary
    console.print(f"[bold]📦 Carrier:[/bold] {carrier_path.name} ({format_size(carrier_path.stat().st_size)})")
    for p in payload_paths:
        console.print(f"[bold]🔐 Payload:[/bold] {p.name} ({format_size(p.stat().st_size)})")
    console.print(f"[bold]📝 Output:[/bold]  {output_path}")
    if password:
        console.print("[bold]🔑 Encryption:[/bold] [green]AES-256-GCM[/green]")
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Hiding payload...", total=100)

            progress.update(task, advance=30, description="[cyan]Reading files...")
            result = engine_hide(
                carrier_path=carrier_path,
                payload_paths=payload_paths,
                output_path=output_path,
                password=password,
                compress_payload=not no_compress,
            )
            progress.update(task, advance=70, description="[green]Complete!")

        # Success summary
        console.print()
        panel_content = (
            f"[green]✅ Payload hidden successfully![/green]\n\n"
            f"  Output:      {output_path}\n"
            f"  Output size: {format_size(output_path.stat().st_size)}\n"
            f"  Encrypted:   {'✅ Yes' if result.is_encrypted else '❌ No'}\n"
            f"  Compressed:  {'✅ Yes' if result.is_compressed else '❌ No'}\n"
            f"  Files:       {result.file_count}\n"
            f"  Checksum:    {result.checksum_hex[:16]}..."
        )
        console.print(Panel(panel_content, title="[bold green]Success[/bold green]", border_style="green"))

    except PhantomError as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def extract(
    file: str = typer.Argument(
        ..., help="Path to the file containing hidden data"
    ),
    output: str = typer.Option(
        "./extracted", "--output", "-o", help="Output directory for extracted files"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password for decryption"
    ),
):
    """
    📤 Extract hidden file(s) from a steganography file.

    Examples:
        phantom extract output.pdf -o ./extracted/ -p "mypassword"
        phantom extract steg_image.png -o ./out/
    """
    console.print(BANNER_SMALL)
    console.print()

    file_path = Path(file)
    output_dir = Path(output)

    if not file_path.exists():
        console.print(f"[red]❌ File not found:[/red] {file_path}")
        raise typer.Exit(1)

    console.print(f"[bold]📂 Input:[/bold]  {file_path.name} ({format_size(file_path.stat().st_size)})")
    console.print(f"[bold]📝 Output:[/bold] {output_dir}/")
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Extracting payload...", total=100)

            progress.update(task, advance=30, description="[cyan]Parsing header...")
            extracted_files = engine_extract(
                steg_file_path=file_path,
                output_dir=output_dir,
                password=password,
            )
            progress.update(task, advance=70, description="[green]Complete!")

        # Success summary
        console.print()

        table = Table(title="📦 Extracted Files", border_style="green")
        table.add_column("File", style="cyan")
        table.add_column("Size", style="green", justify="right")

        for fp in extracted_files:
            table.add_row(fp.name, format_size(fp.stat().st_size))

        console.print(table)
        console.print(f"\n[green]✅ {len(extracted_files)} file(s) extracted to:[/green] {output_dir}/")

    except PayloadNotFoundError as e:
        console.print(f"[yellow]⚠️ {e}[/yellow]")
        raise typer.Exit(1)
    except DecryptionError as e:
        console.print(f"[red]🔐 {e}[/red]")
        raise typer.Exit(1)
    except IntegrityError as e:
        console.print(f"[red]⚠️ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
