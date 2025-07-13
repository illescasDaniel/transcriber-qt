import os
from typing import Optional

import torch
from PySide6.QtCore import QObject, Signal
from faster_whisper import WhisperModel
import whisperx
from whisperx.diarize import DiarizationPipeline


class TranscriptionModel(QObject):
	"""Model: Handles the transcription logic and data"""

	progressUpdate = Signal(str, str, int, int)  # stage, detail, current, total
	transcriptionComplete = Signal()
	transcriptionError = Signal(str)

	def __init__(self):
		super().__init__()
		self.faster_whisper_model = None
		self.diarize_model: Optional[DiarizationPipeline] = None
		self.audio_file: str = ""
		self.output_file: str = ""
		self.device = self.__get_best_device()
		self.compute_type = 'float16' if self.device == 'cuda' else 'int8'

	def load_model(self):
		if not self.faster_whisper_model:
			cpu_count = os.cpu_count()
			self.faster_whisper_model = WhisperModel(
				'deepdml/faster-whisper-large-v3-turbo-ct2',
				device=self.device,
				compute_type=self.compute_type,
				cpu_threads=cpu_count if cpu_count is not None else 0
			)

	def load_diarization_model(self):
		if not self.diarize_model:
			self.diarize_model = DiarizationPipeline(use_auth_token=os.environ['HF_TOKEN'], device=self.device)

	def transcribe(self, audio_file: str, output_file: str, min_speakers: int, max_speakers: int):
		self.audio_file = audio_file
		self.output_file = output_file

		try:
			# Determine total steps based on whether we need diarization
			total_steps = 5 if max_speakers > 1 else 3
			current_step = 0

			# Step 1: Load models
			current_step += 1
			self.progressUpdate.emit(
				f'Step {current_step}/{total_steps}: Loading transcription model',
				'This may take a moment on first run...',
				0, 0
			)
			self.load_model()

			if not self.faster_whisper_model:
				self.transcriptionError.emit('Transcription model not loaded')
				return

			# Step 2: Transcribe with faster-whisper (with real progress!)
			current_step += 1
			self.progressUpdate.emit(
				f'Step {current_step}/{total_steps}: Transcribing audio',
				'0%',
				0, 100
			)

			# Use faster-whisper for transcription with progress tracking
			segments_list = []
			segments_generator, info = self.faster_whisper_model.transcribe(
				audio_file,
				word_timestamps=True
			)

			total_duration = info.duration

			# Collect segments and track progress
			for segment in segments_generator:
				segments_list.append({
					'start': segment.start,
					'end': segment.end,
					'text': segment.text.strip(),
					'words': [
						{
							'start': word.start,
							'end': word.end,
							'word': word.word,
							'probability': word.probability
						} for word in segment.words
					] if segment.words else []
				})

				# Update progress
				percentage = int((segment.end / total_duration) * 100)
				self.progressUpdate.emit(
					f'Step {current_step}/{total_steps}: Transcribing audio',
					f'{percentage}%',
					percentage,
					100
				)

			# Ensure we show 100% completion
			self.progressUpdate.emit(
				f'Step {current_step}/{total_steps}: Transcribing audio',
				'100%',
				100, 100
			)

			# Create result in WhisperX format
			result = {
				'segments': segments_list,
				'language': info.language
			}

			# Step 3: Align transcript using WhisperX
			current_step += 1
			self.progressUpdate.emit(
				f'Step {current_step}/{total_steps}: Aligning transcript',
				'Loading alignment model...',
				0, 100
			)

			# Load audio for WhisperX
			audio = whisperx.load_audio(audio_file)

			# Load alignment model
			model_a, metadata = whisperx.load_align_model(
				language_code=result["language"],
				device=self.device
			)

			self.progressUpdate.emit(
				f'Step {current_step}/{total_steps}: Aligning transcript',
				'Aligning segments...',
				50, 100
			)

			# Align segments
			result = whisperx.align(
				result["segments"],
				model_a,
				metadata,
				audio,
				self.device,
				return_char_alignments=False
			)

			self.progressUpdate.emit(
				f'Step {current_step}/{total_steps}: Aligning transcript',
				'100%',
				100, 100
			)

			# Step 4 & 5: Diarize (only if we expect multiple speakers)
			if max_speakers > 1:
				# Step 4: Load diarization model
				current_step += 1
				self.progressUpdate.emit(
					f'Step {current_step}/{total_steps}: Loading speaker diarization',
					'Loading diarization model...',
					0, 0
				)
				self.load_diarization_model()

				if not self.diarize_model:
					self.transcriptionError.emit('Diarization model not loaded')
					return

				# Step 5: Identify speakers
				current_step += 1
				self.progressUpdate.emit(
					f'Step {current_step}/{total_steps}: Identifying speakers',
					'Processing speaker segments...',
					0, 100
				)

				diarize_segments = self.diarize_model(
					audio_file,
					min_speakers=min_speakers,
					max_speakers=max_speakers
				)

				self.progressUpdate.emit(
					f'Step {current_step}/{total_steps}: Identifying speakers',
					'Assigning speaker labels...',
					50, 100
				)

				result = whisperx.assign_word_speakers(
					diarize_segments,
					result
				)

				self.progressUpdate.emit(
					f'Step {current_step}/{total_steps}: Identifying speakers',
					'100%',
					100, 100
				)

			# Final Step: Write output
			current_step = total_steps  # This ensures we're on the final step
			self.progressUpdate.emit(
				f'Step {current_step}/{total_steps}: Writing transcript',
				'0%',
				0, 100
			)

			# Calculate progress based on segments written
			total_segments = len(result['segments'])
			segments_written = 0

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

					# Update progress
					segments_written += 1
					percentage = int((segments_written / total_segments) * 100)
					self.progressUpdate.emit(
						f'Step {current_step}/{total_steps}: Writing transcript',
						f'{percentage}%',
						percentage,
						100
					)

			# Complete
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
		if torch.cuda.is_available():
			print("info: GPU Support enabled")
			return 'cuda'
		# 'mps' doesn't seem to work on macOS for this model, it might not be supported yet
		print("info: No GPU Support")
		return 'cpu'