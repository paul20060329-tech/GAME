import random
import tkinter as tk
from math import cos, pi, sin
from typing import List, Sequence, Tuple


def _heart_xy(t: float) -> Tuple[float, float]:
    x = 16 * (sin(t) ** 3)
    y = 13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t)
    return x, y


def _generate_heart_positions(
    screen_w: int,
    screen_h: int,
    window_w: int,
    window_h: int,
    *,
    count: int,
    margin: int = 18,
) -> List[Tuple[int, int]]:
    usable_w = max(1, screen_w - margin * 2)
    usable_h = max(1, screen_h - margin * 2)

    center_x = margin + usable_w / 2
    center_y = margin + usable_h / 2

    scale = min(usable_w / (32 + 6), usable_h / (30 + 6))
    scale *= 0.95

    positions: List[Tuple[int, int]] = []
    for i in range(count):
        t = (i / max(1, count)) * (2 * pi)
        x, y = _heart_xy(t)
        px = int(center_x + x * scale)
        py = int(center_y - y * scale)

        px += random.randint(-10, 10)
        py += random.randint(-10, 10)

        px = max(0, min(px, screen_w - window_w))
        py = max(0, min(py, screen_h - window_h))
        positions.append((px, py))

    return positions


def _pick(seq: Sequence[str]) -> str:
    return seq[random.randint(0, len(seq) - 1)]


class PopupManager:
    def __init__(
        self,
        root: tk.Tk,
        messages: Sequence[str],
        colors: Sequence[str],
        *,
        count_heart: int = 160,
        count_random: int = 120,
        interval_ms: int = 25,
        size: Tuple[int, int] = (240, 70),
        fg: str = "#333333",
        font: Tuple[str, int, str] = ("Microsoft YaHei", 13, "bold"),
        topmost: bool = True,
    ) -> None:
        self.root = root
        self.messages = list(messages)
        self.colors = list(colors)
        self.count_heart = count_heart
        self.count_random = count_random
        self.interval_ms = interval_ms
        self.width, self.height = size
        self.fg = fg
        self.font = font
        self.topmost = topmost

        self._alive: List[tk.Toplevel] = []
        self._phase = "heart"
        self._spawned = 0
        self._heart_positions: List[Tuple[int, int]] = []

    def stop(self) -> None:
        for w in list(self._alive):
            try:
                w.destroy()
            except tk.TclError:
                pass
        self._alive.clear()

    def start(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self._heart_positions = _generate_heart_positions(
            screen_w,
            screen_h,
            self.width,
            self.height,
            count=self.count_heart,
        )
        self._schedule_next()

    def _schedule_next(self) -> None:
        if self._phase == "done":
            return
        self.root.after(self.interval_ms, self._spawn_one)

    def _spawn_one(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        if self._phase == "heart":
            if self._spawned >= self.count_heart:
                self._phase = "random"
                self._spawned = 0
                self._schedule_next()
                return
            x, y = self._heart_positions[self._spawned]
        else:
            if self._spawned >= self.count_random:
                self._phase = "done"
                return
            x = random.randint(0, max(0, screen_w - self.width))
            y = random.randint(0, max(0, screen_h - self.height))

        w = tk.Toplevel(self.root)
        w.overrideredirect(True)  # 移除系统边框，呈现悬浮卡片效果
        w.attributes("-alpha", 0.92)  # 添加透明度，视觉更轻盈
        w.geometry(f"{self.width}x{self.height}+{x}+{y}")
        if self.topmost:
            w.attributes("-topmost", True)

        bg = _pick(self.colors)
        # 添加浅色高亮边框
        container = tk.Frame(w, bg=bg, highlightbackground="#ffb3c6", highlightthickness=2)
        container.pack(fill="both", expand=True)

        # 调整装饰爱心的大小和位置
        tk.Label(container, text="❤", bg=bg, fg="#ff4d6d", font=("Microsoft YaHei", 10)).place(x=6, y=4)
        tk.Label(container, text="❤", bg=bg, fg="#ff4d6d", font=("Microsoft YaHei", 10)).place(
            x=self.width - 22, y=self.height - 24
        )

        # 仅在第一个窗口提示退出方式，避免干扰画面
        if self._spawned == 0:
            tk.Label(container, text="按 ESC 退出", bg=bg, fg="#ff7b93", font=("Microsoft YaHei", 8, "bold")).place(relx=0.5, y=12, anchor="center")

        label = tk.Label(container, text=_pick(self.messages), bg=bg, fg=self.fg, font=self.font)
        label.place(relx=0.5, rely=0.5, anchor="center")

        self._alive.append(w)
        self._spawned += 1

        self._schedule_next()

def _run() -> None:
    root = tk.Tk()
    root.withdraw()

    messages = [
        "保持好心情",
        "今天过得开心嘛",
        "每天都要元气满满",
        "好好爱自己",
        "早安午安晚安",
        "别熬夜",
        "早点休息",
        "顺顺利利",
        "期待下一次见面",
        "想你了",
        "我想你了",
        "愿所有烦恼都消失",
        "梦想成真",
    ]

    colors = ["#ffd1dc", "#cdeffd", "#d9fdd3", "#ffe7c7", "#efe0ff", "#fff3b0"]

    popups = PopupManager(
        root,
        messages,
        colors,
        count_heart=180,
        count_random=160,
        interval_ms=25,  # 提高弹出速度，动画更连贯
        size=(240, 70),  # 稍微缩小尺寸，让整体呈现更加精致
        fg="#333333",
        font=("Microsoft YaHei", 13, "bold"),
        topmost=True,
    )

    def on_close() -> None:
        popups.stop()
        root.destroy()

    root.bind_all("<Escape>", lambda _evt: on_close())

    popups.start()
    root.mainloop()


if __name__ == "__main__":
    _run()
