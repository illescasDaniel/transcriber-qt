import os
import subprocess
from typing import Optional

from PySide6.QtCore import QObject, Signal
import whisperx
from whisperx.diarize import DiarizationPipeline


class TranscriptionModel(QObject):
	"""Model: Handles the transcription logic and data"""

	progressUpdate = Signal(str, str, int, int)  # stage, detail, current, total
	transcriptionComplete = Signal()
	transcriptionError = Signal(str)

	def __init__(self):
		super().__init__()
		self.model = None
		self.diarize_model: Optional[DiarizationPipeline] = None
		self.audio_file: str = ""
		self.output_file: str = ""
		self.device = self.__get_best_device()
		self.compute_type = 'float16' if self.device == 'cuda' else 'int8'

	def load_model(self):
		if not self.model:
			self.model = whisperx.load_model(
				'deepdml/faster-whisper-large-v3-turbo-ct2',
				self.device,
				compute_type=self.compute_type,
				language='en'  # TODO: change??
			)

	def load_diarization_model(self):
		if not self.diarize_model:
			self.diarize_model = DiarizationPipeline(use_auth_token=os.environ['HF_TOKEN'], device=self.device)

	def transcribe(self, audio_file: str, output_file: str, min_speakers: int = 1, max_speakers: int = 1):

		self.audio_file = audio_file
		self.output_file = output_file

		try:
			# Step 0: Load models
			self.progressUpdate.emit('Loading transcription model...', '', 0, 0)
			self.load_model()

			if not self.model:
				self.transcriptionError.emit('Main model not loaded')
				return

			# Step 1: Transcribe with WhisperX
			self.progressUpdate.emit('Transcribing audio...', '', 0, 0)

			audio = whisperx.load_audio(audio_file)

			result = self.model.transcribe(audio, batch_size=16)

			# Step 2: Align whisper output
			self.progressUpdate.emit("Aligning transcript...", "", 25, 100)
			model_a, metadata = whisperx.load_align_model(
				language_code=result["language"],
				device=self.device
			)

			result = whisperx.align(
				result["segments"],
				model_a,
				metadata,
				audio,
				self.device,
				return_char_alignments=False
			)

			# Step 3: Diarize (only if we expect multiple speakers)
			if max_speakers > 1:
				self.progressUpdate.emit('Loading speaker diarization model...', '', 50, 100)
				self.load_diarization_model()

				if not self.diarize_model:
					self.transcriptionError.emit('Diarization model not loaded')
					return

				self.progressUpdate.emit('Identifying speakers...', '', 60, 100)
				diarize_segments = self.diarize_model(
					audio_file,
					min_speakers=min_speakers,
					max_speakers=max_speakers
				)

				# Assign speaker labels
				self.progressUpdate.emit('Assigning speaker labels...', '', 75, 100)
				result = whisperx.assign_word_speakers(
					diarize_segments,
					result
				)

			# Step 4: Write output

			# TODO: fix progress!!!

			self.progressUpdate.emit('Writing transcript...', '', 90, 100)
			with open(output_file, 'w', buffering=8192) as f:
				for segment in result['segments']:
					# Format with speaker info if available
					if 'speaker' in segment and max_speakers > 1:
						speaker_label = f'[Speaker {segment["speaker"]}]'
					else:
						speaker_label = ""

					start_time = segment.get('start', 0)
					end_time = segment.get('end', 0)
					text = segment.get('text', '').strip()

					output = f"[{start_time:.2f}s -> {end_time:.2f}s] {speaker_label} {text}"
					f.write(output + '\n')

			# Step 5: Complete
			output_name = os.path.basename(output_file)
			self.progressUpdate.emit(
				'Transcription complete!',
				f'Output file: "{output_name}"',
				100,
				100
			)
			self.transcriptionComplete.emit()

		except Exception as e:
			self.transcriptionError.emit(str(e))

	def __get_best_device(self) -> str:
		if self.__has_cuda_via_nvidia_smi():
			return 'cuda'
		# 'mps' doesn't seem to work on macOS for this model, it might not be supported yet
		return 'auto'

	def __has_cuda_via_nvidia_smi(self) -> bool:
		try:
			subprocess.check_output(['nvidia-smi'], stderr=subprocess.DEVNULL)
			return True
		except (FileNotFoundError, subprocess.CalledProcessError):
			return False
