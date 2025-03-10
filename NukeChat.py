import os
import sys
import socket
import datetime
import time
import random
import json
import nuke
import hashlib
import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
from PySide2.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from nukescripts import panels
from NukeChatClipboardSharing import ScriptBubbleWidget, ClipboardHandler, encodeScriptData, decodeScriptData
from AvatarManager import AvatarManager, AvatarUploadDialog

class ToastNotification(QtWidgets.QWidget):
    """Notification window that appears briefly in the bottom right corner of the screen"""

    def __init__(self, message, sender="", parent=None, duration=3000):
        super(ToastNotification, self).__init__(parent)
        self.duration = duration

        # Window settings
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Notification panel - LIGHT GRAY background
        self.notification_frame = QtWidgets.QFrame()
        self.notification_frame.setStyleSheet("""
            QFrame {
                background-color: #DDDDDD;
                border-radius: 8px;
                border: 1px solid #BBBBBB;
            }
        """)
        frame_layout = QtWidgets.QVBoxLayout(self.notification_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)

        # Content layout (avatar + message)
        content_layout = QtWidgets.QHBoxLayout()

        # Show avatar
        avatar_label = QtWidgets.QLabel()
        avatar_label.setFixedSize(40, 40)
        avatar_label.setStyleSheet("border-radius: 20px;")  # Rounded avatar

        if sender:
            # Create avatar from sender information
            sender_parts = sender.split(' - ')
            if len(sender_parts) > 1 and sender_parts[1].startswith('(') and sender_parts[1].endswith(')'):
                # Username format: "Name - (computer_name)"
                hostname = sender_parts[1][1:-1]  # Remove parentheses
                # Use hostname as avatar ID
                avatar_pixmap = parent.avatar_manager.load_avatar(hostname, 40)
            else:
                # Plain username - use username directly as avatar ID
                avatar_pixmap = parent.avatar_manager.load_avatar(sender, 40)
        else:
            # If no sender, use system avatar
            avatar_pixmap = parent.avatar_manager.create_default_avatar("system", 40)

        avatar_label.setPixmap(avatar_pixmap)
        content_layout.addWidget(avatar_label)

        # Message content
        message_label = QtWidgets.QLabel(message)
        message_label.setStyleSheet("color: #333333;")
        message_label.setWordWrap(True)
        content_layout.addWidget(message_label, 1)  # 1=stretch factor

        # Close button - top right
        close_button = QtWidgets.QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #777777;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #333333;
            }
        """)
        close_button.clicked.connect(self.close)
        content_layout.addWidget(close_button, 0, QtCore.Qt.AlignTop)

        frame_layout.addLayout(content_layout)
        layout.addWidget(self.notification_frame)

        # Timer for auto-close
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.fadeOut)
        self.timer.setSingleShot(True)

        # Opacity effect for animation
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)

        # Fade-in animation
        self.fade_in_anim = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(300)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)

        # Fade-out animation
        self.fade_out_anim = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self.close)

        # Size
        self.setFixedWidth(300)
        self.adjustSize()

    def showEvent(self, event):
        """Capture show event and start animations"""
        super(ToastNotification, self).showEvent(event)

        # Position in the bottom right corner of the screen
        desktop = QtWidgets.QApplication.desktop()
        screen_rect = desktop.screenGeometry()
        self.move(screen_rect.width() - self.width() - 20,
                  screen_rect.height() - self.height() - 20)

        # Start fade-in animation
        self.fade_in_anim.start()

        # Start close timer after a certain duration
        self.timer.start(self.duration)

    def fadeOut(self):
        """Start fade-out animation"""
        self.fade_out_anim.start()
class MessageWidget(QtWidgets.QWidget):
    def __init__(self, username, timestamp, message, is_self=False, parent=None, row_index=0):
        super(MessageWidget, self).__init__(parent)

        # Make row color alternate - dark gray and slightly darker gray
        if row_index % 2 == 0:
            bg_color = "#333333"
        else:
            bg_color = "#2D2D2D"

        # Set the entire widget background
        self.setStyleSheet(f"background-color: {bg_color}; color: white;")

        # Expand main layout and make it fill the entire area
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # No spacing

        # Content container - expanded to cover the full width
        container = QtWidgets.QWidget()
        container.setStyleSheet(f"background-color: {bg_color};")
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        container_layout = QtWidgets.QHBoxLayout(container)

        # Our own messages on the right, others on the left
        if is_self:
            container_layout.addStretch(1)  # Add empty space to align right

        # Use AvatarManager for avatar
        avatar_label = QtWidgets.QLabel()
        avatar_label.setFixedSize(50, 50)

        # Get AvatarManager reference from parent
        avatar_manager = None
        if parent and hasattr(parent, 'avatar_manager'):
            avatar_manager = parent.avatar_manager
        else:
            # If can't access directly, try to get from main application
            main_app = QtWidgets.QApplication.instance()
            for widget in main_app.topLevelWidgets():
                if hasattr(widget, 'avatar_manager'):
                    avatar_manager = widget.avatar_manager
                    break

        # Try to extract computer name from username
        user_parts = username.split(' - ')
        if len(user_parts) > 1 and user_parts[1].startswith('(') and user_parts[1].endswith(')'):
            # Username format: "Name - (computer_name)"
            hostname = user_parts[1][1:-1]  # Remove parentheses
            user_id = hostname  # Use computer name as user ID
        else:
            # Plain username - use username directly as user ID
            user_id = username.replace(" ", "_").lower()  # Replace spaces with underscores

        if avatar_manager:
            # Load avatar using AvatarManager
            avatar_pixmap = avatar_manager.load_avatar(user_id, 50)
        else:
            # If AvatarManager not found, create default avatar
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_folder = os.path.join(script_dir, "db")
            avatar_path = os.path.join(db_folder, "avatar.png")

            if os.path.exists(avatar_path):
                # Load avatar file if it exists
                avatar_pixmap = QtGui.QPixmap(avatar_path)
                avatar_pixmap = avatar_pixmap.scaled(50, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            else:
                # Otherwise create default gray circle
                avatar_pixmap = QtGui.QPixmap(50, 50)
                avatar_pixmap.fill(QtCore.Qt.transparent)

                painter = QtGui.QPainter(avatar_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setBrush(QtGui.QBrush(QtGui.QColor("#555555")))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(0, 0, 50, 50)
                painter.end()

        avatar_label.setPixmap(avatar_pixmap)

        # Avatar on the right for our messages, on the left for others
        if is_self:
            container_layout.addLayout(self._createMessageLayout(username, timestamp, message, True))
            container_layout.addWidget(avatar_label)
        else:
            container_layout.addWidget(avatar_label)
            container_layout.addLayout(self._createMessageLayout(username, timestamp, message, False))

        if not is_self:
            container_layout.addStretch(1)  # Add empty space to align left

        # Add container to main layout and make it cover the full width
        main_layout.addWidget(container, 1)  # 1 = stretch factor

    def _createMessageLayout(self, username, timestamp, message, is_self):
        """Creates message content layout"""
        message_layout = QtWidgets.QVBoxLayout()
        message_layout.setSpacing(4)

        # Title (Username and timestamp) layout
        header_layout = QtWidgets.QHBoxLayout()

        # Align right for our messages, left for others
        if is_self:
            header_layout.addStretch(1)

        # Username (without bubble)
        username_label = QtWidgets.QLabel(username.upper())
        username_label.setStyleSheet("font-weight: bold; color: white;")
        header_layout.addWidget(username_label)

        # Only get the time information (timestamp: "YYYY-MM-DD HH:MM:SS" format)
        try:
            dt_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = dt_obj.strftime("%H:%M")
        except:
            time_str = timestamp.split(" ")[-1] if " " in timestamp else timestamp

        # Bubble for time info
        time_bubble = QtWidgets.QWidget()
        time_bubble.setStyleSheet("""
            background-color: #444444;
            border-radius: 8px;
            padding: 2px;
        """)
        time_layout = QtWidgets.QHBoxLayout(time_bubble)
        time_layout.setContentsMargins(8, 2, 8, 2)

        time_label = QtWidgets.QLabel(time_str)
        time_label.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        time_layout.addWidget(time_label)

        header_layout.addWidget(time_bubble)

        if not is_self:
            header_layout.addStretch(1)

        message_layout.addLayout(header_layout)

        # Check message content - normal message, script message, or expression message?
        if "[SCRIPT_DATA]" in message and "[/SCRIPT_DATA]" in message:
            # Process script message
            self._processScriptMessage(message_layout, message, is_self)
        elif "[EXPRESSION_DATA]" in message and "[/EXPRESSION_DATA]" in message:
            # Process expression message
            self._processExpressionMessage(message_layout, message, is_self)
        else:
            # Normal text message
            message_label = QtWidgets.QLabel(message)
            message_label.setWordWrap(True)
            message_label.setStyleSheet("color: white;")

            # Align right for our messages, left for others
            if is_self:
                message_label.setAlignment(QtCore.Qt.AlignRight)
            else:
                message_label.setAlignment(QtCore.Qt.AlignLeft)

            message_layout.addWidget(message_label)

        return message_layout

    def _processScriptMessage(self, message_layout, message, is_self):
        """Processes and displays script message"""
        try:
            # Extract and decode script data
            start_tag = "[SCRIPT_DATA]"
            end_tag = "[/SCRIPT_DATA]"
            start_idx = message.find(start_tag) + len(start_tag)
            end_idx = message.find(end_tag)

            if start_idx > -1 and end_idx > -1:
                encoded_data = message[start_idx:end_idx]
                script_data = decodeScriptData(encoded_data)

                if script_data:
                    # Create script bubble widget
                    script_bubble = ScriptBubbleWidget(script_data, self)

                    # Align right for our messages, left for others
                    if is_self:
                        message_layout.addWidget(script_bubble, 0, QtCore.Qt.AlignRight)
                    else:
                        message_layout.addWidget(script_bubble, 0, QtCore.Qt.AlignLeft)
                else:
                    # Show as normal message if decoding fails
                    error_label = QtWidgets.QLabel("Could not decode script data!")
                    error_label.setStyleSheet("color: #FF6666;")

                    if is_self:
                        error_label.setAlignment(QtCore.Qt.AlignRight)
                    else:
                        error_label.setAlignment(QtCore.Qt.AlignLeft)

                    message_layout.addWidget(error_label)

        except Exception as e:
            # Show as normal message if error occurs
            error_text = f"Script display error: {str(e)}"
            error_label = QtWidgets.QLabel(error_text)
            error_label.setStyleSheet("color: #FF6666;")

            if is_self:
                error_label.setAlignment(QtCore.Qt.AlignRight)
            else:
                error_label.setAlignment(QtCore.Qt.AlignLeft)

            message_layout.addWidget(error_label)

    def _processExpressionMessage(self, message_layout, message, is_self):
        """Processes and displays expression message"""
        try:
            # Extract and decode expression data
            start_tag = "[EXPRESSION_DATA]"
            end_tag = "[/EXPRESSION_DATA]"
            start_idx = message.find(start_tag) + len(start_tag)
            end_idx = message.find(end_tag)

            if start_idx > -1 and end_idx > -1:
                encoded_data = message[start_idx:end_idx]
                expression_data = decodeExpressionData(encoded_data)

                if expression_data:
                    # Create expression bubble widget
                    from ExpressionHandler import ExpressionBubbleWidget
                    expression_bubble = ExpressionBubbleWidget(expression_data, self)

                    # Align right for our messages, left for others
                    if is_self:
                        message_layout.addWidget(expression_bubble, 0, QtCore.Qt.AlignRight)
                    else:
                        message_layout.addWidget(expression_bubble, 0, QtCore.Qt.AlignLeft)
                else:
                    # Show as normal message if decoding fails
                    error_label = QtWidgets.QLabel("Could not decode expression data!")
                    error_label.setStyleSheet("color: #FF6666;")

                    if is_self:
                        error_label.setAlignment(QtCore.Qt.AlignRight)
                    else:
                        error_label.setAlignment(QtCore.Qt.AlignLeft)

                    message_layout.addWidget(error_label)

        except Exception as e:
            # Show as normal message if error occurs
            error_text = f"Expression display error: {str(e)}"
            error_label = QtWidgets.QLabel(error_text)
            error_label.setStyleSheet("color: #FF6666;")

            if is_self:
                error_label.setAlignment(QtCore.Qt.AlignRight)
            else:
                error_label.setAlignment(QtCore.Qt.AlignLeft)

            message_layout.addWidget(error_label)

class NukeChat(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # Save JSON files to "db" folder in the same directory as current Python file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.network_folder = os.path.join(script_dir, "db")  # "db" folder in the same directory as Python file

        # Create object for avatar management (after network_folder is defined)
        self.avatar_manager = AvatarManager(self.network_folder)

        self.onlineUsersTimer = QtCore.QTimer()
        self.onlineUsersTimer.timeout.connect(self.updateOnlineUsers)


        # Create "db" folder if it doesn't exist
        if not os.path.exists(self.network_folder):
            try:
                os.makedirs(self.network_folder)
                print(f"\"db\" folder created: {self.network_folder}")
            except Exception as e:
                print(f"Folder creation error: {str(e)}")
                # Alternative location in case of error
                self.network_folder = os.path.dirname(os.path.abspath(__file__))
                print(f"Using alternative location: {self.network_folder}")

        # Path for message data
        self.chat_file = os.path.join(self.network_folder, "nukechat_messages.json")
        # Path for user settings
        self.settings_file = os.path.join(self.network_folder, "nukechat_settings.json")
        self.notifications_file = os.path.join(self.network_folder, "notifications.json")
        # Path for presence file
        self.presence_file = os.path.join(self.network_folder, "presence.json")

        self.config_file = None
        # Print file location to screen
        print("NukeChat JSON file will be saved to:", self.chat_file)

        # To track last update time
        self.last_update_time = 0

        # Unique user ID (machine name + random ID)
        self.user_id = f"{socket.gethostname()}_{random.randint(1000, 9999)}"

        # Username setting
        self.custom_username = ""
        self.loadSettings()

        # Main layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # Search and filter area
        search_container = QtWidgets.QWidget()
        search_container.setStyleSheet("background-color: #333333;")
        search_layout = QtWidgets.QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 5, 10, 5)

        # Search label
        search_label = QtWidgets.QLabel("Search:")
        search_label.setStyleSheet("color: white;")
        search_layout.addWidget(search_label)

        # Search input box
        self.searchInput = QtWidgets.QLineEdit()
        self.searchInput.setPlaceholderText("Search messages...")
        self.searchInput.setStyleSheet("""
            QLineEdit {
                background-color: #444444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        search_layout.addWidget(self.searchInput)

        # Filter dropdown
        self.filterCombo = QtWidgets.QComboBox()
        self.filterCombo.addItems(["All Messages", "My Messages", "Other Messages"])
        self.filterCombo.setStyleSheet("""
            QComboBox {
                background-color: #444444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 10px;
                height: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #444444;
                color: white;
                selection-background-color: #555555;
                selection-color: white;
                border: none;
            }
        """)
        search_layout.addWidget(self.filterCombo)

        # Search and filter buttons
        self.searchButton = QtWidgets.QPushButton("Search")
        self.searchButton.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        search_layout.addWidget(self.searchButton)

        self.clearButton = QtWidgets.QPushButton("Clear")
        self.clearButton.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        search_layout.addWidget(self.clearButton)

        self.layout().addWidget(search_container)

        # Create tab widget
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #282828;
            }
            QTabBar::tab {
                background-color: #333333;
                color: white;
                padding: 8px 12px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #282828;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3A3A3A;
            }
        """)

        # Messages tab
        self.messagesTab = QtWidgets.QWidget()
        self.messagesTabLayout = QtWidgets.QVBoxLayout(self.messagesTab)
        self.messagesTabLayout.setContentsMargins(0, 0, 0, 0)
        self.messagesTabLayout.setSpacing(0)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.statusLabel = QtWidgets.QLabel("Ready")
        # Area where messages will be displayed - change background to original
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setStyleSheet("""
            QScrollArea {
                background-color: #282828;
                border: none;
            }
            QScrollBar:vertical {
                background: #333333;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #666666;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        self.messagesContainer = QtWidgets.QWidget()
        # Make the messages container background darker gray
        self.messagesContainer.setStyleSheet("background-color: #282828;")
        self.messagesLayout = QtWidgets.QVBoxLayout(self.messagesContainer)
        self.messagesLayout.setContentsMargins(0, 0, 0, 0)
        self.messagesLayout.setSpacing(0)
        # Add stretch to show messages from bottom to top
        self.messagesLayout.addStretch(1)

        self.scrollArea.setWidget(self.messagesContainer)
        self.messagesTabLayout.addWidget(self.scrollArea)

        # Settings tab
        self.settingsTab = QtWidgets.QWidget()
        self.settingsTabLayout = QtWidgets.QVBoxLayout(self.settingsTab)
        self.settingsTabLayout.setContentsMargins(20, 20, 20, 20)
        self.settingsTabLayout.setSpacing(10)

        # Username setting
        username_layout = QtWidgets.QHBoxLayout()
        username_label = QtWidgets.QLabel("Username:")
        username_label.setStyleSheet("color: white;")
        username_layout.addWidget(username_label)

        self.usernameInput = QtWidgets.QLineEdit()
        self.usernameInput.setPlaceholderText("Custom username (computer name will be used if left empty)")
        self.usernameInput.setStyleSheet("""
            QLineEdit {
                background-color: #444444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.usernameInput.setText(self.custom_username)
        username_layout.addWidget(self.usernameInput)

        # Save button
        self.saveSettingsButton = QtWidgets.QPushButton("Save")
        self.saveSettingsButton.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        username_layout.addWidget(self.saveSettingsButton)

        self.settingsTabLayout.addLayout(username_layout)
        # Avatar change button
        avatar_settings_layout = QtWidgets.QHBoxLayout()
        avatar_label = QtWidgets.QLabel("Avatar:")
        avatar_label.setStyleSheet("color: white;")
        avatar_settings_layout.addWidget(avatar_label)

        # Avatar preview
        self.avatar_preview = QtWidgets.QLabel()
        self.avatar_preview.setFixedSize(70, 70)
        self.avatar_preview.setStyleSheet("""
            background-color: #444444;
            border-radius: 35px;
            padding: 0px;
        """)
        avatar_settings_layout.addWidget(self.avatar_preview)

        # Avatar change button
        self.changeAvatarButton = QtWidgets.QPushButton("Change Avatar")
        self.changeAvatarButton.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        self.changeAvatarButton.clicked.connect(self.showAvatarDialog)
        avatar_settings_layout.addWidget(self.changeAvatarButton)
        avatar_settings_layout.addStretch(1)

        self.settingsTabLayout.addLayout(avatar_settings_layout)

        # Load current avatar
        self.updateAvatarPreview()

        self.settingsTabLayout.addStretch(1)  # Leave space at the bottom

        # Add tabs
        self.tabWidget.addTab(self.messagesTab, "Messages")
        self.tabWidget.addTab(self.settingsTab, "Settings")

        self.layout().addWidget(self.tabWidget, 1)  # 1 = stretch factor

        # Input area background
        input_container = QtWidgets.QWidget()
        input_container.setStyleSheet("background-color: #333333;")
        input_layout = QtWidgets.QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)

        # Message input container
        message_input_container = QtWidgets.QWidget()
        message_input_container.setStyleSheet("""
            QWidget {
                background-color: #444444;
                border-radius: 4px;
            }
        """)
        message_input_layout = QtWidgets.QVBoxLayout(message_input_container)
        message_input_layout.setContentsMargins(8, 8, 8, 8)
        message_input_layout.setSpacing(5)

        # Message writing area - as QTextEdit (expandable)
        self.messageInput = QtWidgets.QTextEdit()
        self.messageInput.setPlaceholderText("Type your message...")
        self.messageInput.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: white;
                border: none;
                padding: 0px;
                min-height: 40px;
                max-height: 100px;
                font-size: 14px;  /* You can adjust font size here */
            }
        """)
        self.messageInput.setMinimumHeight(40)
        self.messageInput.setMaximumHeight(100)

        # Message/status notification area
        self.notificationLayout = QtWidgets.QHBoxLayout()
        # self.statusLabel = QtWidgets.QLabel("Ready")
        self.statusLabel.setStyleSheet("color: rgba(170, 170, 170, 0.7); font-size: 10px;")
        self.notificationLayout.addWidget(self.statusLabel)

        # Send button SVG icon
        script_dir = os.path.dirname(os.path.abspath(__file__))
        send_svg_path = os.path.join(script_dir, "db", "send.svg")

        # Send button settings
        self.sendButton = QtWidgets.QPushButton()
        self.sendButton.setFixedSize(24, 24)
        self.sendButton.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        color: white;
                        font-weight: bold;
                        padding: 0px;
                    }
                    QPushButton:hover {
                        color: #aaaaaa;
                    }
                """)

        if os.path.exists(send_svg_path):
            self.sendButton.setIcon(QIcon(send_svg_path))
            self.sendButton.setText("")
        else:
            self.sendButton.setText("➤")

        self.notificationLayout.addWidget(self.sendButton)

        # Top-down layout: message writing area, status label
        message_input_layout.addWidget(self.messageInput)
        message_input_layout.addLayout(self.notificationLayout)

        # Add message input to main layout
        input_layout.addWidget(message_input_container)

        self.layout().addWidget(input_container)

        # Window resizing policy settings
        self.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        ))

        # Send button connection
        self.sendButton.clicked.connect(self.sendMessage)

        # Username save button connection
        self.saveSettingsButton.clicked.connect(self.saveSettings)

        # Search and filter connections
        self.searchButton.clicked.connect(self.searchMessages)
        self.clearButton.clicked.connect(self.clearSearch)
        self.searchInput.returnPressed.connect(self.searchMessages)
        self.filterCombo.currentIndexChanged.connect(self.filterMessages)

        # Enter key to send - special key handler needed for QTextEdit
        self.messageInput.installEventFilter(self)

        # Timer setup - regularly updates messages
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.checkForUpdates)
        self.updateTimer.start(1000)  # Update every 1 second
        self.notificationTimer = QtCore.QTimer()
        self.notificationTimer.timeout.connect(self.checkNotifications)
        self.notificationTimer.start(3000)  # Check notifications every 3 seconds
        # Second timer - for presence updates
        self.presenceTimer = QtCore.QTimer()
        self.presenceTimer.timeout.connect(self.updatePresence)
        self.presenceTimer.start(5000)  # Report our presence every 5 seconds

        # Report our presence at startup
        self.updatePresence()

        # Load existing messages at startup
        self.loadMessages()

        # General style
        self.setStyleSheet("""
                    QWidget {
                        font-family: 'Segoe UI', 'Arial', sans-serif;
                    }
                """)

        # Search and filter variables
        self.current_search = ""
        self.current_filter = 0  # 0: All, 1: Mine, 2: Others

        self.clipboard_handler = ClipboardHandler(self)
        # Add paste button (next to message input area)
        self.pasteScriptButton = QtWidgets.QPushButton()
        self.pasteScriptButton.setFixedSize(30, 30)
        self.pasteScriptButton.setToolTip("Paste Nuke Script")
        self.pasteScriptButton.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            border: none;
                            color: #AAAAAA;
                            font-weight: bold;
                            font-size: 16px;
                        }
                        QPushButton:hover {
                            color: #FFFFFF;
                        }
                        QPushButton:disabled {
                            color: #555555;
                        }
                    """)

        self.pasteScriptButton.setText("")  # Remove text, just show the icon
        self.notificationLayout.insertWidget(self.notificationLayout.count() - 1, self.pasteScriptButton)

        # Timer for regular clipboard checking
        self.clipboardCheckTimer = QtCore.QTimer(self)
        self.clipboardCheckTimer.timeout.connect(self.checkClipboardForScript)
        self.clipboardCheckTimer.start(1000)  # Check every second

        self.sendButton.clicked.connect(self.handleSendAction)

        self.loadOnlineUsers()
        self.onlineUsersTimer.start(5000)

    def showAvatarDialog(self):
        """Shows avatar upload dialog"""
        hostname = socket.gethostname()
        dialog = AvatarUploadDialog(self.avatar_manager, hostname, self.getCurrentUser(), self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Avatar may have been updated, reload
            self.updateAvatarPreview()

    def updateAvatarPreview(self):
        """Updates avatar preview on settings page"""
        hostname = socket.gethostname()
        pixmap = self.avatar_manager.load_avatar(hostname, 70)
        self.avatar_preview.setPixmap(pixmap)

    def checkClipboardForScript(self):
        """Checks if clipboard contains a Nuke script"""
        # Check clipboard content and store result in a class variable
        self.has_script_in_clipboard = self.clipboard_handler.checkClipboard()

        # If there's a Nuke script in the clipboard
        if self.has_script_in_clipboard:
            self.statusLabel.setStyleSheet("color: #FF9900; font-weight: bold; font-size: 12px;")
            self.statusLabel.setText("Press Enter to share the Nuke script")
        else:
            current_status = self.statusLabel.text()
            if "Nuke script" in current_status:
                self.statusLabel.setStyleSheet("color: rgba(255, 153, 0, 0.8); font-weight: bold; font-size: 12px;")
                self.statusLabel.setText("Ready")

    def handleSendAction(self):
        """Called when send button is clicked or Enter key is pressed"""
        # Get text from message area
        message = self.messageInput.toPlainText().strip()

        # If clipboard contains Nuke script and text area is empty
        if not message and self.has_script_in_clipboard:
            # Send script
            self.pasteNukeScript()
        else:
            # Send normal message
            self.sendMessage()

    def pasteNukeScript(self):
        """Gets Nuke script from clipboard and shares in chat"""
        # Get script data from clipboard
        script_data = self.clipboard_handler.getScriptFromClipboard()

        if script_data:
            # Create dialog for adding description
            description_dialog = QtWidgets.QDialog(self)
            description_dialog.setWindowTitle("Script Description")
            description_dialog.setMinimumWidth(400)
            description_dialog.setStyleSheet("""
                        QDialog {
                            background-color: #333333;
                            color: white;
                        }
                        QLabel {
                            color: white;
                        }
                        QLineEdit {
                            background-color: #444444;
                            color: white;
                            border: 1px solid #555555;
                            border-radius: 4px;
                            padding: 5px;
                        }
                        QPushButton {
                            background-color: #555555;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 6px 12px;
                        }
                        QPushButton:hover {
                            background-color: #666666;
                        }
                    """)

            dialog_layout = QtWidgets.QVBoxLayout(description_dialog)

            # Description label
            desc_label = QtWidgets.QLabel("Enter a description for the script fragment:")
            dialog_layout.addWidget(desc_label)

            # Description input
            desc_input = QtWidgets.QLineEdit()
            desc_input.setPlaceholderText("E.g.: Blur Effect, Transform Nodes, etc.")
            dialog_layout.addWidget(desc_input)

            # Button layout
            button_layout = QtWidgets.QHBoxLayout()
            cancel_button = QtWidgets.QPushButton("Cancel")
            send_button = QtWidgets.QPushButton("Send")
            send_button.setDefault(True)

            button_layout.addWidget(cancel_button)
            button_layout.addWidget(send_button)
            dialog_layout.addLayout(button_layout)

            # Button connections
            cancel_button.clicked.connect(description_dialog.reject)
            send_button.clicked.connect(description_dialog.accept)

            # Show dialog
            result = description_dialog.exec_()

            if result == QtWidgets.QDialog.Accepted:
                # Add description
                script_data["description"] = desc_input.text()
                # Send script message
                self.sendScriptMessage(script_data)

        else:
            self.updateStatus("No valid Nuke script data found in clipboard")

    def sendScriptMessage(self, script_data):
        """Sends script data as a message"""
        try:
            # Encode script data
            encoded_data = encodeScriptData(script_data)

            if encoded_data:
                # Send script message with special format
                script_message = f"[SCRIPT_DATA]{encoded_data}[/SCRIPT_DATA]"

                # Save and send message (use normal message sending function)
                if self.saveMessage(script_message):
                    # Update and display messages
                    self.loadMessages()

                    # Update status bar
                    description = script_data.get("description", "")
                    if description:
                        status_text = f"Script fragment \"{description}\" shared"
                    else:
                        status_text = "Script fragment shared"

                    self.updateStatus(status_text)

                    # Clear message box (should already be empty, but clear anyway)
                    self.messageInput.clear()

        except Exception as e:
            self.updateStatus(f"Error sending script message: {str(e)}")

    def updateOnlineUsers(self):
        """Updates online user list"""
        # First clear current online users widget
        while self.settingsTabLayout.count() > 2:  # Keep first two widgets
            item = self.settingsTabLayout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()

        # Reload online users
        self.loadOnlineUsers()

    def loadOnlineUsers(self):
        """Loads and displays online users"""
        try:
            # Area for online users
            online_users_container = QtWidgets.QWidget()
            online_users_layout = QtWidgets.QVBoxLayout(online_users_container)
            online_users_layout.setContentsMargins(0, 0, 0, 0)
            online_users_layout.setSpacing(10)

            # Online users title
            online_title = QtWidgets.QLabel("Currently Online")
            online_title.setStyleSheet("""
                        font-size: 16px;
                        font-weight: bold;
                        color: white;
                        margin-bottom: 10px;
                    """)
            online_users_layout.addWidget(online_title)

            # Read online users from presence file
            online_users = []
            current_time = time.time()
            if os.path.exists(self.presence_file):
                try:
                    with open(self.presence_file, 'r', encoding='utf-8') as file:
                        presence_data = json.load(file)

                        # Find users active in last 30 seconds
                        for uid, data in presence_data.items():
                            if current_time - data["last_seen"] < 30:  # Active within 30 seconds
                                online_users.append(data["user"])
                except Exception as e:
                    print(f"Error reading online users: {str(e)}")

            if online_users:
                # List online users
                for user in online_users:
                    user_widget = QtWidgets.QWidget()
                    user_layout = QtWidgets.QHBoxLayout(user_widget)
                    user_layout.setContentsMargins(10, 5, 10, 5)
                    user_layout.setSpacing(10)

                    # Online user icon - colored circle with HTML
                    online_icon = QtWidgets.QLabel("•")
                    online_icon.setStyleSheet("""
                                    color: #00CC00;
                                    font-size: 24px;
                                    font-weight: bold;
                                """)
                    user_layout.addWidget(online_icon)

                    # Username
                    user_label = QtWidgets.QLabel(user)
                    user_label.setStyleSheet("""
                                color: white;
                                font-size: 14px;
                            """)
                    user_layout.addWidget(user_label)

                    user_layout.addStretch(1)
                    online_users_layout.addWidget(user_widget)
            else:
                # If no one is online
                no_users_label = QtWidgets.QLabel("No users currently online")
                no_users_label.setStyleSheet("""
                            color: #888888;
                            font-style: italic;
                            padding: 10px;
                        """)
                online_users_layout.addWidget(no_users_label)

            online_users_layout.addStretch(1)

            # Add to existing settingsTabLayout
            self.settingsTabLayout.addWidget(online_users_container)

        except Exception as e:
            print(f"Error loading online users: {str(e)}")

    def eventFilter(self, obj, event):
        """Event filter to enable sending with Enter key in QTextEdit"""
        if obj is self.messageInput and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and not event.modifiers() & QtCore.Qt.ShiftModifier:
                self.handleSendAction()
                return True
            if event.key() == QtCore.Qt.Key_Return and event.modifiers() & QtCore.Qt.ShiftModifier:
                # Shift+Enter for new line
                cursor = self.messageInput.textCursor()
                cursor.insertText("\n")
                return True
        return super(NukeChat, self).eventFilter(obj, event)

    def loadSettings(self):
        """Load settings"""
        try:
            # Path for config.json file
            self.config_file = os.path.join(self.network_folder, "config.json")

            # If config.json file exists
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    config = json.load(file)

                    # Get username for computer name
                    hostname = socket.gethostname()
                    if hostname in config:
                        self.custom_username = config[hostname]

            # Also check old settings.json file (for backward compatibility)
            elif os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as file:
                    settings = json.load(file)
                    if 'username' in settings:
                        self.custom_username = settings['username']

                        # Convert old settings to new format
                        self.saveSettings()
        except Exception as e:
            print(f"Error loading settings: {str(e)}")

    def saveSettings(self):
        """Save settings"""
        try:
            # Get entered username
            self.custom_username = self.usernameInput.text().strip()

            # Load or create new config.json file
            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as file:
                        config = json.load(file)
                except:
                    # Create new if file is corrupted
                    config = {}

            # Save username for computer name
            hostname = socket.gethostname()
            config[hostname] = self.custom_username

            # Save to config.json
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)

            self.updateStatus("Username saved")
            self.updateAvatarPreview()
        except Exception as e:
            self.updateStatus(f"Could not save settings: {str(e)}")

    def getCurrentUser(self):
        """Returns username (custom name if set, otherwise machine name)"""
        if self.custom_username:
            return f"{self.custom_username} - ({socket.gethostname()})"
        return socket.gethostname()

    def updateStatus(self, status):
        """Updates status label"""
        self.statusLabel.setText(status)

        # Return to "Ready" message after 3 seconds (for important messages)
        QtCore.QTimer.singleShot(3000, lambda: self.statusLabel.setText("Ready"))

    def updatePresence(self):
        """Updates presence information"""
        try:
            # Load current presence data
            presence_data = {}
            if os.path.exists(self.presence_file):
                try:
                    with open(self.presence_file, 'r', encoding='utf-8') as file:
                        presence_data = json.load(file)
                except:
                    # File might be locked or corrupted, create new file
                    presence_data = {}

            # Add/update our presence
            current_time = time.time()
            presence_data[self.user_id] = {
                "user": self.getCurrentUser(),
                "last_seen": current_time
            }

            # Clean up old records (not active in last 30 seconds)
            active_users = {}
            for uid, data in presence_data.items():
                if current_time - data["last_seen"] < 30:  # Remove ones older than 30 seconds
                    active_users[uid] = data

            # Save to file
            with open(self.presence_file, 'w', encoding='utf-8') as file:
                json.dump(active_users, file, ensure_ascii=False)

        except Exception as e:
            self.updateStatus(f"Presence Error: {str(e)}")

    def checkForUpdates(self):
        """Checks file for new messages"""
        try:
            if not os.path.exists(self.chat_file):
                # Create empty JSON if file doesn't exist
                with open(self.chat_file, 'w', encoding='utf-8') as file:
                    json.dump([], file)
                self.last_update_time = time.time()
                return

            # Check file last modification time
            file_mod_time = os.path.getmtime(self.chat_file)

            if file_mod_time > self.last_update_time:
                # Save current message count
                old_message_count = 0
                if os.path.exists(self.chat_file):
                    try:
                        with open(self.chat_file, 'r', encoding='utf-8') as file:
                            old_message_count = len(json.load(file))
                    except:
                        old_message_count = 0

                # Load messages
                self.loadMessages()

                # Check new message count
                new_message_count = 0
                if os.path.exists(self.chat_file):
                    try:
                        with open(self.chat_file, 'r', encoding='utf-8') as file:
                            new_message_count = len(json.load(file))
                    except:
                        new_message_count = 0

                # Show notification if there are new messages
                if new_message_count > old_message_count:
                    self.showNotification(new_message_count - old_message_count)

                self.last_update_time = file_mod_time
                self.updateStatus("Messages Updated")
        except Exception as e:
            self.updateStatus(f"Update Error: {str(e)}")

    def showNotification(self, count):
        """Shows notification in Nuke"""
        try:
            # Update tab title
            self.tabWidget.setTabText(0, f"Messages ({count} new)")

            # Make notification area more visible
            self.statusLabel.setStyleSheet("color: #FF9900; font-weight: bold; font-size: 12px;")
            self.statusLabel.setText(f"{count} new messages!")

            # Show notification in Nuke's main window (optional)
            import nuke
            nuke.message(f"{count} new NukeChat messages!")

            # Play notification sound (optional)
            # You can play a sound file here

            # Return notification style to normal after 5 seconds
            QtCore.QTimer.singleShot(5000, lambda: self.resetNotification())
        except Exception as e:
            print(f"Error showing notification: {str(e)}")

    def resetNotification(self):
        """Resets notification indicator"""
        self.tabWidget.setTabText(0, "Messages")
        self.statusLabel.setStyleSheet("color: rgba(170, 170, 170, 1); font-size: 14px;")
        self.statusLabel.setText("Ready")

    def tabChanged(self, index):
        """Called when tab is changed"""
        if index == 0:  # Reset notification when Messages tab is selected
            self.resetNotification()

    def loadMessages(self):
        """Loads messages from JSON file and displays them"""
        try:
            if os.path.exists(self.chat_file):
                with open(self.chat_file, 'r', encoding='utf-8') as file:
                    messages = json.load(file)

                # Apply search and filter
                filtered_messages = self.applySearchAndFilter(messages)

                # First clear current messages (except stretch)
                while self.messagesLayout.count() > 1:
                    item = self.messagesLayout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

                # Our own username
                current_user = self.getCurrentUser()

                # Add new message widgets
                for idx, msg in enumerate(filtered_messages):
                    # Check if message belongs to us
                    is_self = msg['user'] == current_user

                    # Create message widget and pass self (NukeChat) as parent
                    message_widget = MessageWidget(
                        msg['user'],
                        msg['timestamp'],
                        msg['message'],
                        is_self=is_self,
                        parent=self,  # Passing self (NukeChat) here
                        row_index=idx
                    )

                    # Add message at bottom (above stretch)
                    self.messagesLayout.insertWidget(self.messagesLayout.count() - 1, message_widget)

                # Scroll to bottom
                self.scrollToBottom()

            self.updateStatus("Ready")
        except Exception as e:
            self.updateStatus(f"Loading Error: {str(e)}")

    def applySearchAndFilter(self, messages):
        """Applies search and filter criteria"""
        filtered_messages = []
        current_user = self.getCurrentUser()

        for msg in messages:
            # Apply filter
            if self.current_filter == 1 and msg['user'] != current_user:  # Only my messages
                continue
            if self.current_filter == 2 and msg['user'] == current_user:  # Only other messages
                continue

            # Apply search
            if self.current_search and self.current_search.lower() not in msg['message'].lower():
                continue

            filtered_messages.append(msg)

        return filtered_messages

    def searchMessages(self):
        """Searches messages"""
        self.current_search = self.searchInput.text()
        self.loadMessages()

    def clearSearch(self):
        """Clears search and filters"""
        self.searchInput.clear()
        self.filterCombo.setCurrentIndex(0)
        self.current_search = ""
        self.current_filter = 0
        self.loadMessages()

    def filterMessages(self, index):
        """Changes filter type"""
        self.current_filter = index
        self.loadMessages()

    def scrollToBottom(self):
        """Scrolls to bottom"""
        QTimer = QtCore.QTimer
        QTimer.singleShot(100, lambda: self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        ))

    def saveMessage(self, message):
        """Saves message to JSON file"""
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Wait a bit before locking file (to avoid race condition)
                time.sleep(random.uniform(0.1, 0.5))

                # Load existing messages or create new list
                messages = []
                if os.path.exists(self.chat_file):
                    with open(self.chat_file, 'r', encoding='utf-8') as file:
                        messages = json.load(file)

                # Add new message
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_message = {
                    "user": self.getCurrentUser(),
                    "message": message,
                    "timestamp": current_time
                }
                messages.append(new_message)

                # Save to file
                with open(self.chat_file, 'w', encoding='utf-8') as file:
                    json.dump(messages, file, ensure_ascii=False, indent=4)

                self.updateStatus("Message Sent")
                return True

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.updateStatus(f"Message Could Not Be Saved: {str(e)}")
                    return False
                time.sleep(random.uniform(0.5, 1.0))  # Wait a bit longer before retrying

        return False

    def sendMessage(self):
        """Message sending function"""
        message = self.messageInput.toPlainText()
        if message.strip():
            self.updateStatus("Sending Message...")
            # Save message
            if self.saveMessage(message):
                # Create notification
                self.createNotification(message)
                # Update and show messages
                self.loadMessages()
                # Clear message area
                self.messageInput.clear()

    def createNotification(self, message):
        """Creates notification for other users"""
        try:
            # Load existing notifications
            notifications = {}
            if os.path.exists(self.notifications_file):
                try:
                    with open(self.notifications_file, 'r', encoding='utf-8') as file:
                        notifications = json.load(file)
                except:
                    notifications = {}

            # Get active users from presence file
            active_users = []
            if os.path.exists(self.presence_file):
                try:
                    with open(self.presence_file, 'r', encoding='utf-8') as file:
                        presence_data = json.load(file)
                        # Get all active users except ourselves
                        for uid, data in presence_data.items():
                            if uid != self.user_id:
                                active_users.append(uid)
                except:
                    pass

            # Create notification for each active user
            current_time = time.time()
            sender_name = self.getCurrentUser()
            message_preview = message[:50] + "..." if len(message) > 50 else message

            for user_id in active_users:
                if user_id not in notifications:
                    notifications[user_id] = []

                # Add notification
                notifications[user_id].append({
                    "timestamp": current_time,
                    "sender": sender_name,
                    "message": message_preview,
                    "read": False
                })

            # Save notifications
            with open(self.notifications_file, 'w', encoding='utf-8') as file:
                json.dump(notifications, file, ensure_ascii=False)

        except Exception as e:
            print(f"Error creating notification: {str(e)}")
            self.updateStatus(f"Error creating notification: {str(e)}")

    def checkNotifications(self):
        """Checks for new notifications"""
        try:
            if not os.path.exists(self.notifications_file):
                return

            # Load notifications
            notifications = {}
            try:
                with open(self.notifications_file, 'r', encoding='utf-8') as file:
                    notifications = json.load(file)
            except:
                return

            # My notifications
            my_notifications = notifications.get(self.user_id, [])

            # Filter unread notifications
            unread_notifications = [n for n in my_notifications if not n.get("read", False)]

            if unread_notifications:
                # Show notification
                count = len(unread_notifications)

                # Update tab title
                self.tabWidget.setTabText(0, f"Messages ({count} new)")

                # Update status bar
                self.statusLabel.setStyleSheet("color: #FF9900; font-weight: bold; font-size: 12px;")

                if count == 1:
                    # For single notification
                    notification = unread_notifications[0]
                    sender = notification["sender"]
                    message = notification["message"]
                    self.statusLabel.setText(f"New message: {sender}: {message}")

                    # Show toast notification
                    toast = ToastNotification(message=message, sender=sender, parent=self, duration=5000)
                    toast.show()

                else:
                    # For multiple notifications
                    self.statusLabel.setText(f"{count} new messages!")

                    # Full notification for first message
                    notification = unread_notifications[0]
                    first_sender = notification["sender"]
                    first_message = notification["message"]

                    # Summary info for other messages
                    summary = f"... and {count - 1} more messages"

                    # Show toast notification
                    toast = ToastNotification(message=f"{first_message}\n\n{summary}",
                                              sender=first_sender,
                                              parent=self,
                                              duration=5000)
                    toast.show()

                # Mark notifications as read
                for notification in my_notifications:
                    notification["read"] = True

                # Save updated notifications
                notifications[self.user_id] = my_notifications
                with open(self.notifications_file, 'w', encoding='utf-8') as file:
                    json.dump(notifications, file, ensure_ascii=False)

        except Exception as e:
            print(f"Error checking notifications: {str(e)}")
            self.updateStatus(f"Error checking notifications: {str(e)}")

    panels.registerWidgetAsPanel('NukeChat', 'NukeChat', 'uk.co.thefoundry.NukeChat')
