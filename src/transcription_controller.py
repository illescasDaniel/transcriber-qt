import os

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from transcription_model import TranscriptionModel
from transcription_thread import TranscriptionThread


class TranscriptionController(QObject):
	"""Controller: Manages UI state and mediates between view and model"""

	# Property notifications
	audioFileNameChanged = Signal()
	outputFileChanged = Signal()
	canTranscribeChanged = Signal()
	isTranscribingChanged = Signal()
	statusMessageChanged = Signal()
	statusColorChanged = Signal()
	progressStageChanged = Signal()
	progressDetailChanged = Signal()
	currentSegmentChanged = Signal()
	totalSegmentsChanged = Signal()
	minSpeakersChanged = Signal()
	maxSpeakersChanged = Signal()

	def __init__(self):
		super().__init__()
		self._audio_file = ""
		self._audio_file_name = ""
		self._output_file = ""
		self._can_transcribe = False
		self._is_transcribing = False
		self._status_message = ""
		self._status_color = "#2196f3"
		self._progress_stage = ""
		self._progress_detail = ""
		self._current_segment = 0
		self._total_segments = 0
		self._min_speakers = 1
		self._max_speakers = 1

		# Create model
		self.model = TranscriptionModel()
		self.model.progressUpdate.connect(self._on_progress_update)
		self.model.transcriptionComplete.connect(self._on_transcription_complete)
		self.model.transcriptionError.connect(self._on_transcription_error)

		self.worker_thread = None

	# Properties
	@Property(str, notify=audioFileNameChanged) # type: ignore
	def audioFileName(self):
		return self._audio_file_name

	@Property(str, notify=outputFileChanged) # type: ignore
	def outputFile(self) -> str: # type: ignore
		return self._output_file

	@outputFile.setter
	def outputFile(self, value: str):
		if self._output_file != value:
			self._output_file = value
			self.outputFileChanged.emit()
			self._update_can_transcribe()

	@Property(bool, notify=canTranscribeChanged) # type: ignore
	def canTranscribe(self):
		return self._can_transcribe

	@Property(bool, notify=isTranscribingChanged) # type: ignore
	def isTranscribing(self):
		return self._is_transcribing

	@Property(str, notify=statusMessageChanged) # type: ignore
	def statusMessage(self):
		return self._status_message

	@Property(str, notify=statusColorChanged) # type: ignore
	def statusColor(self):
		return self._status_color

	@Property(str, notify=progressStageChanged) # type: ignore
	def progressStage(self):
		return self._progress_stage

	@Property(str, notify=progressDetailChanged) # type: ignore
	def progressDetail(self):
		return self._progress_detail

	@Property(int, notify=currentSegmentChanged) # type: ignore
	def currentSegment(self):
		return self._current_segment

	@Property(int, notify=totalSegmentsChanged) # type: ignore
	def totalSegments(self):
		return self._total_segments

	@Property(int, notify=minSpeakersChanged) # type: ignore
	def minSpeakers(self): # type: ignore
		return self._min_speakers

	@minSpeakers.setter
	def minSpeakers(self, value: int):
		if value > 0 and self._min_speakers != value:
			self._min_speakers = value
			# Ensure max is at least equal to min
			if self._max_speakers < value:
				self.maxSpeakers = value # type: ignore
			self.minSpeakersChanged.emit()

	@Property(int, notify=maxSpeakersChanged) # type: ignore
	def maxSpeakers(self): # type: ignore
		return self._max_speakers

	@maxSpeakers.setter
	def maxSpeakers(self, value: int):
		if value > 0 and self._max_speakers != value:
			self._max_speakers = value
			# Ensure min is not greater than max
			if self._min_speakers > value:
				self.minSpeakers = value # type: ignore
			self.maxSpeakersChanged.emit()

	# Methods

	@Slot(str)
	def manuallSetOutputFile(self, file_url: str):
		url = QUrl(file_url)
		if url.isLocalFile():
			file_path = url.toLocalFile()
		else:
			file_path = file_url.replace('file://', '')
		if file_path:
			self.outputFile = file_path # type: ignore

	@Slot(str)
	def setAudioFile(self, file_url: str):
		# Convert QUrl to path
		url = QUrl(file_url)
		if url.isLocalFile():
			file_path = url.toLocalFile()
		else:
			file_path = file_url.replace('file://', '')

		# Validate audio file
		if os.path.isfile(file_path):
			self._audio_file = file_path
			self._audio_file_name = os.path.basename(file_path)
			self.audioFileNameChanged.emit()

			# Auto-suggest output file
			base_name = os.path.splitext(file_path)[0]
			self.outputFile = f"{base_name}_transcript.txt" # type: ignore

			self._set_status(f"Audio file loaded: {self._audio_file_name}", "#2e7d32")
			self._update_can_transcribe()
		else:
			self._set_status("Invalid audio file format", "#d32f2f")

	@Slot()
	def startTranscription(self):
		if not self._can_transcribe:
			return

		self._is_transcribing = True
		self.isTranscribingChanged.emit()
		self._set_status("", "")

		# Start transcription in worker thread
		self.worker_thread = TranscriptionThread(
			self.model,
			self._audio_file,
			self._output_file,
			self._min_speakers,
			self._max_speakers
		)
		self.worker_thread.start()

	@Slot()
	def closeProgress(self):
		self._is_transcribing = False
		self.isTranscribingChanged.emit()
		self._progress_stage = ""
		self.progressStageChanged.emit()

	def _update_can_transcribe(self):
		can_transcribe = bool(self._audio_file and self._output_file)
		if self._can_transcribe != can_transcribe:
			self._can_transcribe = can_transcribe
			self.canTranscribeChanged.emit()

	def _set_status(self, message, color):
		self._status_message = message
		self._status_color = color
		self.statusMessageChanged.emit()
		self.statusColorChanged.emit()

	def _on_progress_update(self, stage, detail, current, total):
		self._progress_stage = stage
		self._progress_detail = detail
		self._current_segment = current
		self._total_segments = total

		self.progressStageChanged.emit()
		self.progressDetailChanged.emit()
		self.currentSegmentChanged.emit()
		self.totalSegmentsChanged.emit()

	def _on_transcription_complete(self):
		self._set_status("Transcription completed successfully!", "#2e7d32")

	def _on_transcription_error(self, error_msg):
		self._is_transcribing = False
		self.isTranscribingChanged.emit()
		self._set_status(f"Error: {error_msg}", "#d32f2f")
