"""
AvatarManager.py

This module provides user avatar management for the NukeChat application.
It includes functions for loading, changing, deleting, and displaying user avatars.
"""

import os
import sys
import nuke
import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
from PySide2.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QFont
import random
import hashlib

class AvatarManager:
    """Management class for user avatars"""

    def __init__(self, db_folder):
        """
        Initializes the avatar management class

        Args:
            db_folder (str): The main folder path where avatar files will be stored
        """
        self.db_folder = db_folder

        # Create the avatar folder path
        self.avatar_folder = os.path.join(self.db_folder, "avatars")

        # Create the avatar folder if it doesn't exist
        if not os.path.exists(self.avatar_folder):
            try:
                os.makedirs(self.avatar_folder)
                print(f"\"avatars\" folder created: {self.avatar_folder}")
            except Exception as e:
                print(f"Error creating avatar folder: {str(e)}")

    def get_avatar_path(self, user_id):
        """
        Returns the avatar file path based on the user ID

        Args:
            user_id (str): The unique user ID

        Returns:
            str: The full path of the avatar file
        """
        # Determine the avatar path using the user ID as the file name
        return os.path.join(self.avatar_folder, f"{user_id}.png")

    def load_avatar(self, user_id, size=50):
        """
        Loads the avatar of a specific user

        Args:
            user_id (str): The unique user ID
            size (int): The size of the avatar image (in pixels)

        Returns:
            QPixmap: The avatar image (default avatar if file does not exist)
        """
        avatar_path = self.get_avatar_path(user_id)

        # Load the file if it exists
        if os.path.exists(avatar_path):
            original_pixmap = QtGui.QPixmap(avatar_path)

            # Create a rounded avatar
            rounded_pixmap = QtGui.QPixmap(size, size)
            rounded_pixmap.fill(QtCore.Qt.transparent)

            painter = QtGui.QPainter(rounded_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

            # Create a circular mask
            path = QtGui.QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)

            # Scale and draw the original image
            scaled_pixmap = original_pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio,
                                                   QtCore.Qt.SmoothTransformation)

            # Draw the image centered
            x_offset = (size - scaled_pixmap.width()) // 2
            y_offset = (size - scaled_pixmap.height()) // 2
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

            painter.end()
            return rounded_pixmap
        else:
            # Create a default avatar
            return self.create_default_avatar(user_id, size)

    def create_default_avatar(self, user_id, size=50, username=None):
        """
        Creates a default avatar (initials on a colored background)

        Args:
            user_id (str): The unique user ID
            size (int): The size of the avatar image (in pixels)
            username (str, optional): The username (if not specified, user_id is used)

        Returns:
            QPixmap: The created default avatar image
        """
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)

        # Generate a consistent color based on the user ID
        color = self._generate_color_from_id(user_id)

        # Create a painter
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Draw the background circle
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)

        # Determine the initials
        if username:
            initials = self._get_initials(username)
        else:
            # Try to extract something from the user ID
            parts = user_id.split('_')
            if len(parts) > 0:
                initials = self._get_initials(parts[0])
            else:
                initials = user_id[:2].upper()

        # Text drawing settings
        font = QtGui.QFont()
        font.setPixelSize(size * 0.4)  # Size adjustment
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))  # White text

        # Draw the text centered
        rect = QtCore.QRect(0, 0, size, size)
        painter.drawText(rect, QtCore.Qt.AlignCenter, initials)

        painter.end()
        return pixmap

    def _get_initials(self, name):
        """
        Extracts initials from a name

        Args:
            name (str): The username or name

        Returns:
            str: The initials of the name (maximum 2 letters)
        """
        # Split the name into parts by spaces
        parts = name.split()
        initials = ""

        if len(parts) >= 2:
            # Take the first letters of the first two words
            initials = parts[0][0].upper() + parts[1][0].upper()
        elif len(parts) == 1:
            # If it's a single word, take the first two letters or use the single letter if only one
            if len(parts[0]) >= 2:
                initials = parts[0][0].upper() + parts[0][1].upper()
            else:
                initials = parts[0][0].upper()
        else:
            # If there are no words, use the default letter "U" (User)
            initials = "U"

        return initials[:2]  # Maximum 2 letters

    def _generate_color_from_id(self, user_id):
        """
        Generates a consistent color based on the user ID

        Args:
            user_id (str): The unique user ID

        Returns:
            QColor: The generated color
        """
        # Create a hash from the user ID
        hash_obj = hashlib.md5(user_id.encode())
        hash_hex = hash_obj.hexdigest()

        # Create an RGB color from the first 6 characters of the hash
        r = int(hash_hex[0:2], 16)
        g = int(hash_hex[2:4], 16)
        b = int(hash_hex[4:6], 16)

        # Ensure the colors are not too dark (for readability)
        min_brightness = 60
        r = max(r, min_brightness)
        g = max(g, min_brightness)
        b = max(b, min_brightness)

        return QtGui.QColor(r, g, b)

    def save_avatar(self, user_id, pixmap):
        """
        Saves the avatar image

        Args:
            user_id (str): The unique user ID
            pixmap (QPixmap): The avatar image to be saved

        Returns:
            bool: True if the operation is successful, False otherwise
        """
        try:
            avatar_path = self.get_avatar_path(user_id)

            # Check the size and resize if necessary
            if pixmap.width() > 150 or pixmap.height() > 150:
                pixmap = pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            # Save as PNG
            return pixmap.save(avatar_path, "PNG")
        except Exception as e:
            print(f"Error saving avatar: {str(e)}")
            return False

    def delete_avatar(self, user_id):
        """
        Deletes the user's avatar

        Args:
            user_id (str): The unique user ID

        Returns:
            bool: True if the operation is successful, False otherwise
        """
        try:
            avatar_path = self.get_avatar_path(user_id)
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting avatar: {str(e)}")
            return False


