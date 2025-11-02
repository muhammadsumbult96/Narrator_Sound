"""Main Gradio application for Text-to-Speech with voice cloning."""

import logging
import tempfile
from pathlib import Path
from typing import Tuple

import gradio as gr

from src.voice_cloner import VoiceCloner

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
            _voice_cloner.initialize()
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
            return "", None, "Sẵn sàng", ""

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[text_input, audio_output, status, error_output],
        )

        # Example texts
        gr.Markdown("### Ví dụ văn bản:")
        examples = [
            "Hello, this is a text-to-speech application with voice cloning.",
            "The darkness holds many secrets, and we are about to uncover them.",
            "In the depths of the dungeon, heroes face their greatest fears.",
            "Victory, so close, yet so far away in the face of overwhelming odds.",
        ]

        example_selector = gr.Examples(
            examples=examples,
            inputs=text_input,
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

