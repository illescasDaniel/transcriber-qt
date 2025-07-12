import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import Qt.labs.platform as Platform
import QtQuick.Controls.Material

ApplicationWindow {
	id: window
	width: 600
	height: Math.max(450, contentLayout.implicitHeight + 40) // Dynamic height based on content
	minimumHeight: 450
	visible: true
	title: qsTr("TranscriberQt - Audio Transcription Tool with Speaker Diarization")

	// Force Material theme with explicit colors
	Material.theme: Material.Light
	Material.accent: Material.Blue

	Rectangle {
		anchors.fill: parent
		color: "#f5f5f5"

		ColumnLayout {
			id: contentLayout
			anchors.fill: parent
			anchors.margins: 20
			spacing: 20

			// Drag and Drop Area
			Rectangle {
				id: dropArea
				Layout.fillWidth: true
				Layout.preferredHeight: 200
				color: dropZone.containsDrag ? "#e3f2fd" : "#ffffff"
				border.color: dropZone.containsDrag ? "#2196f3" : "#e0e0e0"
				border.width: 2
				radius: 8

				Behavior on color {
					ColorAnimation { duration: 150 }
				}

				DropArea {
					id: dropZone
					anchors.fill: parent
					keys: [
						"text/uri-list",
						// Audio MIME types
						"audio/mpeg", "audio/wav", "audio/mp4", "audio/flac", "audio/ogg",
						"audio/opus", "audio/x-ms-wma", "audio/aac",
						// Video MIME types
						"video/mp4", "video/avi", "video/x-msvideo", "video/quicktime",
						"video/x-ms-wmv", "video/x-flv", "video/webm", "video/x-matroska",
						"video/3gpp", "video/mp2t"
					]

					onEntered: (drag) => {
						drag.accept()
					}

					onDropped: (drop) => {
						if (drop.hasUrls) {
							controller.setAudioFile(drop.urls[0])
						}
					}
				}

				Column {
					anchors.centerIn: parent
					spacing: 10

					Image {
						source: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='%23999999' stroke-width='2'><path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'></path><polyline points='7 10 12 15 17 10'></polyline><line x1='12' y1='15' x2='12' y2='3'></line></svg>"
						anchors.horizontalCenter: parent.horizontalCenter
						opacity: 0.5
					}

					Text {
						text: controller.audioFileName || qsTr("Drag and drop video or audio file here")
						font.pixelSize: 14
						color: controller.audioFileName ? "#2e7d32" : "#666666"
						anchors.horizontalCenter: parent.horizontalCenter
					}

					Text {
						text: qsTr("Supported: MP3, WAV, M4A, FLAC, OGG, OPUS, WMA, AAC, MP4, AVI, MKV, MOV, WMV, FLV, WebM, 3GP,")
						font.pixelSize: 10
						color: "#999999"
						anchors.horizontalCenter: parent.horizontalCenter
						visible: !controller.audioFileName
					}
				}

				MouseArea {
					anchors.fill: parent
					onClicked: fileDialog.open()
				}
			}

			// Output File Section
			RowLayout {
				Layout.fillWidth: true
				spacing: 10

				Text {
					text: qsTr("Output File:")
					font.pixelSize: 14
					color: "#000000"
				}

				TextField {
					id: outputField
					Layout.fillWidth: true
					text: controller.outputFile
					placeholderText: qsTr("Enter output file path...")
					onTextChanged: controller.outputFile = text
					color: "#000000"
					placeholderTextColor: "#999999"

					background: Rectangle {
						color: "#ffffff"
						border.color: outputField.activeFocus ? "#2196f3" : "#e0e0e0"
						border.width: 1
						radius: 4
					}
				}

				Button {
					text: qsTr("Browse")

					contentItem: Text {
						text: parent.text
						font.pixelSize: 14
						color: "#000000"
						horizontalAlignment: Text.AlignHCenter
						verticalAlignment: Text.AlignVCenter
					}

					onClicked: saveDialog.open()
				}
			}

			// Speaker Settings Section
			RowLayout {
				Layout.fillWidth: true
				spacing: 20

				// Minimum Speakers
				RowLayout {
					spacing: 10

					Text {
						text: qsTr("Minimum Speakers:")
						font.pixelSize: 14
						color: "#000000"
					}

					SpinBox {
						id: minSpeakersSpinBox
						from: 1
						to: 99
						value: controller.minSpeakers
						editable: true

						onValueChanged: {
							controller.minSpeakers = value
						}

						background: Rectangle {
							color: "#ffffff"
							border.color: minSpeakersSpinBox.activeFocus ? "#2196f3" : "#e0e0e0"
							border.width: 1
							radius: 4
						}
					}
				}

				// Maximum Speakers
				RowLayout {
					spacing: 10

					Text {
						text: qsTr("Maximum Speakers:")
						font.pixelSize: 14
						color: "#000000"
					}

					SpinBox {
						id: maxSpeakersSpinBox
						from: 1
						to: 99
						value: controller.maxSpeakers
						editable: true

						onValueChanged: {
							controller.maxSpeakers = value
						}

						background: Rectangle {
							color: "#ffffff"
							border.color: maxSpeakersSpinBox.activeFocus ? "#2196f3" : "#e0e0e0"
							border.width: 1
							radius: 4
						}
					}
				}
			}

			// Help text for speaker settings
			Text {
				Layout.fillWidth: true
				text: qsTr("Set both values to 1 to disable speaker diarization")
				font.pixelSize: 11
				color: "#666666"
				font.italic: true
				horizontalAlignment: Text.AlignHCenter
			}

			// Transcribe Button
			Button {
				id: transcribeButton
				Layout.alignment: Qt.AlignHCenter
				Layout.preferredWidth: 200
				Layout.preferredHeight: 40
				text: qsTr("Transcribe")
				enabled: controller.canTranscribe

				contentItem: Text {
					text: transcribeButton.text
					font.pixelSize: 16
					color: transcribeButton.enabled ? "#ffffff" : "#999999"
					horizontalAlignment: Text.AlignHCenter
					verticalAlignment: Text.AlignVCenter
				}

				background: Rectangle {
					color: transcribeButton.enabled ?
						   (transcribeButton.pressed ? "#1976d2" : "#2196f3") : "#e0e0e0"
					radius: 4

					Behavior on color {
						ColorAnimation { duration: 100 }
					}
				}

				onClicked: controller.startTranscription()
			}

			// Status Label
			Text {
				Layout.alignment: Qt.AlignHCenter
				text: controller.statusMessage
				color: controller.statusColor
				font.pixelSize: 12
				visible: text !== ""
			}
		}
	}

	// Progress Dialog
	Dialog {
		id: progressDialog
		anchors.centerIn: parent
		modal: true
		closePolicy: Dialog.NoAutoClose
		visible: controller.isTranscribing

		width: 400
		height: 250

		background: Rectangle {
			color: "#ffffff"
			radius: 8
			border.color: "#e0e0e0"
		}

		contentItem: ColumnLayout {
			spacing: 20

			Text {
				Layout.alignment: Qt.AlignHCenter
				text: controller.progressStage
				font.pixelSize: 14
				font.bold: true
				color: "#000000"
			}

			ProgressBar {
				id: progressBar
				Layout.fillWidth: true
				Layout.preferredHeight: 8
				from: 0
				to: controller.totalSegments
				value: controller.currentSegment
				indeterminate: controller.progressStage.includes("Loading") ||
							  controller.progressStage.includes("Transcribing") ||
							  controller.progressStage.includes("Aligning") ||
							  controller.progressStage.includes("Identifying")

				background: Rectangle {
					color: "#e0e0e0"
					radius: 4
				}

				contentItem: Item {
					Rectangle {
						width: progressBar.visualPosition * parent.width
						height: parent.height
						radius: 4
						color: "#2196f3"
					}
				}
			}

			Text {
				Layout.alignment: Qt.AlignHCenter
				Layout.fillWidth: true
				Layout.maximumWidth: parent.width * 0.9
				text: controller.progressDetail
				font.pixelSize: 12
				color: "#666666"
				visible: text !== ""
				wrapMode: Text.WordWrap
				horizontalAlignment: Text.AlignHCenter
			}

			Button {
				Layout.alignment: Qt.AlignHCenter
				text: qsTr("Close")
				visible: controller.progressStage.includes("complete")

				contentItem: Text {
					text: parent.text
					font.pixelSize: 14
					color: "#000000"
					horizontalAlignment: Text.AlignHCenter
					verticalAlignment: Text.AlignVCenter
				}

				onClicked: controller.closeProgress()
			}
		}
	}

	// File Dialogs
	FileDialog {
		id: fileDialog
		title: qsTr("Select Audio File")
		nameFilters: [
			"Media files (*.mp3 *.wav *.m4a *.flac *.ogg *.opus *.wma *.aac *.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp *.ts *.mts *.m2ts)",
			"All files (*)"
		]
		onAccepted: {
			controller.setAudioFile(selectedFile)
		}
		onRejected: {

		}
	}

	FileDialog {
		id: saveDialog
		title: qsTr("Save Transcription As")
		fileMode: FileDialog.SaveFile
		nameFilters: ["Text files (*.txt)", "All files (*)"]
		defaultSuffix: "txt"
		onAccepted: {
			controller.manuallSetOutputFile(selectedFile)
		}
		onRejected: {

		}
	}
}