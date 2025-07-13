from PySide6.QtCore import QThread

from transcription_model import TranscriptionModel


class TranscriptionThread(QThread):
	"""Worker thread for transcription"""

	def __init__(self, model: TranscriptionModel, audio_file: str, output_file: str, min_speakers: int, max_speakers: int):
		super().__init__()
		self.model = model
		self.audio_file = audio_file
		self.output_file = output_file
		self.min_speakers = min_speakers
		self.max_speakers = max_speakers

	def run(self):
		self.model.transcribe(self.audio_file, self.output_file, self.min_speakers, self.max_speakers)