import sys
import os
import glob
import shutil
import ctypes

# ── Скрываем консольное окно cmd на Windows ──────────────────────────────────
if sys.platform == 'win32':
    _hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if _hwnd:
        ctypes.windll.user32.ShowWindow(_hwnd, 0)

# Run from script directory so relative paths (./Files/...) work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QAbstractItemView,
    QTextEdit, QLineEdit, QStackedWidget, QFrame, QDialog,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QTextCursor, QPainter, QColor, QPen

from core import Binary2text as b2t
from core import Text2bin as t2b
from core import IDremover as idr

# ── Локализация ───────────────────────────────────────────────────────────────
CURRENT_LANG = 'ru'

STRINGS = {
    'en': {
        'title':       'GTA SA IPL Utility',
        'nav_b2t':     'Bin  →  Text',
        'nav_t2b':     'Text  →  Bin',
        'nav_idr':     'ID Remover',
        'files_bin':   'Files in bin_import/  (.ipl)',
        'files_text':  'Files in text_export/  (.ipl)',
        'refresh':     'Refresh',
        'select_all':  'Select All',
        'convert':     'Convert  →',
        'log':         'Log',
        'no_files':    'No files selected.\n',
        'remove':      'Remove',
        'query_label': 'Remove query — IDs, model names or prefixes:',
        'query_hint':  'e.g.   700, 3336    or    sm_veg, cxref    or    sm_veg 700',
        'no_query':    'No query entered.\n',
        'no_valid':    'No valid IDs or prefixes parsed.\n',
        'sep':         '========',
        'results':     'Results:',
        'r_file':      'File name:',
        'r_found':     "Founded ID's:",
        'r_del':       "Deleted ID's:",
        'r_out':       'Output: Files/bin_export/',
        'r_sum':       '{ok} converted',
        'r_fail':      ',  {fail} failed',
    },
    'ru': {
        'title':       'GTA SA IPL Utility',
        'nav_b2t':     'Bin  →  Text',
        'nav_t2b':     'Text  →  Bin',
        'nav_idr':     'Удалить ID',
        'files_bin':   'Файлы в bin_import/  (.ipl)',
        'files_text':  'Файлы в text_export/  (.ipl)',
        'refresh':     'Обновить',
        'select_all':  'Выбрать все',
        'convert':     'Конвертировать  →',
        'log':         'Лог',
        'no_files':    'Файлы не выбраны.\n',
        'remove':      'Удалить',
        'query_label': 'Запрос удаления — ID, имена моделей или префиксы:',
        'query_hint':  'напр.   700, 3336    или    sm_veg, cxref    или    sm_veg 700',
        'no_query':    'Запрос не введён.\n',
        'no_valid':    'Нет корректных ID или префиксов.\n',
        'sep':         '========',
        'results':     'Результаты:',
        'r_file':      'Файл:',
        'r_found':     'Найдено ID:',
        'r_del':       'Удалено ID:',
        'r_out':       'Папка: Files/bin_export/',
        'r_sum':       '{ok} конвертировано',
        'r_fail':      ',  {fail} с ошибкой',
    },
}

def _t(key):
    return STRINGS[CURRENT_LANG].get(key, key)


# ── Colours ───────────────────────────────────────────────────────────────────
SIDEBAR_BG  = "#1e2030"
SIDEBAR_ACT = "#3d59a1"
SIDEBAR_HOV = "#2d3f6d"
CONTENT_BG  = "#f5f6fa"
LOG_BG      = "#1e1e1e"
LOG_FG      = "#d4d4d4"
ACCENT      = "#4a9eff"
BTN_PRIMARY = "#4a9eff"
BTN_PRIM_HV = "#2d7dd2"
BTN_GREY    = "#6c757d"
BTN_GREY_HV = "#545b62"
BTN_RED     = "#dc3545"
BTN_RED_HV  = "#b02a37"
LANG_ACT    = "#4a9eff"
LANG_INACT  = "#3a3f55"