class AvatarUploadDialog(QtWidgets.QDialog):
    """Dialog for uploading and editing avatars"""

    def __init__(self, avatar_manager, user_id, username=None, parent=None):
        """
        Initializes the avatar upload dialog

        Args:
            avatar_manager (AvatarManager): Reference for avatar management
            user_id (str): The unique user ID
            username (str, optional): The username
            parent (QWidget, optional): Parent widget
        """
        super(AvatarUploadDialog, self).__init__(parent)

        self.avatar_manager = avatar_manager
        self.user_id = user_id
        self.username = username
        self.current_pixmap = None

        self.setWindowTitle("Avatar Settings")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #333333;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
            QPushButton#deleteButton {
                background-color: #aa3333;
            }
            QPushButton#deleteButton:hover {
                background-color: #cc3333;
            }
        """)

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info label
        info_label = QtWidgets.QLabel("Upload or change your avatar image. "
                                     "Maximum size is 150x150 pixels.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Avatar preview area
        preview_layout = QtWidgets.QHBoxLayout()
        preview_layout.setAlignment(QtCore.Qt.AlignCenter)

        self.avatar_preview = QtWidgets.QLabel()
        self.avatar_preview.setFixedSize(120, 120)
        self.avatar_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.avatar_preview.setStyleSheet("""
            background-color: #222222;
            border-radius: 60px;
            border: 2px solid #555555;
        """)

        preview_layout.addWidget(self.avatar_preview)
        layout.addLayout(preview_layout)

        # Load the current avatar
        self.load_current_avatar()

        # Buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Upload avatar button
        self.upload_button = QtWidgets.QPushButton("Upload from File")
        self.upload_button.clicked.connect(self.upload_avatar)
        buttons_layout.addWidget(self.upload_button)

        # Delete avatar button
        self.delete_button = QtWidgets.QPushButton("Delete Avatar")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.clicked.connect(self.delete_avatar)
        buttons_layout.addWidget(self.delete_button)

        layout.addLayout(buttons_layout)

        # Bottom layout - Close button
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch(1)

        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_button)

        layout.addLayout(bottom_layout)

    def load_current_avatar(self):
        """Loads and displays the current avatar"""
        pixmap = self.avatar_manager.load_avatar(self.user_id, 120)
        self.current_pixmap = pixmap
        self.avatar_preview.setPixmap(pixmap)

    def upload_avatar(self):
        """Starts the file selection process and updates the avatar"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setWindowTitle("Select Avatar Image")
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg *.bmp)")

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
                try:
                    # Load the image
                    pixmap = QtGui.QPixmap(image_path)

                    # Resize
                    pixmap = pixmap.scaled(120, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

                    # Show preview
                    self.avatar_preview.setPixmap(pixmap)
                    self.current_pixmap = pixmap

                    # Save
                    success = self.avatar_manager.save_avatar(self.user_id, pixmap)
                    if success:
                        QtWidgets.QMessageBox.information(self, "Success", "Avatar updated successfully.")
                    else:
                        QtWidgets.QMessageBox.warning(self, "Error", "An error occurred while saving the avatar.")

                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Error loading image: {str(e)}")

    def delete_avatar(self):
        """Deletes the current avatar and reverts to the default avatar"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Avatar",
            "Are you sure you want to delete your avatar image?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            # Delete the avatar
            success = self.avatar_manager.delete_avatar(self.user_id)

            # Show the default avatar
            self.load_current_avatar()

            if success:
                QtWidgets.QMessageBox.information(self, "Success", "Avatar deleted successfully.")
