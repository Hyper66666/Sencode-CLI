"""Exercise the real Sengoo CLI in an owned, hidden Windows console.

No user terminal is attached or driven. The controller starts a separate
console, assigns its worker to a kill-on-close Job, then releases the worker.
Only synthetic state and an isolated profile are used; no API is contacted.
Snapshots record actual console cells and attributes, not a simulated renderer.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback


class Coord(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]


class SmallRect(ctypes.Structure):
    _fields_ = [("Left", wintypes.SHORT), ("Top", wintypes.SHORT),
                ("Right", wintypes.SHORT), ("Bottom", wintypes.SHORT)]


class ScreenInfo(ctypes.Structure):
    _fields_ = [("dwSize", Coord), ("dwCursorPosition", Coord),
                ("wAttributes", wintypes.WORD), ("srWindow", SmallRect),
                ("dwMaximumWindowSize", Coord)]


class CharUnion(ctypes.Union):
    # Use raw UTF-16 units so lone surrogates survive console-cell snapshots.
    _fields_ = [("UnicodeChar", wintypes.WORD), ("AsciiChar", ctypes.c_char)]


class CharInfo(ctypes.Structure):
    _fields_ = [("Char", CharUnion), ("Attributes", wintypes.WORD)]


class KeyEvent(ctypes.Structure):
    _fields_ = [("bKeyDown", wintypes.BOOL), ("wRepeatCount", wintypes.WORD),
                ("wVirtualKeyCode", wintypes.WORD), ("wVirtualScanCode", wintypes.WORD),
                ("uChar", CharUnion), ("dwControlKeyState", wintypes.DWORD)]


class InputUnion(ctypes.Union):
    _fields_ = [("KeyEvent", KeyEvent), ("padding", ctypes.c_byte * 16)]


class InputRecord(ctypes.Structure):
    _fields_ = [("EventType", wintypes.WORD), ("Event", InputUnion)]


class JobBasicLimits(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]


class IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class JobExtendedLimits(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", JobBasicLimits), ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


def kernel_api():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "GetStdHandle": ([wintypes.DWORD], wintypes.HANDLE),
        "GetConsoleMode": ([wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        "GetConsoleScreenBufferInfo": ([wintypes.HANDLE, ctypes.POINTER(ScreenInfo)], wintypes.BOOL),
        "SetConsoleScreenBufferSize": ([wintypes.HANDLE, Coord], wintypes.BOOL),
        "SetConsoleWindowInfo": ([wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(SmallRect)], wintypes.BOOL),
        "SetConsoleCursorPosition": ([wintypes.HANDLE, Coord], wintypes.BOOL),
        "SetConsoleTextAttribute": ([wintypes.HANDLE, wintypes.WORD], wintypes.BOOL),
        "FillConsoleOutputCharacterW": ([wintypes.HANDLE, wintypes.WCHAR, wintypes.DWORD, Coord, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        "FillConsoleOutputAttribute": ([wintypes.HANDLE, wintypes.WORD, wintypes.DWORD, Coord, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        "ReadConsoleOutputW": ([wintypes.HANDLE, ctypes.POINTER(CharInfo), Coord, Coord, ctypes.POINTER(SmallRect)], wintypes.BOOL),
        "WriteConsoleInputW": ([wintypes.HANDLE, ctypes.POINTER(InputRecord), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        "WriteConsoleW": ([wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL),
        "FlushConsoleInputBuffer": ([wintypes.HANDLE], wintypes.BOOL),
        "GetConsoleCP": ([], wintypes.UINT),
        "GetConsoleOutputCP": ([], wintypes.UINT),
        "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
        "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
        "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
        "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes = arguments
        function.restype = result
    return kernel


def checked(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2), encoding="utf-8")


def remove_owned_tree(root: Path):
    """Inventory and remove literal files, then empty directories only."""
    root = root.resolve()
    paths = list(root.rglob("*"))
    for item in paths:
        if not item.resolve().is_relative_to(root):
            raise AssertionError(f"Refusing cleanup outside the test directory: {item}")
    for item in paths:
        if item.is_file() or item.is_symlink():
            item.unlink()
    for item in sorted((p for p in paths if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        item.rmdir()
    root.rmdir()


def console_text(cells):
    units = []
    for unit, attribute in cells:
        # Wide CJK trailing cells can repeat their character. Low surrogates
        # are kept so emoji pairs normalize back into their actual scalar.
        if attribute & 0x0200 and not 0xDC00 <= unit <= 0xDFFF:
            continue
        units.append(unit)
    raw = b"".join(unit.to_bytes(2, "little") for unit in units)
    return raw.decode("utf-16-le", errors="replace").replace("\x00", " ").rstrip()


class Console:
    def __init__(self):
        self.kernel = kernel_api()
        self.input = self.kernel.GetStdHandle(-10 & 0xFFFFFFFF)
        self.output = self.kernel.GetStdHandle(-11 & 0xFFFFFFFF)
        self.modes()  # Fail explicitly if this is not our real new console.

    def modes(self):
        input_mode, output_mode = wintypes.DWORD(), wintypes.DWORD()
        checked(self.kernel.GetConsoleMode(self.input, ctypes.byref(input_mode)))
        checked(self.kernel.GetConsoleMode(self.output, ctypes.byref(output_mode)))
        return {"input": input_mode.value, "output": output_mode.value,
                "input_codepage": self.kernel.GetConsoleCP(),
                "output_codepage": self.kernel.GetConsoleOutputCP()}

    def info(self):
        info = ScreenInfo()
        checked(self.kernel.GetConsoleScreenBufferInfo(self.output, ctypes.byref(info)))
        return info

    def resize(self, columns, rows=35):
        # Buffer width equals viewport width; otherwise legacy conhost clips
        # horizontally rather than exercising the application's wrapping.
        checked(self.kernel.SetConsoleWindowInfo(self.output, True, ctypes.byref(SmallRect(0, 0, 0, 0))))
        checked(self.kernel.SetConsoleScreenBufferSize(self.output, Coord(columns, 2000)))
        # Follow the host's reflowed cursor. Reusing its old row would place
        # the active prompt outside the viewport and make ANSI motion clamp
        # into unrelated transcript lines, unlike an ordinary window resize.
        cursor = self.info().dwCursorPosition.Y
        top = max(0, min(2000 - rows, cursor - rows + 8))
        checked(self.kernel.SetConsoleWindowInfo(self.output, True, ctypes.byref(SmallRect(0, top, columns - 1, top + rows - 1))))

    def clear(self):
        checked(self.kernel.FlushConsoleInputBuffer(self.input))
        info = self.info()
        amount = info.dwSize.X * info.dwSize.Y
        written = wintypes.DWORD()
        checked(self.kernel.SetConsoleTextAttribute(self.output, 7))
        checked(self.kernel.FillConsoleOutputCharacterW(self.output, " ", amount, Coord(0, 0), ctypes.byref(written)))
        checked(self.kernel.FillConsoleOutputAttribute(self.output, 7, amount, Coord(0, 0), ctypes.byref(written)))
        checked(self.kernel.SetConsoleCursorPosition(self.output, Coord(0, 0)))
        checked(self.kernel.SetConsoleWindowInfo(self.output, True, ctypes.byref(SmallRect(0, 0, info.srWindow.Right, info.srWindow.Bottom - info.srWindow.Top))))

    def emoji_readback(self):
        # Some legacy conhost builds expose supplementary glyphs as U+FFFD
        # through ReadConsoleOutputW even for a direct correct UTF-16 write.
        # Calibrate that observation separately from the application's input.
        self.clear()
        source = ctypes.create_unicode_buffer("😀")
        written = wintypes.DWORD()
        checked(self.kernel.WriteConsoleW(self.output, source, 2, ctypes.byref(written), None))
        if written.value != 2:
            raise AssertionError("Direct console UTF-16 calibration was incomplete")
        observed = self.read()["rows"][0]["text"]
        if observed not in ("😀", "\ufffd"):
            raise AssertionError(f"Unexpected console emoji readback: {observed!r}")
        self.clear()
        return observed

    def inject(self, text="", *, virtual_key=0, modifiers=0):
        encoded = text.encode("utf-16-le")
        units = [int.from_bytes(encoded[i:i + 2], "little") for i in range(0, len(encoded), 2)] or [0]
        events = (InputRecord * len(units))()
        for event, unit in zip(events, units):
            event.EventType = 1
            event.Event.KeyEvent = KeyEvent(True, 1, virtual_key, 0, CharUnion(unit), modifiers)
        written = wintypes.DWORD()
        checked(self.kernel.WriteConsoleInputW(self.input, events, len(events), ctypes.byref(written)))
        if written.value != len(events):
            raise AssertionError("Console input was only partly written")

    def key(self, virtual_key, text="", modifiers=0):
        self.inject(text, virtual_key=virtual_key, modifiers=modifiers)

    def command(self, text):
        self.inject(text)
        self.key(0x0D, "\r")

    def read(self, *, viewport=False):
        info = self.info()
        left = info.srWindow.Left if viewport else 0
        top = info.srWindow.Top if viewport else max(0, info.dwCursorPosition.Y - 100)
        right = info.srWindow.Right if viewport else info.dwSize.X - 1
        bottom = info.srWindow.Bottom if viewport else min(info.dwSize.Y - 1, info.dwCursorPosition.Y + 18)
        width, height = right - left + 1, bottom - top + 1
        cells = (CharInfo * (width * height))()
        region = SmallRect(left, top, right, bottom)
        checked(self.kernel.ReadConsoleOutputW(self.output, cells, Coord(width, height), Coord(0, 0), ctypes.byref(region)))
        rows = []
        for row in range(height):
            raw = [[cells[row * width + column].Char.UnicodeChar,
                    cells[row * width + column].Attributes] for column in range(width)]
            rows.append({"y": top + row, "text": console_text(raw), "cells": raw})
        return {"schema": 1, "width": width, "height": height,
                "window": {"left": info.srWindow.Left, "top": info.srWindow.Top,
                           "right": info.srWindow.Right, "bottom": info.srWindow.Bottom},
                "cursor": {"x": info.dwCursorPosition.X, "y": info.dwCursorPosition.Y},
                "rows": rows, "text": "\n".join(row["text"] for row in rows)}


def active_frame(screen):
    rows = screen["rows"]
    cursor = screen["cursor"]
    starts = [index for index, row in enumerate(rows)
              if row["y"] < cursor["y"] and row["text"].startswith("╭─ Message")]
    if not starts:
        return None
    start = starts[-1]
    bottoms = [index for index in range(start + 1, len(rows)) if rows[index]["text"].startswith("╰")]
    if not bottoms:
        return None
    bottom = bottoms[0]
    if not rows[start]["y"] < cursor["y"] < rows[bottom]["y"]:
        return None
    body = []
    for row in rows[start + 1:bottom]:
        text = row["text"]
        if not text.startswith("│ ") or not text.endswith(" │"):
            return None
        body.append(text[4:-2].rstrip())
    footer = rows[bottom + 1]["text"] if bottom + 1 < len(rows) else ""
    return {"top": rows[start]["y"], "bottom": rows[bottom]["y"], "body": body,
            "text": "\n".join(body), "footer": footer, "cursor": cursor}


def wait_screen(console, process, predicate, description, timeout=10):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = console.read()
        if predicate(last):
            # Wait for a second identical frame; no key is sent during paint.
            time.sleep(0.035)
            stable = console.read()
            if predicate(stable):
                return stable
        if process.poll() is not None:
            raise AssertionError(f"CLI exited {process.returncode} while waiting for {description}: {last['text']}")
        time.sleep(0.02)
    raise AssertionError(f"Timed out waiting for {description}: {last['text'] if last else '<no screen>'}")


def wait_frame(console, process, predicate=lambda frame: True, description="input prompt", timeout=10):
    return wait_screen(console, process, lambda screen: bool((frame := active_frame(screen)) and predicate(frame)), description, timeout)


def environment_for(scratch: Path):
    environment = {name: os.environ[name] for name in
                   ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "PROCESSOR_ARCHITECTURE",
                    "PROCESSOR_IDENTIFIER", "NUMBER_OF_PROCESSORS") if name in os.environ}
    for variable, directory in (("USERPROFILE", "profile"), ("APPDATA", "roaming"),
                                ("LOCALAPPDATA", "local"), ("HOME", "home"),
                                ("TEMP", "temp"), ("TMP", "temp")):
        path = scratch / directory
        path.mkdir(parents=True, exist_ok=True)
        environment[variable] = str(path)
    environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
    environment["TERM"] = "xterm-256color"
    return environment


def worker(arguments):
    deadline = time.monotonic() + 10
    while not arguments.ready.exists():
        if time.monotonic() > deadline:
            raise AssertionError("Parent did not establish the owned process Job")
        time.sleep(0.02)
    console = Console()
    console.resize(110)
    console.clear()
    emoji_projection = console.emoji_readback()
    baseline = console.modes()
    process = None
    report = {"schema": 1, "platform": "windows-x64", "result": "running",
              "actual_console": True, "source": "Win32 console screen cells",
              "binary": str(arguments.executable),
              "binary_sha256": hashlib.sha256(arguments.executable.read_bytes()).hexdigest(),
              "checks": [], "snapshots": [], "console_before": baseline}
    report["console_supplementary_readback"] = {
        "written_via_WriteConsoleW": "😀", "read_via_ReadConsoleOutputW": emoji_projection,
        "lossy_legacy_readback": emoji_projection != "😀",
    }
    workspace = arguments.scratch / "项目 outside repository"
    workspace.mkdir()
    database = arguments.scratch / "isolated.sqlite"
    environment = environment_for(arguments.scratch)
    snapshot_directory = arguments.evidence.with_name(arguments.evidence.stem + "-screens")

    def passed(name):
        report["checks"].append({"name": name, "status": "passed"})

    def projected(text):
        return text.replace("😀", emoji_projection)

    def snapshot(name):
        path = snapshot_directory / (name + ".json")
        screen = console.read(viewport=True)
        screen["name"] = name
        write_json(path, screen)
        report["snapshots"].append(str(path))

    def launch(*positionals, extra_environment=None):
        console.clear()
        env = dict(environment, **(extra_environment or {}))
        return subprocess.Popen([str(arguments.executable), *positionals, "--tui", "scrolling", "--database", str(database)],
                                cwd=workspace, env=env)

    def quit_cli(*, eof=False):
        nonlocal process
        if eof:
            console.key(0, "\x04", 0x08)
        else:
            console.command("/quit")
        if process.wait(timeout=8) != 0:
            raise AssertionError(f"CLI exited with code {process.returncode}")
        restored = console.modes()
        if restored != baseline:
            raise AssertionError(f"Console modes/codepages changed: {baseline} -> {restored}")
        process = None

    try:
        process = launch()
        screen = wait_frame(console, process)
        if "S E N C O D E" not in screen["text"] or "workspace" not in screen["text"]:
            raise AssertionError("Real application welcome was not rendered")
        if not any(attribute & 0xFF != 7 for row in screen["rows"] for _, attribute in row["cells"]):
            raise AssertionError("Default TUI has no colored console cells")
        with sqlite3.connect(database) as db:
            session = db.execute("SELECT id FROM sessions").fetchone()[0]
        report["session_id"] = session
        snapshot("01-welcome")
        passed("application welcome, current workspace and colored composer")

        console.inject("你😀好")
        wait_frame(console, process, lambda frame: frame["text"] == projected("你😀好"), "Unicode typing")
        console.key(0x25)  # Left, before 好.
        console.key(0x08, "\b")  # Delete the complete preceding emoji scalar.
        console.inject("中")
        wait_frame(console, process, lambda frame: frame["text"] == "你中好", "Unicode scalar editing")
        console.key(0x0D, "\r", 0x10)  # SHIFT_PRESSED.
        console.key(0x23)  # End.
        console.inject("第二行")
        wait_frame(console, process, lambda frame: frame["body"] == ["你中", "好第二行"], "Shift+Enter multiline composer")
        snapshot("02-unicode-multiline")
        passed("Chinese and emoji scalar editing plus Shift+Enter multiline")

        console.key(0, "\x15", 0x08)  # Ctrl+U removes all preceding text.
        wait_frame(console, process, lambda frame: frame["text"] == "", "clear multiline input")
        console.inject("\x1b[200~粘贴\n中文😀\x1b[201~")
        wait_frame(console, process, lambda frame: frame["body"] == ["粘贴", projected("中文😀")], "bracketed multiline paste")
        console.key(0, "\x15", 0x08)
        wait_frame(console, process, lambda frame: frame["text"] == "", "clear pasted input")
        passed("bracketed Unicode multiline paste remains one editable draft")
        console.command("/help")
        wait_screen(console, process, lambda screen: active_frame(screen) is not None and "/consult QUESTION" in screen["text"], "slash help")
        console.inject("草稿😀")
        wait_frame(console, process, lambda frame: frame["text"] == projected("草稿😀"), "draft typing")
        console.key(0x26)  # Up.
        wait_frame(console, process, lambda frame: frame["text"] == "/help", "history recall")
        console.key(0x28)  # Down.
        wait_frame(console, process, lambda frame: frame["text"] == projected("草稿😀"), "draft restoration")
        console.inject(" next")
        console.key(0, "\x17", 0x08)  # Ctrl+W.
        wait_frame(console, process, lambda frame: frame["text"] == projected("草稿😀"), "word deletion")
        passed("slash help, history draft restoration and word editing")

        console.key(0, "\x15", 0x08)
        long_text = "宽界😀" * 10
        console.inject(long_text)
        wait_frame(console, process, lambda frame: frame["text"] == projected(long_text), "wide composer")
        snapshot("02b-before-resize")
        write_json(snapshot_directory / "02b-before-resize-buffer.json", console.read())
        console.resize(48)
        screen = wait_frame(console, process,
                            lambda frame: "".join(frame["body"]) == projected(long_text) and len(frame["body"]) == 2,
                            "narrow resize wrapping")
        frame = active_frame(screen)
        stale = [row for row in screen["rows"] if frame["bottom"] + 2 < row["y"] <= frame["bottom"] + 7 and row["text"]]
        if stale:
            raise AssertionError(f"Stale composer or footer remains below the resized frame: {[(row['y'], row['text']) for row in stale]}")
        snapshot("03-narrow-resize")
        console.resize(110)
        screen = wait_frame(console, process, lambda frame: frame["text"] == projected(long_text) and len(frame["body"]) == 1, "wide resize cleanup")
        frame = active_frame(screen)
        stale = [row for row in screen["rows"] if frame["bottom"] + 2 < row["y"] <= frame["bottom"] + 7 and row["text"]]
        if stale:
            raise AssertionError(f"Stale multiline border remains after widening: {[(row['y'], row['text']) for row in stale]}")
        snapshot("04-wide-resize")
        passed("real console 110 to 48 to 110 resize, wrapping and stale-row cleanup")

        console.key(0, "\x15", 0x08)
        tall_text = "\n".join(f"row-{i} " + "宽界" * 8 for i in range(8))
        console.inject("\x1b[200~" + tall_text + "\x1b[201~")
        wait_frame(console, process, lambda frame: len(frame["body"]) == 8, "tall multiline composer")
        console.key(0x24)  # Home places the cursor before all eight rows.
        wait_frame(console, process, lambda frame: frame["body"][0].startswith("row-0"), "tall composer Home")
        console.resize(48)
        screen = wait_frame(console, process, lambda frame: len(frame["body"]) == 8 and frame["body"][0].startswith("row-0"), "tall composer narrow resize")
        frame = active_frame(screen)
        stale = [row for row in screen["rows"] if frame["bottom"] + 2 < row["y"] <= frame["bottom"] + 30 and row["text"]]
        if stale:
            raise AssertionError(f"Tall composer left old rows below its footer: {[(row['y'], row['text']) for row in stale]}")
        console.resize(110)
        wait_frame(console, process, lambda frame: len(frame["body"]) == 8 and frame["body"][0].startswith("row-0"), "tall composer wide resize")
        snapshot("04b-tall-resize")
        passed("eight-row composer resize with cursor at Home clears the old tail")

        console.key(0x43, "\x03", 0x08)  # Ctrl+C is a real input record, not a user-console signal.
        wait_screen(console, process, lambda screen: bool((frame := active_frame(screen)) and frame["text"] == "" and "cancelled" in screen["text"]), "cancelled composer")
        console.inject("/per")
        wait_frame(console, process, lambda frame: "Tab complete:" in frame["footer"], "slash completion hint")
        console.key(0x09, "\t")
        wait_frame(console, process, lambda frame: frame["text"] == "/permissions", "Tab command completion")
        console.key(0, "\x15", 0x08)
        wait_frame(console, process, lambda frame: frame["text"] == "", "clear completion")
        passed("slash command hints and Tab completion")
        console.command("/model fixture-ui")
        wait_frame(console, process, lambda frame: "fixture-ui" in frame["footer"], "model selection footer")
        console.command("/plan")
        wait_frame(console, process, lambda frame: "PLAN" in frame["footer"], "Plan footer")
        snapshot("05-plan-mode")
        console.command("/plan approve")
        wait_frame(console, process, lambda frame: "BUILD" in frame["footer"], "Plan approval footer")
        console.command("/agents")
        wait_screen(console, process, lambda screen: active_frame(screen) is not None and "Sessions" in screen["text"] and session in screen["text"], "project sessions view")
        snapshot("06-sessions")
        passed("Ctrl+C, model switching, Plan approval and sessions view")
        quit_cli()
        passed("normal quit restores input/output modes and codepages")

        process = launch("resume", session)
        screen = wait_frame(console, process)
        if session not in screen["text"]:
            raise AssertionError("resume ID did not show the existing session")
        console.command("/context")
        wait_screen(console, process, lambda screen: active_frame(screen) is not None and "0 saved messages" in screen["text"], "resumed context")
        quit_cli()
        process = launch("resume")
        screen = wait_frame(console, process)
        if session not in screen["text"]:
            raise AssertionError("resume without ID changed the current project session")
        quit_cli()
        with sqlite3.connect(database) as db:
            if db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] != 1:
                raise AssertionError("resume created an additional session")
        passed("exact and latest resume reuse the same project session")

        process = launch("resume", extra_environment={"NO_COLOR": "1"})
        screen = wait_frame(console, process)
        if any(attribute & 0xFF != 7 for row in screen["rows"] for _, attribute in row["cells"]):
            raise AssertionError("NO_COLOR still emitted colored console cells")
        snapshot("07-no-color")
        console.inject("abcd")
        console.key(0x24)  # Home.
        console.key(0, "\x04", 0x08)
        wait_frame(console, process, lambda frame: frame["text"] == "bcd", "Ctrl+D forward deletion")
        console.key(0x23)  # End.
        console.key(0, "\x15", 0x08)
        wait_frame(console, process, lambda frame: frame["text"] == "", "empty Ctrl+D exit preparation")
        quit_cli(eof=True)
        passed("NO_COLOR monochrome composer and Ctrl+D deletion/empty exit")

        redirected = subprocess.run([str(arguments.executable), "resume", session, "--database", str(database)],
                                    cwd=workspace, env=environment, input="/agents\n/quit\n",
                                    capture_output=True, encoding="utf-8", timeout=12)
        if redirected.returncode != 0 or "\x1b" in redirected.stdout or "╭" in redirected.stdout:
            raise AssertionError(f"Redirected output gained TUI escapes: {redirected.returncode} {redirected.stdout!r}")
        document = json.loads(redirected.stdout)
        if document["sessions"][0]["id"] != session:
            raise AssertionError("Headless session JSON changed")
        passed("redirected output preserves ANSI-free session JSON")
        report["console_after"] = console.modes()
        report["result"] = "passed"
    except BaseException as error:
        report["result"] = "failed"
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        try:
            snapshot("failure")
            write_json(snapshot_directory / "failure-buffer.json", console.read())
        except BaseException as snapshot_error:
            report["snapshot_error"] = str(snapshot_error)
        raise
    finally:
        if process is not None and process.poll() is None:
            try:
                console.key(0x43, "\x03", 0x08)
                time.sleep(0.1)
                console.command("/quit")
                process.wait(timeout=3)
            except BaseException:
                process.terminate()
                process.wait(timeout=3)
        report["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_json(arguments.evidence, report)


def controller(arguments):
    kernel = kernel_api()
    scratch = Path(tempfile.mkdtemp(prefix="sencode-tui-中文-"))
    ready = scratch / "job-ready"
    job = checked(kernel.CreateJobObjectW(None, None))
    worker_process = None
    try:
        limits = JobExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0  # SW_HIDE: never open a visible test terminal.
        worker_process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                           str(arguments.executable), "--worker", "--scratch", str(scratch),
                                           "--ready", str(ready), "--evidence", str(arguments.evidence)],
                                          startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE)
        checked(kernel.AssignProcessToJobObject(job, wintypes.HANDLE(worker_process._handle)))
        ready.write_text("assigned", encoding="ascii")
        try:
            code = worker_process.wait(timeout=115)
        except subprocess.TimeoutExpired:
            raise AssertionError("Hidden-console acceptance exceeded 115 seconds")
        if not arguments.evidence.exists():
            raise AssertionError(f"Worker exited {code} without evidence")
        evidence = json.loads(arguments.evidence.read_text(encoding="utf-8"))
        if code or evidence["result"] != "passed":
            raise AssertionError(evidence.get("error", f"Worker exited {code}"))
        print(f"Real hidden-console TUI acceptance passed: {len(evidence['checks'])} checks")
        print(f"Evidence: {arguments.evidence}")
        return 0
    finally:
        checked(kernel.CloseHandle(job))  # Stops only our worker and descendants.
        if worker_process is not None:
            worker_process.wait(timeout=5)
        remove_owned_tree(scratch)


def main():
    if os.name != "nt":
        raise SystemExit("This gate requires a real Windows console; unsupported hosts do not count as passes.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--scrolling", action="store_true", help="Verify the retained scrolling compatibility UI")
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parents[1] / "target/tui-console-evidence.json")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scratch", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--ready", type=Path, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    arguments.executable = arguments.executable.resolve(strict=True)
    arguments.evidence = arguments.evidence.resolve()
    if arguments.worker:
        worker(arguments)
        return 0
    return controller(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
