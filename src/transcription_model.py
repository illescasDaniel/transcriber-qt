import os
import subprocess

from PySide6.QtCore import QObject, Signal, Slot
from faster_whisper import WhisperModel


class TranscriptionModel(QObject):
	"""Model: Handles the transcription logic and data"""

	progressUpdate = Signal(str, str, int, int)  # stage, detail, current, total
	transcriptionComplete = Signal(str)
	transcriptionError = Signal(str)

	def __init__(self):
		super().__init__()
		self.model = None
		self.audio_file = ""
		self.output_file = ""

	def load_model(self):
		if not self.model:
			cpu_count = os.cpu_count()
			self.model = WhisperModel(
				'deepdml/faster-whisper-large-v3-turbo-ct2',
				device=self.__get_best_device(),
				cpu_threads=cpu_count if cpu_count != None else 0
			)

	@Slot(str, str)
	def transcribe(self, audio_file, output_file):
		self.audio_file = audio_file
		self.output_file = output_file

		try:
			# Step 0: Load model
			self.progressUpdate.emit("Loading model (first time may take longer)...", "", 0, 0)
			self.load_model()

			# Step 1: Transcribe
			segments, info = self.model.transcribe(audio_file, word_timestamps=True) # type: ignore

			# Step 2: Process segments with percentage progress
			total_duration = info.duration
			self.progressUpdate.emit("Transcribing audio", "0%", 0, 100)

			with open(output_file, 'w', buffering=8192) as f:
				for segment in segments:
					output = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}"
					f.write(output + '\n')

					# Update progress as percentage
					percentage = int((segment.end / total_duration) * 100)
					self.progressUpdate.emit(
						"Transcribing audio",
						f"{percentage}%",
						percentage,
						100
					)

			# Step 3: Complete
			output_name = os.path.basename(output_file)
			self.progressUpdate.emit(
				"Transcription complete!",
				f'Output file: "{output_name}"',
				100,
				100
			)
			self.transcriptionComplete.emit(output_file)

		except Exception as e:
			self.transcriptionError.emit(str(e))

	def __get_best_device(self) -> str:
		if self.__has_cuda_via_nvidia_smi():
			return 'cuda'
		# manually setting 'mps' doesn't seem to work on macOS for this model
		return 'auto'

	def __has_cuda_via_nvidia_smi(self) -> bool:
		try:
			subprocess.check_output(['nvidia-smi'], stderr=subprocess.DEVNULL)
			return True
		except (FileNotFoundError, subprocess.CalledProcessError):
			return False