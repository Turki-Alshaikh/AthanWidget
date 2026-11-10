import sys
import os
import requests
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QSlider, QPushButton, QColorDialog, QSystemTrayIcon, QMenu, QFrame,
                             QScrollArea, QSpinBox, QLineEdit, QListWidget, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QFont, QIcon, QCursor, QPixmap

# ==========================================
# بيانات التطبيق
# ==========================================
APP_VERSION = "1.1.0"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ==========================================
# 1. إعدادات التطبيق (آمنة لبيئة MSIX المعزولة)
# ==========================================
DEFAULT_CONFIG = {
    "x": 100, "y": 100,
    "width": 280, "height": 160,
    "bg_alpha": 0.80,
    "font_family": "Segoe UI",
    "bg_color": "#1C1C1E",
    "text_primary": "#FFFFFF",
    "text_secondary": "#8E8E93",
    "accent_color": "#0A84FF",
    "arabic_numbers": False,       
    "show_bg": True,               
    "show_borders": True,          
    "notify_pre_athan": True,      
    "pre_athan_mins": 5,           
    "notify_at_athan": True,
    "custom_city": ""              
}

def load_config():
    settings = QSettings("TurkiAlshaikh", "AthanWidgetStore")
    config = DEFAULT_CONFIG.copy()
    for k, default_val in config.items():
        if settings.contains(k):
            if isinstance(default_val, bool):
                config[k] = settings.value(k, type=bool)
            elif isinstance(default_val, int):
                config[k] = settings.value(k, type=int)
            elif isinstance(default_val, float):
                config[k] = settings.value(k, type=float)
            else:
                config[k] = settings.value(k, type=str)
    return config

def save_config(config):
    settings = QSettings("TurkiAlshaikh", "AthanWidgetStore")
    for k, v in config.items():
        settings.setValue(k, v)

def convert_to_arabic(text):
    return text.translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))

# ==========================================
# 2. كائن جلب البيانات
# ==========================================
class PrayerTimeFetcher(QThread):
    data_fetched = pyqtSignal(tuple)
    error_occurred = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            custom_city = self.config.get("custom_city", "").strip()
            
            if custom_city:
                url = f"http://api.aladhan.com/v1/timingsByAddress?address={custom_city}&method=4"
                pray_res = requests.get(url, timeout=5).json()
                timings = pray_res['data']['timings']
                city_name = custom_city
            else:
                loc_res = requests.get('https://ipinfo.io/json', timeout=5).json()
                lat, lon = loc_res['loc'].split(',')
                city_name = loc_res.get('city', 'المنطقة')
                
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
            self.data_fetched.emit((city_name, prayers))
        except:
            self.error_occurred.emit("لا يوجد اتصال بالإنترنت")

# ==========================================
# 3. واجهة المستخدم وعناصر التحكم
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

