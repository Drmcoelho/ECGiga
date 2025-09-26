"""Asset management and downloads CLI."""

from __future__ import annotations
import pathlib
from typing import Optional

import typer
from rich import print
from rich.panel import Panel

from .logging_utils import get_logger

logger = get_logger(__name__)

assets_app = typer.Typer(help="Asset management and downloads")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


@assets_app.command()
def download(
    asset_type: str = typer.Argument(..., help="Asset type: ecg_images, ecg_datasets"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
    manifest: Optional[str] = typer.Option(None, "--manifest", help="Custom manifest file"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Maximum number of assets to download"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
):
    """Download assets from manifest."""
    logger.info(f"Downloading assets: {asset_type}")
    
    # Determine manifest file
    if manifest:
        manifest_path = pathlib.Path(manifest)
    else:
        manifest_path = REPO_ROOT / "assets" / "manifest" / f"{asset_type}.v1.jsonl"
    
    if not manifest_path.exists():
        typer.echo(f"Manifest não encontrado: {manifest_path}", err=True)
        raise typer.Exit(code=2)
    
    # Determine output directory
    if output_dir:
        output_path = pathlib.Path(output_dir)
    else:
        output_path = REPO_ROOT / "assets" / "downloaded" / asset_type
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.debug(f"Manifest: {manifest_path}")
    logger.debug(f"Output: {output_path}")
    logger.debug(f"Limit: {limit}, Force: {force}")
    
    # Read manifest
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse JSONL format
        import json
        entries = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON on line {line_num}: {e}")
        
        if limit:
            entries = entries[:limit]
        
        total = len(entries)
        if total == 0:
            typer.echo("Nenhum asset encontrado no manifest.")
            return
        
        print(Panel.fit(f"[bold]Downloading {total} assets to {output_path}[/]"))
        
        # Download placeholder (actual implementation would use requests)
        downloaded = 0
        skipped = 0
        failed = 0
        
        for i, entry in enumerate(entries, 1):
            asset_id = entry.get('id', f'asset_{i}')
            filename = entry.get('filename', f'{asset_id}.dat')
            url = entry.get('url', 'https://example.com/placeholder')
            
            output_file = output_path / filename
            
            # Check if file exists
            if output_file.exists() and not force:
                logger.debug(f"Skipping existing file: {filename}")
                skipped += 1
                continue
            
            # Placeholder download
            typer.echo(f"[{i}/{total}] Downloading {filename}...")
            
            try:
                # This would be actual download logic:
                # response = requests.get(url)
                # output_file.write_bytes(response.content)
                
                # For now, create placeholder file
                output_file.write_text(f"Placeholder for {asset_id}\nURL: {url}")
                downloaded += 1
                
            except Exception as e:
                logger.error(f"Failed to download {filename}: {e}")
                failed += 1
        
        # Summary
        print(Panel.fit(
            f"[bold green]Download complete![/]\n"
            f"Downloaded: {downloaded}\n"
            f"Skipped: {skipped}\n"
            f"Failed: {failed}"
        ))
        
        logger.info(f"Download summary: {downloaded} downloaded, {skipped} skipped, {failed} failed")
        
    except Exception as e:
        typer.echo(f"Erro ao processar manifest: {e}", err=True)
        raise typer.Exit(code=2)


@assets_app.command()
def list_manifests():
    """List available asset manifests."""
    logger.info("Listing available manifests")
    
    manifests_dir = REPO_ROOT / "assets" / "manifest"
    
    if not manifests_dir.exists():
        typer.echo("Diretório de manifests não encontrado.")
        return
    
    manifest_files = list(manifests_dir.glob("*.jsonl"))
    
    if not manifest_files:
        typer.echo("Nenhum manifest encontrado.")
        return
    
    print(Panel.fit("[bold]Available Asset Manifests[/]"))
    
    for manifest in sorted(manifest_files):
        try:
            # Count entries in manifest
            with open(manifest, 'r', encoding='utf-8') as f:
                count = sum(1 for line in f if line.strip())
            
            asset_type = manifest.stem.replace('.v1', '')
            typer.echo(f"• {asset_type}: {count} assets ({manifest.name})")
            
        except Exception as e:
            typer.echo(f"• {manifest.name}: Error reading ({e})")
            logger.warning(f"Failed to read manifest {manifest}: {e}")


@assets_app.command()
def verify(
    asset_type: str = typer.Argument(..., help="Asset type to verify"),
    assets_dir: Optional[str] = typer.Option(None, "--dir", help="Assets directory to verify"),
):
    """Verify downloaded assets integrity."""
    logger.info(f"Verifying assets: {asset_type}")
    
    # Determine assets directory
    if assets_dir:
        assets_path = pathlib.Path(assets_dir)
    else:
        assets_path = REPO_ROOT / "assets" / "downloaded" / asset_type
    
    if not assets_path.exists():
        typer.echo(f"Diretório de assets não encontrado: {assets_path}", err=True)
        raise typer.Exit(code=2)
    
    # Count files
    files = list(assets_path.glob("*"))
    files = [f for f in files if f.is_file()]
    
    total_files = len(files)
    total_size = sum(f.stat().st_size for f in files)
    
    print(Panel.fit(
        f"[bold]Asset Verification: {asset_type}[/]\n"
        f"Directory: {assets_path}\n"
        f"Files: {total_files}\n"
        f"Total size: {total_size / (1024*1024):.1f} MB"
    ))
    
    # Basic integrity checks
    empty_files = [f for f in files if f.stat().st_size == 0]
    if empty_files:
        typer.echo(f"[bold yellow]Warning:[/] {len(empty_files)} empty files found")
        for empty in empty_files[:5]:  # Show first 5
            typer.echo(f"  • {empty.name}")
        if len(empty_files) > 5:
            typer.echo(f"  ... and {len(empty_files) - 5} more")
    
    logger.info(f"Verification complete: {total_files} files, {total_size} bytes")


@assets_app.command()  
def clean(
    asset_type: str = typer.Argument(..., help="Asset type to clean"),
    confirm: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
):
    """Clean downloaded assets."""
    logger.info(f"Cleaning assets: {asset_type}")
    
    assets_path = REPO_ROOT / "assets" / "downloaded" / asset_type
    
    if not assets_path.exists():
        typer.echo(f"Diretório não encontrado: {assets_path}")
        return
    
    files = list(assets_path.glob("*"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        typer.echo("Nenhum arquivo para limpar.")
        return
    
    total_size = sum(f.stat().st_size for f in files)
    
    if not confirm:
        response = typer.confirm(
            f"Remove {len(files)} files ({total_size / (1024*1024):.1f} MB) from {assets_path}?"
        )
        if not response:
            typer.echo("Operação cancelada.")
            return
    
    # Remove files
    removed = 0
    failed = 0
    
    for file_path in files:
        try:
            file_path.unlink()
            removed += 1
        except Exception as e:
            logger.error(f"Failed to remove {file_path}: {e}")
            failed += 1
    
    print(Panel.fit(
        f"[bold]Clean complete![/]\n"
        f"Removed: {removed} files\n"
        f"Failed: {failed} files"
    ))
    
    logger.info(f"Clean summary: {removed} removed, {failed} failed")


if __name__ == "__main__":
    assets_app()