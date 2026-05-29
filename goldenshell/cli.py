"""
GoldenShell CLI - Giau file ben trong file khac, co ho tro ma hoa.

Cu phap:
    goldenshell hide <hidden_file...> -c <carrier> [-o output] [-p password]
    goldenshell extract <file> -o <output_dir> [-p password]
"""

import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

from .banner import BANNER, BANNER_SMALL
from .core.engine import (
    hide as engine_hide,
    extract as engine_extract,
    GoldenShellError,
    PayloadNotFoundError,
    DecryptionError,
    IntegrityError,
)

console = Console()

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="goldenshell",
    help=(
        "[bold cyan]GoldenShell[/bold cyan] — Cong cu steganography giau file ben trong file khac, co ma hoa AES-256-GCM.\n\n"
        "[bold yellow]Cu phap:[/bold yellow]\n"
        "  goldenshell [bold]hide[/bold]    [dim]<hidden_file...>[/dim] [bold]-c[/bold] [dim]<carrier>[/dim] [[bold]-o[/bold] output] [[bold]-p[/bold] password] [[bold]--no-compress[/bold]]\n"
        "  goldenshell [bold]extract[/bold] [dim]<file>[/dim]           [[bold]-o[/bold] output_dir] [[bold]-p[/bold] password]\n\n"
        "[bold yellow]Vi du nhanh:[/bold yellow]\n"
        "  goldenshell hide secret.txt -c report.pdf\n"
        "  goldenshell hide secret.txt -c report.pdf -p \"pass\"\n"
        "  goldenshell extract report.pdf -o ./output/ -p \"pass\"\n\n"
        "[bold yellow]Cac tuy chon pho bien:[/bold yellow]\n\n"
        "  [bold]-c, --carrier[/bold]      FILE    File carrier chua hidden file ben trong\n"
        "  [bold]-o, --output[/bold]       PATH    File/thu muc dau ra\n"
        "  [bold]-p, --password[/bold]     TEXT    Mat khau ma hoa / giai ma (AES-256-GCM)\n"
        "  [bold]--no-compress[/bold]              Tat nen (khi hidden file da nen san)\n\n"
        "Dung [bold]goldenshell hide --help[/bold] hoac [bold]goldenshell extract --help[/bold] de xem day du."
    ),
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """GoldenShell - Steganography CLI Tool"""
    if ctx.invoked_subcommand is None:
        show_banner()


def show_banner():
    """Display the ASCII art banner."""
    console.print(BANNER)


# ---------------------------------------------------------------------------
# hide command
# ---------------------------------------------------------------------------

HIDE_EPILOG = (
    "[bold yellow]Bang tuy chon:[/bold yellow]\n\n"
    "  [bold]-c, --carrier[/bold]    FILE   [required] File carrier (PDF, PNG, JPEG, ZIP, MP3...)\n"
    "  [bold]-o, --output[/bold]     FILE   Ten file output. Mac dinh: giu nguyen ten carrier\n"
    "  [bold]-p, --password[/bold]   TEXT   Mat khau ma hoa AES-256-GCM. Bo qua neu khong can\n"
    "  [bold]--no-compress[/bold]           Tat nen. Dung khi hidden file da nen san (ZIP, MP4...)\n\n"
    "[bold yellow]Vi du:[/bold yellow]\n\n"
    "  # Giau 1 file, output = ten carrier\n"
    "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf\n\n"
    "  # Giau 1 file co ma hoa AES-256-GCM\n"
    "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf [bold]-p[/bold] \"pass\"\n\n"
    "  # Giau 1 file, dat ten output thu cong\n"
    "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf [bold]-o[/bold] output.pdf [bold]-p[/bold] \"pass\"\n\n"
    "  # Giau nhieu file cung luc\n"
    "  goldenshell hide file1.txt file2.zip photo.jpg [bold]-c[/bold] cover.png [bold]-p[/bold] \"pass\"\n\n"
    "  # Tat nen khi hidden file la ZIP/MP4 da nen san\n"
    "  goldenshell hide archive.zip [bold]-c[/bold] cover.png [bold]--no-compress[/bold]\n\n"
    "  # Dung duong dan tuyet doi\n"
    "  goldenshell hide /mnt/data/secret.zip [bold]-c[/bold] /home/user/report.pdf"
)


