import sys
import os
import json
import winreg
import requests
import subprocess
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QSlider, QPushButton, QColorDialog, QSystemTrayIcon, QMenu, QFrame,
                             QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QFont, QIcon, QCursor, QPixmap

APP_VERSION = "1.0.0"
CONFIG_FILE = "AthanWidget_config.json"
REPO_OWNER = "Turki-Alshaikh"
REPO_NAME = "AthanWidget"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

DEFAULT_CONFIG = {
    "x": 100, "y": 100,
    "width": 280, "height": 160,
    "bg_alpha": 0.80,
    "font_family": "Segoe UI",
    "bg_color": "#1C1C1E",
    "text_primary": "#FFFFFF",
    "text_secondary": "#8E8E93",
    "accent_color": "#0A84FF",
    "arabic_numbers": True,
    "run_at_startup": True
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except: pass
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def set_startup(enable):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, "AthanWidget", 0, winreg.REG_SZ, sys.executable + ' "' + os.path.abspath(__file__) + '"')
        else:
            winreg.DeleteValue(key, "AthanWidget")
        winreg.CloseKey(key)
    except: pass

def convert_to_arabic(text):
    return text.translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))

# ==========================================
# كائن جلب البيانات
# ==========================================
class PrayerTimeFetcher(QThread):
    data_fetched = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            loc_res = requests.get('https://ipinfo.io/json', timeout=5).json()
            lat, lon = loc_res['loc'].split(',')
            
            url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lon}&method=4"
            pray_res = requests.get(url, timeout=5).json()
            timings = pray_res['data']['timings']
            
            prayers = {
                'الفجر': timings['Fajr'],
                'الظهر': timings['Dhuhr'],
                'العصر': timings['Asr'],
                'المغرب': timings['Maghrib'],
                'العشاء': timings['Isha']
            }
            self.data_fetched.emit(prayers)
        except:
            self.error_occurred.emit("لا يوجد اتصال بالإنترنت")

