import nuke
import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
from nukescripts import panels
import json
import os
import socket
import datetime
import time
import random


class ToastNotification(QtWidgets.QWidget):
    """Ekranın sağ alt köşesinde kısa süre görünen bildirim penceresi"""

    def __init__(self, message, sender="", parent=None, duration=3000):
        super(ToastNotification, self).__init__(parent)
        self.duration = duration

        # Pencere ayarları
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        # Ana düzen
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Bildirim paneli - AÇIK GRİ arka plan
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

        # İçerik düzeni (avatar + mesaj)
        content_layout = QtWidgets.QHBoxLayout()

        # Avatar ekle
        avatar_label = QtWidgets.QLabel()
        avatar_label.setFixedSize(40, 40)

        # avatar.png'yi yüklemeye çalış
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_folder = os.path.join(script_dir, "db")
        avatar_path = os.path.join(db_folder, "avatar.png")

        if os.path.exists(avatar_path):
            # Avatar dosyası varsa yükle
            avatar_pixmap = QtGui.QPixmap(avatar_path)
            avatar_pixmap = avatar_pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        else:
            # Yoksa varsayılan gri daire oluştur
            avatar_pixmap = QtGui.QPixmap(40, 40)
            avatar_pixmap.fill(QtCore.Qt.transparent)

            painter = QtGui.QPainter(avatar_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setBrush(QtGui.QBrush(QtGui.QColor("#777777")))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(0, 0, 40, 40)
            painter.end()

        avatar_label.setPixmap(avatar_pixmap)
        content_layout.addWidget(avatar_label)

        # Mesaj içerik alanı (gönderen + mesaj)
        message_container = QtWidgets.QWidget()
        message_layout = QtWidgets.QVBoxLayout(message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(5)

        if sender:
            # Gönderen adını ekle
            sender_label = QtWidgets.QLabel(sender)
            sender_label.setStyleSheet("color: #444444; font-weight: bold;")
            message_layout.addWidget(sender_label)

        # Mesaj içeriği
        message_label = QtWidgets.QLabel(message)
        message_label.setStyleSheet("color: #333333;")
        message_label.setWordWrap(True)
        message_layout.addWidget(message_label)

        content_layout.addWidget(message_container, 1)  # 1=stretch faktörü

        # Kapat butonu - üst sağda
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

        # Otomatik kapanma için zamanlayıcı
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.fadeOut)
        self.timer.setSingleShot(True)

        # Animasyon için opacity efekti
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)

        # Fade-in animasyonu
        self.fade_in_anim = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_anim.setDuration(300)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)

        # Fade-out animasyonu
        self.fade_out_anim = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.finished.connect(self.close)

        # Boyut
        self.setFixedWidth(300)
        self.adjustSize()

    def showEvent(self, event):
        """Gösterme olayını yakala ve animasyonları başlat"""
        super(ToastNotification, self).showEvent(event)

        # Ekranın sağ alt köşesinde konumlandır
        desktop = QtWidgets.QApplication.desktop()
        screen_rect = desktop.screenGeometry()
        self.move(screen_rect.width() - self.width() - 20,
                  screen_rect.height() - self.height() - 20)

        # Fade-in animasyonu başlat
        self.fade_in_anim.start()

        # Belirli bir süre sonra kapanma zamanlayıcısını başlat
        self.timer.start(self.duration)

    def fadeOut(self):
        """Fade-out animasyonunu başlat"""
        self.fade_out_anim.start()