# ── Stream redirect (thread-safe via Qt signals) ──────────────────────────────
class LogStream(QObject):
    written = pyqtSignal(str)

    def write(self, text):
        if text:
            self.written.emit(text)

    def flush(self):
        pass


# ── Worker thread ─────────────────────────────────────────────────────────────
class Worker(QThread):
    log      = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, func):
        super().__init__()
        self._func = func

    def run(self):
        stream = LogStream()
        stream.written.connect(self.log)
        old = sys.stdout
        sys.stdout = stream
        try:
            self._func()
        except Exception as e:
            self.log.emit(f"\nERROR: {e}\n")
        finally:
            sys.stdout = old
        self.finished.emit()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_log():
    w = QTextEdit()
    w.setReadOnly(True)
    w.setFont(QFont("Consolas", 9))
    w.setStyleSheet(f"""
        QTextEdit {{
            background: {LOG_BG}; color: {LOG_FG};
            border: none; border-radius: 4px; padding: 6px;
        }}
    """)
    return w


def _append(log_widget, text):
    log_widget.moveCursor(QTextCursor.End)
    log_widget.insertPlainText(text)
    log_widget.moveCursor(QTextCursor.End)


def _style_btn(btn, bg=BTN_PRIMARY, hv=BTN_PRIM_HV):
    btn.setFixedHeight(32)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {bg}; color: #fff;
            border: none; border-radius: 4px;
            padding: 0 14px; font-size: 12px; font-weight: 600;
        }}
        QPushButton:hover    {{ background: {hv}; }}
        QPushButton:disabled {{ background: #444; color: #888; }}
    """)


def _make_file_list():
    lst = QListWidget()
    lst.setSelectionMode(QAbstractItemView.ExtendedSelection)
    lst.setMaximumHeight(160)
    lst.setStyleSheet("""
        QListWidget {
            border: 1px solid #ccc; border-radius: 4px;
            background: #fff; font-size: 12px;
        }
        QListWidget::item:selected { background: #4a9eff; color: #fff; }
    """)
    return lst


def _btn_row(*buttons):
    row = QHBoxLayout()
    row.setSpacing(6)
    for b in buttons:
        if b is None:
            row.addStretch()
        else:
            row.addWidget(b)
    return row


def _sec_lbl():
    lbl = QLabel()
    lbl.setStyleSheet("font-weight: 600; font-size: 12px;")
    return lbl


def _open_folder(path: str):
    """Открывает папку в Проводнике Windows. Создаёт если не существует."""
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    os.startfile(abs_path)


def _is_binary_ipl(path: str) -> bool:
    """Проверяет, является ли .ipl файл бинарным (magic 'bnry')."""
    try:
        with open(path, 'rb') as f:
            return f.read(4) == b'bnry'
    except Exception:
        return False


def _make_folder_btn(icon='📂'):
    """Кнопка открытия папки — квадратная, серая."""
    btn = QPushButton(icon)
    btn.setFixedSize(32, 32)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setToolTip('')
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {BTN_GREY}; color: #fff;
            border: none; border-radius: 4px;
            font-size: 14px;
        }}
        QPushButton:hover {{ background: {BTN_GREY_HV}; }}
    """)
    return btn



# ── Drag-and-drop mixin ───────────────────────────────────────────────────────
class _DropMixin:
    """
    Mixin: перетаскивай .ipl файлы прямо на панель.
    Подкласс задаёт:
        _drop_dest   : str  — папка назначения (относительно CWD)
        _drop_binary : bool — True  = принимать только бинарный IPL,
                              False = только текстовый IPL
    Подкласс должен иметь self.log (QTextEdit) и self.refresh().
    """
    def _setup_drop(self):
        self.setAcceptDrops(True)
        self._drag_active = False

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(
            u.isLocalFile() and u.toLocalFile().lower().endswith('.ipl')
            for u in event.mimeData().urls()
        ):
            self._drag_active = True
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._drag_active = False
        self.update()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        self._drag_active = False
        self.update()
        import shutil
        dest = os.path.abspath(self._drop_dest)
        os.makedirs(dest, exist_ok=True)
        moved, skipped = [], []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            src = url.toLocalFile()
            if not src.lower().endswith('.ipl'):
                continue
            if _is_binary_ipl(src) != self._drop_binary:
                kind = 'not binary' if self._drop_binary else 'binary'
                skipped.append(f"{os.path.basename(src)} ({kind})")
                continue
            dst = os.path.join(dest, os.path.basename(src))
            shutil.move(src, dst)
            moved.append(os.path.basename(src))
        if moved:
            dest_rel = self._drop_dest.replace('./', '')
            _append(self.log, f"\u2192 {dest_rel}/\n  " + "\n  ".join(moved) + "\n")
            self.refresh()
        if skipped:
            _append(self.log, "\u2717 " + ", ".join(skipped) + "\n")
        event.acceptProposedAction()

    def paintEvent(self, event):
        from PyQt5.QtWidgets import QWidget as _QW
        _QW.paintEvent(self, event)
        if getattr(self, '_drag_active', False):
            from PyQt5.QtGui import QPainter, QColor, QPen
            p = QPainter(self)
            p.fillRect(self.rect(), QColor(74, 158, 255, 40))
            p.setPen(QPen(QColor(74, 158, 255, 220), 2))
            p.drawRect(self.rect().adjusted(2, 2, -3, -3))


# ── Sidebar nav button ────────────────────────────────────────────────────────
class NavButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self._refresh(False)

    def _refresh(self, active):
        bg     = SIDEBAR_ACT if active else SIDEBAR_BG
        border = f"border-left: 3px solid {ACCENT};" if active else "border-left: 3px solid transparent;"
        weight = "700" if active else "400"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: #cdd6f4;
                font-size: 13px; font-weight: {weight};
                text-align: left; padding-left: 20px;
                border: none; {border}
            }}
            QPushButton:hover {{ background: {SIDEBAR_HOV}; }}
        """)

    def setActive(self, v):
        self._refresh(v)
        self.setChecked(v)


# ══════════════════════════════════════════════════════════════════════════════
# Panel 0 — Bin → Text
# ══════════════════════════════════════════════════════════════════════════════
class Bin2TextPanel(_DropMixin, QWidget):
    _drop_dest   = './Files/bin_import'
    _drop_binary = True

    def __init__(self):
        super().__init__()
        self._setup_drop()
        self.worker = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        self._lbl_files = _sec_lbl()
        lay.addWidget(self._lbl_files)

        self.file_list = _make_file_list()
        lay.addWidget(self.file_list)

        self._btn_refresh = QPushButton()
        _style_btn(self._btn_refresh, BTN_GREY, BTN_GREY_HV)
        self._btn_refresh.clicked.connect(self.refresh)

        self._btn_all = QPushButton()
        _style_btn(self._btn_all, BTN_GREY, BTN_GREY_HV)
        self._btn_all.clicked.connect(self.file_list.selectAll)

        self._btn_convert = QPushButton()
        _style_btn(self._btn_convert)
        self._btn_convert.clicked.connect(self.run)

        self._btn_folder = _make_folder_btn()
        self._btn_folder.clicked.connect(lambda: _open_folder('./Files/bin_import'))

        lay.addLayout(_btn_row(self._btn_refresh, self._btn_all, None, self._btn_folder, self._btn_convert))

        self._lbl_log = _sec_lbl()
        lay.addWidget(self._lbl_log)
        self.log = _make_log()
        lay.addWidget(self.log, 1)

        self.retranslate()
        self.refresh()

    def retranslate(self):
        self._lbl_files.setText(_t('files_bin'))
        self._lbl_log.setText(_t('log'))
        self._btn_refresh.setText(_t('refresh'))
        self._btn_all.setText(_t('select_all'))
        self._btn_convert.setText(_t('convert'))
        self._btn_folder.setToolTip('Files/bin_import/')

    def refresh(self):
        self.file_list.clear()
        for f in sorted(glob.glob("./Files/bin_import/*.ipl")):
            self.file_list.addItem(os.path.basename(f))
        self.file_list.selectAll()

    def run(self):
        selected = [item.text() for item in self.file_list.selectedItems()]
        if not selected:
            _append(self.log, _t('no_files'))
            return
        self.log.clear()
        self._btn_convert.setEnabled(False)
        paths = [f"./Files/bin_import/{n}" for n in selected]

        def task():
            b2t.checks(paths)

        w = Worker(task)
        w.log.connect(lambda t: _append(self.log, t))
        w.finished.connect(lambda: self._btn_convert.setEnabled(True))
        self.worker = w
        w.start()


# ══════════════════════════════════════════════════════════════════════════════
# Panel 1 — Text → Bin
# ══════════════════════════════════════════════════════════════════════════════
class Text2BinPanel(_DropMixin, QWidget):
    _drop_dest   = './Files/text_export'
    _drop_binary = False

    def __init__(self):
        super().__init__()
        self._setup_drop()
        self.worker = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        self._lbl_files = _sec_lbl()
        lay.addWidget(self._lbl_files)

        self.file_list = _make_file_list()
        lay.addWidget(self.file_list)

        self._btn_refresh = QPushButton()
        _style_btn(self._btn_refresh, BTN_GREY, BTN_GREY_HV)
        self._btn_refresh.clicked.connect(self.refresh)

        self._btn_all = QPushButton()
        _style_btn(self._btn_all, BTN_GREY, BTN_GREY_HV)
        self._btn_all.clicked.connect(self.file_list.selectAll)

        self._btn_convert = QPushButton()
        _style_btn(self._btn_convert)
        self._btn_convert.clicked.connect(self.run)

        self._btn_folder = _make_folder_btn()
        self._btn_folder.clicked.connect(lambda: _open_folder('./Files/bin_export'))

        lay.addLayout(_btn_row(self._btn_refresh, self._btn_all, None, self._btn_folder, self._btn_convert))

        self._lbl_log = _sec_lbl()
        lay.addWidget(self._lbl_log)
        self.log = _make_log()
        lay.addWidget(self.log, 1)

        self.retranslate()
        self.refresh()

    def retranslate(self):
        self._lbl_files.setText(_t('files_text'))
        self._btn_folder.setToolTip('Files/bin_export/')
        self._lbl_log.setText(_t('log'))
        self._btn_refresh.setText(_t('refresh'))
        self._btn_all.setText(_t('select_all'))
        self._btn_convert.setText(_t('convert'))

    def refresh(self):
        self.file_list.clear()
        for f in sorted(glob.glob("./Files/text_export/*.ipl")):
            self.file_list.addItem(os.path.basename(f))
        self.file_list.selectAll()

    def run(self):
        selected = [item.text() for item in self.file_list.selectedItems()]
        if not selected:
            _append(self.log, _t('no_files'))
            return
        self.log.clear()
        self._btn_convert.setEnabled(False)
        paths = [f"./Files/text_export/{n}" for n in selected]

        # Захватываем строки до старта потока
        r_sum  = _t('r_sum')
        r_fail = _t('r_fail')
        r_out  = _t('r_out')

        def task():
            t2b.ensure_dir("Files/bin_export")
            ok = fail = 0
            for fp in paths:
                if t2b.convert_text2bin(fp, "Files/bin_export"):
                    ok += 1
                else:
                    fail += 1
            print("\n=========================")
            summary = r_sum.format(ok=ok)
            if fail:
                summary += r_fail.format(fail=fail)
            print(summary)
            print(r_out)

        w = Worker(task)
        w.log.connect(lambda t: _append(self.log, t))
        w.finished.connect(lambda: self._btn_convert.setEnabled(True))
        self.worker = w
        w.start()


# ══════════════════════════════════════════════════════════════════════════════
# Panel 2 — ID Remover
# ══════════════════════════════════════════════════════════════════════════════
class IDRemoverPanel(_DropMixin, QWidget):
    _drop_dest   = './Files/text_export'
    _drop_binary = False

    def __init__(self):
        super().__init__()
        self._setup_drop()
        self.worker = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        self._lbl_files = _sec_lbl()
        lay.addWidget(self._lbl_files)

        self.file_list = _make_file_list()
        lay.addWidget(self.file_list)

        self._btn_refresh = QPushButton()
        _style_btn(self._btn_refresh, BTN_GREY, BTN_GREY_HV)
        self._btn_refresh.clicked.connect(self.refresh)

        self._btn_all = QPushButton()
        _style_btn(self._btn_all, BTN_GREY, BTN_GREY_HV)
        self._btn_all.clicked.connect(self.file_list.selectAll)

        lay.addLayout(_btn_row(self._btn_refresh, self._btn_all))

        self._lbl_query = _sec_lbl()
        lay.addWidget(self._lbl_query)

        self.query = QLineEdit()
        self.query.setFixedHeight(30)
        self.query.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 0 8px; }"
        )
        lay.addWidget(self.query)

        self._btn_remove = QPushButton()
        _style_btn(self._btn_remove, BTN_RED, BTN_RED_HV)
        self._btn_remove.clicked.connect(self.run)
        # Enter в поле запроса тоже запускает удаление
        self.query.returnPressed.connect(self.run)

        self._btn_folder = _make_folder_btn()
        self._btn_folder.clicked.connect(lambda: _open_folder('./Files/text_export'))

        lay.addLayout(_btn_row(None, self._btn_folder, self._btn_remove))

        self._lbl_log = _sec_lbl()
        lay.addWidget(self._lbl_log)
        self.log = _make_log()
        lay.addWidget(self.log, 1)

        self.retranslate()
        self.refresh()

    def retranslate(self):
        self._lbl_files.setText(_t('files_text'))
        self._btn_folder.setToolTip('Files/text_export/')
        self._lbl_log.setText(_t('log'))
        self._btn_refresh.setText(_t('refresh'))
        self._btn_all.setText(_t('select_all'))
        self._btn_remove.setText(_t('remove'))
        self._lbl_query.setText(_t('query_label'))
        self.query.setPlaceholderText(_t('query_hint'))

    def refresh(self):
        self.file_list.clear()
        for f in sorted(glob.glob("./Files/text_export/*.ipl")):
            self.file_list.addItem(os.path.basename(f))
        self.file_list.selectAll()

    def run(self):
        # Если предыдущий поток ещё работает — не запускаем новый
        if self.worker is not None:
            return

        selected = [item.text() for item in self.file_list.selectedItems()]
        query    = self.query.text().strip()
        if not selected:
            _append(self.log, _t('no_files'));  return
        if not query:
            _append(self.log, _t('no_query'));  return
        remove_ids, remove_prefixes = idr.parse_query(query)
        if not remove_ids and not remove_prefixes:
            _append(self.log, _t('no_valid')); return

        self.log.clear()
        self._btn_remove.setEnabled(False)
        paths = [f"./Files/text_export/{n}" for n in selected]

        # Захватываем строки до старта потока
        sep     = _t('sep')
        results = _t('results')
        r_file  = _t('r_file')
        r_found = _t('r_found')
        r_del   = _t('r_del')

        def task():
            print(sep)
            print(results)
            for fp in paths:
                fname = os.path.basename(fp)
                with open(fp, 'r') as fh:
                    lns = fh.readlines()
                new_lines, removed = idr.process_file(lns, remove_ids, remove_prefixes)
                with open(fp, 'w') as fh:
                    fh.writelines(new_lines)
                print(f"{r_file:<14} {fname}")
                print(f"{r_found:<14} {removed}")
                print(f"{r_del:<14} {removed}")
            print(sep)

        w = Worker(task)
        w.log.connect(lambda t: _append(self.log, t))
        w.finished.connect(self._on_worker_done)
        self.worker = w
        w.start()

    def _on_worker_done(self):
        # Вызывается из GUI-потока через Qt signal — безопасно
        self._btn_remove.setEnabled(True)
        # Держим ссылку до полной остановки потока
        if self.worker is not None:
            self.worker.quit()
            self.worker.wait()
            self.worker = None


# ══════════════════════════════════════════════════════════════════════════════
# Main window
# ══════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(860, 560)
        self.setMinimumSize(700, 460)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(172)
        sidebar.setStyleSheet(f"background: {SIDEBAR_BG};")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        self._lbl_title = QLabel()
        self._lbl_title.setFixedHeight(52)
        self._lbl_title.setStyleSheet(f"""
            color: #cdd6f4; font-size: 14px; font-weight: 700;
            background: {SIDEBAR_BG}; padding-left: 20px;
            border-bottom: 1px solid #2d3149;
        """)
        sb.addWidget(self._lbl_title)

        # Порядок вкладок: Bin→Text, Text→Bin, ID Remover
        self._nav_keys = ['nav_b2t', 'nav_t2b', 'nav_idr']
        self._nav_btns = []
        for key in self._nav_keys:
            btn = NavButton(_t(key))
            btn.clicked.connect(lambda _, b=btn: self._activate(b))
            sb.addWidget(btn)
            self._nav_btns.append(btn)

        sb.addStretch()

        # Кнопки RU / EN — выше версии, широкие, по центру
        lang_row = QWidget()
        lang_row.setFixedHeight(38)
        lang_row.setStyleSheet(f"background: {SIDEBAR_BG};")
        lr = QHBoxLayout(lang_row)
        lr.setContentsMargins(14, 6, 14, 6)
        lr.setSpacing(8)

        self._btn_ru = QPushButton("RU")
        self._btn_en = QPushButton("EN")
        for btn in (self._btn_ru, self._btn_en):
            btn.setFixedHeight(26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(btn.sizePolicy().Expanding, btn.sizePolicy().Fixed)
        self._btn_ru.clicked.connect(lambda: self._set_lang('ru'))
        self._btn_en.clicked.connect(lambda: self._set_lang('en'))
        lr.addStretch(1)
        lr.addWidget(self._btn_ru)
        lr.addWidget(self._btn_en)
        lr.addStretch(1)
        sb.addWidget(lang_row)

        # Версия — кликабельная
        self._lbl_ver = QLabel("v1.0")
        self._lbl_ver.setAlignment(Qt.AlignCenter)
        self._lbl_ver.setFixedHeight(22)
        self._lbl_ver.setCursor(Qt.PointingHandCursor)
        self._lbl_ver.setStyleSheet(
            f"color: #4a6080; font-size: 11px; background: {SIDEBAR_BG};"
            " text-decoration: underline;"
        )
        self._lbl_ver.mousePressEvent = lambda _: self._show_about()
        sb.addWidget(self._lbl_ver)
        sb.addSpacing(6)

        # ── Separator ────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #2d3149;")

        # ── Content stack: Bin→Text (0), Text→Bin (1), ID Remover (2) ────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {CONTENT_BG};")
        self._panels = [Bin2TextPanel(), Text2BinPanel(), IDRemoverPanel()]
        for p in self._panels:
            self._stack.addWidget(p)

        root.addWidget(sidebar)
        root.addWidget(sep)
        root.addWidget(self._stack, 1)

        self._set_index(0)
        self._refresh_lang_btns()
        self.retranslate()

    # ── Язык ──────────────────────────────────────────────────────────────────
    def _set_lang(self, lang):
        global CURRENT_LANG
        CURRENT_LANG = lang
        self._refresh_lang_btns()
        self.retranslate()

    def _refresh_lang_btns(self):
        for btn, code in ((self._btn_ru, 'ru'), (self._btn_en, 'en')):
            active = (CURRENT_LANG == code)
            bg = LANG_ACT if active else LANG_INACT
            fw = "700"    if active else "400"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg}; color: #fff;
                    border: none; border-radius: 3px;
                    font-size: 11px; font-weight: {fw};
                }}
                QPushButton:hover {{ background: {ACCENT}; }}
            """)

    def retranslate(self):
        self.setWindowTitle(_t('title'))
        self._lbl_title.setText(f"  {_t('title')}")
        for i, btn in enumerate(self._nav_btns):
            btn.setText(_t(self._nav_keys[i]))
        for p in self._panels:
            p.retranslate()

    # ── Навигация ──────────────────────────────────────────────────────────────
    def _activate(self, btn):
        self._set_index(self._nav_btns.index(btn))

    def _set_index(self, idx):
        for i, b in enumerate(self._nav_btns):
            b.setActive(i == idx)
        self._stack.setCurrentIndex(idx)

    def _show_about(self):
        ru = (CURRENT_LANG == 'ru')
        dlg = QDialog(self)
        dlg.setWindowTitle("О программе" if ru else "About")
        dlg.setFixedWidth(430)
        dlg.setStyleSheet(f"""
            QDialog {{ background: {CONTENT_BG}; }}
            QLabel  {{ color: #1e2030; }}
        """)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(0)

        # Заголовок
        title = QLabel("GTA SA IPL Utility")
        title.setStyleSheet("font-size: 18px; font-weight: 800; letter-spacing: 0.5px;")
        lay.addWidget(title)
        ver_lbl = QLabel("version 2.0")
        ver_lbl.setStyleSheet(f"font-size: 11px; color: {BTN_GREY}; margin-bottom: 12px;")
        lay.addWidget(ver_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #d0d3e0; margin-bottom: 14px;")
        lay.addWidget(sep)

        # Данные авторов
        authors = [
            {
                'nick':  'MadGamerHD',
                'role_ru': 'Автор оригинального декомпилятора',
                'role_en': 'Original decompiler author',
                'url':   'https://github.com/MadGamerHD',
                'repo':  'GTA-SA-Binary-IPL-Inspector',
                'repo_url': 'https://github.com/MadGamerHD/GTA-SA-Binary-IPL-Inspector',
            },
            {
                'nick':  'Shifaau9',
                'role_ru': 'Автор оригинального компилятора',
                'role_en': 'Original compiler author',
                'url':   'https://github.com/Shifaau9',
                'repo':  'Binary-IPl-Converter',
                'repo_url': 'https://github.com/Shifaau9/Binary-IPl-Converter',
            },
            {
                'nick':  'h.w',
                'role_ru': 'Автор доработок и UI',
                'role_en': 'Improvements & UI author',
                'url':   'https://github.com/Hw-g-it',
                'repo':  None,
                'repo_url': None,
            },
        ]

        for a in authors:
            card = QWidget()
            card.setStyleSheet("""
                QWidget {
                    background: #eef0f8;
                    border-radius: 6px;
                }
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(3)

            nick = QLabel(f'<a href="{a["url"]}" style="color:{ACCENT}; text-decoration:none; font-size:14px; font-weight:700;">{a["nick"]}</a>')
            nick.setOpenExternalLinks(True)
            cl.addWidget(nick)

            role = QLabel(a['role_ru'] if ru else a['role_en'])
            role.setStyleSheet(f"font-size: 11px; color: {BTN_GREY};")
            cl.addWidget(role)

            if a['repo']:
                repo_lbl = QLabel(f'→ <a href="{a["repo_url"]}" style="color:{ACCENT};">{a["repo"]}</a>')
                repo_lbl.setOpenExternalLinks(True)
                repo_lbl.setStyleSheet("font-size: 11px;")
                cl.addWidget(repo_lbl)

            lay.addWidget(card)
            lay.addSpacing(8)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #d0d3e0; margin-top: 4px;")
        lay.addWidget(sep2)
        lay.addSpacing(10)

        btn_ok = QPushButton("OK")
        _style_btn(btn_ok)
        btn_ok.setFixedWidth(80)
        btn_ok.clicked.connect(dlg.accept)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_ok)
        lay.addLayout(h)

        dlg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
