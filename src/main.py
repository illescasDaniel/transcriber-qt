import sys

from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine

from transcription_controller import TranscriptionController


if __name__ == "__main__":
	app = QApplication(sys.argv)

	# Create controller instance first
	controller = TranscriptionController()

	engine = QQmlApplicationEngine()

	# Make controller available to QML before loading
	engine.rootContext().setContextProperty("controller", controller)

	# Load QML
	qml_file = Path(__file__).parent / "TranscriptionView.qml"
	engine.load(qml_file)

	if not engine.rootObjects():
		sys.exit(-1)

	sys.exit(app.exec())
