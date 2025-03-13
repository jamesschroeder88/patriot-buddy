from PySide6.QtWidgets import (QFrame)


class ModernFrame(QFrame):
    """Custom frame with modern styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            ModernFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }}
        """)