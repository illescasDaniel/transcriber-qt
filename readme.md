# TranscriberQt

An easy-to-use GUI to easily transcribe speech to text, either from videos or directly from audio files.

> **NEW** alternative version with multiple speakers support: https://github.com/illescasDaniel/transcriber-qt/tree/feature/multipleSpeakers


- **UI**: PySide6 using QML (Qt)
- **AI models**:
	- Speech recognition: **whisper**-large-v3-turbo ('deepdml/faster-whisper-large-v3-turbo-ct2'). Using `faster-whisper`.

<img src="docs/screenshot-windows.png" width="334">

**How to use:**
1. Drag and drop your video or audio.
2. Click transcribe.
3. By default, the transcription text file will be located in the same folder as the original input file.

**Dependencies**:
- See `environment.yml` for a basic conda environment with all necessary dependencies including nvidia ones for GPU support.
- Use `environment-cpu.yml` if you don't have a nvidia gpu.
(`conda env create -f environment.yml`)

**How to run it**:
Run `python main.py` inside `src` folder
