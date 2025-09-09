"""Main sales coach orchestrator that coordinates all components."""

import logging
import time
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

from .src.models.config import SalesCoachConfig, load_config
from .src.models.conversation import ConversationTurn, CoachingResponse, Speaker
from .src.audio.capture import AudioCaptureSystem
from .src.audio.vad import create_vad, VoiceSegment
from .src.audio.diarization import create_diarization_system, SpeakerSegment
from .src.audio.transcription import create_transcription_system
from .src.llm.coaching import create_coaching_system


logger = logging.getLogger(__name__)


class SalesCoach:
    """Main sales coach system that orchestrates all components."""
    
    def __init__(self, config_path: Optional[Path] = None):
        # Load configuration
        self.config = load_config(config_path)
        self.config.create_directories()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.console = Console()
        self.audio_capture: Optional[AudioCaptureSystem] = None
        self.vad_system = None
        self.diarization_system = None
        self.transcription_system = None
        self.coaching_system = None
        
        # State
        self.is_running = False
        self.session_start_time: Optional[datetime] = None
        
        # Recent data for display
        self.recent_turns: List[ConversationTurn] = []
        self.recent_coaching: List[CoachingResponse] = []
        self.current_advice: Optional[CoachingResponse] = None
        
        # Statistics
        self.stats = {
            "session_duration": 0.0,
            "total_turns": 0,
            "coaching_events": 0,
            "audio_chunks_processed": 0
        }
        
        logger.info("Sales coach initialized")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.system.log_level)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File logging if enabled
        if self.config.system.log_to_file:
            log_file = self.config.system.logs_dir / "sales_coach.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logging.getLogger().addHandler(file_handler)
    
    def initialize_components(self) -> bool:
        """Initialize all system components."""
        self.console.print("[yellow]Initializing sales coach components...[/yellow]")
        
        try:
            # Initialize audio capture
            self.console.print("• Loading audio capture system...")
            self.audio_capture = AudioCaptureSystem(self.config.audio)
            self.audio_capture.set_audio_callback(self._handle_audio_chunk)
            
            # Initialize VAD
            self.console.print("• Loading voice activity detection...")
            self.vad_system = create_vad(self.config.audio, adaptive=True)
            if hasattr(self.vad_system, 'start_adaptation'):
                self.vad_system.start_adaptation()
            
            # Initialize speaker diarization
            self.console.print("• Loading speaker diarization...")
            self.diarization_system = create_diarization_system(self.config.models)
            
            # Initialize transcription
            self.console.print("• Loading speech-to-text system...")
            self.transcription_system = create_transcription_system(self.config.models)
            if not self.transcription_system:
                raise Exception("Failed to initialize transcription system")
            
            self.transcription_system.set_turn_callback(self._handle_conversation_turn)
            
            # Initialize coaching system
            self.console.print("• Loading AI coaching system...")
            self.coaching_system = create_coaching_system(
                self.config.models, 
                self.config.coaching
            )
            if not self.coaching_system:
                raise Exception("Failed to initialize coaching system")
            
            self.coaching_system.set_coaching_callback(self._handle_coaching_response)
            
            self.console.print("[green]✅ All components initialized successfully[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to initialize components: {e}[/red]")
            logger.error(f"Component initialization failed: {e}")
            return False
    
    def _handle_audio_chunk(self, audio_chunk) -> None:
        """Handle incoming audio chunk."""
        if not self.vad_system:
            return
        
        timestamp = time.time()
        self.stats["audio_chunks_processed"] += 1
        
        # Process with VAD
        voice_segments = self.vad_system.process_audio_stream(audio_chunk, timestamp)
        
        if voice_segments and self.diarization_system:
            # Process speaker diarization
            speaker_segments = self.diarization_system.process_real_time(audio_chunk, timestamp)
            
            # Send to transcription system
            if self.transcription_system:
                self.transcription_system.process_voice_segments(voice_segments, speaker_segments)
    
    def _handle_conversation_turn(self, turn: ConversationTurn) -> None:
        """Handle new conversation turn."""
        self.recent_turns.append(turn)
        if len(self.recent_turns) > 20:  # Keep only recent turns
            self.recent_turns = self.recent_turns[-20:]
        
        self.stats["total_turns"] += 1
        
        # Send to coaching system
        if self.coaching_system:
            self.coaching_system.add_conversation_turn(turn)
        
        logger.info(f"New turn: {turn.speaker.value}: {turn.text[:50]}...")
    
    def _handle_coaching_response(self, coaching: CoachingResponse) -> None:
        """Handle coaching response."""
        self.recent_coaching.append(coaching)
        if len(self.recent_coaching) > 10:  # Keep only recent coaching
            self.recent_coaching = self.recent_coaching[-10:]
        
        self.current_advice = coaching
        self.stats["coaching_events"] += 1
        
        logger.info(f"New coaching: {coaching.primary_advice.category.value} - {coaching.primary_advice.insight[:50]}...")
    
    def start(self) -> bool:
        """Start the sales coach system."""
        if self.is_running:
            self.console.print("[yellow]Sales coach is already running[/yellow]")
            return True
        
        # Initialize components if not done
        if not self.audio_capture:
            if not self.initialize_components():
                return False
        
        self.console.print("[green]Starting sales coach...[/green]")
        
        try:
            # Start audio capture
            if not self.audio_capture.start_capture():
                self.console.print("[red]Failed to start audio capture[/red]")
                return False
            
            # Start transcription system
            if self.transcription_system:
                self.transcription_system.start()
            
            # Start coaching analysis
            if self.coaching_system:
                self.coaching_system.start_analysis()
            
            self.is_running = True
            self.session_start_time = datetime.now()
            
            self.console.print("[green]✅ Sales coach is running![/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Failed to start sales coach: {e}[/red]")
            logger.error(f"Failed to start: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the sales coach system."""
        if not self.is_running:
            return
        
        self.console.print("[yellow]Stopping sales coach...[/yellow]")
        
        try:
            # Stop audio capture
            if self.audio_capture:
                self.audio_capture.stop_capture()
            
            # Stop transcription
            if self.transcription_system:
                self.transcription_system.stop()
            
            # Stop coaching analysis
            if self.coaching_system:
                self.coaching_system.stop_analysis()
            
            # Stop VAD adaptation
            if self.vad_system and hasattr(self.vad_system, 'stop_adaptation'):
                self.vad_system.stop_adaptation()
            
            self.is_running = False
            self.console.print("[green]Sales coach stopped[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Error stopping sales coach: {e}[/red]")
            logger.error(f"Error stopping: {e}")
    
    def create_status_display(self) -> Layout:
        """Create status display layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="conversation", ratio=2),
            Layout(name="coaching", ratio=1)
        )
        
        # Header
        header = Panel(
            f"[bold green]Stealth Sales Coach[/bold green] - Session: {self._format_duration()}",
            border_style="green"
        )
        layout["header"].update(header)
        
        # Conversation panel
        conversation_text = ""
        for turn in self.recent_turns[-5:]:  # Show last 5 turns
            speaker_color = "blue" if turn.speaker == Speaker.SALES_REP else "cyan"
            timestamp = turn.timestamp.strftime("%H:%M:%S")
            conversation_text += f"[dim]{timestamp}[/dim] [{speaker_color}]{turn.speaker.value}[/{speaker_color}]: {turn.text}\n\n"
        
        if not conversation_text:
            conversation_text = "[dim]Waiting for conversation...[/dim]"
        
        conversation_panel = Panel(
            conversation_text,
            title="Live Conversation",
            border_style="blue"
        )
        layout["conversation"].update(conversation_panel)
        
        # Coaching panel
        coaching_text = ""
        if self.current_advice:
            advice = self.current_advice.primary_advice
            priority_colors = {
                "HIGH": "red",
                "MEDIUM": "yellow",
                "LOW": "green"
            }
            color = priority_colors.get(advice.priority.value, "white")
            
            coaching_text = f"""[bold {color}]Priority: {advice.priority.value}[/bold {color}]
[cyan]Category:[/cyan] {advice.category.value}

[bold]💡 Insight:[/bold]
{advice.insight}

[bold]🎯 Action:[/bold]
{advice.suggested_action}"""

            if advice.example_phrase:
                coaching_text += f"\n\n[bold]💬 Try saying:[/bold]\n\"{advice.example_phrase}\""
        else:
            coaching_text = "[dim]Analyzing conversation...[/dim]"
        
        coaching_panel = Panel(
            coaching_text,
            title="AI Coach",
            border_style="yellow"
        )
        layout["coaching"].update(coaching_panel)
        
        # Footer with stats
        stats_text = f"Turns: {self.stats['total_turns']} | Coaching: {self.stats['coaching_events']} | Audio chunks: {self.stats['audio_chunks_processed']}"
        footer = Panel(stats_text, border_style="dim")
        layout["footer"].update(footer)
        
        return layout
    
    def _format_duration(self) -> str:
        """Format session duration."""
        if not self.session_start_time:
            return "00:00:00"
        
        duration = datetime.now() - self.session_start_time
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def run_interactive(self) -> None:
        """Run the coach in interactive mode with live display."""
        if not self.start():
            return
        
        try:
            with Live(self.create_status_display(), refresh_per_second=2) as live:
                while self.is_running:
                    live.update(self.create_status_display())
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Received interrupt signal[/yellow]")
        finally:
            self.stop()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            "is_running": self.is_running,
            "session_duration": self._format_duration(),
            "stats": self.stats.copy(),
            "components": {}
        }
        
        if self.audio_capture:
            status["components"]["audio_capture"] = self.audio_capture.get_status()
        
        if self.vad_system:
            status["components"]["vad"] = self.vad_system.get_stats()
        
        if self.diarization_system:
            status["components"]["diarization"] = self.diarization_system.get_stats()
        
        if self.transcription_system:
            status["components"]["transcription"] = self.transcription_system.transcriber.get_stats()
        
        if self.coaching_system:
            status["components"]["coaching"] = self.coaching_system.get_stats()
        
        return status
    
    def list_audio_devices(self) -> List[Dict[str, Any]]:
        """List available audio devices."""
        if not self.audio_capture:
            self.audio_capture = AudioCaptureSystem(self.config.audio)
        
        return self.audio_capture.list_devices()
    
    def test_audio_setup(self) -> Dict[str, Any]:
        """Test current audio setup."""
        from .src.audio.capture import AudioTestUtility
        
        # Get current device
        if not self.audio_capture:
            self.audio_capture = AudioCaptureSystem(self.config.audio)
        
        device = self.audio_capture.device_manager.get_best_capture_device()
        if not device:
            return {"success": False, "error": "No suitable audio device found"}
        
        # Test the device
        return AudioTestUtility.test_device(device.index, duration=3.0)


def create_coach(config_path: Optional[Path] = None) -> SalesCoach:
    """Factory function to create sales coach."""
    return SalesCoach(config_path)