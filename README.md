# Darkest Dungeon Text-to-Speech Voice Cloning

TTS application with voice cloning capabilities from Darkest Dungeon game audio samples. Uses Coqui TTS (XTTS v2) to generate deep, narrator-style voice that matches the game's atmosphere.

## Features

- ✅ **Voice Cloning** from Darkest Dungeon audio samples
- ✅ **Deep Voice Processing** - Automatically deepens voice with pitch shifting and formant adjustment
- ✅ Web interface with Gradio (easy to use)
- ✅ CPU support (no GPU required)
- ✅ Automatic text splitting for long texts
- ✅ Automatic selection of best voice samples
- ✅ 100+ Darkest Dungeon-themed example texts shuffled on each app start
- ✅ Beautiful English UI focused on Darkest Dungeon atmosphere

## Yêu cầu hệ thống

- Python 3.10 hoặc cao hơn
- Hệ điều hành: Windows, Linux, hoặc macOS
- RAM: Tối thiểu 4GB (khuyến nghị 8GB+)
- Ổ cứng: ~5GB để lưu models và dependencies

## Cài đặt

### 1. Clone repository và vào thư mục

```bash
cd Project_Sound_DD
```

### 2. Kích hoạt virtual environment (nếu có)

Windows:
```powershell
.\venv\Scripts\Activate.ps1
```

Linux/Mac:
```bash
source venv/bin/activate
```

### 3. Cài đặt dependencies

**Cách 1: Sử dụng script tự động (Khuyến nghị)**

Windows PowerShell:
```powershell
.\install_dependencies.ps1
```

**Cách 2: Cài đặt thủ công**

```bash
pip install -e .
pip install bnnumerizer gruut
```

**Lưu ý quan trọng**: 
- Một số packages (`gruut`, `jieba`) cần được cài từ source để tránh lỗi missing files
- Script `install_dependencies.ps1` sẽ tự động xử lý điều này
- Package `bnnumerizer` có thể gặp vấn đề cài đặt. Nếu gặp lỗi, tạo file stub:
  - Tạo file `venv\Lib\site-packages\bnnumerizer.py` với nội dung:
    ```python
    def numerize(text):
        return text
    ```
- Lần đầu tiên chạy sẽ tự động tải TTS model (~2GB), có thể mất vài phút.

**Xử lý lỗi dependencies:**
- Nếu gặp lỗi `ModuleNotFoundError` với `gruut` hoặc `jieba`, cài lại từ source:
  ```powershell
  .\venv\Scripts\pip.exe install --force-reinstall --no-cache-dir gruut==2.2.3
  .\venv\Scripts\pip.exe install --force-reinstall --no-cache-dir jieba
  ```
- Nếu gặp lỗi `cannot import name 'BeamSearchScorer' from 'transformers'`, downgrade transformers:
  ```powershell
  .\venv\Scripts\pip.exe install "transformers>=4.33.0,<4.40.0"
  ```
- Nếu gặp lỗi `Weights only load failed` hoặc `weights_only` với PyTorch, downgrade PyTorch:
  ```powershell
  .\venv\Scripts\pip.exe install "torch>=2.0.0,<2.6.0" "torchaudio>=2.0.0,<2.6.0"
  ```

## Sử dụng

### Chạy ứng dụng web

```bash
python app.py
```

Sau đó mở trình duyệt và truy cập: `http://localhost:7860`

### Sử dụng trong code Python

```python
from src.voice_cloner import VoiceCloner

# Khởi tạo voice cloner
cloner = VoiceCloner(sound_dir="Sound")
cloner.initialize()

# Tạo âm thanh từ văn bản tiếng Anh
audio = cloner.synthesize_simple(
    text="Hello, this is a text-to-speech application with voice cloning.",
    output_path="output.wav"
)
```

## Cấu trúc project

```
Project_Sound_DD/
├── Sound/                 # Thư mục chứa các file .wav mẫu (481 files)
├── src/
│   ├── __init__.py
│   ├── audio_processor.py   # Xử lý và chuẩn hóa file âm thanh
│   ├── tts_engine.py         # TTS engine với Coqui TTS
│   ├── text_processor.py     # Xử lý văn bản tiếng Anh
│   └── voice_cloner.py       # Module voice cloning chính
├── tests/                   # Unit tests
├── app.py                   # Ứng dụng Gradio
├── pyproject.toml          # Dependencies và cấu hình
└── README.md
```

## Tối ưu hóa cho CPU

- Model được tối ưu để chạy trên CPU
- Sử dụng threading giới hạn để tránh quá tải
- Tự động chia nhỏ văn bản dài
- Caching models để tái sử dụng

## Xử lý lỗi thường gặp

### Lỗi: "No voice samples available"
- Đảm bảo thư mục `Sound` có chứa các file `.wav`
- Kiểm tra quyền truy cập file

### Lỗi: "TTS model not initialized"
- Kiểm tra kết nối internet (lần đầu cần tải model)
- Đảm bảo đã cài đặt đầy đủ dependencies

### Chạy chậm
- Bình thường khi chạy trên CPU, mỗi câu có thể mất 10-30 giây
- Có thể giảm độ dài văn bản để tăng tốc

## Phát triển

### Chạy tests

```bash
pytest tests/
```

### Cài đặt development dependencies

```bash
pip install -e ".[dev]"
```

## Giấy phép

MIT License

## Tác giả

Dự án phát triển cho Vietnamese TTS với voice cloning.

## Ghi chú

- Model XTTS v2 hỗ trợ nhiều ngôn ngữ (tiếng Anh, Tây Ban Nha, Pháp, Đức, v.v.) nhưng không hỗ trợ tiếng Việt
- Ứng dụng này được thiết kế cho tiếng Anh để tạo giọng narrator từ game
- Chất lượng giọng nói phụ thuộc vào chất lượng file mẫu trong thư mục `Sound`
- Lần đầu tiên sử dụng cần thời gian để tải và khởi tạo model

