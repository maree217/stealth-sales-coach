"""Command-line interface for the Sales Coach."""

import typer
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .coach import create_coach
from .src.models.config import load_config


app = typer.Typer(help="Stealth Sales Coach - Local AI-powered sales coaching")
console = Console()


@app.command()
def start(
    config: Optional[Path] = typer.Option(
        None, 
        "--config", 
        "-c", 
        help="Path to configuration file"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i/-ni",
        help="Run in interactive mode with live display"
    )
):
    """Start the sales coach system."""
    console.print("[green]Starting Stealth Sales Coach...[/green]")
    
    coach = create_coach(config)
    
    if interactive:
        coach.run_interactive()
    else:
        if coach.start():
            console.print("[green]Sales coach started successfully![/green]")
            console.print("[yellow]Press Ctrl+C to stop[/yellow]")
            
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping...[/yellow]")
                coach.stop()


@app.command()
def devices():
    """List available audio devices."""
    console.print("[blue]Available Audio Devices:[/blue]")
    
    coach = create_coach()
    devices = coach.list_audio_devices()
    
    table = Table()
    table.add_column("Index", justify="center")
    table.add_column("Name")
    table.add_column("Channels", justify="center")
    table.add_column("Sample Rate", justify="center")
    table.add_column("Input", justify="center")
    table.add_column("Output", justify="center")
    
    for device in devices:
        table.add_row(
            str(device["index"]),
            device["name"],
            str(device["channels"]),
            f"{device['sample_rate']:,.0f} Hz",
            "✅" if device["is_input"] else "❌",
            "✅" if device["is_output"] else "❌"
        )
    
    console.print(table)


@app.command()
def test_audio(
    duration: float = typer.Option(
        3.0,
        "--duration",
        "-d", 
        help="Test duration in seconds"
    )
):
    """Test audio capture setup."""
    console.print(f"[blue]Testing audio setup for {duration} seconds...[/blue]")
    console.print("[yellow]Speak into your microphone and play some system audio[/yellow]")
    
    coach = create_coach()
    results = coach.test_audio_setup()
    
    if results["success"]:
        console.print("[green]✅ Audio test successful![/green]")
        console.print(f"Peak level: {results['peak_level']:.3f}")
        console.print(f"Silence ratio: {results['silence_ratio']:.1%}")
        
        if results['peak_level'] < 0.01:
            console.print("[yellow]⚠️  Very low audio levels detected[/yellow]")
        elif results['silence_ratio'] > 0.9:
            console.print("[yellow]⚠️  Mostly silence detected[/yellow]")
        else:
            console.print("[green]Audio levels look good![/green]")
    else:
        console.print(f"[red]❌ Audio test failed: {results['error']}[/red]")


@app.command()
def status():
    """Show system status and statistics."""
    coach = create_coach()
    
    if not coach.is_running:
        console.print("[yellow]Sales coach is not running[/yellow]")
        console.print("Run 'sales-coach start' to begin")
        return
    
    status = coach.get_system_status()
    
    # Main status
    panel_content = f"""[green]Running[/green] - Session Duration: {status['session_duration']}
    
[bold]Statistics:[/bold]
• Conversation turns: {status['stats']['total_turns']}
• Coaching events: {status['stats']['coaching_events']}
• Audio chunks processed: {status['stats']['audio_chunks_processed']}"""

    console.print(Panel(panel_content, title="Sales Coach Status"))
    
    # Component status
    if status.get("components"):
        table = Table(title="Component Status")
        table.add_column("Component")
        table.add_column("Status")
        table.add_column("Details")
        
        for component, details in status["components"].items():
            if isinstance(details, dict):
                status_text = "✅ Running" if details.get("is_running") or details.get("is_loaded") else "❌ Stopped"
                detail_text = ", ".join([f"{k}: {v}" for k, v in list(details.items())[:3]])
            else:
                status_text = "✅ Active"
                detail_text = str(details)
            
            table.add_row(component.title(), status_text, detail_text)
        
        console.print(table)


@app.command()
def config_init(
    output: Path = typer.Option(
        Path("config/sales_coach.yaml"),
        "--output",
        "-o",
        help="Output configuration file path"
    )
):
    """Initialize a default configuration file."""
    from .src.models.config import SalesCoachConfig
    
    config = SalesCoachConfig()
    config.to_file(output)
    
    console.print(f"[green]Configuration file created: {output}[/green]")
    console.print("Edit the configuration file and run 'sales-coach start --config <path>'")


@app.command()
def config_show(
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file"
    )
):
    """Show current configuration."""
    config = load_config(config_path)
    
    config_dict = config.dict()
    console.print(Panel(
        json.dumps(config_dict, indent=2, default=str),
        title="Current Configuration"
    ))


@app.command() 
def setup_guide():
    """Show setup guide for audio configuration."""
    guide_text = """[bold blue]Stealth Sales Coach Setup Guide[/bold blue]

[yellow]1. Install Audio Routing (Optional but Recommended)[/yellow]
For best results, install BlackHole for system audio routing:
```
brew install blackhole-2ch
```

[yellow]2. Configure Audio (macOS)[/yellow]
Open Audio MIDI Setup (Applications > Utilities):

• Create Multi-Output Device:
  - Check your speakers/headphones
  - Check BlackHole 2ch
  - Set as system output

• Create Aggregate Device:
  - Check your microphone  
  - Check BlackHole 2ch
  - Use this device name in config

[yellow]3. Test Your Setup[/yellow]
```
sales-coach devices          # List available devices
sales-coach test-audio       # Test audio capture
```

[yellow]4. Download Models[/yellow]
The system will automatically try to find models, or you can:
• Download Whisper models via whisper-cpp
• Download Llama models from HuggingFace
• Set model paths in configuration

[yellow]5. Start Coaching[/yellow]
```
sales-coach start --interactive
```

[green]Need help? Check the README.md file for detailed instructions.[/green]"""

    console.print(Panel(guide_text, border_style="blue"))


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()