"""Main Gradio application for Text-to-Speech with voice cloning."""

import logging
import tempfile
from pathlib import Path
from typing import Tuple

import gradio as gr

from src.voice_cloner import VoiceCloner
from src.example_generator import ExampleGenerator
from src.transcript_manager import TranscriptManager
from src.audio_processor import AudioProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize voice cloner (will be loaded on first use)
_voice_cloner: VoiceCloner | None = None


def get_voice_cloner() -> VoiceCloner:
    """Get or initialize voice cloner instance.

    Returns:
        VoiceCloner instance
    """
    global _voice_cloner
    
    if _voice_cloner is None:
        logger.info("Initializing voice cloner...")
        _voice_cloner = VoiceCloner(sound_dir="Sound")
        try:
            _voice_cloner.initialize(require_transcript=True)
        except ValueError as e:
            if "No audio files with transcripts" in str(e):
                logger.error(str(e))
                raise RuntimeError(
                    "No audio files with transcripts found!\n\n"
                    "Please run the transcription script first:\n"
                    "  python scripts/transcribe_audio.py\n\n"
                    "This will automatically transcribe all audio files using Whisper."
                ) from e
            raise
        except Exception as e:
            logger.error(f"Error initializing voice cloner: {e}")
            raise
    return _voice_cloner


def synthesize_text(text: str) -> Tuple[str | None, str | None]:
    """Synthesize text to speech.

    Args:
        text: Input Vietnamese text

    Returns:
        Tuple of (audio_file_path, error_message)
    """
    if not text or not text.strip():
        return None, "Vui lòng nhập văn bản"

    try:
        logger.info(f"Synthesizing text: {text[:50]}...")

        voice_cloner = get_voice_cloner()

        # Create temporary file for output
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav",
            dir=tempfile.gettempdir(),
        ) as tmp_file:
            output_path = tmp_file.name

        # Synthesize
        audio_array = voice_cloner.synthesize_simple(
            text=text.strip(),
            output_path=output_path,
        )
        
        # Verify the file was created and has content
        import os
        if not os.path.exists(output_path):
            return None, "Lỗi: File âm thanh không được tạo"
        
        file_size = os.path.getsize(output_path)
        if file_size < 1000:  # Less than 1KB is suspicious
            return None, f"Lỗi: File âm thanh quá nhỏ ({file_size} bytes)"

        logger.info(f"Successfully generated audio: {output_path} (size: {file_size} bytes)")
        return output_path, None

    except Exception as e:
        error_msg = f"Lỗi khi tạo âm thanh: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg


