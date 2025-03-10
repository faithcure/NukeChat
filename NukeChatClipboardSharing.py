"""
NukeChatClipboardSharing.py

This module enables sharing Nuke script parts through NukeChat using copy-paste method.
"""

import nuke
import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
import json
import base64
import os
import re


class ScriptBubbleWidget(QtWidgets.QWidget):
    """Widget that displays Nuke script part as a bubble"""

    def __init__(self, script_data, parent=None):
        super(ScriptBubbleWidget, self).__init__(parent)

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Script bubble container
        self.bubble = QtWidgets.QFrame()
        self.bubble.setObjectName("scriptBubble")
        self.bubble.setStyleSheet("""
            #scriptBubble {
                background-color: #2D2D2D;
                border: 1px solid #555555;
                border-radius: 8px;
            }
        """)

        bubble_layout = QtWidgets.QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(10, 10, 10, 10)
        bubble_layout.setSpacing(8)

        # Title layout
        header_layout = QtWidgets.QHBoxLayout()

        # Script icon
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("""
            background-color: #444444;
            border-radius: 2px;
            border: 1px solid #777777;
        """)
        header_layout.addWidget(icon_label)

        # Determine the number of nodes
        node_count = self.countNodes(script_data["script"])
        node_text = f"{node_count} Node" if node_count == 1 else f"{node_count} Nodes"

        # Check the description text - show description if available, otherwise show default value
        description = script_data.get("description", "")
        if description:
            header_title = QtWidgets.QLabel(f"<b>{description}</b> ({node_text})")
        else:
            header_title = QtWidgets.QLabel(f"<b>Script Part</b> ({node_text})")

        header_title.setStyleSheet("color: #FFFFFF; font-size: 13px;")
        header_layout.addWidget(header_title)
        header_layout.addStretch(1)

        # Removed checkbox - there's no selection box here anymore

        bubble_layout.addLayout(header_layout)

        # Line separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setStyleSheet("border: 1px solid #444444;")
        bubble_layout.addWidget(line)

        # Script code area
        script_text = QtWidgets.QTextEdit()
        script_text.setReadOnly(True)
        script_text.setPlainText(script_data["script"])
        script_text.setStyleSheet("""
            QTextEdit {
                background-color: #222222;
                color: #CCCCCC;
                border: 1px solid #444444;
                font-family: "Courier New", monospace;
                font-size: 12px;
                padding: 5px;
            }
        """)

        # Maximum height for script area
        script_text.setMaximumHeight(250)
        bubble_layout.addWidget(script_text)

        # Layout for button
        buttons_layout = QtWidgets.QHBoxLayout()

        # "Copy" button
        copy_button = QtWidgets.QPushButton("Copy")
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
            QPushButton:pressed {
                background-color: #2D2D2D;
            }
        """)
        copy_button.clicked.connect(lambda: self.copyScriptToClipboard(script_data["script"]))
        buttons_layout.addWidget(copy_button)

        bubble_layout.addLayout(buttons_layout)
        layout.addWidget(self.bubble)

    def copyScriptToClipboard(self, script):
        """Copies script to clipboard"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(script)

        # Show feedback to user in status bar
        try:
            # Check if there's a global statusbar in Nuke main module
            import nuke
            if hasattr(nuke, 'NukeChat') and hasattr(nuke.NukeChat, 'updateStatus'):
                nuke.NukeChat.updateStatus("Script copied to clipboard!")
            else:
                # Alternatively show with QToolTip
                tooltip = QtWidgets.QToolTip
                tooltip.showText(QtGui.QCursor.pos(), "Script copied to clipboard!")
        except:
            # If Nuke is not available or error occurs, show a simple tooltip
            tooltip = QtWidgets.QToolTip
            tooltip.showText(QtGui.QCursor.pos(), "Script copied to clipboard!")

    def countNodes(self, script):
        """Determines the number of nodes in the script"""
        # Use a simple count to find the number of nodes
        # This method should be improved for more complex scripts
        node_count = 0
        for line in script.splitlines():
            # Node lines typically contain a name and curly brackets
            if re.search(r'\w+\s*\{', line) and not line.strip().startswith('#'):
                node_count += 1
        return node_count


class ClipboardHandler(QtCore.QObject):
    """Monitors clipboard changes and identifies Nuke script parts"""

    def __init__(self, parent=None):
        super(ClipboardHandler, self).__init__(parent)
        self.parent = parent

        # Get reference to the clipboard object
        self.clipboard = QtWidgets.QApplication.clipboard()

    def checkClipboard(self):
        """Checks clipboard content and returns True if it's a Nuke script part"""
        try:
            # Get text from clipboard
            clipboard_text = self.clipboard.text()

            # Check if it's a Nuke script part
            if clipboard_text and self.isNukeScript(clipboard_text):
                return True
        except:
            pass

        return False

    def isNukeScript(self, text):
        """Checks if the text is a Nuke script part"""
        # Check for typical signatures of Nuke scripts
        nuke_indicators = [
            "set cut_paste_input",
            "version",
            "push $",
            "Blur {",
            "Grade {",
            "Transform {",
            "Merge2 {",
            "Read {",
            "Write {",
            "ColorCorrect {",
            "xpos",
            "ypos"
        ]

        # If the text contains at least a few of these indicators, it's probably a Nuke script
        indicator_count = 0
        for indicator in nuke_indicators:
            if indicator in text:
                indicator_count += 1

        # Accept as a Nuke script if there are at least 3 indicators
        return indicator_count >= 3

    def getScriptFromClipboard(self):
        """Gets Nuke script from clipboard and processes it"""
        clipboard_text = self.clipboard.text()

        if clipboard_text and self.isNukeScript(clipboard_text):
            # Format as script data
            script_data = {
                "script": clipboard_text,
                "type": "script"
            }

            return script_data

        return None


def encodeScriptData(script_data):
    """Converts script data to a JSON string, then encodes with base64"""
    try:
        # Convert script data to JSON string
        json_str = json.dumps(script_data, ensure_ascii=False)

        # Encode with base64
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

        return encoded
    except Exception as e:
        print(f"Script data encoding error: {str(e)}")
        return None


def decodeScriptData(encoded_data):
    """Decodes base64 encoded JSON script data"""
    try:
        # Decode base64 code
        json_str = base64.b64decode(encoded_data.encode('utf-8')).decode('utf-8')

        # Convert from JSON to dict
        script_data = json.loads(json_str)

        return script_data
    except Exception as e:
        print(f"Script data decoding error: {str(e)}")
        return None
