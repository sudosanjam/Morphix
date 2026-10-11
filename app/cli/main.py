"""Morphix Command-Line Interface."""

import sys
import os
import json
import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from app.config import config, VERSION, APP_NAME
from app.core.detector import detect_file_format, canonical_format
from app.core.registry import registry
from app.core.planner import plan_conversion
from app.core.converter import execute_conversion
from app.core.metadata import inspect_file, format_bytes
from app.services.presets import presets
from app.services.history import history
from app.services.diagnostics import run_diagnostics

app = typer.Typer(
    name="morphix",
    help="Universal Offline File Conversion, Optimization, and Processing Suite",
    no_args_is_help=True
)
console = Console()
err_console = Console(stderr=True)


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]{APP_NAME}[/bold cyan] version [bold white]{VERSION}[/bold white]")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show Morphix version and exit."
    )
):
    pass


@app.command("convert")
def convert_cmd(
    source: Path = typer.Argument(..., help="Path to the source file to convert", exists=True),
    to: str = typer.Option(..., "--to", "-t", help="Target output format (e.g. webp, mp3, pdf, csv)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output file or directory"),
    preset: Optional[str] = typer.Option(None, "--preset", "-p", help="Apply a pre-configured preset"),
    quality: Optional[int] = typer.Option(None, "--quality", "-q", help="Quality (1-100) for lossy images/audio"),
    width: Optional[int] = typer.Option(None, "--width", "-w", help="Target width in pixels (images)"),
    height: Optional[int] = typer.Option(None, "--height", "-h", help="Target height in pixels (images)"),
    bitrate: Optional[str] = typer.Option(None, "--bitrate", "-b", help="Audio bitrate (e.g. 192k, 320k)"),
    sample_rate: Optional[int] = typer.Option(None, "--sample-rate", help="Audio sample rate (e.g. 44100, 48000)"),
    channels: Optional[str] = typer.Option(None, "--channels", help="Audio channels (mono, stereo, preserve)"),
    loudness_norm: bool = typer.Option(False, "--loudnorm", help="Apply EBU R128 loudness normalization"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing output files"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON result"),
):
    """Convert a single file with optional advanced format-specific settings."""
    settings = {}

    # Apply preset if specified
    if preset:
        p_obj = presets.get_preset(preset)
        if not p_obj:
            err_console.print(f"[bold red]Error:[/bold red] Preset '{preset}' not found.")
            raise typer.Exit(code=2)
        settings.update(p_obj.settings)
        if not to:
            to = p_obj.target_format

    # Command line options override preset values
    if quality is not None:
        settings["quality"] = quality
    if width is not None:
        settings["width"] = width
    if height is not None:
        settings["height"] = height
    if bitrate is not None:
        settings["bitrate"] = bitrate
    if sample_rate is not None:
        settings["sample_rate"] = sample_rate
    if channels is not None:
        settings["channels"] = channels
    if loudness_norm:
        settings["loudness_norm"] = True

    overwrite_policy = "overwrite" if overwrite else "rename"

    try:
        planned = plan_conversion(
            source_path=source,
            target_format=to,
            output_destination=output,
            raw_settings=settings,
            overwrite_policy=overwrite_policy
        )
    except Exception as e:
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            err_console.print(f"[bold red]Planning Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    if not json_output:
        console.print(f"[dim]Engine:[/dim] [cyan]{planned.route.engine_name}[/cyan] | [dim]Target:[/dim] [green]{planned.target_path.name}[/green]")
        if planned.warnings:
            for w in planned.warnings:
                console.print(f"[yellow]Warning:[/yellow] {w}")

    # Run conversion with progress bar
    try:
        if json_output:
            result = execute_conversion(planned)
            print(json.dumps({
                "status": "success",
                **result.to_dict()
            }))
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task_id = progress.add_task(f"Converting {source.name}...", total=100)

                def update_cb(pct: int, msg: str):
                    progress.update(task_id, completed=pct, description=msg)

                result = execute_conversion(planned, progress_callback=update_cb)

            console.print(f"[bold green]Converted successfully:[/bold green] {result.output_path}")
            console.print(f"Size: [dim]{format_bytes(result.source_size_bytes)} -> {format_bytes(result.output_size_bytes)}[/dim] | Duration: [cyan]{result.duration_seconds:.2f}s[/cyan]")

    except Exception as e:
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            err_console.print(f"[bold red]Conversion Failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("batch")
def batch_cmd(
    source_dir: Path = typer.Argument(..., help="Source directory containing files to convert", exists=True),
    to: str = typer.Option(..., "--to", "-t", help="Target output format"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output directory"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Traverse subdirectories recursively"),
    pattern: str = typer.Option("*", "--pattern", help="Filename pattern to match (e.g. '*.png')"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing files"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON summary"),
):
    """Batch convert all matching files in a folder."""
    if not source_dir.is_dir():
        err_console.print(f"[bold red]Error:[/bold red] '{source_dir}' is not a directory.")
        raise typer.Exit(code=2)

    files = list(source_dir.rglob(pattern)) if recursive else list(source_dir.glob(pattern))
    files = [f for f in files if f.is_file()]

    if not files:
        if json_output:
            print(json.dumps({"status": "success", "total": 0, "converted": 0, "results": []}))
        else:
            console.print("[yellow]No matching files found.[/yellow]")
        return

    out_dir = output or (source_dir / "converted")
    out_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    results_list = []

    if not json_output:
        console.print(f"Found [bold cyan]{len(files)}[/bold cyan] files. Starting batch conversion...")

    for f in files:
        try:
            planned = plan_conversion(
                source_path=f,
                target_format=to,
                output_destination=out_dir,
                overwrite_policy="overwrite" if overwrite else "rename"
            )
            res = execute_conversion(planned)
            success_count += 1
            results_list.append({"file": str(f), "status": "success", "output": str(res.output_path)})
            if not json_output:
                console.print(f"  [green]OK[/green] {f.name} -> {res.output_path.name}")
        except Exception as e:
            fail_count += 1
            results_list.append({"file": str(f), "status": "failed", "error": str(e)})
            if not json_output:
                console.print(f"  [red]FAIL[/red] {f.name}: {e}")

    if json_output:
        print(json.dumps({
            "status": "completed",
            "total": len(files),
            "success": success_count,
            "failed": fail_count,
            "results": results_list
        }))
    else:
        console.print(f"\n[bold]Batch Completed:[/bold] [green]{success_count} succeeded[/green], [red]{fail_count} failed[/red].")


@app.command("inspect")
def inspect_cmd(
    file_path: Path = typer.Argument(..., help="Path to file to inspect", exists=True),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON metadata"),
):
    """Deep inspect metadata, dimensions, streams, and properties of any file."""
    try:
        data = inspect_file(file_path)
    except Exception as e:
        err_console.print(f"[bold red]Inspection Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(data, indent=2))
        return

    table = Table(title=f"File Inspection: {data['name']}", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="bold white")
    table.add_column("Value", style="green")

    table.add_row("Format", data["format"].upper())
    table.add_row("Category / Family", data["family"].capitalize())
    table.add_row("File Size", data["size_formatted"])
    table.add_row("Detection Method", data["detected_by"])

    if data.get("mismatch_warning"):
        table.add_row("Warning", f"[yellow]{data['mismatch_warning']}[/yellow]")

    for k, v in data.get("properties", {}).items():
        if v is not None:
            table.add_row(k.replace("_", " ").capitalize(), str(v))

    console.print(table)


@app.command("formats")
def formats_cmd(
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="Inspect available destinations for a file"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON format list"),
):
    """List all supported formats or targets for a specific input file."""
    if input_file:
        detection = detect_file_format(input_file)
        targets = registry.get_available_targets(detection.format_id)
        if json_output:
            print(json.dumps({
                "source_format": detection.format_id,
                "available_targets": targets
            }, indent=2))
        else:
            table = Table(title=f"Available Targets for '{input_file.name}' ({detection.format_id.upper()})")
            table.add_column("Format", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Engine", style="green")
            table.add_column("Lossiness", style="yellow")
            for t in targets:
                table.add_row(t["format"].upper(), t["name"], t["engine"], t["lossiness"])
            console.print(table)
    else:
        all_fmts = registry.get_all_supported_formats()
        if json_output:
            print(json.dumps(all_fmts, indent=2))
        else:
            table = Table(title="Morphix Supported Formats & Runtime Availability")
            table.add_column("Format", style="cyan")
            table.add_column("Family", style="magenta")
            table.add_column("Name", style="white")
            table.add_column("Available", style="bold")
            for f, info in all_fmts.items():
                avail_str = "[green]Yes[/green]" if info["available"] else "[red]Missing Engine[/red]"
                table.add_row(f.upper(), info["family"].capitalize(), info["name"], avail_str)
            console.print(table)


@app.command("preset")
def preset_cmd(
    action: str = typer.Argument("list", help="'list', 'show', or 'delete'"),
    preset_id: Optional[str] = typer.Argument(None, help="Preset identifier"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """List or inspect pre-configured conversion presets."""
    if action == "list":
        p_list = presets.list_presets()
        if json_output:
            print(json.dumps([p.model_dump() for p in p_list], indent=2))
        else:
            table = Table(title="Available Morphix Presets")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="bold white")
            table.add_column("Category", style="magenta")
            table.add_column("Format", style="green")
            table.add_column("Built-in", style="dim")
            for p in p_list:
                table.add_row(p.id, p.name, p.category, p.target_format.upper(), "Yes" if p.is_builtin else "Custom")
            console.print(table)
    elif action == "show" and preset_id:
        p = presets.get_preset(preset_id)
        if not p:
            err_console.print(f"[red]Preset '{preset_id}' not found.[/red]")
            raise typer.Exit(code=1)
        if json_output:
            print(json.dumps(p.model_dump(), indent=2))
        else:
            console.print(Panel(
                f"[bold]{p.name}[/bold]\n"
                f"Target: [green]{p.target_format.upper()}[/green]\n"
                f"Description: {p.description}\n"
                f"Settings: [dim]{json.dumps(p.settings, indent=2)}[/dim]",
                title=f"Preset: {p.id}"
            ))


@app.command("history")
def history_cmd(
    action: str = typer.Argument("list", help="'list' or 'clear'"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to show"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """View or clear conversion history."""
    if action == "clear":
        c = history.clear_history()
        console.print(f"[green]Cleared {c} history records.[/green]")
    else:
        entries = history.list_history(limit=limit)
        if json_output:
            print(json.dumps(entries, indent=2))
        else:
            table = Table(title="Recent Conversion History")
            table.add_column("ID", style="dim")
            table.add_column("Source", style="white")
            table.add_column("Target Format", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Duration", style="yellow")
            for e in entries:
                status_color = "green" if e["status"] == "completed" else "red"
                dur = f"{e['duration_seconds']:.2f}s" if e.get("duration_seconds") else "N/A"
                src_name = Path(e["source_path"]).name
                table.add_row(e["id"][:8], src_name, e["target_format"].upper(), f"[{status_color}]{e['status']}[/{status_color}]", dur)
            console.print(table)


@app.command("doctor")
def doctor_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output JSON diagnostic report"),
):
    """Run comprehensive system diagnostics, engine verification, and permission checks."""
    diag = run_diagnostics()
    if json_output:
        print(json.dumps(diag, indent=2))
        return

    console.print(f"[bold cyan]{APP_NAME}[/bold cyan] [bold white]Doctor Diagnostic Report[/bold white]")
    console.print(f"OS: [white]{diag['system']['os']} {diag['system']['os_release']} ({diag['system']['architecture']})[/white]")
    console.print(f"Python: [white]{diag['system']['python_version']}[/white] at [dim]{diag['system']['python_executable']}[/dim]")
    console.print(f"Free Disk Space: [green]{diag['storage']['disk_free_formatted']}[/green] / {diag['storage']['disk_total_formatted']}")

    table = Table(title="Conversion Engines Status", show_header=True)
    table.add_column("Engine", style="bold white")
    table.add_column("Status", style="bold")
    table.add_column("Version", style="cyan")
    table.add_column("Path / Binary", style="dim")

    for eng in diag["capabilities"]["engines"]:
        status_str = "[green]Available[/green]" if eng["available"] else "[yellow]Not Installed[/yellow]"
        ver_str = eng["version"] or "N/A"
        path_str = eng["path"] or "None"
        table.add_row(eng["display_name"], status_str, ver_str, path_str)

    console.print(table)
    console.print(f"Active Conversion Routes: [bold green]{diag['capabilities']['active_routes']}[/bold green] / {diag['capabilities']['total_routes']}\n")


@app.command("serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(7474, "--port", "-p", help="Port number"),
    open_browser: bool = typer.Option(True, "--open-browser/--no-open-browser", help="Open browser on launch"),
):
    """Launch the local offline web GUI server."""
    import uvicorn
    import webbrowser

    console.print(f"[bold cyan]{APP_NAME}[/bold cyan] Web GUI starting at [bold green]http://{host}:{port}[/bold green]...")
    console.print("[dim]Press Ctrl+C to stop the server.[/dim]")

    if open_browser:
        def _open():
            import time
            time.sleep(1.2)
            try:
                webbrowser.open(f"http://{host}:{port}")
            except Exception:
                pass
        import threading
        threading.Thread(target=_open, daemon=True).start()

    from app.main import app as fastapi_app
    uvicorn.run(fastapi_app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    app()
