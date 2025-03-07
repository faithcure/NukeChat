"""
AvatarManager.py

Bu modül, NukeChat uygulaması için kullanıcı avatarlarının yönetimini sağlar.
Kullanıcı avatarlarını yükleme, değiştirme, silme ve gösterme işlevlerini içerir.
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
    """Kullanıcı avatarları için yönetim sınıfı"""

    def __init__(self, db_folder):
        """
        Avatar yönetim sınıfını başlatır

        Args:
            db_folder (str): Avatar dosyalarının saklanacağı ana klasör yolu
        """
        self.db_folder = db_folder

        # Avatar klasörü yolunu oluştur
        self.avatar_folder = os.path.join(self.db_folder, "avatars")

        # Avatar klasörü yoksa oluştur
        if not os.path.exists(self.avatar_folder):
            try:
                os.makedirs(self.avatar_folder)
                print(f"\"avatars\" klasörü oluşturuldu: {self.avatar_folder}")
            except Exception as e:
                print(f"Avatar klasörü oluşturma hatası: {str(e)}")

    def get_avatar_path(self, user_id):
        """
        Kullanıcı ID'sine göre avatar dosya yolunu döndürür

        Args:
            user_id (str): Kullanıcı benzersiz ID'si

        Returns:
            str: Avatar dosyasının tam yolu
        """
        # Kullanıcı ID'sini dosya adı olarak kullanarak avatar yolunu belirle
        return os.path.join(self.avatar_folder, f"{user_id}.png")

    def load_avatar(self, user_id, size=50):
        """
        Belirli bir kullanıcının avatarını yükler

        Args:
            user_id (str): Kullanıcı benzersiz ID'si
            size (int): Avatar görüntüsü boyutu (piksel cinsinden)

        Returns:
            QPixmap: Avatar görüntüsü (dosya yoksa oluşturulan varsayılan avatar)
        """
        avatar_path = self.get_avatar_path(user_id)

        # Dosya varsa yükle
        if os.path.exists(avatar_path):
            original_pixmap = QtGui.QPixmap(avatar_path)

            # Yuvarlatılmış avatar oluştur
            rounded_pixmap = QtGui.QPixmap(size, size)
            rounded_pixmap.fill(QtCore.Qt.transparent)

            painter = QtGui.QPainter(rounded_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

            # Daire şeklinde bir maske oluştur
            path = QtGui.QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)

            # Orijinal resmi ölçeklendirip çiz
            scaled_pixmap = original_pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio,
                                                   QtCore.Qt.SmoothTransformation)

            # Resmi ortalayarak çiz
            x_offset = (size - scaled_pixmap.width()) // 2
            y_offset = (size - scaled_pixmap.height()) // 2
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

            painter.end()
            return rounded_pixmap
        else:
            # Varsayılan avatar oluştur
            return self.create_default_avatar(user_id, size)

    def create_default_avatar(self, user_id, size=50, username=None):
        """
        Varsayılan bir avatar oluşturur (renkli arka plan üzerinde isim baş harfleri)

        Args:
            user_id (str): Kullanıcı benzersiz ID'si
            size (int): Avatar görüntüsü boyutu (piksel cinsinden)
            username (str, optional): Kullanıcı adı (belirtilmezse user_id kullanılır)

        Returns:
            QPixmap: Oluşturulan varsayılan avatar görüntüsü
        """
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)

        # Kullanıcı ID'sine göre tutarlı bir renk üret
        color = self._generate_color_from_id(user_id)

        # Ressam oluştur
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Arkaplan çemberi çiz
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)

        # İsim baş harflerini belirle
        if username:
            initials = self._get_initials(username)
        else:
            # Kullanıcı ID'sinden bir şeyler çıkarmaya çalış
            parts = user_id.split('_')
            if len(parts) > 0:
                initials = self._get_initials(parts[0])
            else:
                initials = user_id[:2].upper()

        # Metni yazma ayarları
        font = QtGui.QFont()
        font.setPixelSize(size * 0.4)  # Boyut ayarı
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))  # Beyaz metin

        # Metni merkeze hizalı çiz
        rect = QtCore.QRect(0, 0, size, size)
        painter.drawText(rect, QtCore.Qt.AlignCenter, initials)

        painter.end()
        return pixmap

    def _get_initials(self, name):
        """
        İsimden baş harfleri çıkarır

        Args:
            name (str): Kullanıcı adı veya isim

        Returns:
            str: İsmin baş harfleri (en fazla 2 harf)
        """
        # Boşluklarla ayrılmış isimleri parçalara ayır
        parts = name.split()
        initials = ""

        if len(parts) >= 2:
            # İlk iki kelimenin baş harflerini al
            initials = parts[0][0].upper() + parts[1][0].upper()
        elif len(parts) == 1:
            # Tek kelime ise, ilk iki harfi al veya tek harf varsa onu kullan
            if len(parts[0]) >= 2:
                initials = parts[0][0].upper() + parts[0][1].upper()
            else:
                initials = parts[0][0].upper()
        else:
            # Hiç kelime yoksa varsayılan olarak "U" harfini kullan (User)
            initials = "U"

        return initials[:2]  # En fazla 2 harf

    def _generate_color_from_id(self, user_id):
        """
        Kullanıcı ID'sine göre tutarlı bir renk üretir

        Args:
            user_id (str): Kullanıcı benzersiz ID'si

        Returns:
            QColor: Oluşturulan renk
        """
        # Kullanıcı ID'sinden hash oluştur
        hash_obj = hashlib.md5(user_id.encode())
        hash_hex = hash_obj.hexdigest()

        # Hash'in ilk 6 karakterini alarak RGB rengi oluştur
        r = int(hash_hex[0:2], 16)
        g = int(hash_hex[2:4], 16)
        b = int(hash_hex[4:6], 16)

        # Renkler çok koyu olmasın (okunabilirlik için)
        min_brightness = 60
        r = max(r, min_brightness)
        g = max(g, min_brightness)
        b = max(b, min_brightness)

        return QtGui.QColor(r, g, b)

    def save_avatar(self, user_id, pixmap):
        """
        Avatar görüntüsünü kaydeder

        Args:
            user_id (str): Kullanıcı benzersiz ID'si
            pixmap (QPixmap): Kaydedilecek avatar görüntüsü

        Returns:
            bool: İşlem başarılıysa True, değilse False
        """
        try:
            avatar_path = self.get_avatar_path(user_id)

            # Boyut kontrolü yap ve gerekirse yeniden boyutlandır
            if pixmap.width() > 150 or pixmap.height() > 150:
                pixmap = pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            # PNG olarak kaydet
            return pixmap.save(avatar_path, "PNG")
        except Exception as e:
            print(f"Avatar kaydetme hatası: {str(e)}")
            return False

    def delete_avatar(self, user_id):
        """
        Kullanıcı avatarını siler

        Args:
            user_id (str): Kullanıcı benzersiz ID'si

        Returns:
            bool: İşlem başarılıysa True, değilse False
        """
        try:
            avatar_path = self.get_avatar_path(user_id)
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
                return True
            return False
        except Exception as e:
            print(f"Avatar silme hatası: {str(e)}")
            return False


class AvatarUploadDialog(QtWidgets.QDialog):
    """Avatar yükleme ve düzenleme için iletişim kutusu"""

    def __init__(self, avatar_manager, user_id, username=None, parent=None):
        """
        Avatar yükleme iletişim kutusunu başlatır

        Args:
            avatar_manager (AvatarManager): Avatar yönetimi için referans
            user_id (str): Kullanıcı benzersiz ID'si
            username (str, optional): Kullanıcı adı
            parent (QWidget, optional): Ebeveyn widget
        """
        super(AvatarUploadDialog, self).__init__(parent)

        self.avatar_manager = avatar_manager
        self.user_id = user_id
        self.username = username
        self.current_pixmap = None

        self.setWindowTitle("Avatar Ayarları")
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

        # Ana düzen
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Bilgi etiketi
        info_label = QtWidgets.QLabel("Avatar resminizi yükleyin veya değiştirin. "
                                     "Maksimum boyut 150x150 pikseldir.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Avatar önizleme alanı
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

        # Mevcut avatarı yükle
        self.load_current_avatar()

        # Butonlar
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Avatar yükleme butonu
        self.upload_button = QtWidgets.QPushButton("Dosyadan Yükle")
        self.upload_button.clicked.connect(self.upload_avatar)
        buttons_layout.addWidget(self.upload_button)

        # Avatar silme butonu
        self.delete_button = QtWidgets.QPushButton("Avatarı Sil")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.clicked.connect(self.delete_avatar)
        buttons_layout.addWidget(self.delete_button)

        layout.addLayout(buttons_layout)

        # Alt düzen - Kapat butonu
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch(1)

        self.close_button = QtWidgets.QPushButton("Kapat")
        self.close_button.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_button)

        layout.addLayout(bottom_layout)

    def load_current_avatar(self):
        """Mevcut avatarı yükler ve gösterir"""
        pixmap = self.avatar_manager.load_avatar(self.user_id, 120)
        self.current_pixmap = pixmap
        self.avatar_preview.setPixmap(pixmap)

    def upload_avatar(self):
        """Dosya seçme işlemini başlatır ve avatarı günceller"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setWindowTitle("Avatar Resmi Seç")
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Resim Dosyaları (*.png *.jpg *.jpeg *.bmp)")

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
                try:
                    # Resmi yükle
                    pixmap = QtGui.QPixmap(image_path)

                    # Yeniden boyutlandır
                    pixmap = pixmap.scaled(120, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

                    # Önizleme göster
                    self.avatar_preview.setPixmap(pixmap)
                    self.current_pixmap = pixmap

                    # Kaydet
                    success = self.avatar_manager.save_avatar(self.user_id, pixmap)
                    if success:
                        QtWidgets.QMessageBox.information(self, "Başarılı", "Avatar başarıyla güncellendi.")
                    else:
                        QtWidgets.QMessageBox.warning(self, "Hata", "Avatar kaydedilirken bir hata oluştu.")

                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Hata", f"Resim yüklenirken hata oluştu: {str(e)}")

    def delete_avatar(self):
        """Mevcut avatarı siler ve varsayılan avatara döner"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Avatarı Sil",
            "Avatar resminizi silmek istediğinizden emin misiniz?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            # Avatarı sil
            success = self.avatar_manager.delete_avatar(self.user_id)

            # Varsayılan avatarı göster
            self.load_current_avatar()

            if success:
                QtWidgets.QMessageBox.information(self, "Başarılı", "Avatar başarıyla silindi.")