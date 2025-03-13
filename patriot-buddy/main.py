import sys
from VoiceAssistantGUI import VoiceAssistantGUI
from PySide6.QtWidgets import (QApplication)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceAssistantGUI()
    window.show()
    sys.exit(app.exec())
