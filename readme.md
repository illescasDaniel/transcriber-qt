# TranscriberQt

An easy-to-use GUI to easily transcribe speech to text, either from videos or directly from audio files.

Made using PySide6 (Qt) (mostly made with Claude.ai + some tweaks).

<img src="docs/screenshot-windows.png" width="334">

**How to use:**
1. Drag and drop your video or audio.
2. Click transcribe.
3. The transcription text file will be located in the same folder as the original input file.

**Dependencies**:
- See `environment.yml` for a basic conda environment with all necessary dependencies including nvidia ones for GPU support.
- Use `environment-cpu.yml` if you don't have a nvidia gpu.
(`conda env create -f environment.yml`)


conda create --name transcriber2 python=3.11
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
conda install ffmpeg -c conda-forge
conda install cudnn=8.* -c conda-forge
pip install whisperx
pip install PySide6


**How to run it**:
You need to create a hugging-face READ token and then accept these terms manually here: https://huggingface.co/pyannote/speaker-diarization-3.1 and https://hf.co/pyannote/segmentation-3.0 and https://huggingface.co/pyannote/segmentation

- Windows:
	- Run `set HF_TOKEN=<your hugging face token here> && python main.py` inside `src` folder
- Unix:
	- Run `HF_TOKEN=<your hugging face token here> python main.py` inside `src` folder



todo:
from dotenv import load_dotenv

load_dotenv()  # Load from .env file