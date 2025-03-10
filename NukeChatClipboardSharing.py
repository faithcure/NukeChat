"""
NukeChatClipboardSharing.py

Bu modül, Nuke script parçalarını kopyala-yapıştır yöntemiyle NukeChat üzerinden paylaşmayı sağlar.
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
    """Nuke script parçasını baloncuk şeklinde gösteren widget"""

    def __init__(self, script_data, parent=None):
        super(ScriptBubbleWidget, self).__init__(parent)

        # Ana düzen
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Script baloncuğu container'ı
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

        # Başlık düzeni
        header_layout = QtWidgets.QHBoxLayout()

        # Script ikonu
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("""
            background-color: #444444;
            border-radius: 2px;
            border: 1px solid #777777;
        """)
        header_layout.addWidget(icon_label)

        # Node sayısını belirle
        node_count = self.countNodes(script_data["script"])
        node_text = f"{node_count} Node" if node_count == 1 else f"{node_count} Nodes"

        # Açıklama metnini kontrol et - varsa açıklamayı göster, yoksa default değeri göster
        description = script_data.get("description", "")
        if description:
            header_title = QtWidgets.QLabel(f"<b>{description}</b> ({node_text})")
        else:
            header_title = QtWidgets.QLabel(f"<b>Script Parçası</b> ({node_text})")

        header_title.setStyleSheet("color: #FFFFFF; font-size: 13px;")
        header_layout.addWidget(header_title)
        header_layout.addStretch(1)

        # Checkbox'u kaldırdık - artık burada seçim kutusu yok

        bubble_layout.addLayout(header_layout)

        # Çizgi ayırıcı
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setStyleSheet("border: 1px solid #444444;")
        bubble_layout.addWidget(line)

        # Script kod alanı
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

        # Script alanı için maksimum yükseklik
        script_text.setMaximumHeight(250)
        bubble_layout.addWidget(script_text)

        # Buton için düzen
        buttons_layout = QtWidgets.QHBoxLayout()

        # "Kopyala" butonu
        copy_button = QtWidgets.QPushButton("Kopyala")
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
        """Script'i panoya kopyalar"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(script)

        # Kullanıcıya durum çubuğunda geri bildirim göster
        try:
            # Nuke ana modülünde bir global statusbar var mı kontrol et
            import nuke
            if hasattr(nuke, 'NukeChat') and hasattr(nuke.NukeChat, 'updateStatus'):
                nuke.NukeChat.updateStatus("Script panoya kopyalandı!")
            else:
                # Alternatif olarak QToolTip ile göster
                tooltip = QtWidgets.QToolTip
                tooltip.showText(QtGui.QCursor.pos(), "Script panoya kopyalandı!")
        except:
            # Nuke yoksa veya hata oluşursa basit bir tooltip göster
            tooltip = QtWidgets.QToolTip
            tooltip.showText(QtGui.QCursor.pos(), "Script panoya kopyalandı!")

    def countNodes(self, script):
        """Script içindeki node sayısını belirler"""
        # Node sayısını bulmak için basit bir sayım kullan
        # Bu metot, daha karmaşık scriptler için geliştirilmelidir
        node_count = 0
        for line in script.splitlines():
            # Node satırları genellikle bir isim ve süslü parantez içerir
            if re.search(r'\w+\s*\{', line) and not line.strip().startswith('#'):
                node_count += 1
        return node_count


class ClipboardHandler(QtCore.QObject):
    """Pano değişikliklerini izler ve Nuke script parçalarını tanımlar"""

    def __init__(self, parent=None):
        super(ClipboardHandler, self).__init__(parent)
        self.parent = parent

        # Pano nesnesine referans al
        self.clipboard = QtWidgets.QApplication.clipboard()

    def checkClipboard(self):
        """Pano içeriğini kontrol eder ve Nuke script parçasıysa True döner"""
        try:
            # Panodaki metni al
            clipboard_text = self.clipboard.text()

            # Nuke script parçası olup olmadığını kontrol et
            if clipboard_text and self.isNukeScript(clipboard_text):
                return True
        except:
            pass

        return False

    def isNukeScript(self, text):
        """Metnin Nuke script parçası olup olmadığını kontrol eder"""
        # Nuke script'lerinin tipik imzalarını kontrol et
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

        # Metinde bu göstergelerden en az birkaçı varsa muhtemelen bir Nuke script'idir
        indicator_count = 0
        for indicator in nuke_indicators:
            if indicator in text:
                indicator_count += 1

        # En az 3 gösterge varsa, bir Nuke script olarak kabul et
        return indicator_count >= 3

    def getScriptFromClipboard(self):
        """Panodan Nuke script'ini alır ve işler"""
        clipboard_text = self.clipboard.text()

        if clipboard_text and self.isNukeScript(clipboard_text):
            # Script verisi olarak formatla
            script_data = {
                "script": clipboard_text,
                "type": "script"
            }

            return script_data

        return None


def encodeScriptData(script_data):
    """Script verilerini bir JSON stringine dönüştürür, sonra base64 ile kodlar"""
    try:
        # Script verilerini JSON string'e dönüştür
        json_str = json.dumps(script_data, ensure_ascii=False)

        # Base64 ile kodla
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

        return encoded
    except Exception as e:
        print(f"Script verisi kodlama hatası: {str(e)}")
        return None


def decodeScriptData(encoded_data):
    """Base64 ile kodlanmış JSON script verilerini çözer"""
    try:
        # Base64 kodunu çöz
        json_str = base64.b64decode(encoded_data.encode('utf-8')).decode('utf-8')

        # JSON'dan dict'e dönüştür
        script_data = json.loads(json_str)

        return script_data
    except Exception as e:
        print(f"Script verisi çözme hatası: {str(e)}")
        return None