class SettingsWindow(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("إعدادات AthanWidget")
        
        # --- حل مشكلة ظهور الأيقونة في شريط المهام في ويندوز ---
        import ctypes
        myappid = f'TurkiAlshaikh.AthanWidgetStore.{APP_VERSION}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        icon_path = resource_path("icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        # --------------------------------------------------------
        
        self.resize(850, 600)
        self.setMinimumSize(800, 500)
        self.setStyleSheet("background-color: #111111; color: white;")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft) 

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItems(["عام", "المظهر والألوان", "التنبيهات", "حول البرنامج"])
        self.sidebar.setCurrentRow(0)
        self.sidebar.setStyleSheet(f"""
            QListWidget {{ background-color: #1C1C1E; border-radius: 12px; padding: 10px; font-family: '{self.config['font_family']}'; font-size: 16px; font-weight: bold; border: none; outline: none; }}
            QListWidget::item {{ padding: 15px; margin-bottom: 8px; border-radius: 8px; color: #8E8E93; }}
            QListWidget::item:selected {{ background-color: #0A84FF; color: white; }}
            QListWidget::item:hover:!selected {{ background-color: #2C2C2E; color: white; }}
        """)
        self.sidebar.currentRowChanged.connect(self.change_page)

        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"background-color: #1C1C1E; border-radius: 12px; font-family: '{self.config['font_family']}';")
        
        self.pages.addWidget(self.create_general_page())
        self.pages.addWidget(self.create_appearance_page())
        self.pages.addWidget(self.create_alerts_page())
        self.pages.addWidget(self.create_about_page())

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)
        self.setLayout(main_layout)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

    def create_page_container(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(lbl_title)
        
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #3A3A3C;")
        layout.addWidget(line)
        
        return page, layout

    def create_general_page(self):
        page, layout = self.create_page_container("إعدادات عامة")
        
        lbl_city = QLabel("المدينة / المحافظة (لزيادة الدقة):")
        lbl_city.setStyleSheet("font-size: 16px; color: #8E8E93;")
        layout.addWidget(lbl_city)
        
        self.txt_city = QLineEdit()
        self.txt_city.setText(self.config.get("custom_city", ""))
        self.txt_city.setPlaceholderText("اتركه فارغاً للتحديد التلقائي للموقع")
        self.txt_city.setStyleSheet("QLineEdit { background-color: #2C2C2E; color: white; border: 1px solid #3A3A3C; border-radius: 8px; padding: 12px; font-size: 16px; }")
        layout.addWidget(self.txt_city)
        
        self.add_toggle_row(layout, "استخدام الأرقام العربية (١٢٣)", self.config["arabic_numbers"], self.toggle_arabic)
        
        layout.addStretch()

        # --- زر الحفظ الجديد ---
        self.btn_save_general = QPushButton("حفظ الإعدادات")
        self.btn_save_general.setFixedSize(160, 45)
        self.btn_save_general.setStyleSheet("QPushButton { background-color: #0A84FF; color: white; border-radius: 8px; font-weight: bold; font-size: 16px; } QPushButton:hover { background-color: #0070E0; }")
        self.btn_save_general.clicked.connect(self.save_general_settings)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save_general)
        layout.addLayout(btn_layout)
        
        return page

    def create_appearance_page(self):
        page, layout = self.create_page_container("المظهر والألوان")
        
        lbl_alpha = QLabel("شفافية نافذة الأذان:")
        lbl_alpha.setStyleSheet("font-size: 16px; color: #8E8E93;")
        layout.addWidget(lbl_alpha)
        
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(20, 100)
        self.alpha_slider.setValue(int(self.config["bg_alpha"] * 100))
        self.alpha_slider.setStyleSheet("QSlider::groove:horizontal { border-radius: 3px; height: 6px; background: #3A3A3C; } QSlider::handle:horizontal { background: #0A84FF; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }")
        self.alpha_slider.valueChanged.connect(self.update_alpha)
        layout.addWidget(self.alpha_slider)
        
        self.add_toggle_row(layout, "إظهار لون الخلفية", self.config["show_bg"], self.toggle_bg)
        self.add_toggle_row(layout, "إظهار الحدود السفلية الزخرفية", self.config["show_borders"], self.toggle_borders)
        
        layout.addSpacing(10)
        lbl_colors = QLabel("تخصيص الألوان:")
        lbl_colors.setStyleSheet("font-size: 16px; color: #8E8E93;")
        layout.addWidget(lbl_colors)
        
        self.add_color_row(layout, "لون الخلفية", "bg_color")
        self.add_color_row(layout, "لون النص الأساسي (اسم الصلاة)", "text_primary")
        self.add_color_row(layout, "لون العداد التنازلي", "accent_color")
        
        layout.addStretch()
        return page

    def create_alerts_page(self):
        page, layout = self.create_page_container("تنبيهات الصلاة")
        
        self.add_toggle_row(layout, "إظهار إشعار وقت دخول الصلاة", self.config["notify_at_athan"], self.toggle_at_athan)
        
        row_pre = QHBoxLayout()
        lbl_pre = QLabel("تنبيه قبل الأذان بـ (دقائق):")
        lbl_pre.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        row_pre.addWidget(lbl_pre)
        
        self.spin_pre = QSpinBox()
        self.spin_pre.setRange(1, 60)
        self.spin_pre.setValue(self.config["pre_athan_mins"])
        self.spin_pre.setStyleSheet("QSpinBox { background-color: #2C2C2E; color: white; border: none; border-radius: 6px; padding: 5px; font-size: 16px; }")
        self.spin_pre.valueChanged.connect(self.update_pre_mins)
        row_pre.addWidget(self.spin_pre)
        
        tgl_pre = IOSToggle(self.config["notify_pre_athan"])
        tgl_pre.stateChanged.connect(self.toggle_pre_athan)
        row_pre.addWidget(tgl_pre)
        
        layout.addLayout(row_pre)
        layout.addStretch()
        return page

    def create_about_page(self):
        page, layout = self.create_page_container("حول البرنامج")
        
        lbl_desc = QLabel("<b>AthanWidget</b><br><br>تطبيق مصغر لعرض أوقات الصلاة على سطح المكتب.<br>هذه النسخة مخصصة لمتجر مايكروسوفت.")
        lbl_desc.setStyleSheet("font-size: 16px; color: #8E8E93; line-height: 1.5;")
        layout.addWidget(lbl_desc)
        
        lbl_link = QLabel(f'<a href="https://github.com/Turki-Alshaikh/AthanWidget" style="color:#0A84FF; text-decoration:none;">زيارة المشروع الأساسي على GitHub</a>')
        lbl_link.setOpenExternalLinks(True)
        lbl_link.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_link)
        
        layout.addStretch()
        return page

    def add_toggle_row(self, layout, text, initial_state, command):
        row = QHBoxLayout()
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        row.addWidget(lbl)
        tgl = IOSToggle(initial_state)
        tgl.stateChanged.connect(command)
        row.addWidget(tgl)
        layout.addLayout(row)

    def add_color_row(self, layout, text, key):
        row = QHBoxLayout()
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        row.addWidget(lbl)
        btn = QPushButton("اختيار لون")
        btn.setFixedSize(100, 35)
        btn.setStyleSheet("QPushButton { background-color: #2C2C2E; color: #0A84FF; border-radius: 8px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #3A3A3C; color: white; }")
        btn.clicked.connect(lambda: self.pick_color(key))
        row.addWidget(btn)
        layout.addLayout(row)

    # --- دوال الحفظ ---
    def save_general_settings(self):
        new_city = self.txt_city.text().strip()
        if self.config["custom_city"] != new_city:
            self.config["custom_city"] = new_city
            self.save_and_emit()
            
        # تأثير بصري لتأكيد الحفظ
        self.btn_save_general.setText("تم الحفظ ✔")
        self.btn_save_general.setStyleSheet("QPushButton { background-color: #34C759; color: white; border-radius: 8px; font-weight: bold; font-size: 16px; }")
        QTimer.singleShot(2000, self.reset_save_button)

    def reset_save_button(self):
        self.btn_save_general.setText("حفظ الإعدادات")
        self.btn_save_general.setStyleSheet("QPushButton { background-color: #0A84FF; color: white; border-radius: 8px; font-weight: bold; font-size: 16px; } QPushButton:hover { background-color: #0070E0; }")

    def update_alpha(self, val):
        self.config["bg_alpha"] = val / 100.0
        self.save_and_emit()
        
    def toggle_bg(self, state):
        self.config["show_bg"] = state
        self.save_and_emit()

    def toggle_borders(self, state):
        self.config["show_borders"] = state
        self.save_and_emit()

    def update_pre_mins(self, val):
        self.config["pre_athan_mins"] = val
        self.save_and_emit()

    def toggle_pre_athan(self, state):
        self.config["notify_pre_athan"] = state
        self.save_and_emit()

    def toggle_at_athan(self, state):
        self.config["notify_at_athan"] = state
        self.save_and_emit()

    def pick_color(self, key):
        color = QColorDialog.getColor(QColor(self.config[key]), self, "اختر لوناً")
        if color.isValid():
            self.config[key] = color.name()
            self.save_and_emit()

    def toggle_arabic(self, state):
        self.config["arabic_numbers"] = state
        self.save_and_emit()

    def save_and_emit(self):
        save_config(self.config)
        self.settings_changed.emit()

