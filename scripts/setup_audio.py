#!/usr/bin/env python3
"""Script to help set up audio configuration for the sales coach."""

import sys
from pathlib import Path
import subprocess

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_coach.src.audio.capture import AudioDeviceManager, AudioTestUtility
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt


console = Console()


def check_blackhole_installation() -> bool:
    """Check if BlackHole is installed."""
    try:
        # Check if BlackHole driver is available
        device_manager = AudioDeviceManager()
        blackhole_device = device_manager.find_device("blackhole")
        return blackhole_device is not None
    except Exception:
        return False


def install_blackhole():
    """Guide user through BlackHole installation."""
    console.print("[yellow]BlackHole 2ch is recommended for capturing system audio[/yellow]")
    console.print("This allows the coach to hear both your voice and the customer's voice")
    
    if Confirm.ask("Would you like to install BlackHole 2ch?"):
        console.print("\n[blue]Installing BlackHole via Homebrew...[/blue]")
        
        try:
            # Check if Homebrew is installed
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            
            # Install BlackHole
            result = subprocess.run(["brew", "install", "blackhole-2ch"], 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[green]✅ BlackHole 2ch installed successfully![/green]")
                console.print("[yellow]Please restart your audio applications[/yellow]")
                return True
            else:
                console.print(f"[red]Failed to install BlackHole: {result.stderr}[/red]")
                return False
                
        except subprocess.CalledProcessError:
            console.print("[red]Homebrew not found![/red]")
            console.print("Please install Homebrew first: https://brew.sh")
            return False
        except Exception as e:
            console.print(f"[red]Installation failed: {e}[/red]")
            return False
    
    return False


def list_audio_devices():
    """List and analyze available audio devices."""
    console.print("\n[blue]Available Audio Devices:[/blue]")
    
    device_manager = AudioDeviceManager()
    devices = device_manager.get_input_devices()
    
    table = Table()
    table.add_column("Index", justify="center") 
    table.add_column("Name")
    table.add_column("Channels", justify="center")
    table.add_column("Sample Rate", justify="center") 
    table.add_column("Recommended", justify="center")
    
    recommended_patterns = ["aggregate", "blackhole", "multi", "soundflower"]
    
    for device in devices:
        is_recommended = any(pattern in device.name.lower() for pattern in recommended_patterns)
        recommendation = "✅ Yes" if is_recommended else "❌ Basic"
        
        table.add_row(
            str(device.index),
            device.name,
            str(device.channels),
            f"{device.sample_rate:,.0f} Hz",
            recommendation
        )
    
    console.print(table)
    
    # Provide guidance
    console.print("\n[yellow]Device Recommendations:[/yellow]")
    console.print("• [green]Aggregate Device[/green]: Best for capturing mic + system audio")
    console.print("• [green]BlackHole[/green]: Good for system audio routing")
    console.print("• [yellow]Built-in Microphone[/yellow]: Basic, mic only")


def test_audio_device():
    """Interactively test audio devices."""
    device_manager = AudioDeviceManager()
    devices = device_manager.get_input_devices()
    
    if not devices:
        console.print("[red]No input devices found![/red]")
        return
    
    # Show devices
    list_audio_devices()
    
    while True:
        try:
            device_index = Prompt.ask(
                "\nEnter device index to test (or 'q' to quit)",
                default="q"
            )
            
            if device_index.lower() == 'q':
                break
            
            device_idx = int(device_index)
            
            # Find device
            selected_device = None
            for device in devices:
                if device.index == device_idx:
                    selected_device = device
                    break
            
            if not selected_device:
                console.print("[red]Invalid device index[/red]")
                continue
            
            console.print(f"\n[blue]Testing device: {selected_device.name}[/blue]")
            console.print("[yellow]Speak into your microphone and play some system audio...[/yellow]")
            
            # Test the device
            results = AudioTestUtility.test_device(device_idx, duration=5.0)
            
            if results["success"]:
                console.print("[green]✅ Test completed successfully![/green]")
                
                # Analyze results
                peak_level = results["peak_level"]
                silence_ratio = results["silence_ratio"]
                
                console.print(f"Peak audio level: {peak_level:.3f}")
                console.print(f"Silence ratio: {silence_ratio:.1%}")
                
                # Provide feedback
                if peak_level < 0.005:
                    console.print("[red]⚠️  Very low audio levels - check your setup[/red]")
                elif peak_level < 0.02:
                    console.print("[yellow]⚠️  Low audio levels - may need adjustment[/yellow]")
                else:
                    console.print("[green]✅ Good audio levels detected[/green]")
                
                if silence_ratio > 0.8:
                    console.print("[yellow]⚠️  Mostly silence - ensure audio is playing[/yellow]")
                
                # RMS levels over time
                if results["rms_levels"]:
                    avg_rms = sum(results["rms_levels"]) / len(results["rms_levels"])
                    console.print(f"Average RMS level: {avg_rms:.4f}")
                
            else:
                console.print(f"[red]❌ Test failed: {results['error']}[/red]")
                
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
        except KeyboardInterrupt:
            break


def create_audio_midi_guide():
    """Show guide for setting up Audio MIDI Setup."""
    guide = """[bold blue]Audio MIDI Setup Configuration[/bold blue]

[yellow]1. Open Audio MIDI Setup[/yellow]
• Press Cmd+Space and type "Audio MIDI Setup"
• Or go to Applications > Utilities > Audio MIDI Setup

[yellow]2. Create Multi-Output Device (for system audio capture)[/yellow]
• Click the "+" button (bottom left)
• Select "Create Multi-Output Device"
• Check your normal speakers/headphones
• Check "BlackHole 2ch" (if installed)
• Right-click and "Use This Device For Sound Output"

[yellow]3. Create Aggregate Device (for combined audio)[/yellow] 
• Click the "+" button again
• Select "Create Aggregate Device"
• Check your microphone (Built-in Microphone)
• Check "BlackHole 2ch" (if available)
• This device will capture both mic and system audio

[yellow]4. Test Your Setup[/yellow]
• Use this script to test: python scripts/setup_audio.py
• The aggregate device should capture both voices in a call

[green]💡 Tip: If you don't have BlackHole, the system can still work with just your microphone, but it won't capture the other party's audio in calls.[/green]"""

    console.print(Panel(guide, border_style="blue"))


def recommend_best_device():
    """Recommend the best available device.""" 
    device_manager = AudioDeviceManager()
    best_device = device_manager.get_best_capture_device()
    
    if best_device:
        console.print(f"\n[green]🎯 Recommended device: {best_device.name}[/green]")
        console.print(f"Index: {best_device.index}")
        console.print("You can use this device name in your configuration file")
        
        # Test the recommended device
        if Confirm.ask("Would you like to test this device?"):
            console.print(f"\n[blue]Testing recommended device...[/blue]")
            results = AudioTestUtility.test_device(best_device.index, duration=5.0)
            
            if results["success"]:
                console.print("[green]✅ Recommended device works well![/green]")
            else:
                console.print(f"[yellow]⚠️  Issue with recommended device: {results['error']}[/yellow]")
    
    else:
        console.print("[yellow]No optimal capture device found[/yellow]")
        console.print("Consider setting up BlackHole for better audio capture")


def main():
    """Main setup function."""
    console.print(Panel(
        "[bold green]Sales Coach Audio Setup[/bold green]\n"
        "This script will help you configure audio for the sales coach",
        border_style="green"
    ))
    
    # Check BlackHole installation
    if not check_blackhole_installation():
        console.print("\n[yellow]BlackHole 2ch not detected[/yellow]")
        install_blackhole()
    else:
        console.print("\n[green]✅ BlackHole 2ch detected[/green]")
    
    while True:
        console.print("\n[blue]What would you like to do?[/blue]")
        options = [
            "1. List audio devices",
            "2. Test audio devices", 
            "3. Find recommended device",
            "4. Show Audio MIDI Setup guide",
            "5. Exit"
        ]
        
        for option in options:
            console.print(f"  {option}")
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            list_audio_devices()
        elif choice == "2":
            test_audio_device()
        elif choice == "3":
            recommend_best_device()
        elif choice == "4":
            create_audio_midi_guide()
        elif choice == "5":
            console.print("[green]Setup complete! Run 'sales-coach start' to begin.[/green]")
            break


if __name__ == "__main__":
    main()