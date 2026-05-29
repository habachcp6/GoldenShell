"""
GoldenShell CLI — Giấu file bên trong file khác, có hỗ trợ mã hóa.

Cú pháp:
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
from rich import print as rprint

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
app = typer.Typer(
    name="goldenshell",
    help=(
        "🐚 [bold cyan]GoldenShell[/bold cyan] — Công cụ [bold]steganography[/bold] giấu file bên trong file khác, có mã hóa AES-256-GCM.\n\n"
        "[bold yellow]Cú pháp chung:[/bold yellow]\n"
        "  goldenshell [bold]hide[/bold]    [dim]<hidden_file...>[/dim] [bold]-c[/bold] [dim]<carrier>[/dim] [[bold]-o[/bold] output] [[bold]-p[/bold] password] [[bold]--no-compress[/bold]]\n"
        "  goldenshell [bold]extract[/bold] [dim]<file>[/dim]       [[bold]-o[/bold] output_dir] [[bold]-p[/bold] password]\n\n"
        "[bold yellow]Ví dụ nhanh:[/bold yellow]\n"
        "  goldenshell hide secret.txt -c report.pdf\n"
        "  goldenshell hide secret.txt -c report.pdf -p \"pass\"\n"
        "  goldenshell extract report.pdf -o ./output/ -p \"pass\""
    ),
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    epilog="Dùng [bold]goldenshell hide --help[/bold] hoặc [bold]goldenshell extract --help[/bold] để xem chi tiết từng lệnh.",
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
    """🐚 GoldenShell - Steganography & Polyglot CLI Tool"""
    if ctx.invoked_subcommand is None:
        show_banner()


@app.command(
    epilog=(
        "[bold yellow]Ví dụ:[/bold yellow]\n\n"
        "  [dim]# Giấu 1 file, output = tên carrier (report.pdf)[/dim]\n"
        "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf\n\n"
        "  [dim]# Giấu 1 file với mã hóa AES-256-GCM[/dim]\n"
        "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf [bold]-p[/bold] \"pass\"\n\n"
        "  [dim]# Giấu 1 file, đặt tên output thủ công[/dim]\n"
        "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf [bold]-o[/bold] output.pdf [bold]-p[/bold] \"pass\"\n\n"
        "  [dim]# Giấu nhiều file cùng lúc[/dim]\n"
        "  goldenshell hide file1.txt file2.zip photo.jpg [bold]-c[/bold] cover.png [bold]-p[/bold] \"pass\"\n\n"
        "  [dim]# Tắt nén (khi hidden file là ZIP/MP4 đã nén sẵn)[/dim]\n"
        "  goldenshell hide archive.zip [bold]-c[/bold] cover.png [bold]--no-compress[/bold]\n\n"
        "  [dim]# Dùng đường dẫn tuyệt đối[/dim]\n"
        "  goldenshell hide /mnt/data/secret.zip [bold]-c[/bold] /home/user/report.pdf"
    )
)
def hide(
    payloads: List[str] = typer.Argument(
        ..., help="[bold]Hidden file(s) — file cần giấu[/bold]. Có thể truyền nhiều file cách nhau bằng dấu cách."
    ),
    carrier: str = typer.Option(
        ..., "--carrier", "-c",
        help="[bold]File carrier[/bold] — file chứa hidden file bên trong (PDF, PNG, JPEG, ZIP, MP3,...). File này vẫn mở bình thường."
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="[bold]File output[/bold] — tên file kết quả. [dim]Mặc định: giữ nguyên tên carrier, lưu vào thư mục hiện tại.[/dim]"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="[bold]Mật khẩu mã hóa[/bold] — dùng AES-256-GCM. [dim]Bỏ qua nếu không cần mã hóa.[/dim]"
    ),
    no_compress: bool = typer.Option(
        False, "--no-compress",
        help="[bold]Tắt nén[/bold] — dùng khi hidden file đã nén sẵn (ZIP, MP4, RAR,...) để tránh tăng kích thước."
    ),
):
    """
    🔒 Giấu một hoặc nhiều hidden file bên trong file carrier.

    File carrier [bold]vẫn mở và hoạt động bình thường[/bold] sau khi nhúng hidden file.
    Hidden file được nén (zlib) và tùy chọn mã hóa (AES-256-GCM) trước khi nhúng.
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
        console.print("[red]❌ Cần ít nhất một hidden file.[/red]")
        raise typer.Exit(1)

    if not carrier_path.exists():
        console.print(f"[red]❌ Không tìm thấy file carrier:[/red] {carrier_path}")
        raise typer.Exit(1)

    for p in payload_paths:
        if not p.exists():
            console.print(f"[red]❌ Không tìm thấy hidden file:[/red] {p}")
            raise typer.Exit(1)

    # Show operation summary
    console.print(f"[bold]📦 Carrier:[/bold] {carrier_path.name} ({format_size(carrier_path.stat().st_size)})")
    for p in payload_paths:
        console.print(f"[bold]🔐 Hidden file:[/bold] {p.name} ({format_size(p.stat().st_size)})")
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
            task = progress.add_task("[cyan]Hiding hidden file...", total=100)

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
            f"[green]✅ Hidden file embedded successfully![/green]\n\n"
            f"  Output:      {output_path}\n"
            f"  Output size: {format_size(output_path.stat().st_size)}\n"
            f"  Encrypted:   {'✅ Yes' if result.is_encrypted else '❌ No'}\n"
            f"  Compressed:  {'✅ Yes' if result.is_compressed else '❌ No'}\n"
            f"  Files:       {result.file_count}\n"
            f"  Checksum:    {result.checksum_hex[:16]}..."
        )
        console.print(Panel(panel_content, title="[bold green]Success[/bold green]", border_style="green"))

    except GoldenShellError as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command(
    epilog=(
        "[bold yellow]Ví dụ:[/bold yellow]\n\n"
        "  [dim]# Trích xuất file không mã hóa vào thư mục ./output/[/dim]\n"
        "  goldenshell extract report.pdf [bold]-o[/bold] ./output/\n\n"
        "  [dim]# Trích xuất file có mã hóa, cung cấp mật khẩu[/dim]\n"
        "  goldenshell extract report.pdf [bold]-o[/bold] ./output/ [bold]-p[/bold] \"pass\"\n\n"
        "  [dim]# Dùng thư mục mặc định (./extracted/)[/dim]\n"
        "  goldenshell extract report.pdf\n\n"
        "  [dim]# Đường dẫn tuyệt đối[/dim]\n"
        "  goldenshell extract /home/user/report.pdf [bold]-o[/bold] /tmp/result/ [bold]-p[/bold] \"pass\""
    )
)
def extract(
    file: str = typer.Argument(
        ..., help="[bold]File nguồn[/bold] — file chứa dữ liệu ẩn (đã được tạo bởi 'goldenshell hide')."
    ),
    output: str = typer.Option(
        "./extracted", "--output", "-o",
        help="[bold]Thư mục đầu ra[/bold] — nơi lưu các file được trích xuất. [dim]Mặc định: ./extracted/[/dim]"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="[bold]Mật khẩu giải mã[/bold] — bắt buộc nếu file được mã hóa bằng AES-256-GCM. [dim]Bỏ qua nếu không có mã hóa.[/dim]"
    ),
):
    """
    📤 Trích xuất file ẩn từ file steganography.

    Khôi phục các file đã nhúng bằng [bold]goldenshell hide[/bold].
    Nếu file có mã hóa, [bold]phải cung cấp đúng mật khẩu[/bold] — sai password sẽ báo lỗi.
    """
    console.print(BANNER_SMALL)
    console.print()

    file_path = Path(file)
    output_dir = Path(output)

    if not file_path.exists():
        console.print(f"[red]❌ Không tìm thấy file:[/red] {file_path}")
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
            task = progress.add_task("[cyan]Extracting hidden file...", total=100)

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
