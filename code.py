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


class AnimatedPopup:
    """带全套动感特效的弹窗类"""
    def __init__(self, root: tk.Tk, x: int, y: int, w: int, h: int,
                 bg_color: str, text: str, fg: str, font, win_w: int, win_h: int):
        self.root = root
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.win_w = win_w
        self.win_h = win_h
        self.bg_color = bg_color
        self.text = text
        self.fg = fg
        self.font = font

        # 动画参数
        self.alpha = 0.0
        self.float_offset = 0
        self.scale_rate = 1.0
        self.fade_out_start = False
        self.life_time = random.randint(4500, 7000)

        # 创建窗口
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-alpha", self.alpha)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"{self.win_w}x{self.win_h}+{self.x}+{self.y}")

        # 容器与边框
        self.container = tk.Frame(self.win, bg=bg_color,
                                  highlightbackground="#ffb3c6", highlightthickness=2)
        self.container.pack(fill="both", expand=True)

        # 装饰跳动爱心
        self.heart1 = tk.Label(self.container, text="❤", bg=bg_color, fg="#ff4d6d",
                               font=("Microsoft YaHei", 10))
        self.heart1.place(x=6, y=4)
        self.heart2 = tk.Label(self.container, text="❤", bg=bg_color, fg="#ff4d6d",
                               font=("Microsoft YaHei", 10))
        self.heart2.place(x=self.win_w - 22, y=self.win_h - 24)

        # 主文案
        self.label = tk.Label(self.container, text=self.text, bg=bg_color,
                              fg=self.fg, font=self.font)
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        # 启动所有动画
        self.fade_in()
        self.float_animate()
        self.pulse_scale()
        self.heart_beat()
        self.auto_life()

    def fade_in(self):
        """渐入动画"""
        if self.alpha < 0.92 and not self.fade_out_start:
            self.alpha += 0.04
            self.win.attributes("-alpha", self.alpha)
            self.root.after(30, self.fade_in)

    def fade_out(self):
        """渐出消失"""
        if self.alpha > 0:
            self.alpha -= 0.03
            self.win.attributes("-alpha", self.alpha)
            self.root.after(30, self.fade_out)
        else:
            try:
                self.win.destroy()
            except:
                pass

    def float_animate(self):
        """缓慢上浮+左右轻微漂移"""
        if self.fade_out_start:
            return
        self.float_offset += 1
        new_y = self.y - int(self.float_offset / 8) + int(sin(self.float_offset/3) * 6)
        self.win.geometry(f"{self.win_w}x{self.win_h}+{self.x}+{new_y}")
        self.root.after(50, self.float_animate)

    def pulse_scale(self):
        """呼吸缩放脉动"""
        if self.fade_out_start:
            return
        self.scale_rate += 0.0025
        if self.scale_rate > 1.06 or self.scale_rate < 0.96:
            self.scale_rate = 1.0
        self.root.after(60, self.pulse_scale)

    def heart_beat(self):
        """角落爱心跳动变色"""
        if self.fade_out_start:
            return
        color_list = ["#ff4d6d", "#ff758f", "#ff9aa2"]
        self.heart1.config(fg=_pick(color_list))
        self.heart2.config(fg=_pick(color_list))
        self.root.after(180, self.heart_beat)

    def auto_life(self):
        """存活时间到自动淡出"""
        self.root.after(self.life_time, self.start_fade_out)

    def start_fade_out(self):
        self.fade_out_start = True
        self.fade_out()

    def destroy(self):
        try:
            self.win.destroy()
        except:
            pass


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

        self._alive: List[AnimatedPopup] = []
        self._phase = "heart"
        self._spawned = 0
        self._heart_positions: List[Tuple[int, int]] = []

    def stop(self) -> None:
        for w in self._alive:
            w.destroy()
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

        bg = _pick(self.colors)
        text = _pick(self.messages)

        # 创建带动画的弹窗
        popup = AnimatedPopup(
            self.root, x, y, self.width, self.height,
            bg, text, self.fg, self.font, self.width, self.height
        )
        self._alive.append(popup)
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
        interval_ms=20,
        size=(240, 70),
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