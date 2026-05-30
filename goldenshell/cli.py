"""
GoldenShell CLI - Giau file ben trong file khac, co ho tro ma hoa.
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


def _print_main_help():
    """Render the main --help screen — clean CLI style."""
    console.print(BANNER)
    console.print()

    # --- Syntax ---
    console.print("[bold]Cú pháp:[/bold]")
    console.print("  [white]goldenshell hide[/white]    [dim]secret.txt[/dim] -c [dim]report.pdf[/dim] [-o output.pdf] [-p \"pass\"] [--no-compress]")
    console.print("  [white]goldenshell extract[/white] [dim]report.pdf[/dim] [-o ./output/] [-p \"pass\"]")
    console.print()

    # --- Commands ---
    console.print("[bold]Câu lệnh:[/bold]")
    cmds = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    cmds.add_column(style="bold cyan", no_wrap=True)
    cmds.add_column(style="white")
    cmds.add_row("hide", "Giấu file vào trong carrier")
    cmds.add_row("extract", "Trích xuất file đã giấu")
    console.print(cmds)
    console.print()

    # --- Options ---
    console.print("[bold]Tùy chọn:[/bold]")
    opts = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    opts.add_column(style="bold yellow", no_wrap=True)
    opts.add_column(style="white", no_wrap=True)
    opts.add_column(style="dim green", no_wrap=True)
    opts.add_row("-c, --carrier FILE", "File carrier [dim](bắt buộc)[/dim]", "-c report.pdf")
    opts.add_row("-o, --output PATH", "File hoặc thư mục đầu ra", "-o output.pdf")
    opts.add_row("-p, --password TEXT", "Mật khẩu AES-256-GCM", '-p "mypassword"')
    opts.add_row("--no-compress", "Tắt nén zlib", "")
    opts.add_row("--help", "Hiển thị trợ giúp", "")
    console.print(opts)
    console.print()

    # --- Examples ---
    console.print("[bold]Ví dụ:[/bold]")
    console.print("  [green]goldenshell hide secret.txt -c report.pdf[/green]")
    console.print("  [green]goldenshell hide secret.txt -c report.pdf -p \"mypassword\"[/green]")
    console.print("  [green]goldenshell hide secret.txt data.zip -c report.pdf -p \"mypassword\"[/green]")
    console.print("  [green]goldenshell extract report.pdf -o ./output/[/green]")
    console.print("  [green]goldenshell extract report.pdf -o ./output/ -p \"mypassword\"[/green]")
    console.print()

    console.print(
        "[dim]Dùng [bold]goldenshell hide --help[/bold] hoặc "
        "[bold]goldenshell extract --help[/bold] để xem chi tiết.[/dim]"
    )
    console.print()


def _print_hide_help():
    """Render the hide --help screen — clean CLI style."""
    console.print(BANNER_SMALL)
    console.print()

    # --- Syntax ---
    console.print("[bold]Lệnh: hide[/bold] — Giấu file vào trong carrier")
    console.print()
    console.print("[bold]Cú pháp:[/bold]")
    console.print("  goldenshell hide [dim]secret.txt[/dim] -c [dim]report.pdf[/dim] [-o output.pdf] [-p \"pass\"] [--no-compress]")
    console.print()

    # --- Arguments ---
    console.print("[bold]Tham số:[/bold]")
    args = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    args.add_column(style="bold magenta", no_wrap=True)
    args.add_column(style="white", no_wrap=True)
    args.add_column(style="dim green", no_wrap=True)
    args.add_row("PAYLOADS FILE...", "File cần giấu [dim](bắt buộc)[/dim]", "secret.txt data.zip")
    console.print(args)
    console.print()

    # --- Options ---
    console.print("[bold]Tùy chọn:[/bold]")
    opts = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    opts.add_column(style="bold yellow", no_wrap=True)
    opts.add_column(style="white", no_wrap=True)
    opts.add_column(style="dim green", no_wrap=True)
    opts.add_row("-c, --carrier FILE", "File carrier [dim](bắt buộc)[/dim]", "-c report.pdf")
    opts.add_row("-o, --output FILE", "File đầu ra (mặc định: tên carrier)", "-o output.pdf")
    opts.add_row("-p, --password TEXT", "Mật khẩu AES-256-GCM", '-p "mypassword"')
    opts.add_row("--no-compress", "Tắt nén zlib", "")
    opts.add_row("--help", "Hiển thị trợ giúp", "")
    console.print(opts)
    console.print()

    # --- Examples ---
    console.print("[bold]Ví dụ:[/bold]")
    console.print("  [green]goldenshell hide secret.txt -c report.pdf[/green]")
    console.print("  [green]goldenshell hide secret.txt -c report.pdf -p \"mypassword\"[/green]")
    console.print("  [green]goldenshell hide secret.txt -c report.pdf -o output.pdf -p \"mypassword\"[/green]")
    console.print("  [green]goldenshell hide secret.txt data.zip -c report.pdf -p \"mypassword\"[/green]")
    console.print("  [green]goldenshell hide secret.zip -c report.pdf --no-compress[/green]")
    console.print()


def _print_extract_help():
    """Render the extract --help screen — clean CLI style."""
    console.print(BANNER_SMALL)
    console.print()

    # --- Syntax ---
    console.print("[bold]Lệnh: extract[/bold] — Trích xuất file đã giấu")
    console.print()
    console.print("[bold]Cú pháp:[/bold]")
    console.print("  goldenshell extract [dim]report.pdf[/dim] [-o ./output/] [-p \"mypassword\"]")
    console.print()

    # --- Arguments ---
    console.print("[bold]Tham số:[/bold]")
    args = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    args.add_column(style="bold magenta", no_wrap=True)
    args.add_column(style="white", no_wrap=True)
    args.add_column(style="dim green", no_wrap=True)
    args.add_row("FILE", "File chứa dữ liệu ẩn [dim](bắt buộc)[/dim]", "report.pdf")
    console.print(args)
    console.print()

    # --- Options ---
    console.print("[bold]Tùy chọn:[/bold]")
    opts = Table(box=None, show_header=False, padding=(0, 2), pad_edge=False)
    opts.add_column(style="bold yellow", no_wrap=True)
    opts.add_column(style="white", no_wrap=True)
    opts.add_column(style="dim green", no_wrap=True)
    opts.add_row("-o, --output DIR", "Thư mục đầu ra (mặc định: ./extracted/)", "-o ./output/")
    opts.add_row("-p, --password TEXT", "Mật khẩu giải mã AES-256-GCM", '-p "mypassword"')
    opts.add_row("--help", "Hiển thị trợ giúp", "")
    console.print(opts)
    console.print()

    # --- Examples ---
    console.print("[bold]Ví dụ:[/bold]")
    console.print("  [green]goldenshell extract report.pdf -o ./output/[/green]")
    console.print("  [green]goldenshell extract report.pdf -o ./output/ -p \"mypassword\"[/green]")
    console.print("  [green]goldenshell extract report.pdf[/green]")
    console.print()


# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="goldenshell",
    help="[bold cyan]GoldenShell[/bold cyan] — Công cụ steganography giấu file bên trong file khác, có mã hóa AES-256-GCM.",
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="rich",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    help_flag: bool = typer.Option(False, "--help", "-h", is_eager=True, help="Hiển thị trợ giúp"),
):
    """GoldenShell - Steganography CLI Tool"""
    if help_flag:
        _print_main_help()
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        _print_main_help()
        raise typer.Exit(0)


def show_banner():
    """Display the ASCII art banner."""
    console.print(BANNER)


# ---------------------------------------------------------------------------
# hide command
# ---------------------------------------------------------------------------

@app.command()
def hide(
    payloads: List[str] = typer.Argument(
        None, help="Hidden file(s) cần giấu."
    ),
    carrier: Optional[str] = typer.Option(
        None, "--carrier", "-c",
        help="File carrier."
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Tên file output."
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="Mật khẩu mã hóa AES-256-GCM."
    ),
    no_compress: bool = typer.Option(
        False, "--no-compress",
        help="Tắt nén."
    ),
    help_flag: bool = typer.Option(False, "--help", "-h", is_eager=True, help="Hiển thị trợ giúp"),
):
    """
    Giấu một hoặc nhiều hidden file bên trong file carrier.
    """
    if help_flag:
        _print_hide_help()
        raise typer.Exit(0)

    console.print(BANNER_SMALL)
    console.print()

    # Validate required args manually since we disabled typer's auto-help
    if not payloads:
        console.print("[red]Lỗi: Cần ít nhất một hidden file.[/red]")
        console.print("[dim]Dùng [bold]goldenshell hide --help[/bold] để xem hướng dẫn.[/dim]")
        raise typer.Exit(1)

    if not carrier:
        console.print("[red]Lỗi: Thiếu tùy chọn --carrier (-c).[/red]")
        console.print("[dim]Dùng [bold]goldenshell hide --help[/bold] để xem hướng dẫn.[/dim]")
        raise typer.Exit(1)

    carrier_path = Path(carrier)
    payload_paths = [Path(p) for p in payloads]

    # Auto-generate output: same name as carrier, in current directory
    if output:
        output_path = Path(output)
    else:
        output_path = Path(carrier_path.name)

    if not carrier_path.exists():
        console.print(f"[red]Lỗi: Không tìm thấy file carrier:[/red] {carrier_path}")
        raise typer.Exit(1)

    for p in payload_paths:
        if not p.exists():
            console.print(f"[red]Lỗi: Không tìm thấy hidden file:[/red] {p}")
            raise typer.Exit(1)

    # Show operation summary table
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Label", style="bold")
    summary.add_column("Value")
    summary.add_row("Carrier     :", f"{carrier_path.name}  ({format_size(carrier_path.stat().st_size)})")
    for p in payload_paths:
        summary.add_row("Hidden file :", f"{p.name}  ({format_size(p.stat().st_size)})")
    summary.add_row("Output      :", str(output_path))
    summary.add_row("Mã hóa      :", "AES-256-GCM" if password else "Không")
    summary.add_row("Nén         :", "Không" if no_compress else "Có (zlib)")
    console.print(summary)
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Đang nhúng hidden file...", total=100)

            progress.update(task, advance=30, description="[cyan]Đang đọc file...")
            result = engine_hide(
                carrier_path=carrier_path,
                payload_paths=payload_paths,
                output_path=output_path,
                password=password,
                compress_payload=not no_compress,
            )
            progress.update(task, advance=70, description="[green]Hoàn thành!")

        # Success summary
        console.print()
        result_table = Table(show_header=False, box=None, padding=(0, 2))
        result_table.add_column("Label", style="bold green")
        result_table.add_column("Value")
        result_table.add_row("Output      :", str(output_path))
        result_table.add_row("Kích thước  :", format_size(output_path.stat().st_size))
        result_table.add_row("Mã hóa      :", "Có" if result.is_encrypted else "Không")
        result_table.add_row("Nén         :", "Có" if result.is_compressed else "Không")
        result_table.add_row("Số file     :", str(result.file_count))
        result_table.add_row("Checksum    :", f"{result.checksum_hex[:16]}...")
        console.print(Panel(
            result_table,
            title="[bold green]Nhúng hidden file thành công[/bold green]",
            border_style="green"
        ))

    except GoldenShellError as e:
        console.print(f"[red]Lỗi:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Lỗi không xác định:[/red] {e}")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# extract command
# ---------------------------------------------------------------------------

@app.command()
def extract(
    file: Optional[str] = typer.Argument(
        None, help="File nguồn chứa dữ liệu ẩn."
    ),
    output: str = typer.Option(
        "./extracted", "--output", "-o",
        help="Thư mục đầu ra."
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="Mật khẩu giải mã AES-256-GCM."
    ),
    help_flag: bool = typer.Option(False, "--help", "-h", is_eager=True, help="Hiển thị trợ giúp"),
):
    """
    Trích xuất hidden file từ file steganography.
    """
    if help_flag:
        _print_extract_help()
        raise typer.Exit(0)

    console.print(BANNER_SMALL)
    console.print()

    if not file:
        console.print("[red]Lỗi: Cần cung cấp file nguồn.[/red]")
        console.print("[dim]Dùng [bold]goldenshell extract --help[/bold] để xem hướng dẫn.[/dim]")
        raise typer.Exit(1)

    file_path = Path(file)
    output_dir = Path(output)

    if not file_path.exists():
        console.print(f"[red]Lỗi: Không tìm thấy file:[/red] {file_path}")
        raise typer.Exit(1)

    # Show summary
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Label", style="bold")
    summary.add_column("Value")
    summary.add_row("Input  :", f"{file_path.name}  ({format_size(file_path.stat().st_size)})")
    summary.add_row("Output :", str(output_dir) + "/")
    console.print(summary)
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Đang trích xuất hidden file...", total=100)

            progress.update(task, advance=30, description="[cyan]Đang phân tích header...")
            extracted_files = engine_extract(
                steg_file_path=file_path,
                output_dir=output_dir,
                password=password,
            )
            progress.update(task, advance=70, description="[green]Hoàn thành!")

        # Success summary
        console.print()

        table = Table(title="Các file đã trích xuất", border_style="green")
        table.add_column("File", style="cyan")
        table.add_column("Kích thước", style="green", justify="right")

        for fp in extracted_files:
            table.add_row(fp.name, format_size(fp.stat().st_size))

        console.print(table)
        console.print(f"\n[green]{len(extracted_files)} file(s) được trích xuất vào:[/green] {output_dir}/")

    except PayloadNotFoundError as e:
        console.print(f"[yellow]Cảnh báo: {e}[/yellow]")
        raise typer.Exit(1)
    except DecryptionError as e:
        console.print(f"[red]Lỗi giải mã: {e}[/red]")
        raise typer.Exit(1)
    except IntegrityError as e:
        console.print(f"[red]Lỗi toàn vẹn dữ liệu: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Lỗi không xác định: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