@app.command(epilog=HIDE_EPILOG)
def hide(
    payloads: List[str] = typer.Argument(
        ..., help="Hidden file(s) can giau. Co the truyen nhieu file cach nhau bang dau cach."
    ),
    carrier: str = typer.Option(
        ..., "--carrier", "-c",
        help="File carrier — chua hidden file ben trong (PDF, PNG, JPEG, ZIP, MP3...). File nay van mo binh thuong."
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Ten file output. Mac dinh: giu nguyen ten carrier, luu vao thu muc hien tai."
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="Mat khau ma hoa AES-256-GCM. Bo qua neu khong can ma hoa."
    ),
    no_compress: bool = typer.Option(
        False, "--no-compress",
        help="Tat nen — dung khi hidden file da nen san (ZIP, MP4, RAR...) de tranh tang kich thuoc."
    ),
):
    """
    Giau mot hoac nhieu hidden file ben trong file carrier.

    File carrier van mo va hoat dong binh thuong sau khi nhung hidden file.
    Hidden file duoc nen (zlib) va tuy chon ma hoa (AES-256-GCM) truoc khi nhung.
    """
    console.print(BANNER_SMALL)
    console.print()

    carrier_path = Path(carrier)
    payload_paths = [Path(p) for p in payloads]

    # Auto-generate output: same name as carrier, in current directory
    if output:
        output_path = Path(output)
    else:
        output_path = Path(carrier_path.name)

    # Validate
    if not payload_paths:
        console.print("[red]Error: Can it nhat mot hidden file.[/red]")
        raise typer.Exit(1)

    if not carrier_path.exists():
        console.print(f"[red]Error: Khong tim thay file carrier:[/red] {carrier_path}")
        raise typer.Exit(1)

    for p in payload_paths:
        if not p.exists():
            console.print(f"[red]Error: Khong tim thay hidden file:[/red] {p}")
            raise typer.Exit(1)

    # Show operation summary table
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Label", style="bold")
    summary.add_column("Value")
    summary.add_row("Carrier   :", f"{carrier_path.name}  ({format_size(carrier_path.stat().st_size)})")
    for p in payload_paths:
        summary.add_row("Hidden file:", f"{p.name}  ({format_size(p.stat().st_size)})")
    summary.add_row("Output    :", str(output_path))
    summary.add_row("Encryption:", "AES-256-GCM" if password else "None")
    summary.add_row("Compress  :", "No" if no_compress else "Yes (zlib)")
    console.print(summary)
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Embedding hidden file...", total=100)

            progress.update(task, advance=30, description="[cyan]Reading files...")
            result = engine_hide(
                carrier_path=carrier_path,
                payload_paths=payload_paths,
                output_path=output_path,
                password=password,
                compress_payload=not no_compress,
            )
            progress.update(task, advance=70, description="[green]Done!")

        # Success summary
        console.print()
        result_table = Table(show_header=False, box=None, padding=(0, 2))
        result_table.add_column("Label", style="bold green")
        result_table.add_column("Value")
        result_table.add_row("Output     :", str(output_path))
        result_table.add_row("Output size:", format_size(output_path.stat().st_size))
        result_table.add_row("Encrypted  :", "Yes" if result.is_encrypted else "No")
        result_table.add_row("Compressed :", "Yes" if result.is_compressed else "No")
        result_table.add_row("Files      :", str(result.file_count))
        result_table.add_row("Checksum   :", f"{result.checksum_hex[:16]}...")
        console.print(Panel(result_table, title="[bold green]Hidden file embedded successfully[/bold green]", border_style="green"))

    except GoldenShellError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# extract command
# ---------------------------------------------------------------------------

EXTRACT_EPILOG = (
    "[bold yellow]Bang tuy chon:[/bold yellow]\n\n"
    "  [bold]-o, --output[/bold]     DIR    Thu muc luu file duoc trich xuat. Mac dinh: ./extracted/\n"
    "  [bold]-p, --password[/bold]   TEXT   Mat khau giai ma. Bat buoc neu file duoc ma hoa\n\n"
    "[bold yellow]Vi du:[/bold yellow]\n\n"
    "  # Trich xuat file khong ma hoa vao thu muc ./output/\n"
    "  goldenshell extract report.pdf [bold]-o[/bold] ./output/\n\n"
    "  # Trich xuat file co ma hoa, cung cap mat khau\n"
    "  goldenshell extract report.pdf [bold]-o[/bold] ./output/ [bold]-p[/bold] \"pass\"\n\n"
    "  # Dung thu muc mac dinh (./extracted/)\n"
    "  goldenshell extract report.pdf\n\n"
    "  # Duong dan tuyet doi\n"
    "  goldenshell extract /home/user/report.pdf [bold]-o[/bold] /tmp/result/ [bold]-p[/bold] \"pass\""
)


@app.command(epilog=EXTRACT_EPILOG)
def extract(
    file: str = typer.Argument(
        ..., help="File nguon — file chua du lieu an (da duoc tao boi 'goldenshell hide')."
    ),
    output: str = typer.Option(
        "./extracted", "--output", "-o",
        help="Thu muc dau ra — noi luu cac file duoc trich xuat. Mac dinh: ./extracted/"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="Mat khau giai ma — bat buoc neu file duoc ma hoa bang AES-256-GCM. Bo qua neu khong co ma hoa."
    ),
):
    """
    Trich xuat hidden file tu file steganography.

    Khoi phuc cac file da nhung bang goldenshell hide.
    Neu file co ma hoa, phai cung cap dung mat khau — sai password se bao loi.
    """
    console.print(BANNER_SMALL)
    console.print()

    file_path = Path(file)
    output_dir = Path(output)

    if not file_path.exists():
        console.print(f"[red]Error: Khong tim thay file:[/red] {file_path}")
        raise typer.Exit(1)

    # Show summary
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Label", style="bold")
    summary.add_column("Value")
    summary.add_row("Input :", f"{file_path.name}  ({format_size(file_path.stat().st_size)})")
    summary.add_row("Output:", str(output_dir) + "/")
    console.print(summary)
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Extracting hidden file...", total=100)

            progress.update(task, advance=30, description="[cyan]Parsing header...")
            extracted_files = engine_extract(
                steg_file_path=file_path,
                output_dir=output_dir,
                password=password,
            )
            progress.update(task, advance=70, description="[green]Done!")

        # Success summary
        console.print()

        table = Table(title="Extracted Files", border_style="green")
        table.add_column("File", style="cyan")
        table.add_column("Size", style="green", justify="right")

        for fp in extracted_files:
            table.add_row(fp.name, format_size(fp.stat().st_size))

        console.print(table)
        console.print(f"\n[green]{len(extracted_files)} file(s) extracted to:[/green] {output_dir}/")

    except PayloadNotFoundError as e:
        console.print(f"[yellow]Warning: {e}[/yellow]")
        raise typer.Exit(1)
    except DecryptionError as e:
        console.print(f"[red]Decryption error: {e}[/red]")
        raise typer.Exit(1)
    except IntegrityError as e:
        console.print(f"[red]Integrity error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
