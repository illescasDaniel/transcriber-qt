from PySide6.QtCore import QThread


class TranscriptionThread(QThread):
	"""Worker thread for transcription"""

	def __init__(self, model, audio_file, output_file):
		super().__init__()
		self.model = model
		self.audio_file = audio_file
		self.output_file = output_file

	def run(self):
		self.model.transcribe(self.audio_file, self.output_file)
