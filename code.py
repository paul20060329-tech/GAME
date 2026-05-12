import random
import tkinter as tk
from dataclasses import dataclass
from math import cos, pi, sin
from typing import Callable, List, Optional, Sequence, Tuple


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
        t = (i / max(1, count)) * (2 * pi) + random.uniform(-0.035, 0.035)
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
    return random.choice(seq)


def _rounded_rect_points(x1: int, y1: int, x2: int, y2: int, r: int) -> List[int]:
    r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    return [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
    ]


@dataclass(frozen=True)
class PopupStyle:
    size: Tuple[int, int] = (240, 70)
    fg: str = "#2c2c2c"
    font: Tuple[str, int, str] = ("Microsoft YaHei", 13, "bold")
    hint_font: Tuple[str, int, str] = ("Microsoft YaHei", 8, "bold")
    deco_font: Tuple[str, int] = ("Microsoft YaHei", 10)
    radius: int = 14
    border: str = "#ffb3c6"
    border_width: int = 2
    shadow: str = "#000000"
    shadow_alpha: float = 0.16
    shadow_offset: Tuple[int, int] = (3, 4)
    window_alpha: float = 0.94
    fade_in_ms: int = 220
    fade_out_ms: int = 260
    hold_ms: Optional[int] = None
    float_px: int = 10