# ==========================================
# كائن تحميل التحديثات (يعمل بالخلفية كي لا يتجمد البرنامج)
# ==========================================
class UpdateDownloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True, timeout=10)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            # مسار التحميل (بجانب البرنامج الحالي)
            exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
            dir_name = os.path.dirname(exe_path)
            new_file_path = os.path.join(dir_name, "AthanWidget_update.exe")

            with open(new_file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            prog = int((downloaded / total_size) * 100)
                            self.progress.emit(prog)
            
            self.finished.emit(new_file_path)
        except Exception as e:
            self.error.emit(str(e))

# ==========================================
# زر التبديل الاحترافي
# ==========================================
class IOSToggle(QWidget):
    stateChanged = pyqtSignal(bool)

    def __init__(self, state=False):
        super().__init__()
        self.setFixedSize(44, 24)
        self._state = state

    def setChecked(self, state):
        self._state = state
        self.update()

    def mousePressEvent(self, event):
        self._state = not self._state
        self.stateChanged.emit(self._state)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#34C759") if self._state else QColor("#3A3A3C")
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.fillPath(path, color)
        x = 22 if self._state else 2
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(x, 2, 20, 20)
        painter.end()

# ==========================================
# نافذة الإعدادات
# ==========================================
class SettingsWindow(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.old_pos = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 420)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background-color: #2C2C2E; border-top-left-radius: 15px; border-top-right-radius: 15px;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        lbl_title = QLabel("الإعدادات")
        lbl_title.setStyleSheet(f"color: white; font-family: '{self.config['font_family']}'; font-size: 14px; font-weight: bold;")
        title_layout.addWidget(lbl_title)
        title_layout.addStretch()
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("QPushButton { background-color: transparent; color: #8E8E93; font-weight: bold; font-size: 14px; border: none; } QPushButton:hover { color: #FF3B30; }")
        btn_close.clicked.connect(self.close)
        title_layout.addWidget(btn_close)
        main_layout.addWidget(title_bar)

        content = QWidget()
        content.setStyleSheet("background-color: #1C1C1E; border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)

        font_sub = f"color: #8E8E93; font-family: '{self.config['font_family']}'; font-size: 12px;"
        font_main = f"color: white; font-family: '{self.config['font_family']}'; font-size: 14px; font-weight: bold;"

        lbl_alpha = QLabel("شفافية الخلفية:")
        lbl_alpha.setStyleSheet(font_sub)
        content_layout.addWidget(lbl_alpha)
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(20, 100)
        self.alpha_slider.setValue(int(self.config["bg_alpha"] * 100))
        self.alpha_slider.setStyleSheet("QSlider::groove:horizontal { border-radius: 2px; height: 4px; background: #2C2C2E; } QSlider::handle:horizontal { background: #0A84FF; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }")
        self.alpha_slider.valueChanged.connect(self.update_alpha)
        content_layout.addWidget(self.alpha_slider)
        content_layout.addSpacing(15)

        lbl_colors = QLabel("تخصيص الألوان:")
        lbl_colors.setStyleSheet(font_sub)
        content_layout.addWidget(lbl_colors)

        def add_color_row(text, key):
            row = QHBoxLayout()
            lbl = QLabel(text)
            lbl.setStyleSheet(font_main)
            row.addWidget(lbl)
            btn = QPushButton("تغيير")
            btn.setFixedSize(60, 26)
            btn.setStyleSheet("QPushButton { background-color: #2C2C2E; color: #0A84FF; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #3A3A3C; color: white; }")
            btn.clicked.connect(lambda: self.pick_color(key))
            row.addWidget(btn)
            content_layout.addLayout(row)

        add_color_row("لون الخلفية", "bg_color")
        add_color_row("لون النص الأساسي", "text_primary")
        add_color_row("لون العداد", "accent_color")
        
        content_layout.addSpacing(10)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #2C2C2E;")
        content_layout.addWidget(line)
        content_layout.addSpacing(10)

        def add_toggle_row(text, initial_state, command):
            row = QHBoxLayout()
            lbl = QLabel(text)
            lbl.setStyleSheet(font_main)
            row.addWidget(lbl)
            tgl = IOSToggle(initial_state)
            tgl.stateChanged.connect(command)
            row.addWidget(tgl)
            content_layout.addLayout(row)

        add_toggle_row("الأرقام العربية", self.config["arabic_numbers"], self.toggle_arabic)
        add_toggle_row("التشغيل مع الويندوز", self.config["run_at_startup"], self.toggle_startup)

        content_layout.addStretch()
        main_layout.addWidget(content)
        self.setLayout(main_layout)

    def mousePressEvent(self, event):
        if event.pos().y() <= 40:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def update_alpha(self, val):
        self.config["bg_alpha"] = val / 100.0
        self.save_and_emit()

    def pick_color(self, key):
        color = QColorDialog.getColor(QColor(self.config[key]), self, "اختر لوناً")
        if color.isValid():
            self.config[key] = color.name()
            self.save_and_emit()

    def toggle_arabic(self, state):
        self.config["arabic_numbers"] = state
        self.save_and_emit()

    def toggle_startup(self, state):
        self.config["run_at_startup"] = state
        set_startup(state)
        self.save_and_emit()

    def save_and_emit(self):
        save_config(self.config)
        self.settings_changed.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        painter.setClipPath(path)
        painter.end()

# ==========================================
# الويدجت الرئيسي (الواجهة العائمة)
# ==========================================
class AthanWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.prayers = None
        self.old_pos = None
        self.is_resizing = False

        self.init_ui()
        self.init_tray_icon()

        self.fetcher = PrayerTimeFetcher()
        self.fetcher.data_fetched.connect(self.on_data_fetched)
        self.fetcher.error_occurred.connect(self.on_error)
        self.fetcher.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(self.config["x"], self.config["y"], self.config["width"], self.config["height"])

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 15)
        
        self.lbl_title = QLabel(" AthanWidget")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prayer = QLabel("جاري التحميل...")
        self.lbl_prayer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time = QLabel("--:--:--")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_prayer)
        layout.addWidget(self.lbl_time)
        self.setLayout(layout)
        
        self.setMouseTracking(True)
        self.apply_styles()

    def apply_styles(self):
        w = self.width()
        scale = w / 280.0
        ff = self.config["font_family"]
        self.lbl_title.setStyleSheet(f"color: {self.config['text_secondary']}; font-family: '{ff}'; font-size: {int(11*scale)}px; font-weight: bold;")
        self.lbl_prayer.setStyleSheet(f"color: {self.config['text_primary']}; font-family: '{ff}'; font-size: {int(22*scale)}px; font-weight: bold;")
        self.lbl_time.setStyleSheet(f"color: {self.config['accent_color']}; font-family: '{ff}'; font-size: {int(34*scale)}px; font-weight: bold;")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_color = QColor(self.config["bg_color"])
        bg_color.setAlphaF(self.config["bg_alpha"]) 
        path = QPainterPath()
        r = int(25 * (self.width() / 280.0))
        path.addRoundedRect(0, 0, self.width(), self.height(), r, r)
        painter.fillPath(path, bg_color)
        painter.setPen(QColor(self.config["text_secondary"]))
        w, h = self.width(), self.height()
        scale = w / 280.0
        for i in range(3):
            offset = i * 4 * scale
            painter.drawLine(int(w - 6*scale - offset), int(h - 6*scale), int(w - 6*scale), int(h - 6*scale - offset))
        painter.end()

    def init_tray_icon(self):
        icon_path = resource_path("icon.ico")
        qicon = QIcon(icon_path)
        if qicon.isNull():
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setFont(QFont("Segoe UI", 40))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "")
            painter.end()
            qicon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(qicon, self)
        self.tray_icon.setToolTip("AthanWidget")
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet("QMenu { background-color: #1C1C1E; color: white; border: 1px solid #2C2C2E; } QMenu::item:selected { background-color: #0A84FF; }")
        
        action_settings = tray_menu.addAction(" إعدادات الويدجت")
        action_settings.triggered.connect(self.open_settings)
        action_update = tray_menu.addAction(" التحقق من التحديثات")
        action_update.triggered.connect(self.check_for_updates)
        tray_menu.addSeparator()
        action_exit = tray_menu.addAction(" خروج")
        action_exit.triggered.connect(self.safe_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().x() > self.width() - 30 and event.pos().y() > self.height() - 30:
                self.is_resizing = True
            else:
                self.is_resizing = False
            self.old_pos = event.globalPosition().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            menu.setStyleSheet("QMenu { background-color: #1C1C1E; color: white; border: 1px solid #2C2C2E; font-size: 13px; } QMenu::item:selected { background-color: #0A84FF; }")
            action_sett = menu.addAction(" إعدادات")
            action_sett.triggered.connect(self.open_settings)
            menu.addSeparator()
            action_cls = menu.addAction(" إغلاق البرنامج")
            action_cls.triggered.connect(self.safe_exit)
            menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.pos().x() > self.width() - 30 and event.pos().y() > self.height() - 30:
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        if not self.old_pos: return
        if self.is_resizing:
            delta = event.globalPosition().toPoint() - self.old_pos
            new_width = max(180, min(600, self.width() + delta.x()))
            new_height = int(new_width * (160 / 280))
            self.resize(new_width, new_height)
            self.apply_styles()
            self.old_pos = event.globalPosition().toPoint()
        else:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        self.is_resizing = False
        self.config["x"] = self.x()
        self.config["y"] = self.y()
        self.config["width"] = self.width()
        self.config["height"] = self.height()
        save_config(self.config)

    def on_data_fetched(self, prayers):
        self.prayers = prayers
        self.update_clock()

    def on_error(self, error_msg):
        self.lbl_prayer.setText(error_msg)

    def update_clock(self):
        if not self.prayers: return
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        next_name, next_time = None, None
        for name, time_str in self.prayers.items():
            if current_time_str < time_str:
                next_name = name
                next_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                break
                
        if not next_name:
            next_name = 'الفجر'
            next_time = datetime.strptime(self.prayers['الفجر'], "%H:%M").replace(year=now.year, month=now.month, day=now.day) + timedelta(days=1)

        diff = next_time - now
        total_seconds = int(diff.total_seconds())
        h, m, s = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60
        
        timer_str = f"{h:02d}:{m:02d}:{s:02d}"
        if self.config["arabic_numbers"]:
            timer_str = convert_to_arabic(timer_str)
        self.lbl_prayer.setText(f"صلاة {next_name}")
        self.lbl_time.setText(timer_str)

    def open_settings(self):
        if hasattr(self, 'settings_win') and self.settings_win.isVisible():
            self.settings_win.activateWindow()
            return
        self.settings_win = SettingsWindow(self.config)
        self.settings_win.settings_changed.connect(self.on_settings_changed)
        self.settings_win.move(self.x() + 50, self.y() + 50)
        self.settings_win.show()

    def on_settings_changed(self):
        self.config = load_config()
        self.apply_styles()
        self.update_clock()

    # ==========================================
    # التحديث التلقائي الفعلي
    # ==========================================
    def check_for_updates(self):
        try:
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
            response = requests.get(url, timeout=5).json()
            
            latest_version = response.get("tag_name", "").replace("v", "")
            
            if latest_version and latest_version > APP_VERSION:
                # العثور على ملف الـ exe من المرفقات
                assets = response.get("assets", [])
                download_url = None
                for asset in assets:
                    if asset["name"].endswith(".exe"):
                        download_url = asset["browser_download_url"]
                        break
                
                if not download_url:
                    self.tray_icon.showMessage("خطأ", "تم العثور على تحديث ولكن ملف التحميل غير متوفر.", QSystemTrayIcon.MessageIcon.Warning, 3000)
                    return

                # سؤال المستخدم للتحديث
                reply = QMessageBox.question(None, 'تحديث متوفر', f"متوفر تحديث جديد (v{latest_version}).\nهل تريد تحميله وتثبيته الآن تلقائياً؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.start_download(download_url)
            else:
                self.tray_icon.showMessage("تحديثات AthanWidget", f"أنت تستخدم أحدث إصدار (v{APP_VERSION}).", QSystemTrayIcon.MessageIcon.NoIcon, 3000)
        except Exception as e:
            self.tray_icon.showMessage("خطأ", "تعذر الاتصال بخادم التحديثات.", QSystemTrayIcon.MessageIcon.Warning, 3000)

    def start_download(self, url):
        # نافذة تقدم التحميل
        self.progress_dialog = QProgressDialog("جاري تحميل التحديث...", "إلغاء", 0, 100)
        self.progress_dialog.setWindowTitle("تحديث AthanWidget")
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()

        self.downloader = UpdateDownloader(url)
        self.downloader.progress.connect(self.progress_dialog.setValue)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.error.connect(self.on_download_error)
        self.progress_dialog.canceled.connect(self.downloader.terminate)
        
        self.downloader.start()

    def on_download_finished(self, new_file_path):
        self.progress_dialog.close()
        
        # التأكد من أن البرنامج يعمل كـ exe وليس سكربت لكي تنجح عملية الاستبدال
        if not getattr(sys, 'frozen', False):
            QMessageBox.warning(None, "تنبيه", "ميزة التحديث التلقائي والاستبدال تعمل فقط عندما يكون البرنامج بصيغة (exe).")
            return

        exe_path = sys.executable
        bat_path = os.path.join(os.path.dirname(exe_path), "update_athan.bat")
        current_exe_name = os.path.basename(exe_path)
        
        # سكربت الإحلال المخفي
        bat_content = f"""@echo off
timeout /t 2 /nobreak > NUL
:loop
del "{current_exe_name}"
if exist "{current_exe_name}" (
    timeout /t 1 /nobreak > NUL
    goto loop
)
ren "AthanWidget_update.exe" "{current_exe_name}"
start "" "{current_exe_name}"
del "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        
        # تشغيل السكربت في الخلفية بدون شاشة سوداء
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen([bat_path], creationflags=CREATE_NO_WINDOW)
        
        self.safe_exit() # إغلاق البرنامج الحالي للسماح للسكربت باستبداله

    def on_download_error(self, err):
        self.progress_dialog.close()
        QMessageBox.critical(None, "خطأ في التحميل", f"حدث خطأ أثناء تحميل التحديث:\n{err}")

    def safe_exit(self):
        self.config["x"] = self.x()
        self.config["y"] = self.y()
        self.config["width"] = self.width()
        self.config["height"] = self.height()
        save_config(self.config)
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    widget = AthanWidget()
    widget.show()
    
    sys.exit(app.exec())