# ==========================================
# 4. الويدجت الرئيسي (الواجهة العائمة)
# ==========================================
class AthanWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        # أضفنا هذا السطر لحفظ اسم آخر مدينة تم جلبها لتجنب الخلل
        self.last_fetched_city = self.config.get("custom_city", "") 
        
        self.prayers = None
        self.city_name = "AthanWidget"
        self.old_pos = None
        self.is_resizing = False

        self.init_ui()
        self.init_tray_icon()

        self.start_fetching()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

    def start_fetching(self):
        self.lbl_prayer.setText("جاري تحديث الموقع...")
        self.lbl_time.setText("--:--:--")
        
        self.fetcher = PrayerTimeFetcher(self.config)
        self.fetcher.data_fetched.connect(self.on_data_fetched)
        self.fetcher.error_occurred.connect(self.on_error)
        self.fetcher.start()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(self.config["x"], self.config["y"], self.config["width"], self.config["height"])

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 15)
        
        self.lbl_title = QLabel(" جاري تحديد الموقع...")
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
        
        if self.config.get("show_bg", True):
            bg_color = QColor(self.config["bg_color"])
            bg_color.setAlphaF(self.config["bg_alpha"]) 
            path = QPainterPath()
            r = int(25 * (self.width() / 280.0))
            path.addRoundedRect(0, 0, self.width(), self.height(), r, r)
            painter.fillPath(path, bg_color)
            
        if self.config.get("show_borders", True):
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
        self.tray_icon.setToolTip(f"AthanWidget v{APP_VERSION}")
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet("QMenu { background-color: #1C1C1E; color: white; border: 1px solid #2C2C2E; } QMenu::item:selected { background-color: #0A84FF; }")
        
        action_settings = tray_menu.addAction(" إعدادات الويدجت")
        action_settings.triggered.connect(self.open_settings)
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

    def on_data_fetched(self, data):
        self.city_name, self.prayers = data
        self.lbl_title.setText(f" {self.city_name}")
        self.update_clock()

    def on_error(self, error_msg):
        self.lbl_prayer.setText(error_msg)

    def update_clock(self):
        if not self.prayers: return
        
        now = datetime.now()
        
        today_prayers = []
        for name, time_str in self.prayers.items():
            pt = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            today_prayers.append((name, pt))
            
        next_fajr_time = datetime.strptime(self.prayers['الفجر'], "%H:%M").replace(year=now.year, month=now.month, day=now.day) + timedelta(days=1)
        today_prayers.append(('الفجر', next_fajr_time))
        today_prayers.sort(key=lambda x: x[1])

        past_prayer = None
        next_prayer = None
        for name, pt in today_prayers:
            if pt <= now:
                past_prayer = (name, pt)
            else:
                if not next_prayer:
                    next_prayer = (name, pt)

        display_past = False
        if past_prayer:
            diff_past = now - past_prayer[1]
            if diff_past.total_seconds() <= 30 * 60: 
                display_past = True

        if display_past:
            self.lbl_prayer.setText(f"مضى على {past_prayer[0]}")
            diff = now - past_prayer[1]
        else:
            self.lbl_prayer.setText(f"صلاة {next_prayer[0]}")
            diff = next_prayer[1] - now
            
            total_seconds = int(diff.total_seconds())
            
            if self.config.get("notify_pre_athan"):
                pre_target = self.config.get("pre_athan_mins", 5) * 60
                if total_seconds == pre_target:
                    self.tray_icon.showMessage("اقترب وقت الصلاة", f"باقي {self.config.get('pre_athan_mins')} دقائق على صلاة {next_prayer[0]}.", QSystemTrayIcon.MessageIcon.Information, 5000)
            
            if self.config.get("notify_at_athan"):
                if total_seconds == 0:
                    self.tray_icon.showMessage("حان وقت الصلاة", f"حان الآن موعد صلاة {next_prayer[0]} بتوقيت {self.city_name}.", QSystemTrayIcon.MessageIcon.Information, 7000)

        total_seconds = int(diff.total_seconds())
        h, m, s = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60
        timer_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        if self.config.get("arabic_numbers"):
            timer_str = convert_to_arabic(timer_str)
            
        self.lbl_time.setText(timer_str)

    def open_settings(self):
        if hasattr(self, 'settings_win') and self.settings_win.isVisible():
            self.settings_win.activateWindow()
            return
        self.settings_win = SettingsWindow(self.config)
        self.settings_win.settings_changed.connect(self.on_settings_changed)
        self.settings_win.show()

    def on_settings_changed(self):
        self.config = load_config()
        new_city = self.config.get("custom_city", "")
        
        self.apply_styles()
        
        # نقارن مع آخر مدينة جلبناها بدلاً من قراءتها من الإعدادات
        if self.last_fetched_city != new_city:
            self.last_fetched_city = new_city
            self.start_fetching()
        else:
            self.update_clock()

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
    
    # --- إضافة الأيقونة الرئيسية للتطبيق بالكامل ---
    app_icon_path = resource_path("icon.ico")
    app.setWindowIcon(QIcon(app_icon_path))
    # ----------------------------------------------
    
    widget = AthanWidget()
    widget.show()
    
    sys.exit(app.exec())