class PopupWindow:
    def __init__(
        self,
        root: tk.Tk,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
        message: str,
        bg: str,
        style: PopupStyle,
        topmost: bool,
        show_hint: bool,
        on_destroy: Callable[["PopupWindow"], None],
    ) -> None:
        self._root = root
        self._style = style
        self._bg = bg
        self._on_destroy = on_destroy
        self._target_x = x
        self._target_y = y
        self._w = tk.Toplevel(root)
        self._w.overrideredirect(True)
        self._w.attributes("-alpha", 0.0)
        if topmost:
            self._w.attributes("-topmost", True)
        start_y = y + max(0, style.float_px)
        self._w.geometry(f"{width}x{height}+{x}+{start_y}")

        self._canvas = tk.Canvas(self._w, width=width, height=height, highlightthickness=0, bg=bg)
        self._canvas.pack(fill="both", expand=True)

        self._draw(width, height, message, show_hint)

        self._w.bind("<Button-1>", lambda _evt: self.destroy())
        self._w.bind("<Escape>", lambda _evt: self.destroy())

        self._animate_in_started = False
        self._animate_out_started = False
        self._anim_start_ms = 0
        self._anim_after_id: Optional[str] = None

        self._start_in_animation()

        if style.hold_ms is not None:
            self._w.after(style.hold_ms, self._start_out_animation)

    def _draw(self, width: int, height: int, message: str, show_hint: bool) -> None:
        r = self._style.radius
        bx = self._style.border_width
        ox, oy = self._style.shadow_offset

        shadow_color = self._style.shadow
        shadow_stipple = "gray50"
        if self._style.shadow_alpha <= 0.12:
            shadow_stipple = "gray25"
        elif self._style.shadow_alpha <= 0.20:
            shadow_stipple = "gray50"
        elif self._style.shadow_alpha <= 0.30:
            shadow_stipple = "gray75"
        else:
            shadow_stipple = ""

        if shadow_stipple:
            self._canvas.create_polygon(
                _rounded_rect_points(bx + ox, bx + oy, width - bx + ox, height - bx + oy, r),
                fill=shadow_color,
                outline="",
                smooth=True,
                splinesteps=36,
                stipple=shadow_stipple,
            )

        self._canvas.create_polygon(
            _rounded_rect_points(bx, bx, width - bx, height - bx, r),
            fill=self._bg,
            outline=self._style.border,
            width=bx,
            smooth=True,
            splinesteps=36,
        )

        self._canvas.create_text(14, 12, text="❤", fill="#ff4d6d", font=self._style.deco_font, anchor="nw")
        self._canvas.create_text(width - 14, height - 12, text="❤", fill="#ff4d6d", font=self._style.deco_font, anchor="se")

        if show_hint:
            self._canvas.create_text(
                width // 2,
                12,
                text="按 ESC 退出",
                fill="#ff7b93",
                font=self._style.hint_font,
                anchor="n",
            )

        self._canvas.create_text(
            width // 2,
            height // 2 + 2,
            text=message,
            fill=self._style.fg,
            font=self._style.font,
            anchor="center",
        )

    def _now_ms(self) -> int:
        return int(self._root.tk.call("after", "info"))

    def _start_in_animation(self) -> None:
        if self._animate_in_started:
            return
        self._animate_in_started = True
        self._anim_start_ms = self._root.winfo_fpixels("1i")  # stable init
        self._anim_start_time = self._root.winfo_toplevel().tk.call("clock", "milliseconds")
        self._tick_in()

    def _tick_in(self) -> None:
        if self._animate_out_started:
            return
        now = int(self._root.tk.call("clock", "milliseconds"))
        elapsed = max(0, now - int(self._anim_start_time))
        dur = max(1, self._style.fade_in_ms)
        t = min(1.0, elapsed / dur)
        eased = 1 - (1 - t) * (1 - t)

        alpha = self._style.window_alpha * eased
        self._safe_set_alpha(alpha)

        dy = int(round(self._style.float_px * (1 - eased)))
        self._w.geometry(f"+{self._target_x}+{self._target_y + dy}")

        if t < 1.0:
            self._anim_after_id = self._w.after(16, self._tick_in)
        else:
            self._safe_set_alpha(self._style.window_alpha)
            self._w.geometry(f"+{self._target_x}+{self._target_y}")

    def _start_out_animation(self) -> None:
        if self._animate_out_started:
            return
        self._animate_out_started = True
        if self._anim_after_id is not None:
            try:
                self._w.after_cancel(self._anim_after_id)
            except tk.TclError:
                pass
            self._anim_after_id = None
        self._anim_start_time = self._root.winfo_toplevel().tk.call("clock", "milliseconds")
        self._tick_out()

    def _tick_out(self) -> None:
        now = int(self._root.tk.call("clock", "milliseconds"))
        elapsed = max(0, now - int(self._anim_start_time))
        dur = max(1, self._style.fade_out_ms)
        t = min(1.0, elapsed / dur)
        eased = t * t

        alpha = self._style.window_alpha * (1 - eased)
        self._safe_set_alpha(alpha)

        dy = int(round(self._style.float_px * eased))
        self._w.geometry(f"+{self._target_x}+{self._target_y - dy}")

        if t < 1.0:
            self._anim_after_id = self._w.after(16, self._tick_out)
        else:
            self.destroy()

    def _safe_set_alpha(self, alpha: float) -> None:
        try:
            self._w.attributes("-alpha", max(0.0, min(1.0, alpha)))
        except tk.TclError:
            pass

    def destroy(self) -> None:
        try:
            if not self._animate_out_started and self._style.fade_out_ms > 0:
                self._start_out_animation()
                return
        except tk.TclError:
            pass

        try:
            self._w.destroy()
        except tk.TclError:
            pass
        self._on_destroy(self)


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
        style: Optional[PopupStyle] = None,
        topmost: bool = True,
    ) -> None:
        self.root = root
        self.messages = list(messages)
        self.colors = list(colors)
        self.count_heart = count_heart
        self.count_random = count_random
        self.interval_ms = interval_ms
        self.style = style or PopupStyle()
        self.width, self.height = self.style.size
        self.topmost = topmost

        self._alive: List[PopupWindow] = []
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

        bg = _pick(self.colors)

        def _on_destroy(p: PopupWindow) -> None:
            try:
                self._alive.remove(p)
            except ValueError:
                pass

        p = PopupWindow(
            self.root,
            x=x,
            y=y,
            width=self.width,
            height=self.height,
            message=_pick(self.messages),
            bg=bg,
            style=self.style,
            topmost=self.topmost,
            show_hint=(self._spawned == 0),
            on_destroy=_on_destroy,
        )
        self._alive.append(p)
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

    style = PopupStyle(
        size=(240, 70),
        fg="#2c2c2c",
        font=("Microsoft YaHei", 13, "bold"),
        radius=14,
        border="#ffb3c6",
        border_width=2,
        shadow_alpha=0.16,
        shadow_offset=(3, 4),
        window_alpha=0.94,
        fade_in_ms=220,
        fade_out_ms=260,
        hold_ms=None,
        float_px=10,
    )

    popups = PopupManager(
        root,
        messages,
        colors,
        count_heart=180,
        count_random=160,
        interval_ms=25,
        style=style,
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
