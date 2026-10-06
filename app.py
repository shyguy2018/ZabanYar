# -*- coding: utf-8 -*-
"""
Zaban-Yar (زبان‌یار) - fixes words typed in the wrong keyboard layout
(English <-> Persian) on Windows.

 * Watches the keys you type (nothing is saved or sent anywhere).
 * When a word is finished (Space) and it was clearly typed in the wrong
   layout, it either converts it automatically, or shows a small bubble:
   "منظورتون این بود؟"  -> click it (or press the hotkey) to convert.
 * Hotkey (default: Pause/Break, configurable): convert the last word(s)
   manually at any time.
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
import winreg

import core

APP_NAME = 'ZabanYar'
AUTHOR = 'Behrooz Shayestepoor'
VERSION = '1.2'
CONFIG_PATH = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')),
                           APP_NAME, 'config.json')
DEFAULT_CONFIG = {
    'mode': 'smart',        # smart = auto when sure + bubble when unsure
                            # bubble = never change text by itself, always ask
                            # off    = only the manual hotkey works
    'hotkey': 'pause',      # pause | f9 | f10 | scroll | insert
    'bubble_seconds': 7,
    'switch_layout': True,  # also switch the keyboard language after fixing
    'autostart': True,      # start automatically when Windows starts
    'idle_check': True,     # also check a word when you stop typing (search boxes)
}
IDLE_MS = 1100              # pause after which an unfinished word is checked
HOTKEYS = {'pause': 0x13, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'scroll': 0x91, 'insert': 0x2D}

# ------------------------------------------------------------------ win32 ---
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

LRESULT = ctypes.c_ssize_t
ULONG_PTR = ctypes.c_size_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wt.WPARAM, wt.LPARAM)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [('vkCode', wt.DWORD), ('scanCode', wt.DWORD), ('flags', wt.DWORD),
                ('time', wt.DWORD), ('dwExtraInfo', ULONG_PTR)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [('pt', wt.POINT), ('mouseData', wt.DWORD), ('flags', wt.DWORD),
                ('time', wt.DWORD), ('dwExtraInfo', ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [('wVk', wt.WORD), ('wScan', wt.WORD), ('dwFlags', wt.DWORD),
                ('time', wt.DWORD), ('dwExtraInfo', ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [('dx', wt.LONG), ('dy', wt.LONG), ('mouseData', wt.DWORD),
                ('dwFlags', wt.DWORD), ('time', wt.DWORD), ('dwExtraInfo', ULONG_PTR)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [('type', wt.DWORD), ('u', _INPUTUNION)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [('cbSize', wt.DWORD), ('flags', wt.DWORD), ('hwndActive', wt.HWND),
                ('hwndFocus', wt.HWND), ('hwndCapture', wt.HWND), ('hwndMenuOwner', wt.HWND),
                ('hwndMoveSize', wt.HWND), ('hwndCaret', wt.HWND), ('rcCaret', wt.RECT)]


user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD]
user32.SetWindowsHookExW.restype = wt.HHOOK
user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.GetForegroundWindow.restype = wt.HWND
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.GetWindowThreadProcessId.restype = wt.DWORD
user32.GetKeyboardLayout.argtypes = [wt.DWORD]
user32.GetKeyboardLayout.restype = wt.HKL
user32.GetKeyboardLayoutList.argtypes = [ctypes.c_int, ctypes.POINTER(wt.HKL)]
user32.ToUnicodeEx.argtypes = [wt.UINT, wt.UINT, ctypes.POINTER(ctypes.c_ubyte),
                               wt.LPWSTR, ctypes.c_int, wt.UINT, wt.HKL]
user32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.GetKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetGUIThreadInfo.argtypes = [wt.DWORD, ctypes.POINTER(GUITHREADINFO)]
user32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
user32.GetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int]
user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
user32.GetParent.argtypes = [wt.HWND]
user32.GetParent.restype = wt.HWND
kernel32.GetModuleHandleW.restype = wt.HMODULE

WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
WM_LBUTTONDOWN, WM_RBUTTONDOWN = 0x0201, 0x0204
LLKHF_INJECTED = 0x10
INPUT_KEYBOARD, KEYEVENTF_KEYUP, KEYEVENTF_UNICODE = 1, 0x2, 0x4
WM_INPUTLANGCHANGEREQUEST = 0x0050
VK_BACK, VK_TAB, VK_RETURN, VK_SPACE, VK_ESCAPE = 0x08, 0x09, 0x0D, 0x20, 0x1B
VK_SHIFT, VK_CONTROL, VK_MENU, VK_CAPITAL, VK_LWIN, VK_RWIN = 0x10, 0x11, 0x12, 0x14, 0x5B, 0x5C
LANG_EN, LANG_FA = 0x09, 0x29

TYPING_VKS = set(range(0x30, 0x3A)) | set(range(0x41, 0x5B)) | \
    {0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0xC0, 0xDB, 0xDC, 0xDD, 0xDE}
MODIFIER_VKS = {0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x14}


def lang_of(hkl):
    return (hkl or 0) & 0xFF


def foreground():
    hwnd = user32.GetForegroundWindow()
    tid = user32.GetWindowThreadProcessId(hwnd, None)
    return hwnd, tid


def installed_layouts():
    n = user32.GetKeyboardLayoutList(0, None)
    arr = (wt.HKL * n)()
    user32.GetKeyboardLayoutList(n, arr)
    res = {}
    for h in arr:
        res.setdefault(lang_of(h), h)
    return res


def char_for(vk, scan, shift, caps, hkl):
    state = (ctypes.c_ubyte * 256)()
    if shift:
        state[VK_SHIFT] = 0x80
    if caps:
        state[VK_CAPITAL] = 0x01
    buf = ctypes.create_unicode_buffer(8)
    n = user32.ToUnicodeEx(vk, scan, state, buf, 8, 0x4, hkl)   # 0x4: keep kb state
    return buf.value[:n] if n > 0 else ''


def send_unicode(text, backspaces=0):
    items = []

    def key(vk=0, scan=0, flags=0):
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.u.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
        items.append(inp)

    for _ in range(backspaces):
        key(VK_BACK)
        key(VK_BACK, flags=KEYEVENTF_KEYUP)
    for ch in text:
        if ch == '\n':
            key(VK_RETURN); key(VK_RETURN, flags=KEYEVENTF_KEYUP)
            continue
        for unit in ch.encode('utf-16-le').hex(' ', 2).split():   # surrogate pairs
            code = int(unit[2:] + unit[:2], 16)
            key(0, code, KEYEVENTF_UNICODE)
            key(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
    arr = (INPUT * len(items))(*items)
    user32.SendInput(len(items), arr, ctypes.sizeof(INPUT))


def caret_position():
    hwnd, tid = foreground()
    gti = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
    if user32.GetGUIThreadInfo(tid, ctypes.byref(gti)) and gti.hwndCaret:
        pt = wt.POINT(gti.rcCaret.left, gti.rcCaret.bottom)
        user32.ClientToScreen(gti.hwndCaret, ctypes.byref(pt))
        if pt.x or pt.y:
            return pt.x, pt.y + 6
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x + 12, pt.y + 18


# ----------------------------------------------------------------- config ---
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'


def startup_command():
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    pyw = sys.executable.replace('python.exe', 'pythonw.exe')
    return f'"{pyw}" "{os.path.abspath(__file__)}"'


def startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
            return True
    except OSError:
        return False


def set_startup(on):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, startup_command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except OSError:
                pass


# ---------------------------------------------------------------- tracker ---
class Key:
    __slots__ = ('en', 'fa', 'lang')

    def __init__(self, en, fa, lang):
        self.en, self.fa, self.lang = en, fa, lang

    def text(self, lang=None):
        return self.en if (lang or self.lang) == LANG_EN else self.fa


class Tracker:
    """Keeps the characters typed since the last focus change / Enter / click."""

    def __init__(self, events):
        self.events = events          # queue to the UI thread
        self.lock = threading.RLock()
        self.run = []                 # list[Key]  (space is Key(' ', ' ', lang))
        self.hwnd = None
        self.layouts = installed_layouts()
        self.enabled = True
        self.hotkey_vk = 0x13
        self.seq = 0                  # increases with every typed key
        self.pending = None           # (lang, hwnd, until): layout we just switched to
        self.bubble_rect = None       # screen rect of the bubble (set by the UI)

    def reset(self):
        # Clear right here in the hook thread. (Clearing later in the UI thread
        # used to wipe the first letter typed in a newly focused window.)
        with self.lock:
            self.run = []
            self.seq += 1
        self.events.put(('reset',))

    def on_click(self, x, y):
        r = self.bubble_rect
        if r and r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            return                    # click on our own bubble: keep the text
        self.reset()

    # called from the hook thread
    def on_key(self, vk, scan):
        hwnd, tid = foreground()
        if hwnd != self.hwnd:
            self.hwnd = hwnd
            self.reset()
        if vk == self.hotkey_vk:
            self.events.put(('hotkey',))
            return True                               # swallow the hotkey
        if vk in MODIFIER_VKS:
            return False
        ctrl = user32.GetAsyncKeyState(VK_CONTROL) & 0x8000
        alt = user32.GetAsyncKeyState(VK_MENU) & 0x8000
        win = (user32.GetAsyncKeyState(VK_LWIN) | user32.GetAsyncKeyState(VK_RWIN)) & 0x8000
        if ctrl or alt or win:
            self.reset()
            return False
        hkl = user32.GetKeyboardLayout(tid)
        lang = lang_of(hkl)
        # right after we switch the keyboard language the app may not have
        # applied it yet - the first letter of the next word would otherwise
        # be recorded in the old language
        p = self.pending
        if p:
            if lang == p[0] or hwnd != p[1] or time.time() > p[2]:
                self.pending = None
            else:
                lang = p[0]
        if vk == VK_BACK:
            with self.lock:
                if self.run:
                    self.run.pop()
                self.seq += 1
            return False
        if vk == VK_SPACE:
            with self.lock:
                self.run.append(Key(' ', ' ', lang))
                self.seq += 1
                snapshot = list(self.run)
            self.events.put(('space', snapshot))
            return False
        if vk == VK_ESCAPE:
            self.events.put(('escape',))
            return False
        if vk not in TYPING_VKS or lang not in (LANG_EN, LANG_FA):
            self.reset()                              # arrows, Enter, Tab, Home...
            return False
        shift = bool(user32.GetKeyState(VK_SHIFT) & 0x8000)
        caps = bool(user32.GetKeyState(VK_CAPITAL) & 1)
        self.layouts = self.layouts or installed_layouts()
        en_hkl = self.layouts.get(LANG_EN)
        fa_hkl = self.layouts.get(LANG_FA)
        en = char_for(vk, scan, shift, caps, en_hkl) if en_hkl else ''
        fa = char_for(vk, scan, shift, caps, fa_hkl) if fa_hkl else ''
        if not en:
            en = core.fa_to_en(fa) if fa else ''
        if not fa:
            fa = core.en_to_fa(en)
        if not en or not fa:
            self.reset()
            return False
        with self.lock:
            self.run.append(Key(en, fa, lang))
            if len(self.run) > 400:
                self.run = self.run[-200:]
            self.seq += 1
            seq = self.seq
        self.events.put(('typed', seq))
        return False

    # ---- helpers used by the UI thread
    @staticmethod
    def last_word_span(run, skip_trailing_space=True):
        end = len(run)
        if skip_trailing_space and end and run[end - 1].en == ' ':
            end -= 1
        start = end
        while start > 0 and run[start - 1].en != ' ':
            start -= 1
        return start, end

    def convert_from(self, start, target_lang, switch_layout):
        """Retype everything from run[start:] so that keys typed in the wrong
        layout become `target_lang` (keys already in target_lang stay)."""
        with self.lock:
            tail = self.run[start:]
            if not tail:
                return ''
            wrong = LANG_EN if target_lang == LANG_FA else LANG_FA
            new_text = ''.join(k.text(target_lang) if k.lang == wrong else k.text()
                               for k in tail)
            if target_lang == LANG_FA:
                new_text = core.normalize_fa(new_text)
            for k in tail:
                k.lang = target_lang if k.lang == wrong else k.lang
        send_unicode(new_text, backspaces=len(tail))
        if switch_layout:
            hkl = self.layouts.get(target_lang)
            if hkl:
                hwnd, _ = foreground()
                self.pending = (target_lang, hwnd, time.time() + 2.0)
                user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, hkl)
        return new_text


# ------------------------------------------------------------------- hook ---
class Hooks(threading.Thread):
    def __init__(self, tracker):
        super().__init__(daemon=True)
        self.tracker = tracker

    def run(self):
        hmod = kernel32.GetModuleHandleW(None)

        def kb(n, wparam, lparam):
            if n == 0 and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                k = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if not (k.flags & LLKHF_INJECTED):
                    try:
                        if self.tracker.on_key(k.vkCode, k.scanCode):
                            return 1
                    except Exception:
                        pass
            return user32.CallNextHookEx(None, n, wparam, lparam)

        def mouse(n, wparam, lparam):
            if n == 0 and wparam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
                m = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                try:
                    self.tracker.on_click(m.pt.x, m.pt.y)
                except Exception:
                    pass
            return user32.CallNextHookEx(None, n, wparam, lparam)

        self._kb = HOOKPROC(kb)          # keep references alive
        self._ms = HOOKPROC(mouse)
        user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._kb, hmod, 0)
        user32.SetWindowsHookExW(WH_MOUSE_LL, self._ms, hmod, 0)
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


# --------------------------------------------------------------------- UI ---
FONT = 'Tahoma'
BG, FG, ACCENT, MUTED = '#1f2430', '#ffffff', '#4f8cff', '#aab2c5'


class Bubble:
    def __init__(self, app):
        self.app = app
        self.win = None
        self.start = None
        self.target = None
        self.hide_job = None

    def show(self, suggestion, start, target):
        self.hide()
        self.start, self.target = start, target
        root = self.app.root
        w = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes('-topmost', True)
        w.configure(bg=BG)
        frame = tk.Frame(w, bg=BG, padx=12, pady=8, highlightthickness=1,
                         highlightbackground=ACCENT)
        frame.pack()
        tk.Label(frame, text='منظورتون این بود؟' if target == LANG_FA else 'Did you mean?',
                 font=(FONT, 9), fg=MUTED, bg=BG).pack(anchor='e' if target == LANG_FA else 'w')
        btn = tk.Label(frame, text=suggestion, font=(FONT, 14, 'bold'), fg=FG, bg=BG,
                       cursor='hand2')
        btn.pack(fill='x', pady=(2, 4))
        row = tk.Frame(frame, bg=BG)
        row.pack(fill='x')
        ok = tk.Label(row, text=' تبدیل کن ✓ ', font=(FONT, 9, 'bold'), fg=FG, bg=ACCENT,
                      cursor='hand2', padx=6, pady=2)
        ok.pack(side='right')
        tk.Label(row, text=self.app.hotkey_label(), font=(FONT, 8), fg=MUTED,
                 bg=BG).pack(side='right', padx=6)
        no = tk.Label(row, text=' ✕ ', font=(FONT, 9), fg=MUTED, bg=BG, cursor='hand2')
        no.pack(side='left')
        for widget in (btn, ok):
            widget.bind('<Button-1>', lambda e: self.app.root.after(10, self.accept))
        no.bind('<Button-1>', lambda e: self.hide())
        w.update_idletasks()
        x, y = caret_position()
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        x = min(max(0, x), sw - w.winfo_reqwidth() - 4)
        if y + w.winfo_reqheight() > sh - 40:
            y = y - w.winfo_reqheight() - 40
        w.geometry(f'+{x}+{y}')
        # never steal keyboard focus from the app you are typing in
        try:
            hwnd = user32.GetParent(w.winfo_id()) or w.winfo_id()
            ex = user32.GetWindowLongPtrW(hwnd, -20)
            user32.SetWindowLongPtrW(hwnd, -20, ex | 0x08000000 | 0x00000080)  # NOACTIVATE|TOOLWINDOW
        except Exception:
            pass
        self.win = w
        w.update_idletasks()
        self.app.tracker.bubble_rect = (w.winfo_rootx(), w.winfo_rooty(),
                                        w.winfo_rootx() + w.winfo_width(),
                                        w.winfo_rooty() + w.winfo_height())
        self.hide_job = root.after(int(self.app.cfg['bubble_seconds'] * 1000), self.hide)

    def contains(self, x, y):
        if self.win is None:
            return False
        w = self.win
        return (w.winfo_rootx() <= x <= w.winfo_rootx() + w.winfo_width() and
                w.winfo_rooty() <= y <= w.winfo_rooty() + w.winfo_height())

    def visible(self):
        return self.win is not None

    def accept(self):
        if self.win is None:
            return
        start, target = self.start, self.target
        self.hide()
        self.app.tracker.convert_from(start, target, self.app.cfg['switch_layout'])

    def hide(self):
        if self.hide_job:
            try:
                self.app.root.after_cancel(self.hide_job)
            except Exception:
                pass
            self.hide_job = None
        self.app.tracker.bubble_rect = None
        if self.win is not None:
            self.win.destroy()
            self.win = None


class App:
    def __init__(self):
        self.cfg = load_config()
        self.events = queue.Queue()
        self.tracker = Tracker(self.events)
        self.tracker.hotkey_vk = HOTKEYS.get(self.cfg['hotkey'], 0x13)
        self.root = tk.Tk()
        self.root.withdraw()
        self.bubble = Bubble(self)
        core.lexicons()                      # load dictionaries now
        Hooks(self.tracker).start()
        self.tray = None
        self.start_tray()
        self.root.after(30, self.pump)

    def hotkey_label(self):
        return {'pause': 'Pause', 'f8': 'F8', 'f9': 'F9', 'f10': 'F10',
                'scroll': 'ScrollLock', 'insert': 'Insert'}.get(self.cfg['hotkey'], '')

    # ------------------------------------------------------------ events ---
    def pump(self):
        try:
            while True:
                ev = self.events.get_nowait()
                self.handle(ev)
        except queue.Empty:
            pass
        self.root.after(30, self.pump)

    def handle(self, ev):
        kind = ev[0]
        if kind == 'reset':
            # focus change / click / arrows: the tracker already forgot the text
            self.bubble.hide()
            self.last_fix = None
        elif kind == 'typed':
            if self.cfg.get('idle_check', True) and self.cfg['mode'] != 'off':
                seq = ev[1]
                self.root.after(IDLE_MS, lambda: self.on_idle(seq))
        elif kind == 'escape':
            self.bubble.hide()
        elif kind == 'hotkey':
            self.on_hotkey()
        elif kind == 'space':
            self.on_word(ev[1])

    last_fix = None      # (target 'en'/'fa', time) of the previous fixed word

    def on_word(self, run):
        if self.cfg['mode'] == 'off':
            return
        start, end = Tracker.last_word_span(run)
        word = run[start:end]
        if not word:
            return
        langs = {k.lang for k in word}
        if len(langs) != 1:
            return
        typed = langs.pop()
        en_str = ''.join(k.en for k in word)
        fa_str = ''.join(k.fa for k in word)
        ctx = None
        if self.last_fix and time.time() - self.last_fix[1] < 30:
            ctx = self.last_fix[0]
        verdict, repl, target = core.decide(en_str, fa_str, 'en' if typed == LANG_EN else 'fa', ctx)
        if not verdict:
            self.last_fix = None
            return
        target_lang = LANG_FA if target == 'fa' else LANG_EN
        self.last_fix = (target, time.time())
        if self.bubble.visible() and self.bubble.target == target_lang \
                and self.bubble.start is not None and self.bubble.start < start:
            # the earlier word is still waiting - extend the suggestion
            start = self.bubble.start
        if verdict == 'auto' and self.cfg['mode'] == 'smart':
            self.bubble.hide()
            # make sure the tracker still ends with this word + space
            with self.tracker.lock:
                ok = len(self.tracker.run) == len(run)
            if ok:
                self.tracker.convert_from(start, target_lang, self.cfg['switch_layout'])
                return
            # user is still typing fast -> fall back to the bubble
        with self.tracker.lock:
            tail = self.tracker.run[start:]
        wrong = typed
        preview = ''.join(k.text(target_lang) if k.lang == wrong else k.text() for k in tail).strip()
        if target_lang == LANG_FA:
            preview = core.normalize_fa(preview)
        self.bubble.show(preview, start, target_lang)

    def on_idle(self, seq):
        """The user stopped typing in the middle of a word (no Space yet) -
        typical for search boxes (Telegram, Windows search, browsers)."""
        if seq != self.tracker.seq or self.bubble.visible():
            return
        with self.tracker.lock:
            run = list(self.tracker.run)
        if not run or run[-1].en == ' ':
            return
        start, end = Tracker.last_word_span(run, skip_trailing_space=False)
        word = run[start:end]
        if len(word) < 2 or len({k.lang for k in word}) != 1:
            return
        typed = word[0].lang
        en_str = ''.join(k.en for k in word)
        fa_str = ''.join(k.fa for k in word)
        ctx = self.last_fix[0] if self.last_fix and time.time() - self.last_fix[1] < 30 else None
        verdict, repl, target = core.decide(en_str, fa_str, 'en' if typed == LANG_EN else 'fa', ctx)
        if not verdict:
            return
        target_lang = LANG_FA if target == 'fa' else LANG_EN
        if verdict == 'auto' and self.cfg['mode'] == 'smart':
            with self.tracker.lock:
                still = self.tracker.seq == seq
            if still:
                self.last_fix = (target, time.time())
                self.tracker.convert_from(start, target_lang, self.cfg['switch_layout'])
            return
        preview = ''.join(k.text(target_lang) for k in word)
        if target_lang == LANG_FA:
            preview = core.normalize_fa(preview)
        self.bubble.show(preview, start, target_lang)

    def on_hotkey(self):
        if self.bubble.visible():
            self.bubble.accept()
            return
        with self.tracker.lock:
            run = list(self.tracker.run)
        start, end = Tracker.last_word_span(run)
        if start == end:
            return
        lang = run[start].lang
        target = LANG_EN if lang == LANG_FA else LANG_FA
        self.tracker.convert_from(start, target, self.cfg['switch_layout'])

    # -------------------------------------------------------------- tray ---
    def start_tray(self):
        try:
            self._start_tray()
        except Exception:
            log_error('tray icon failed')
            message_box('ZabanYar is running, but the tray icon could not be created.\n\n'
                        'The fixer still works. Details were saved to:\n' + LOG_PATH)

    def _start_tray(self):
        import pystray
        from PIL import Image, ImageDraw, ImageFont
        try:
            img = Image.open(os.path.join(core._resource_dir(), 'tray.png')).convert('RGBA')
        except Exception:
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            ImageDraw.Draw(img).rounded_rectangle((2, 2, 62, 62), 14, fill=(99, 102, 241))

        def set_mode(m):
            def f(icon, item):
                self.cfg['mode'] = m
                save_config(self.cfg)
            return f

        def set_hotkey(h):
            def f(icon, item):
                self.cfg['hotkey'] = h
                self.tracker.hotkey_vk = HOTKEYS[h]
                save_config(self.cfg)
            return f

        def toggle_switch(icon, item):
            self.cfg['switch_layout'] = not self.cfg['switch_layout']
            save_config(self.cfg)

        def toggle_startup(icon, item):
            on = not startup_enabled()
            set_startup(on)
            self.cfg['autostart'] = on
            save_config(self.cfg)

        def quit_app(icon, item):
            icon.stop()
            self.root.after(0, self.root.destroy)

        def about(icon, item):
            message_box(f'ZabanYar  (زبان‌یار)   v{VERSION}\n\n'
                        'Fixes words typed with the wrong keyboard language\n'
                        '(English <-> Persian).\n\n'
                        f'Made by {AUTHOR}')

        M = pystray.MenuItem
        menu = pystray.Menu(
            M(f'ZabanYar v{VERSION} - Made by {AUTHOR}', about, default=True),
            pystray.Menu.SEPARATOR,
            M('Smart: auto-fix when sure, ask when unsure', set_mode('smart'),
              checked=lambda i: self.cfg['mode'] == 'smart', radio=True),
            M('Bubble only: always ask first', set_mode('bubble'),
              checked=lambda i: self.cfg['mode'] == 'bubble', radio=True),
            M('Off (hotkey only)', set_mode('off'),
              checked=lambda i: self.cfg['mode'] == 'off', radio=True),
            pystray.Menu.SEPARATOR,
            M('Hotkey', pystray.Menu(*[
                M(lbl, set_hotkey(h), checked=(lambda h: lambda i: self.cfg['hotkey'] == h)(h),
                  radio=True)
                for h, lbl in [('pause', 'Pause / Break'), ('f8', 'F8'), ('f9', 'F9'),
                               ('f10', 'F10'), ('scroll', 'Scroll Lock'), ('insert', 'Insert')]])),
            M('Switch keyboard language after fixing', toggle_switch,
              checked=lambda i: self.cfg['switch_layout']),
            M('Start with Windows', toggle_startup, checked=lambda i: startup_enabled()),
            pystray.Menu.SEPARATOR,
            M('About', about),
            M('Exit', quit_app),
        )
        self.tray = pystray.Icon(APP_NAME, img, f'ZabanYar - Made by {AUTHOR}', menu)
        self.tray.run_detached()

    def welcome(self):
        """Small notice in the corner so you know the program started."""
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes('-topmost', True)
        f = tk.Frame(w, bg=BG, padx=16, pady=12, highlightthickness=1, highlightbackground=ACCENT)
        f.pack()
        tk.Label(f, text='زبان‌یار روشن است ✓', font=(FONT, 12, 'bold'), fg=FG, bg=BG).pack(anchor='e')
        tk.Label(f, text='ZabanYar is running', font=(FONT, 9), fg=MUTED, bg=BG).pack(anchor='e')
        tk.Label(f, text='Settings: tray icon near the clock (click ^ if hidden)',
                 font=(FONT, 8), fg=MUTED, bg=BG).pack(anchor='e', pady=(4, 0))
        tk.Frame(f, bg='#3a4152', height=1).pack(fill='x', pady=(8, 6))
        tk.Label(f, text=f'Made by {AUTHOR}', font=(FONT, 9, 'bold'), fg='#8fb4ff',
                 bg=BG).pack(anchor='e')
        w.update_idletasks()
        x = w.winfo_screenwidth() - w.winfo_reqwidth() - 20
        y = w.winfo_screenheight() - w.winfo_reqheight() - 70
        w.geometry(f'+{x}+{y}')
        w.bind('<Button-1>', lambda e: w.destroy())
        self.root.after(5000, w.destroy)

    def apply_autostart(self):
        """Start with Windows by default; keep the saved path up to date
        (e.g. if ZabanYar.exe was moved to another folder)."""
        try:
            if self.cfg.get('autostart', True):
                set_startup(True)
            elif startup_enabled():
                set_startup(False)
        except Exception:
            log_error('autostart')

    def run(self):
        self.apply_autostart()
        self.root.after(300, self.welcome)
        self.root.mainloop()


LOG_PATH = os.path.join(os.path.dirname(CONFIG_PATH), 'error.log')


def log_error(where):
    import traceback
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f'--- {time.ctime()} {where}\n{traceback.format_exc()}\n')
    except Exception:
        pass


def message_box(text, error=False):
    user32.MessageBoxW(None, text, 'ZabanYar', 0x10 if error else 0x40)


def single_instance():
    kernel32.CreateMutexW(None, False, 'Local\\ZabanYarSingleInstance')
    return ctypes.get_last_error() != 183      # ERROR_ALREADY_EXISTS


if __name__ == '__main__':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    if not single_instance():
        message_box('ZabanYar is already running.\n\n'
                    'Look for its icon near the clock (click ^ if hidden).\n'
                    'To restart it: Task Manager > ZabanYar > End task, then open it again.')
        sys.exit(0)
    try:
        App().run()
    except Exception:
        log_error('fatal')
        import traceback
        message_box('ZabanYar stopped because of an error:\n\n' +
                    traceback.format_exc()[-800:] + '\n\nSaved to: ' + LOG_PATH, error=True)
