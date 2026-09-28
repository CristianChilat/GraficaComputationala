"""Lab 1: keyboard turtle drawing (criteria 5–10)."""

from __future__ import annotations

import math
import random
import turtle
from typing import Tuple


Rect = Tuple[float, float, float, float]  # left, bottom, right, top


def point_in_rect(x: float, y: float, left: float, bottom: float, right: float, top: float) -> bool:
    return left <= x <= right and bottom <= y <= top


def _orientation(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> float:
    return (by - ay) * (cx - bx) - (bx - ax) * (cy - by)


def _on_segment(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> bool:
    return (
        min(ax, bx) <= cx <= max(ax, bx)
        and min(ay, by) <= cy <= max(ay, by)
    )


def _segments_intersect(
    ax: float, ay: float, bx: float, by: float,
    cx: float, cy: float, dx: float, dy: float,
) -> bool:
    o1 = _orientation(ax, ay, bx, by, cx, cy)
    o2 = _orientation(ax, ay, bx, by, dx, dy)
    o3 = _orientation(cx, cy, dx, dy, ax, ay)
    o4 = _orientation(cx, cy, dx, dy, bx, by)

    if o1 == 0 and _on_segment(ax, ay, bx, by, cx, cy):
        return True
    if o2 == 0 and _on_segment(ax, ay, bx, by, dx, dy):
        return True
    if o3 == 0 and _on_segment(cx, cy, dx, dy, ax, ay):
        return True
    if o4 == 0 and _on_segment(cx, cy, dx, dy, bx, by):
        return True

    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def segment_hits_rect(
    x1: float, y1: float, x2: float, y2: float,
    left: float, bottom: float, right: float, top: float,
) -> bool:
    if point_in_rect(x1, y1, left, bottom, right, top):
        return True
    if point_in_rect(x2, y2, left, bottom, right, top):
        return True
    corners = (
        (left, bottom, right, bottom),
        (right, bottom, right, top),
        (right, top, left, top),
        (left, top, left, bottom),
    )
    for ax, ay, bx, by in corners:
        if _segments_intersect(x1, y1, x2, y2, ax, ay, bx, by):
            return True
    return False


def clamp_step_inside(
    x: float, y: float, nx: float, ny: float,
    half_w: float, half_h: float,
) -> Tuple[float, float]:
    return (
        max(-half_w, min(half_w, nx)),
        max(-half_h, min(half_h, ny)),
    )


WINDOW_W = 800
WINDOW_H = 600
STEP = 20
TURN = 90
COLORS = ["black", "red", "blue", "green", "orange"]
MIN_PEN = 1
MAX_PEN = 20
OBSTACLE_W = 80
OBSTACLE_H = 120


class DrawingApp:
    def __init__(self) -> None:
        self.half_w = WINDOW_W // 2 - 20
        self.half_h = WINDOW_H // 2 - 40
        self.drawing = False
        self.color_index = 0
        self.pen_size = 2
        self.score = 0
        self.error_msg = ""
        self.obstacle_rect: Rect = (0.0, 0.0, 0.0, 0.0)

        self.screen = turtle.Screen()
        self.screen.setup(WINDOW_W, WINDOW_H)
        self.screen.title("Lab 1 — Turtle Drawing")
        self.screen.tracer(0)

        self.artist = turtle.Turtle()
        self.artist.speed(0)
        self.artist.penup()

        self.wall = turtle.Turtle()
        self.wall.hideturtle()
        self.wall.speed(0)
        self.wall.penup()

        self.hud = turtle.Turtle()
        self.hud.hideturtle()
        self.hud.speed(0)
        self.hud.penup()

        self.border = turtle.Turtle()
        self.border.hideturtle()
        self.border.speed(0)
        self.border.penup()

        self._draw_border()
        self._place_obstacle()
        self._apply_pen_look()
        self._bind_keys()
        self._update_hud()
        self.screen.update()

    def _bind_keys(self) -> None:
        s = self.screen
        s.listen()
        for key in ("Up", "w", "W"):
            s.onkey(self.forward, key)
        for key in ("Down", "s", "S"):
            s.onkey(self.backward, key)
        for key in ("Left", "a", "A"):
            s.onkey(self.turn_left, key)
        for key in ("Right", "d", "D"):
            s.onkey(self.turn_right, key)
        s.onkey(self.toggle_pen, "space")
        s.onkey(self.clear_drawing, "c")
        s.onkey(self.clear_drawing, "C")
        s.onkey(self.reset, "r")
        s.onkey(self.reset, "R")
        s.onkey(self.pen_thicker, "plus")
        s.onkey(self.pen_thicker, "equal")
        s.onkey(self.pen_thinner, "minus")
        for i, _ in enumerate(COLORS, start=1):
            s.onkey(lambda idx=i - 1: self.set_color(idx), str(i))

    def _apply_pen_look(self) -> None:
        self.artist.pensize(self.pen_size)
        self.artist.pencolor(COLORS[self.color_index])
        if self.drawing:
            self.artist.color(COLORS[self.color_index], "red")
            self.artist.shape("turtle")
            self.artist.shapesize(1.3, 1.3)
            try:
                self.artist.fillcolor("red")
            except turtle.TurtleGraphicsError:
                pass
        else:
            self.artist.shape("turtle")
            self.artist.shapesize(1.0, 1.0)
            self.artist.color("gray")
            self.artist.pencolor(COLORS[self.color_index])

    def _update_hud(self) -> None:
        self.hud.clear()
        self.hud.goto(-WINDOW_W // 2 + 20, WINDOW_H // 2 - 30)
        tail = "down" if self.drawing else "up"
        self.hud.write(
            f"Score: {self.score}  |  Tail: {tail}  |  "
            f"Color: {COLORS[self.color_index]}  |  Size: {self.pen_size}",
            font=("Arial", 12, "normal"),
        )
        if self.error_msg:
            self.hud.goto(-WINDOW_W // 2 + 20, WINDOW_H // 2 - 50)
            self.hud.pencolor("red")
            self.hud.write(self.error_msg, font=("Arial", 12, "bold"))
            self.hud.pencolor("black")
        self.hud.goto(-WINDOW_W // 2 + 20, -WINDOW_H // 2 + 20)
        self.hud.write(
            "WASD/Arrows move·turn | Space pen | C clear | 1-5 color | +/- size | R reset wall",
            font=("Arial", 10, "normal"),
        )

    def _draw_border(self) -> None:
        left, bottom = -self.half_w, -self.half_h
        right, top = self.half_w, self.half_h
        self.border.clear()
        self.border.pensize(3)
        self.border.pencolor("green")
        self.border.goto(left, bottom)
        self.border.pendown()
        self.border.goto(right, bottom)
        self.border.goto(right, top)
        self.border.goto(left, top)
        self.border.goto(left, bottom)
        self.border.penup()

    def _draw_obstacle(self) -> None:
        left, bottom, right, top = self.obstacle_rect
        self.wall.clear()
        self.wall.fillcolor("red")
        self.wall.pencolor("black")
        self.wall.goto(left, bottom)
        self.wall.pendown()
        self.wall.begin_fill()
        self.wall.goto(right, bottom)
        self.wall.goto(right, top)
        self.wall.goto(left, top)
        self.wall.goto(left, bottom)
        self.wall.end_fill()
        self.wall.penup()

    def _place_obstacle(self) -> None:
        margin = 40
        max_left = self.half_w - OBSTACLE_W - margin
        max_bottom = self.half_h - OBSTACLE_H - margin
        for _ in range(50):
            left = random.randint(int(-max_left), int(max_left))
            bottom = random.randint(int(-max_bottom), int(max_bottom))
            right = left + OBSTACLE_W
            top = bottom + OBSTACLE_H
            # keep clear of origin spawn
            if point_in_rect(0, 0, left - STEP, bottom - STEP, right + STEP, top + STEP):
                continue
            self.obstacle_rect = (float(left), float(bottom), float(right), float(top))
            self._draw_obstacle()
            return
        self.obstacle_rect = (100.0, -60.0, 100.0 + OBSTACLE_W, -60.0 + OBSTACLE_H)
        self._draw_obstacle()

    def _try_move(self, distance: float) -> None:
        x, y = self.artist.position()
        heading = self.artist.heading()
        rad = math.radians(heading)
        nx = x + distance * math.cos(rad)
        ny = y + distance * math.sin(rad)
        cx, cy = clamp_step_inside(x, y, nx, ny, self.half_w, self.half_h)
        if (cx, cy) == (x, y):
            self.screen.update()
            return

        left, bottom, right, top = self.obstacle_rect
        hits_wall = segment_hits_rect(x, y, cx, cy, left, bottom, right, top)
        if hits_wall and self.drawing:
            self.error_msg = "Error! Tail hit the wall — score reset. Press R for a new wall."
            self.score = 0
            self._update_hud()
            self.screen.update()
            return
        if hits_wall:
            self.screen.update()
            return

        self.error_msg = ""
        if self.drawing:
            self.artist.pendown()
            self.score += 1
        else:
            self.artist.penup()
        self.artist.goto(cx, cy)
        self._update_hud()
        self.screen.update()

    def forward(self) -> None:
        self._try_move(STEP)

    def backward(self) -> None:
        self._try_move(-STEP)

    def turn_left(self) -> None:
        self.artist.left(TURN)
        self.screen.update()

    def turn_right(self) -> None:
        self.artist.right(TURN)
        self.screen.update()

    def toggle_pen(self) -> None:
        self.drawing = not self.drawing
        if self.drawing:
            self.artist.pendown()
        else:
            self.artist.penup()
        self._apply_pen_look()
        self._update_hud()
        self.screen.update()

    def clear_drawing(self) -> None:
        self.artist.clear()
        self.error_msg = ""
        self._draw_obstacle()
        self._update_hud()
        self.screen.update()

    def set_color(self, index: int) -> None:
        self.color_index = index
        self._apply_pen_look()
        self._update_hud()
        self.screen.update()

    def pen_thicker(self) -> None:
        self.pen_size = min(MAX_PEN, self.pen_size + 1)
        self.artist.pensize(self.pen_size)
        self._update_hud()
        self.screen.update()

    def pen_thinner(self) -> None:
        self.pen_size = max(MIN_PEN, self.pen_size - 1)
        self.artist.pensize(self.pen_size)
        self._update_hud()
        self.screen.update()

    def reset(self) -> None:
        self.artist.penup()
        self.artist.clear()
        self.artist.home()
        self.drawing = False
        self.score = 0
        self.error_msg = ""
        self._place_obstacle()
        self._apply_pen_look()
        self._update_hud()
        self.screen.update()


def main() -> None:
    app = DrawingApp()
    app.screen.mainloop()


if __name__ == "__main__":
    main()