class MessageWidget(QtWidgets.QWidget):
    def __init__(self, username, timestamp, message, is_self=False, parent=None, row_index=0):
        super(MessageWidget, self).__init__(parent)

        # Satır rengini alternatif yap - koyu gri ve biraz daha koyu gri
        if row_index % 2 == 0:
            bg_color = "#333333"
        else:
            bg_color = "#2D2D2D"

        # Tüm widget arka planını ayarla
        self.setStyleSheet(f"background-color: {bg_color}; color: white;")

        # Ana düzeni genişlet ve tüm alanı doldurmasını sağla
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Boşluk olmasın

        # İçerik konteyneri - tüm genişliği kaplaması için genişletildi
        container = QtWidgets.QWidget()
        container.setStyleSheet(f"background-color: {bg_color};")
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        container_layout = QtWidgets.QHBoxLayout(container)

        # Kendi mesajlarımız sağda, diğerleri solda
        if is_self:
            container_layout.addStretch(1)  # Boş alan ekleyerek sağa yasla

        # Avatar (db klasöründeki avatar.png)
        avatar_label = QtWidgets.QLabel()
        avatar_label.setFixedSize(50, 50)

        # avatar.png'yi yüklemeye çalış
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_folder = os.path.join(script_dir, "db")
        avatar_path = os.path.join(db_folder, "avatar.png")

        if os.path.exists(avatar_path):
            # Avatar dosyası varsa yükle
            avatar_pixmap = QtGui.QPixmap(avatar_path)
            avatar_pixmap = avatar_pixmap.scaled(50, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        else:
            # Yoksa varsayılan gri daire oluştur
            avatar_pixmap = QtGui.QPixmap(50, 50)
            avatar_pixmap.fill(QtCore.Qt.transparent)

            painter = QtGui.QPainter(avatar_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setBrush(QtGui.QBrush(QtGui.QColor("#555555")))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(0, 0, 50, 50)
            painter.end()

        avatar_label.setPixmap(avatar_pixmap)

        # Kendi mesajlarımız için avatar sağda, diğerleri için solda
        if is_self:
            container_layout.addLayout(self._createMessageLayout(username, timestamp, message, True))
            container_layout.addWidget(avatar_label)
        else:
            container_layout.addWidget(avatar_label)
            container_layout.addLayout(self._createMessageLayout(username, timestamp, message, False))

        if not is_self:
            container_layout.addStretch(1)  # Boş alan ekleyerek sola yasla

        # Konteyneri ana düzene ekle ve tam genişliği kaplamasını sağla
        main_layout.addWidget(container, 1)  # 1 = stretch faktörü

    def _createMessageLayout(self, username, timestamp, message, is_self):
        """Mesaj içeriği düzenini oluşturur"""
        message_layout = QtWidgets.QVBoxLayout()
        message_layout.setSpacing(4)

        # Başlık (Kullanıcı adı ve zaman damgası) düzeni
        header_layout = QtWidgets.QHBoxLayout()

        # Kendi mesajlarımız için sağa, diğerleri için sola yasla
        if is_self:
            header_layout.addStretch(1)

        # Kullanıcı adı (baloncuk olmadan)
        username_label = QtWidgets.QLabel(username.upper())
        username_label.setStyleSheet("font-weight: bold; color: white;")
        header_layout.addWidget(username_label)

        # Sadece saat bilgisini al (timestamp: "YYYY-MM-DD HH:MM:SS" formatında)
        try:
            dt_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = dt_obj.strftime("%H:%M")
        except:
            time_str = timestamp.split(" ")[-1] if " " in timestamp else timestamp

        # Saat bilgisi için baloncuk
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

        # Mesaj metni (baloncuk olmadan)
        message_label = QtWidgets.QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: white;")

        # Kendi mesajlarımız için sağa, diğerleri için sola yasla
        if is_self:
            message_label.setAlignment(QtCore.Qt.AlignRight)
        else:
            message_label.setAlignment(QtCore.Qt.AlignLeft)

        message_layout.addWidget(message_label)

        return message_layout

class NukeChat(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # JSON dosyalarını mevcut Python dosyasıyla aynı dizinde "db" klasörüne kaydet
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.network_folder = os.path.join(script_dir, "db")  # Python dosyası ile aynı dizindeki "db" klasörü
        self.loadOnlineUsers()
        self.onlineUsersTimer = QtCore.QTimer()
        self.onlineUsersTimer.timeout.connect(self.updateOnlineUsers)
        self.onlineUsersTimer.start(5000)

        # Eğer "db" klasörü yoksa oluştur
        if not os.path.exists(self.network_folder):
            try:
                os.makedirs(self.network_folder)
                print(f"\"db\" klasörü oluşturuldu: {self.network_folder}")
            except Exception as e:
                print(f"Klasör oluşturma hatası: {str(e)}")
                # Hata durumunda alternatif konum
                self.network_folder = os.path.dirname(os.path.abspath(__file__))
                print(f"Alternatif konum kullanılıyor: {self.network_folder}")

        # Mesaj verileri için dosya yolu
        self.chat_file = os.path.join(self.network_folder, "nukechat_messages.json")
        # Kullanıcı ayarları için dosya yolu
        self.settings_file = os.path.join(self.network_folder, "nukechat_settings.json")
        self.notifications_file = os.path.join(self.network_folder, "notifications.json")
        self.config_file = None
        # Dosya konumunu ekrana yazdır
        print("NukeChat JSON dosyası şuraya kaydedilecek:", self.chat_file)

        # Son güncelleme zamanını takip etmek için
        self.last_update_time = 0

        # Benzersiz kullanıcı ID (makine adı + rastgele ID)
        self.user_id = f"{socket.gethostname()}_{random.randint(1000, 9999)}"

        # Kullanıcı adı ayarı
        self.custom_username = ""
        self.loadSettings()

        # Ana düzen
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # Arama ve filtreleme alanı
        search_container = QtWidgets.QWidget()
        search_container.setStyleSheet("background-color: #333333;")
        search_layout = QtWidgets.QHBoxLayout(search_container)
        search_layout.setContentsMargins(10, 5, 10, 5)

        # Arama etiketi
        search_label = QtWidgets.QLabel("Ara:")
        search_label.setStyleSheet("color: white;")
        search_layout.addWidget(search_label)

        # Arama giriş kutusu
        self.searchInput = QtWidgets.QLineEdit()
        self.searchInput.setPlaceholderText("Mesajlarda ara...")
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

        # Filtreleme açılır kutusu
        self.filterCombo = QtWidgets.QComboBox()
        self.filterCombo.addItems(["Tüm Mesajlar", "Kendi Mesajlarım", "Diğer Mesajlar"])
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

        # Arama ve filtreleme butonları
        self.searchButton = QtWidgets.QPushButton("Ara")
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

        self.clearButton = QtWidgets.QPushButton("Temizle")
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

        # Tab widget oluştur
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

        # Mesajlar tab
        self.messagesTab = QtWidgets.QWidget()
        self.messagesTabLayout = QtWidgets.QVBoxLayout(self.messagesTab)
        self.messagesTabLayout.setContentsMargins(0, 0, 0, 0)
        self.messagesTabLayout.setSpacing(0)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        # Mesajların görüntüleneceği alan - arka planı orijinale çevir
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
        # Mesajların container'ının arka planını daha koyu gri yap
        self.messagesContainer.setStyleSheet("background-color: #282828;")
        self.messagesLayout = QtWidgets.QVBoxLayout(self.messagesContainer)
        self.messagesLayout.setContentsMargins(0, 0, 0, 0)
        self.messagesLayout.setSpacing(0)
        # Mesajları alttan yukarı doğru göstermek için stretch ekleyelim
        self.messagesLayout.addStretch(1)

        self.scrollArea.setWidget(self.messagesContainer)
        self.messagesTabLayout.addWidget(self.scrollArea)

        # Ayarlar tab
        self.settingsTab = QtWidgets.QWidget()
        self.settingsTabLayout = QtWidgets.QVBoxLayout(self.settingsTab)
        self.settingsTabLayout.setContentsMargins(20, 20, 20, 20)
        self.settingsTabLayout.setSpacing(10)

        # Kullanıcı adı ayarı
        username_layout = QtWidgets.QHBoxLayout()
        username_label = QtWidgets.QLabel("Kullanıcı Adı:")
        username_label.setStyleSheet("color: white;")
        username_layout.addWidget(username_label)

        self.usernameInput = QtWidgets.QLineEdit()
        self.usernameInput.setPlaceholderText("Özel kullanıcı adı (boş bırakılırsa bilgisayar adı kullanılır)")
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

        # Kaydet butonu
        self.saveSettingsButton = QtWidgets.QPushButton("Kaydet")
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
        self.settingsTabLayout.addStretch(1)  # Boşluğu alt kısımda bırakmak için

        # Tab'ları ekle
        self.tabWidget.addTab(self.messagesTab, "Mesajlar")
        self.tabWidget.addTab(self.settingsTab, "Ayarlar")

        self.layout().addWidget(self.tabWidget, 1)  # 1 = stretch faktörü

        # Giriş alanı arka planı
        input_container = QtWidgets.QWidget()
        input_container.setStyleSheet("background-color: #333333;")
        input_layout = QtWidgets.QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)

        # Mesaj giriş container'ı
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

        # Mesaj yazma alanı - QTextEdit olarak (genişletilebilir)
        self.messageInput = QtWidgets.QTextEdit()
        self.messageInput.setPlaceholderText("Mesajınızı yazın...")
        self.messageInput.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: white;
                border: none;
                padding: 0px;
                min-height: 40px;
                max-height: 100px;
            }
        """)
        self.messageInput.setMinimumHeight(40)
        self.messageInput.setMaximumHeight(100)

        # Mesaj/durum bildirim alanı
        self.notificationLayout = QtWidgets.QHBoxLayout()
        self.statusLabel = QtWidgets.QLabel("Hazır")
        self.statusLabel.setStyleSheet("color: rgba(170, 170, 170, 0.7); font-size: 10px;")
        self.notificationLayout.addWidget(self.statusLabel)

        # Gönder butonu (ikon)
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
        self.sendButton.setText("➤")  # Ok ikonu

        self.notificationLayout.addWidget(self.sendButton)

        # Yukarıdan aşağı düzen: mesaj yazma alanı, durum etiketi
        message_input_layout.addWidget(self.messageInput)
        message_input_layout.addLayout(self.notificationLayout)

        # Mesaj girişini ana düzene ekle
        input_layout.addWidget(message_input_container)

        self.layout().addWidget(input_container)

        # Pencere boyutlandırma politikası ayarları
        self.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        ))

        # Gönder butonu bağlantısı
        self.sendButton.clicked.connect(self.sendMessage)

        # Kullanıcı adı kaydet butonu bağlantısı
        self.saveSettingsButton.clicked.connect(self.saveSettings)

        # Arama ve filtreleme bağlantıları
        self.searchButton.clicked.connect(self.searchMessages)
        self.clearButton.clicked.connect(self.clearSearch)
        self.searchInput.returnPressed.connect(self.searchMessages)
        self.filterCombo.currentIndexChanged.connect(self.filterMessages)

        # Enter tuşu ile gönderme - QTextEdit için özel tuş işleyicisi gerekiyor
        self.messageInput.installEventFilter(self)

        # Timer kurulumu - mesajları düzenli olarak günceller
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.checkForUpdates)
        self.updateTimer.start(1000)  # 1 saniyede bir güncelle
        self.notificationTimer = QtCore.QTimer()
        self.notificationTimer.timeout.connect(self.checkNotifications)
        self.notificationTimer.start(3000)  # 3 saniyede bir bildirimleri kontrol et
        # İkinci timer - presence güncellemesi için
        self.presenceTimer = QtCore.QTimer()
        self.presenceTimer.timeout.connect(self.updatePresence)
        self.presenceTimer.start(5000)  # 5 saniyede bir varlığımızı bildir

        # Presence dosyası yolu
        self.presence_file = os.path.join(self.network_folder, "presence.json")

        # Başlangıçta varlığımızı bildir
        self.updatePresence()

        # Başlangıçta mevcut mesajları yükle
        self.loadMessages()

        # Genel stil
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
        """)

        # Arama ve filtreleme değişkenleri
        self.current_search = ""
        self.current_filter = 0  # 0: Tüm, 1: Kendi, 2: Diğerleri

    def updateOnlineUsers(self):
        """Online kullanıcı listesini günceller"""
        # Önce mevcut online kullanıcılar widgetını temizle
        while self.settingsTabLayout.count() > 2:  # İlk iki widget korunacak
            item = self.settingsTabLayout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()

        # Tekrar online kullanıcıları yükle
        self.loadOnlineUsers()
    def loadOnlineUsers(self):
        """Online kullanıcıları yükler ve görüntüler"""
        try:
            # Online kullanıcılar için alan
            online_users_container = QtWidgets.QWidget()
            online_users_layout = QtWidgets.QVBoxLayout(online_users_container)
            online_users_layout.setContentsMargins(0, 0, 0, 0)
            online_users_layout.setSpacing(10)

            # Online kullanıcılar başlığı
            online_title = QtWidgets.QLabel("Şu Anda Online")
            online_title.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
            """)
            online_users_layout.addWidget(online_title)

            # Presence dosyasından online kullanıcıları oku
            online_users = []
            current_time = time.time()
            if os.path.exists(self.presence_file):
                try:
                    with open(self.presence_file, 'r', encoding='utf-8') as file:
                        presence_data = json.load(file)

                        # Son 30 saniye içinde aktif olan kullanıcıları bul
                        for uid, data in presence_data.items():
                            if current_time - data["last_seen"] < 30:  # 30 saniye içinde aktif
                                online_users.append(data["user"])
                except Exception as e:
                    print(f"Online kullanıcıları okuma hatası: {str(e)}")

            if online_users:
                # Online kullanıcıları listele
                for user in online_users:
                    user_widget = QtWidgets.QWidget()
                    user_layout = QtWidgets.QHBoxLayout(user_widget)
                    user_layout.setContentsMargins(10, 5, 10, 5)
                    user_layout.setSpacing(10)

                    # Online kullanıcı simgesi
                    online_icon = QtWidgets.QLabel("🟢")
                    online_icon.setStyleSheet("font-size: 14px;")
                    user_layout.addWidget(online_icon)

                    # Kullanıcı adı
                    user_label = QtWidgets.QLabel(user)
                    user_label.setStyleSheet("""
                        color: white;
                        font-size: 14px;
                    """)
                    user_layout.addWidget(user_label)

                    user_layout.addStretch(1)
                    online_users_layout.addWidget(user_widget)
            else:
                # Kimse online değilse
                no_users_label = QtWidgets.QLabel("Şu anda online kullanıcı yok")
                no_users_label.setStyleSheet("""
                    color: #888888;
                    font-style: italic;
                    padding: 10px;
                """)
                online_users_layout.addWidget(no_users_label)

            online_users_layout.addStretch(1)

            # Var olan settingsTabLayout'a ekle
            self.settingsTabLayout.addWidget(online_users_container)

        except Exception as e:
            print(f"Online kullanıcıları yükleme hatası: {str(e)}")

    def eventFilter(self, obj, event):
        """QTextEdit ile Enter tuşu ile göndermeyi etkinleştirmek için event filter"""
        if obj is self.messageInput and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and not event.modifiers() & QtCore.Qt.ShiftModifier:
                self.sendMessage()
                return True
            if event.key() == QtCore.Qt.Key_Return and event.modifiers() & QtCore.Qt.ShiftModifier:
                # Shift+Enter ile yeni satır
                cursor = self.messageInput.textCursor()
                cursor.insertText("\n")
                return True
        return super(NukeChat, self).eventFilter(obj, event)

    def loadSettings(self):
        """Ayarları yükle"""
        try:
            # config.json dosyasının yolu
            self.config_file = os.path.join(self.network_folder, "config.json")

            # Eğer config.json dosyası varsa
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    config = json.load(file)

                    # Bilgisayar adı için kullanıcı adını al
                    hostname = socket.gethostname()
                    if hostname in config:
                        self.custom_username = config[hostname]

            # Ayrıca eski settings.json dosyasını da kontrol et (geriye uyumluluk için)
            elif os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as file:
                    settings = json.load(file)
                    if 'username' in settings:
                        self.custom_username = settings['username']

                        # Eski ayarları yeni formata dönüştür
                        self.saveSettings()
        except Exception as e:
            print(f"Ayarlar yüklenirken hata: {str(e)}")

    def saveSettings(self):
        """Ayarları kaydet"""
        try:
            # Girilen kullanıcı adını al
            self.custom_username = self.usernameInput.text().strip()

            # config.json dosyasını yükle veya yeni oluştur
            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as file:
                        config = json.load(file)
                except:
                    # Dosya bozuksa yeni oluştur
                    config = {}

            # Bilgisayar adına karşılık kullanıcı adını kaydet
            hostname = socket.gethostname()
            config[hostname] = self.custom_username

            # config.json'a kaydet
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)

            self.updateStatus("Kullanıcı adı kaydedildi")
        except Exception as e:
            self.updateStatus(f"Ayarlar kaydedilemedi: {str(e)}")

    def getCurrentUser(self):
        """Kullanıcı adını döndürür (özel ad varsa onu, yoksa makine adını)"""
        if self.custom_username:
            return f"{self.custom_username} - ({socket.gethostname()})"
        return socket.gethostname()

    def updateStatus(self, status):
        """Durum etiketini günceller"""
        self.statusLabel.setText(status)

        # 3 saniye sonra "Hazır" mesajına geri dön (önemli mesajlar için)
        QtCore.QTimer.singleShot(3000, lambda: self.statusLabel.setText("Hazır"))

    def updatePresence(self):
        """Varlık bilgisini günceller"""
        try:
            # Mevcut varlık verilerini yükle
            presence_data = {}
            if os.path.exists(self.presence_file):
                try:
                    with open(self.presence_file, 'r', encoding='utf-8') as file:
                        presence_data = json.load(file)
                except:
                    # Dosya kilitli veya bozuk olabilir, yeni dosya oluştur
                    presence_data = {}

            # Kendi varlığımızı ekle/güncelle
            current_time = time.time()
            presence_data[self.user_id] = {
                "user": self.getCurrentUser(),
                "last_seen": current_time
            }

            # Eski kayıtları temizle (son 30 saniyede aktif olmayanlar)
            active_users = {}
            for uid, data in presence_data.items():
                if current_time - data["last_seen"] < 30:  # 30 saniyeden eski olanları sil
                    active_users[uid] = data

            # Dosyaya kaydet
            with open(self.presence_file, 'w', encoding='utf-8') as file:
                json.dump(active_users, file, ensure_ascii=False)

        except Exception as e:
            self.updateStatus(f"Presence Hatası: {str(e)}")

    def checkForUpdates(self):
        """Yeni mesajlar için dosyayı kontrol eder"""
        try:
            if not os.path.exists(self.chat_file):
                # Dosya yoksa boş JSON oluştur
                with open(self.chat_file, 'w', encoding='utf-8') as file:
                    json.dump([], file)
                self.last_update_time = time.time()
                return

            # Dosya son değişiklik zamanını kontrol et
            file_mod_time = os.path.getmtime(self.chat_file)

            if file_mod_time > self.last_update_time:
                # Mevcut mesaj sayısını kaydet
                old_message_count = 0
                if os.path.exists(self.chat_file):
                    try:
                        with open(self.chat_file, 'r', encoding='utf-8') as file:
                            old_message_count = len(json.load(file))
                    except:
                        old_message_count = 0

                # Mesajları yükle
                self.loadMessages()

                # Yeni mesaj sayısını kontrol et
                new_message_count = 0
                if os.path.exists(self.chat_file):
                    try:
                        with open(self.chat_file, 'r', encoding='utf-8') as file:
                            new_message_count = len(json.load(file))
                    except:
                        new_message_count = 0

                # Yeni mesaj varsa bildirim göster
                if new_message_count > old_message_count:
                    self.showNotification(new_message_count - old_message_count)

                self.last_update_time = file_mod_time
                self.updateStatus("Mesajlar Güncellendi")
        except Exception as e:
            self.updateStatus(f"Güncelleme Hatası: {str(e)}")

    def showNotification(self, count):
        """Nuke içinde bildirim gösterir"""
        try:
            # Tab başlığını güncelleyelim
            self.tabWidget.setTabText(0, f"Mesajlar ({count} yeni)")

            # Bildirim alanını daha belirgin yapalım
            self.statusLabel.setStyleSheet("color: #FF9900; font-weight: bold; font-size: 12px;")
            self.statusLabel.setText(f"{count} yeni mesaj var!")

            # Nuke'un ana penceresinde bildirim göster (opsiyonel)
            import nuke
            nuke.message(f"{count} yeni NukeChat mesajı var!")

            # Bildirim zil sesi çal (opsiyonel)
            # Burada bir ses dosyası çalabilirsiniz

            # 5 saniye sonra bildirim stilini normal hale getir
            QtCore.QTimer.singleShot(5000, lambda: self.resetNotification())
        except Exception as e:
            print(f"Bildirim gösterme hatası: {str(e)}")

    def resetNotification(self):
        """Bildirim göstergesini sıfırlar"""
        self.tabWidget.setTabText(0, "Mesajlar")
        self.statusLabel.setStyleSheet("color: rgba(170, 170, 170, 1); font-size: 14px;")
        self.statusLabel.setText("Hazır")

    def tabChanged(self, index):
        """Tab değiştiğinde çağrılır"""
        if index == 0:  # Mesajlar tabı seçildiğinde bildirimi sıfırla
            self.resetNotification()

    def loadMessages(self):
        """JSON dosyasından mesajları yükler ve görüntüler"""
        try:
            if os.path.exists(self.chat_file):
                with open(self.chat_file, 'r', encoding='utf-8') as file:
                    messages = json.load(file)

                # Arama ve filtreleme uygula
                filtered_messages = self.applySearchAndFilter(messages)

                # Önce mevcut mesajları temizle (stretch hariç)
                while self.messagesLayout.count() > 1:
                    item = self.messagesLayout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

                # Kendi kullanıcı adımız
                current_user = self.getCurrentUser()

                # Yeni mesaj widget'larını ekle
                for idx, msg in enumerate(filtered_messages):
                    # Kendimize ait mesaj mı kontrol et
                    is_self = msg['user'] == current_user

                    # Mesaj widget'ı oluştur
                    message_widget = MessageWidget(
                        msg['user'],
                        msg['timestamp'],
                        msg['message'],
                        is_self=is_self,
                        row_index=idx
                    )

                    # Mesajı en alta ekle (stretch'in üzerine)
                    self.messagesLayout.insertWidget(self.messagesLayout.count() - 1, message_widget)

                # Scroll'u en alta hareket ettir
                self.scrollToBottom()

            self.updateStatus("Hazır")
        except Exception as e:
            self.updateStatus(f"Yükleme Hatası: {str(e)}")

    def applySearchAndFilter(self, messages):
        """Arama ve filtreleme kriterlerini uygular"""
        filtered_messages = []
        current_user = self.getCurrentUser()

        for msg in messages:
            # Filtrelemeyi uygula
            if self.current_filter == 1 and msg['user'] != current_user:  # Sadece kendi mesajlarım
                continue
            if self.current_filter == 2 and msg['user'] == current_user:  # Sadece diğer mesajlar
                continue

            # Aramayı uygula
            if self.current_search and self.current_search.lower() not in msg['message'].lower():
                continue

            filtered_messages.append(msg)

        return filtered_messages

    def searchMessages(self):
        """Mesajlarda arama yapar"""
        self.current_search = self.searchInput.text()
        self.loadMessages()

    def clearSearch(self):
        """Arama ve filtreleri temizler"""
        self.searchInput.clear()
        self.filterCombo.setCurrentIndex(0)
        self.current_search = ""
        self.current_filter = 0
        self.loadMessages()

    def filterMessages(self, index):
        """Filtreleme tipini değiştirir"""
        self.current_filter = index
        self.loadMessages()

    def scrollToBottom(self):
        """Scroll'u en alta hareket ettirir"""
        QTimer = QtCore.QTimer
        QTimer.singleShot(100, lambda: self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        ))

    def saveMessage(self, message):
        """Mesajı JSON dosyasına kaydeder"""
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Dosyayı kilitlemeden önce biraz bekle (race condition'dan kaçınmak için)
                time.sleep(random.uniform(0.1, 0.5))

                # Mevcut mesajları yükle veya yeni liste oluştur
                messages = []
                if os.path.exists(self.chat_file):
                    with open(self.chat_file, 'r', encoding='utf-8') as file:
                        messages = json.load(file)

                # Yeni mesajı ekle
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_message = {
                    "user": self.getCurrentUser(),
                    "message": message,
                    "timestamp": current_time
                }
                messages.append(new_message)

                # Dosyaya kaydet
                with open(self.chat_file, 'w', encoding='utf-8') as file:
                    json.dump(messages, file, ensure_ascii=False, indent=4)

                self.updateStatus("Mesaj Gönderildi")
                return True

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.updateStatus(f"Mesaj Kaydedilemedi: {str(e)}")
                    return False
                time.sleep(random.uniform(0.5, 1.0))  # Tekrar denemeden önce biraz daha uzun bekle

        return False

    def sendMessage(self):
        """Mesaj gönderme işlevi"""
        message = self.messageInput.toPlainText()
        if message.strip():
            self.updateStatus("Mesaj Gönderiliyor...")
            # Mesajı kaydet
            if self.saveMessage(message):
                # Bildirim oluştur
                self.createNotification(message)
                # Mesajları güncelleyerek göster
                self.loadMessages()
            # Mesaj alanını temizle
            self.messageInput.clear()


    def createNotification(self, message):
        """Diğer kullanıcılara bildirim oluşturur"""
        try:
            # Mevcut bildirimleri yükle
            notifications = {}
            if os.path.exists(self.notifications_file):
                try:
                    with open(self.notifications_file, 'r', encoding='utf-8') as file:
                        notifications = json.load(file)
                except:
                    notifications = {}

            # Varlık (presence) dosyasından aktif kullanıcıları al
            active_users = []
            if os.path.exists(self.presence_file):
                try:
                    with open(self.presence_file, 'r', encoding='utf-8') as file:
                        presence_data = json.load(file)
                        # Kendimiz hariç tüm aktif kullanıcıları al
                        for uid, data in presence_data.items():
                            if uid != self.user_id:
                                active_users.append(uid)
                except:
                    pass

            # Her aktif kullanıcı için bildirim oluştur
            current_time = time.time()
            sender_name = self.getCurrentUser()
            message_preview = message[:50] + "..." if len(message) > 50 else message

            for user_id in active_users:
                if user_id not in notifications:
                    notifications[user_id] = []

                # Bildirim ekle
                notifications[user_id].append({
                    "timestamp": current_time,
                    "sender": sender_name,
                    "message": message_preview,
                    "read": False
                })

            # Bildirimleri kaydet
            with open(self.notifications_file, 'w', encoding='utf-8') as file:
                json.dump(notifications, file, ensure_ascii=False)

        except Exception as e:
            print(f"Bildirim oluşturma hatası: {str(e)}")
            self.updateStatus(f"Bildirim oluşturma hatası: {str(e)}")

    def checkNotifications(self):
        """Yeni bildirimleri kontrol eder"""
        try:
            if not os.path.exists(self.notifications_file):
                return

            # Bildirimleri yükle
            notifications = {}
            try:
                with open(self.notifications_file, 'r', encoding='utf-8') as file:
                    notifications = json.load(file)
            except:
                return

            # Benim bildirimlerim
            my_notifications = notifications.get(self.user_id, [])

            # Okunmamış bildirimleri filtrele
            unread_notifications = [n for n in my_notifications if not n.get("read", False)]

            if unread_notifications:
                # Bildirim göster
                count = len(unread_notifications)

                # Tab başlığını güncelle
                self.tabWidget.setTabText(0, f"Mesajlar ({count} yeni)")

                # Durum çubuğunu güncelle
                self.statusLabel.setStyleSheet("color: #FF9900; font-weight: bold; font-size: 12px;")

                if count == 1:
                    # Tek bir bildirim için
                    notification = unread_notifications[0]
                    sender = notification["sender"]
                    message = notification["message"]
                    self.statusLabel.setText(f"Yeni mesaj: {sender}: {message}")

                    # Toast bildirim göster
                    toast = ToastNotification(message=message, sender=sender, parent=self, duration=5000)
                    toast.show()

                else:
                    # Birden fazla bildirim için
                    self.statusLabel.setText(f"{count} yeni mesaj var!")

                    # İlk mesaj için tam bildirim
                    notification = unread_notifications[0]
                    first_sender = notification["sender"]
                    first_message = notification["message"]

                    # Diğer mesajlar için özet bilgi
                    summary = f"... ve {count - 1} mesaj daha"

                    # Toast bildirim göster
                    toast = ToastNotification(message=f"{first_message}\n\n{summary}",
                                              sender=first_sender,
                                              parent=self,
                                              duration=5000)
                    toast.show()

                # Bildirimleri okundu olarak işaretle
                for notification in my_notifications:
                    notification["read"] = True

                # Güncellenmiş bildirimleri kaydet
                notifications[self.user_id] = my_notifications
                with open(self.notifications_file, 'w', encoding='utf-8') as file:
                    json.dump(notifications, file, ensure_ascii=False)

        except Exception as e:
            print(f"Bildirim kontrol hatası: {str(e)}")
            self.updateStatus(f"Bildirim kontrol hatası: {str(e)}")

panels.registerWidgetAsPanel('NukeChat', 'NukeChat', 'uk.co.thefoundry.NukeChat')
