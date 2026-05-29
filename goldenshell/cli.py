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


# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="goldenshell",
    help=(
        "[bold cyan]GoldenShell[/bold cyan] — Công cụ steganography giấu file bên trong file khác, có mã hóa AES-256-GCM.\n\n"
        "[bold yellow]Cú pháp:[/bold yellow]\n"
        "  goldenshell [bold]hide[/bold]    [dim]<hidden_file...>[/dim] [bold]-c[/bold] [dim]<carrier>[/dim] [[bold]-o[/bold] output] [[bold]-p[/bold] password] [[bold]--no-compress[/bold]]\n"
        "  goldenshell [bold]extract[/bold] [dim]<file>[/dim]           [[bold]-o[/bold] output_dir] [[bold]-p[/bold] password]\n\n"
        "[bold yellow]Ví dụ nhanh:[/bold yellow]\n"
        "  goldenshell hide secret.txt -c report.pdf\n"
        "  goldenshell hide secret.txt -c report.pdf -p \"pass\"\n"
        "  goldenshell extract report.pdf -o ./output/ -p \"pass\"\n\n"
        "[bold yellow]Các tùy chọn phổ biến:[/bold yellow]\n\n"
        "  [bold]-c, --carrier[/bold]      FILE    File carrier chứa hidden file bên trong\n"
        "  [bold]-o, --output[/bold]       PATH    File / thư mục đầu ra\n"
        "  [bold]-p, --password[/bold]     TEXT    Mật khẩu mã hóa / giải mã (AES-256-GCM)\n"
        "  [bold]--no-compress[/bold]              Tắt nén (khi hidden file đã nén sẵn)\n\n"
        "Dùng [bold]goldenshell hide --help[/bold] hoặc [bold]goldenshell extract --help[/bold] để xem đầy đủ."
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
    "[bold yellow]Bảng tùy chọn:[/bold yellow]\n\n"
    "  [bold]-c, --carrier[/bold]    FILE   [required] File carrier (PDF, PNG, JPEG, ZIP, MP3...)\n"
    "  [bold]-o, --output[/bold]     FILE   Tên file output. Mặc định: giữ nguyên tên carrier\n"
    "  [bold]-p, --password[/bold]   TEXT   Mật khẩu mã hóa AES-256-GCM. Bỏ qua nếu không cần\n"
    "  [bold]--no-compress[/bold]           Tắt nén. Dùng khi hidden file đã nén sẵn (ZIP, MP4...)\n\n"
    "[bold yellow]Ví dụ:[/bold yellow]\n\n"
    "  # Giấu 1 file, output = tên carrier\n"
    "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf\n\n"
    "  # Giấu 1 file có mã hóa AES-256-GCM\n"
    "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf [bold]-p[/bold] \"pass\"\n\n"
    "  # Giấu 1 file, đặt tên output thủ công\n"
    "  goldenshell hide secret.txt [bold]-c[/bold] report.pdf [bold]-o[/bold] output.pdf [bold]-p[/bold] \"pass\"\n\n"
    "  # Giấu nhiều file cùng lúc\n"
    "  goldenshell hide file1.txt file2.zip photo.jpg [bold]-c[/bold] cover.png [bold]-p[/bold] \"pass\"\n\n"
    "  # Tắt nén khi hidden file là ZIP/MP4 đã nén sẵn\n"
    "  goldenshell hide archive.zip [bold]-c[/bold] cover.png [bold]--no-compress[/bold]\n\n"
    "  # Dùng đường dẫn tuyệt đối\n"
    "  goldenshell hide /mnt/data/secret.zip [bold]-c[/bold] /home/user/report.pdf"
)


@app.command(epilog=HIDE_EPILOG)
def hide(
    payloads: List[str] = typer.Argument(
        ..., help="Hidden file(s) cần giấu. Có thể truyền nhiều file cách nhau bằng dấu cách."
    ),
    carrier: str = typer.Option(
        ..., "--carrier", "-c",
        help="File carrier — chứa hidden file bên trong (PDF, PNG, JPEG, ZIP, MP3...). File này vẫn mở bình thường."
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Tên file output. Mặc định: giữ nguyên tên carrier, lưu vào thư mục hiện tại."
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="Mật khẩu mã hóa AES-256-GCM. Bỏ qua nếu không cần mã hóa."
    ),
    no_compress: bool = typer.Option(
        False, "--no-compress",
        help="Tắt nén — dùng khi hidden file đã nén sẵn (ZIP, MP4, RAR...) để tránh tăng kích thước."
    ),
):
    """
    Giấu một hoặc nhiều hidden file bên trong file carrier.

    File carrier vẫn mở và hoạt động bình thường sau khi nhúng hidden file.
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
        console.print("[red]Loi: Can it nhat mot hidden file.[/red]")
        raise typer.Exit(1)

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

EXTRACT_EPILOG = (
    "[bold yellow]Bảng tùy chọn:[/bold yellow]\n\n"
    "  [bold]-o, --output[/bold]     DIR    Thư mục lưu file được trích xuất. Mặc định: ./extracted/\n"
    "  [bold]-p, --password[/bold]   TEXT   Mật khẩu giải mã. Bắt buộc nếu file được mã hóa\n\n"
    "[bold yellow]Ví dụ:[/bold yellow]\n\n"
    "  # Trích xuất file không mã hóa vào thư mục ./output/\n"
    "  goldenshell extract report.pdf [bold]-o[/bold] ./output/\n\n"
    "  # Trích xuất file có mã hóa, cung cấp mật khẩu\n"
    "  goldenshell extract report.pdf [bold]-o[/bold] ./output/ [bold]-p[/bold] \"pass\"\n\n"
    "  # Dùng thư mục mặc định (./extracted/)\n"
    "  goldenshell extract report.pdf\n\n"
    "  # Đường dẫn tuyệt đối\n"
    "  goldenshell extract /home/user/report.pdf [bold]-o[/bold] /tmp/result/ [bold]-p[/bold] \"pass\""
)


@app.command(epilog=EXTRACT_EPILOG)
def extract(
    file: str = typer.Argument(
        ..., help="File nguồn — file chứa dữ liệu ẩn (đã được tạo bởi 'goldenshell hide')."
    ),
    output: str = typer.Option(
        "./extracted", "--output", "-o",
        help="Thư mục đầu ra — nơi lưu các file được trích xuất. Mặc định: ./extracted/"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="Mật khẩu giải mã — bắt buộc nếu file được mã hóa bằng AES-256-GCM. Bỏ qua nếu không có mã hóa."
    ),
):
    """
    Trích xuất hidden file từ file steganography.

    Khôi phục các file đã nhúng bằng goldenshell hide.
    Nếu file có mã hóa, phải cung cấp đúng mật khẩu — sai password sẽ báo lỗi.
    """
    console.print(BANNER_SMALL)
    console.print()

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
