import threading
import time

import keyboard
import pyautogui

from config import LOOT, WAREHOUSE


class WarehouseRunner:
    def __init__(self) -> None:
        self._running = False
        self._lock = threading.Lock()
        self._stop_requested = threading.Event()
        self._loot_enabled = False
        self._loot_stop_requested = threading.Event()
        self._loot_thread = None
        self._hotkey_handles = []

    def install_hotkeys(self) -> None:
        if not WAREHOUSE.enabled:
            return
        self._hotkey_handles = [
            keyboard.add_hotkey(WAREHOUSE.run_all_hotkey, self.run_all_async),
            keyboard.add_hotkey(WAREHOUSE.stop_hotkey, self.stop),
        ]
        if LOOT.enabled:
            self._hotkey_handles.append(keyboard.add_hotkey(LOOT.toggle_hotkey, self.toggle_loot_spam))
        print(
            f"Warehouse hotkey: press {WAREHOUSE.run_all_hotkey!r} to ctrl+double-click "
            f"{len(WAREHOUSE.points)} slots."
        )
        print(f"Warehouse stop hotkey: press {WAREHOUSE.stop_hotkey!r} to stop the active run.")
        if LOOT.enabled:
            print(f"Loot hotkey: press {LOOT.toggle_hotkey!r} to toggle {LOOT.key!r} spam.")

    def uninstall_hotkeys(self) -> None:
        self.stop_loot_spam()
        for hotkey_handle in self._hotkey_handles:
            keyboard.remove_hotkey(hotkey_handle)
        self._hotkey_handles = []

    def run_all_async(self) -> None:
        with self._lock:
            if self._running:
                print("WAREHOUSE: run already in progress; ignoring hotkey.")
                return
            self._stop_requested.clear()
            self._running = True

        thread = threading.Thread(target=self._run_all_guarded, daemon=True)
        thread.start()

    def stop(self) -> None:
        self._stop_requested.set()
        print("WAREHOUSE: stop requested.")

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def toggle_loot_spam(self) -> None:
        if self._loot_enabled:
            self.stop_loot_spam()
            return
        self.start_loot_spam()

    def start_loot_spam(self) -> None:
        if self._loot_enabled:
            return
        self._loot_enabled = True
        self._loot_stop_requested.clear()
        self._loot_thread = threading.Thread(target=self._loot_spam_loop, daemon=True)
        self._loot_thread.start()
        print("LOOT: space spam ON")

    def stop_loot_spam(self) -> None:
        if not self._loot_enabled:
            return
        self._loot_enabled = False
        self._loot_stop_requested.set()
        print("LOOT: space spam OFF")

    def _run_all_guarded(self) -> None:
        try:
            self.run_all()
        finally:
            with self._lock:
                self._running = False

    def run_all(self) -> None:
        total = len(WAREHOUSE.points)
        if total == 0:
            print("WAREHOUSE: no points configured.")
            return

        print(f"WAREHOUSE: starting ctrl+double-click run for {total} slots.")
        if WAREHOUSE.run_start_delay_seconds > 0:
            time.sleep(WAREHOUSE.run_start_delay_seconds)

        for index, (x, y) in enumerate(WAREHOUSE.points, start=1):
            if self._stop_requested.is_set():
                print(f"WAREHOUSE: stopped before slot {index}/{total}.")
                return
            self._ctrl_left_click_burst_at(x, y)
            print(f"WAREHOUSE: slot {index}/{total} at ({x},{y})")
            if WAREHOUSE.slot_interval_seconds > 0 and index < total:
                if self._sleep_interruptible(WAREHOUSE.slot_interval_seconds):
                    print(f"WAREHOUSE: stopped after slot {index}/{total}.")
                    return

        print("WAREHOUSE: run complete.")

    def _ctrl_left_click_burst_at(self, x: int, y: int) -> None:
        pyautogui.moveTo(x=x, y=y)
        pyautogui.keyDown("ctrl")
        try:
            if self._sleep_interruptible(0.02):
                return
            for click_index in range(max(1, WAREHOUSE.clicks_per_slot)):
                if self._stop_requested.is_set():
                    return
                pyautogui.leftClick()
                more_clicks = click_index < WAREHOUSE.clicks_per_slot - 1
                if more_clicks and WAREHOUSE.click_interval_seconds > 0:
                    if self._sleep_interruptible(WAREHOUSE.click_interval_seconds):
                        return
        finally:
            pyautogui.keyUp("ctrl")

    def _sleep_interruptible(self, seconds: float) -> bool:
        return self._stop_requested.wait(max(0.0, seconds))

    def _loot_spam_loop(self) -> None:
        while not self._loot_stop_requested.is_set():
            if not self.is_running():
                pyautogui.press(LOOT.key)
            self._loot_stop_requested.wait(max(0.01, LOOT.interval_seconds))