def create_interface() -> gr.Blocks:
    """Create Gradio interface.

    Returns:
        Gradio Blocks interface
    """
    with gr.Blocks(title="Text-to-Speech Voice Cloning", theme=gr.themes.Soft()) as app:
        with gr.Row():
            # Left column: Overview (1/3 screen)
            with gr.Column(scale=1):
                gr.Markdown(
                    """
                    # 🎙️ Text-to-Speech with Voice Cloning

                    TTS application with voice cloning capabilities from game audio samples.
                    Uses XTTS v2 to generate deep, narrator-style voice from Darkest Dungeon audio samples.

                    **Note**: First-time use may take time to download models (~2GB).
                    """
                )
            
            # Right column: Examples (2/3 screen)
            with gr.Column(scale=2):
                # Generate and shuffle examples
                example_gen = ExampleGenerator()
                examples = example_gen.get_examples(count=100, shuffle=True)

                gr.Markdown("### 📝 Example Texts")
                gr.Markdown("*Click any example below to use it. Examples are shuffled on each app start.*")
                
                # Create hidden text_input for examples binding
                temp_text_for_examples = gr.Textbox(visible=False)
                
                example_selector = gr.Examples(
                    examples=examples,
                    inputs=[temp_text_for_examples],
                    label="",
                    examples_per_page=10,  # More examples since we have more space
                )
        
        # Define the actual visible text_input for the main form
        text_input = gr.Textbox(
            label="Enter Text",
            placeholder="Enter your text here...",
            lines=5,
            value="Remind yourself that overconfidence is a slow and insidious killer.",
        )
        
        # Sync temp_text_for_examples with text_input when examples are clicked
        # This allows examples to populate the visible text_input
        def sync_text_input(example_text):
            return example_text
        
        temp_text_for_examples.change(
            fn=sync_text_input,
            inputs=[temp_text_for_examples],
            outputs=[text_input],
        )
        
        with gr.Row():
            # Left column: Main content
            with gr.Column(scale=2):

                with gr.Row():
                    generate_btn = gr.Button("Generate Audio", variant="primary")
                    clear_btn = gr.Button("Clear")

                status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    value="Ready",
                )

            # Right column: Audio output (1/3 screen)
            with gr.Column(scale=1):
                audio_output = gr.Audio(
                    label="Generated Audio",
                    type="filepath",
                )

                error_output = gr.Textbox(
                    label="Error Messages",
                    interactive=False,
                    visible=True,
                )

        # Event handlers
        def generate_audio(text: str) -> Tuple[str, str, str]:
            """Generate audio and update UI.

            Args:
                text: Input text

            Returns:
                Tuple of (audio_path, status, error)
            """
            status_msg = "Đang xử lý..."
            error_msg = ""

            try:
                audio_path, error = synthesize_text(text)

                if audio_path:
                    status_msg = "Hoàn thành!"
                    return audio_path, status_msg, ""
                else:
                    error_msg = error or "Có lỗi xảy ra"
                    status_msg = "Lỗi"
                    return None, status_msg, error_msg

            except Exception as e:
                error_msg = f"Lỗi: {str(e)}"
                logger.error(error_msg, exc_info=True)
                status_msg = "Lỗi"
                return None, status_msg, error_msg

        generate_btn.click(
            fn=generate_audio,
            inputs=[text_input],
            outputs=[audio_output, status, error_output],
        )

        def clear_all() -> Tuple[str, None, str, str]:
            """Clear all inputs and outputs.

            Returns:
                Tuple of cleared values
            """
            return "", None, "Ready", ""

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[text_input, audio_output, status, error_output],
        )
        
        # Transcript Management Tab
        with gr.Tab("📝 Transcript Management"):
            gr.Markdown(
                """
                ### Manage Transcripts for Training Dataset
                
                Create transcripts for audio files to prepare a training dataset for fine-tuning.
                Listen to each audio file and enter its transcript below.
                """
            )
            
            # Initialize managers (will be re-initialized in functions to get fresh data)
            def init_managers() -> tuple:
                """Initialize transcript manager and audio processor."""
                tm = TranscriptManager()
                ap = AudioProcessor(sound_dir="Sound")
                ap.discover_audio_files()
                return tm, ap, tm.get_statistics()
            
            # Initial setup
            transcript_manager, audio_processor, initial_stats = init_managers()
            
            with gr.Row():
                with gr.Column(scale=1):
                    stats_display = gr.Markdown(
                        f"""
                        **Statistics:**
                        - Total audio files: {initial_stats['total_audio_files']}
                        - With transcript: {initial_stats['with_transcript']}
                        - Without transcript: {initial_stats['without_transcript']}
                        - Completion: {initial_stats['completion_percentage']:.1f}%
                        """
                    )
                    
                    refresh_stats_btn = gr.Button("🔄 Refresh Statistics", variant="secondary")
                    
                    # Get files without transcript
                    files_without_transcript_list = transcript_manager.get_audio_files_without_transcript(
                        audio_processor.audio_files
                    )
                    files_without_transcript_state = gr.State(value=files_without_transcript_list)
                    
                    if files_without_transcript_list:
                        current_file_idx = gr.State(value=0)
                        current_file_path = gr.State(value=str(files_without_transcript_list[0]))
                        
                        audio_player = gr.Audio(
                            label="Current Audio File",
                            type="filepath",
                            value=str(files_without_transcript_list[0]),
                        )
                        
                        file_info = gr.Textbox(
                            label="File Info",
                            value=f"File 1 of {len(files_without_transcript_list)}: {files_without_transcript_list[0].name}",
                            interactive=False,
                        )
                        
                        transcript_input = gr.Textbox(
                            label="Enter Transcript",
                            placeholder="Type the transcript for this audio file...",
                            lines=5,
                        )
                        
                        save_status = gr.Textbox(label="Save Status", interactive=False, value="")
                        
                        with gr.Row():
                            save_transcript_btn = gr.Button("💾 Save Transcript", variant="primary")
                            next_file_btn = gr.Button("➡️ Next File", variant="secondary")
                            prev_file_btn = gr.Button("⬅️ Previous File", variant="secondary")
                        
                        def get_file_list() -> list:
                            """Get fresh list of files without transcript."""
                            tm, ap, _ = init_managers()
                            return tm.get_audio_files_without_transcript(ap.audio_files)
                        
                        def load_file_at_idx(idx: int, file_list: list) -> tuple:
                            """Load file at index from list."""
                            if 0 <= idx < len(file_list):
                                file_path = Path(file_list[idx])
                                tm, _, _ = init_managers()
                                existing_transcript = tm.get_transcript(file_path) or ""
                                return (
                                    str(file_path),
                                    str(file_path),
                                    f"File {idx + 1} of {len(file_list)}: {file_path.name}",
                                    existing_transcript,
                                )
                            return "", "", "No file", ""
                        
                        def save_and_next(file_path: str, transcript: str, current_idx: int, file_list: list) -> tuple:
                            """Save transcript and move to next file."""
                            try:
                                tm, _, _ = init_managers()
                                tm.set_transcript(file_path, transcript)
                                
                                # Get updated file list
                                ap = AudioProcessor(sound_dir="Sound")
                                ap.discover_audio_files()
                                updated_list = tm.get_audio_files_without_transcript(ap.audio_files)
                                
                                # Move to next if available
                                if current_idx < len(file_list) - 1 and len(updated_list) > 0:
                                    # File was removed from list, stay at same index or adjust
                                    new_idx = min(current_idx, len(updated_list) - 1) if updated_list else 0
                                    if new_idx < len(updated_list):
                                        return load_file_at_idx(new_idx, updated_list) + (new_idx, updated_list, "✅ Transcript saved! Moving to next file...")
                                
                                # Refresh stats
                                stats = tm.get_statistics()
                                new_stats = f"""
                                **Statistics:**
                                - Total audio files: {stats['total_audio_files']}
                                - With transcript: {stats['with_transcript']}
                                - Without transcript: {stats['without_transcript']}
                                - Completion: {stats['completion_percentage']:.1f}%
                                """
                                
                                if updated_list:
                                    return load_file_at_idx(0, updated_list) + (0, updated_list, "✅ Transcript saved!", new_stats)
                                else:
                                    return "", "", "✅ All files have transcripts!", "", 0, [], "✅ Transcript saved! All files completed!", new_stats
                            except Exception as e:
                                return file_path, audio_player.value, file_info.value, transcript_input.value, current_idx, file_list, f"❌ Error: {str(e)}", stats_display.value
                        
                        def load_next(idx: int, file_list: list) -> tuple:
                            """Load next file."""
                            if idx < len(file_list) - 1:
                                return load_file_at_idx(idx + 1, file_list) + (idx + 1, file_list)
                            return load_file_at_idx(idx, file_list) + (idx, file_list)
                        
                        def load_prev(idx: int, file_list: list) -> tuple:
                            """Load previous file."""
                            if idx > 0:
                                return load_file_at_idx(idx - 1, file_list) + (idx - 1, file_list)
                            return load_file_at_idx(idx, file_list) + (idx, file_list)
                        
                        save_transcript_btn.click(
                            fn=save_and_next,
                            inputs=[current_file_path, transcript_input, current_file_idx, files_without_transcript_state],
                            outputs=[current_file_path, audio_player, file_info, transcript_input, current_file_idx, files_without_transcript_state, save_status, stats_display],
                        )
                        
                        next_file_btn.click(
                            fn=load_next,
                            inputs=[current_file_idx, files_without_transcript_state],
                            outputs=[current_file_path, audio_player, file_info, transcript_input, current_file_idx, files_without_transcript_state],
                        )
                        
                        prev_file_btn.click(
                            fn=load_prev,
                            inputs=[current_file_idx, files_without_transcript_state],
                            outputs=[current_file_path, audio_player, file_info, transcript_input, current_file_idx, files_without_transcript_state],
                        )
                    else:
                        gr.Markdown("✅ All audio files have transcripts!")
                
                with gr.Column(scale=1):
                    gr.Markdown("### Export Dataset")
                    gr.Markdown("Export transcripts as CSV format for training.")
                    
                    export_btn = gr.Button("📤 Export Training Dataset", variant="primary")
                    export_status = gr.Textbox(label="Export Status", interactive=False)
                    
                    def export_dataset_fn() -> str:
                        """Export dataset to CSV."""
                        try:
                            tm, _, _ = init_managers()
                            output_path = tm.export_training_dataset()
                            return f"✅ Dataset exported to: {output_path}"
                        except Exception as e:
                            return f"❌ Error: {str(e)}"
                    
                    export_btn.click(
                        fn=export_dataset_fn,
                        outputs=[export_status],
                    )
                    
                    def refresh_stats_fn() -> tuple:
                        """Refresh statistics and file list."""
                        tm, ap, stats = init_managers()
                        ap.discover_audio_files()
                        file_list = tm.get_audio_files_without_transcript(ap.audio_files)
                        stats_text = f"""
                        **Statistics:**
                        - Total audio files: {stats['total_audio_files']}
                        - With transcript: {stats['with_transcript']}
                        - Without transcript: {stats['without_transcript']}
                        - Completion: {stats['completion_percentage']:.1f}%
                        """
                        return stats_text, file_list
                    
                    refresh_stats_btn.click(
                        fn=refresh_stats_fn,
                        outputs=[stats_display, files_without_transcript_state],
                    )

    return app


def main() -> None:
    """Main entry point."""
    import socket
    
    def find_free_port(start_port: int = 7860) -> int:
        """Find a free port starting from start_port."""
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("0.0.0.0", port))
                    return port
            except OSError:
                continue
        raise RuntimeError(f"Could not find free port in range {start_port}-{start_port + 9}")
    
    logger.info("Starting Text-to-Speech Voice Cloning application")

    # Find free port
    port = find_free_port(7860)
    if port != 7860:
        logger.info(f"Port 7860 is in use, using port {port} instead")

    # Create and launch interface
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
    )


if __name__ == "__main__":
    main()

