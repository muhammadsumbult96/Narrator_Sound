# Vietnamese TTS Voice Cloning Application

Ứng dụng Text-to-Speech tiếng Việt với khả năng voice cloning từ các file âm thanh mẫu. Ứng dụng sử dụng Coqui TTS (XTTS v2) để tạo giọng nói từ văn bản tiếng Việt với giọng tương tự như các file âm thanh mẫu trong thư mục `Sound`.

## Tính năng

- ✅ Text-to-Speech tiếng Việt với voice cloning
- ✅ Giao diện web với Gradio (dễ sử dụng)
- ✅ Hỗ trợ CPU (không cần GPU)
- ✅ Xử lý văn bản dài tự động chia nhỏ
- ✅ Chọn tự động các file âm thanh mẫu tốt nhất

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

```bash
pip install -e .
```

Hoặc cài đặt từng package:

```bash
pip install TTS gradio librosa soundfile numpy scipy torch torchaudio pydub underthesea
```

**Lưu ý**: Lần đầu tiên chạy sẽ tự động tải TTS model (~2GB), có thể mất vài phút.

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

# Tạo âm thanh từ văn bản
audio = cloner.synthesize_simple(
    text="Xin chào, đây là ứng dụng text-to-speech tiếng Việt.",
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
│   ├── text_processor.py     # Xử lý văn bản tiếng Việt
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

- Model XTTS v2 hỗ trợ nhiều ngôn ngữ nhưng tối ưu nhất cho tiếng Việt
- Chất lượng giọng nói phụ thuộc vào chất lượng file mẫu trong thư mục `Sound`
- Lần đầu tiên sử dụng cần thời gian để tải và khởi tạo model

