import ctypes
import time
import keyboard
from config import KEYS, THRESHOLDS, TIMINGS


INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_UNICODE = 0x0004
VK_KEYSCAN_SHIFT_MASK = 0x0100


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]


class TriggerController:
    def __init__(self) -> None:
        self._last_action_times = {
            KEYS.hp_key: 0.0,
            KEYS.mp_key: 0.0,
        }

    def _can_fire(self, key: str) -> bool:
        return (time.time() - self._last_action_times[key]) >= TIMINGS.action_cooldown_seconds

    def _send_key(self, key: str) -> None:
        try:
            keyboard.press(key)
            time.sleep(TIMINGS.key_hold_seconds)
            keyboard.release(key)
            return
        except Exception as exc:
            print(f"keyboard fallback failed for {key!r}: {exc}")

        vk_scan = ctypes.windll.user32.VkKeyScanW(ord(key))
        if vk_scan == -1:
            self._send_unicode_key(key)
            return

        vk_code = vk_scan & 0xFF
        needs_shift = bool(vk_scan & VK_KEYSCAN_SHIFT_MASK)
        if needs_shift:
            self._send_virtual_key(0x10, hold=False)

        self._send_virtual_key(vk_code, hold=True)

        if needs_shift:
            self._send_virtual_key(0x10, key_up_only=True)

    def _send_virtual_key(self, vk_code: int, hold: bool = False, key_up_only: bool = False) -> None:
        scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
        extra = ctypes.c_ulong(0)
        key_down = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=vk_code,
                wScan=scan_code,
                dwFlags=0,
                time=0,
                dwExtraInfo=ctypes.pointer(extra),
            ),
        )
        key_up = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=vk_code,
                wScan=scan_code,
                dwFlags=KEYEVENTF_KEYUP,
                time=0,
                dwExtraInfo=ctypes.pointer(extra),
            ),
        )
        sent_down = 1
        if not key_up_only:
            sent_down = ctypes.windll.user32.SendInput(1, ctypes.byref(key_down), ctypes.sizeof(INPUT))
            if hold:
                time.sleep(TIMINGS.key_hold_seconds)
        sent_up = ctypes.windll.user32.SendInput(1, ctypes.byref(key_up), ctypes.sizeof(INPUT))
        if sent_down != 1 or sent_up != 1:
            raise OSError(f"SendInput failed for vk={vk_code!r}: down={sent_down}, up={sent_up}")

    def _send_unicode_key(self, key: str) -> None:
        extra = ctypes.c_ulong(0)
        key_down = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=0,
                wScan=ord(key),
                dwFlags=KEYEVENTF_UNICODE,
                time=0,
                dwExtraInfo=ctypes.pointer(extra),
            ),
        )
        key_up = INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=0,
                wScan=ord(key),
                dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                time=0,
                dwExtraInfo=ctypes.pointer(extra),
            ),
        )
        sent_down = ctypes.windll.user32.SendInput(1, ctypes.byref(key_down), ctypes.sizeof(INPUT))
        time.sleep(TIMINGS.key_hold_seconds)
        sent_up = ctypes.windll.user32.SendInput(1, ctypes.byref(key_up), ctypes.sizeof(INPUT))
        if sent_down != 1 or sent_up != 1:
            raise OSError(f"Unicode SendInput failed for key {key!r}: down={sent_down}, up={sent_up}")

    def _fire(self, key: str, reason: str) -> None:
        if not self._can_fire(key):
            return
        self._send_key(key)
        self._last_action_times[key] = time.time()
        print(f"ACTION: pressed {key} because {reason}")

    def evaluate(self, hp_current: int | None = None, mp_current: int | None = None) -> None:
        if hp_current is not None:
            if hp_current <= THRESHOLDS.hp_trigger_at_or_below:
                self._fire(KEYS.hp_key, f"hp <= {THRESHOLDS.hp_trigger_at_or_below} (hp={hp_current})")

        if mp_current is not None:
            if mp_current <= THRESHOLDS.mp_trigger_at_or_below:
                self._fire(
                    KEYS.mp_key,
                    f"mp <= {THRESHOLDS.mp_trigger_at_or_below} (mp={mp_current})"
                )
