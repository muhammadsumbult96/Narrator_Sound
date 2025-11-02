"""Main Gradio application for Vietnamese TTS with voice cloning."""

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

        logger.info(f"Successfully generated audio: {output_path}")
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
    with gr.Blocks(title="Vietnamese TTS Voice Cloning", theme=gr.themes.Soft()) as app:
        gr.Markdown(
            """
            # 🎙️ Vietnamese Text-to-Speech với Voice Cloning

            Ứng dụng TTS tiếng Việt với khả năng voice cloning từ các file âm thanh mẫu.
            Nhập văn bản tiếng Việt và nhấn nút để tạo âm thanh.

            **Lưu ý**: Lần đầu tiên sử dụng có thể mất thời gian để tải model.
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Nhập văn bản tiếng Việt",
                    placeholder="Ví dụ: Xin chào, đây là ứng dụng text-to-speech tiếng Việt.",
                    lines=5,
                    value="Xin chào, đây là ứng dụng text-to-speech tiếng Việt với voice cloning.",
                )

                with gr.Row():
                    generate_btn = gr.Button("Tạo âm thanh", variant="primary")
                    clear_btn = gr.Button("Xóa")

            with gr.Column(scale=1):
                status = gr.Textbox(
                    label="Trạng thái",
                    interactive=False,
                    value="Sẵn sàng",
                )

        audio_output = gr.Audio(
            label="Âm thanh đã tạo",
            type="filepath",
        )

        error_output = gr.Textbox(
            label="Thông báo lỗi",
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
            "Xin chào, đây là ứng dụng text-to-speech tiếng Việt.",
            "Hôm nay trời rất đẹp, chúng ta đi dạo phố nhé.",
            "Công nghệ trí tuệ nhân tạo đang phát triển rất nhanh.",
            "Tiếng Việt là ngôn ngữ rất phong phú với nhiều dấu thanh.",
        ]

        example_selector = gr.Examples(
            examples=examples,
            inputs=text_input,
        )

    return app


def main() -> None:
    """Main entry point."""
    logger.info("Starting Vietnamese TTS Voice Cloning application")

    # Create and launch interface
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()

