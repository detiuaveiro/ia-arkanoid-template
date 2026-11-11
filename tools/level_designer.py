"""Level designer tool and map format converter for Arkanoid."""

import argparse
import json
import math
import os
import sys
from collections import deque
from typing import Any

from consts import (
    BRICK_HEIGHT,
    BRICK_WIDTH,
    GRID_COLS,
    GRID_GAP_X,
    GRID_GAP_Y,
    GRID_MARGIN_X,
    GRID_MARGIN_Y,
    GRID_ROWS,
)

CHAR_TO_TYPE: dict[str, str] = {
    "R": "red",
    "1": "red",
    "B": "blue",
    "2": "blue",
    "G": "green",
    "3": "green",
    "Y": "yellow",
    "4": "yellow",
    "M": "metal",
    "X": "metal",
    "0": "metal",
}

TYPE_TO_CHAR: dict[str, str] = {
    "red": "R",
    "blue": "B",
    "green": "G",
    "yellow": "Y",
    "metal": "M",
}

TYPE_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (191, 97, 106),       # #BF616A
    "blue": (129, 161, 193),     # #81A1C1
    "green": (163, 190, 140),    # #A3BE8C
    "yellow": (235, 203, 139),   # #EBCB8B
    "metal": (216, 222, 233),    # #D8DEE9
}


def ascii_to_map(
    name: str,
    lines: list[str],
    cols: int = GRID_COLS,
    margin_x: float = GRID_MARGIN_X,
    margin_y: float = GRID_MARGIN_Y,
    gap_x: float = GRID_GAP_X,
    gap_y: float = GRID_GAP_Y,
) -> dict[str, Any]:
    """Convert ASCII art representation into a simplified grid-based map dictionary."""
    bricks: list[dict[str, Any]] = []
    for row_idx, line in enumerate(lines):
        line = line.rstrip("\r\n")
        for col_idx in range(min(len(line), cols)):
            char = line[col_idx]
            if char in CHAR_TO_TYPE:
                b_type = CHAR_TO_TYPE[char]
                bricks.append({"row": row_idx, "col": col_idx, "type": b_type})

    return {
        "name": name,
        "grid": {
            "cols": cols,
            "rows": max(len(lines), GRID_ROWS),
            "margin_x": margin_x,
            "margin_y": margin_y,
            "gap_x": gap_x,
            "gap_y": gap_y,
        },
        "brick_width": BRICK_WIDTH,
        "brick_height": BRICK_HEIGHT,
        "bricks": bricks,
    }


def map_to_ascii(map_data: dict[str, Any]) -> str:
    """Render a map dictionary into an ASCII diagram string."""
    grid = map_data.get("grid", {})
    cols = int(grid.get("cols", GRID_COLS))
    rows = int(grid.get("rows", GRID_ROWS))

    char_grid = [["." for _ in range(cols)] for _ in range(rows)]
    margin_x = float(grid.get("margin_x", GRID_MARGIN_X))
    margin_y = float(grid.get("margin_y", GRID_MARGIN_Y))
    gap_x = float(grid.get("gap_x", GRID_GAP_X))
    gap_y = float(grid.get("gap_y", GRID_GAP_Y))
    b_w = float(map_data.get("brick_width", BRICK_WIDTH))
    b_h = float(map_data.get("brick_height", BRICK_HEIGHT))

    for b in map_data.get("bricks", []):
        if "row" in b and "col" in b:
            r, c = int(b["row"]), int(b["col"])
        else:
            x, y = float(b.get("x", 0.0)), float(b.get("y", 0.0))
            c = int(round((x - margin_x) / (b_w + gap_x)))
            r = int(round((y - margin_y) / (b_h + gap_y)))

        if 0 <= r < rows and 0 <= c < cols:
            b_type = str(b.get("type", "red"))
            char_grid[r][c] = TYPE_TO_CHAR.get(b_type, "?")

    return "\n".join("".join(row) for row in char_grid)


def fit_axis(values: list[float], size: float, margin: float, gap: float) -> tuple[float, float]:
    """Return a (margin, gap) that puts every coordinate on the grid: the defaults if they fit, else the map's own."""
    values = sorted(set(values))
    steps = [b - a for a, b in zip(values, values[1:], strict=False)]
    if values and any((v - margin) % (size + gap) for v in values):
        margin = values[0]
        if steps and min(steps) >= size:
            gap = min(steps) - size
    return margin, gap


def convert_map_to_grid(map_data: dict[str, Any]) -> dict[str, Any]:
    """Convert an existing map (with legacy canvas coordinates) to simplified grid format."""
    grid = map_data.get("grid", {})
    cols = int(grid.get("cols", GRID_COLS))
    margin_x = float(grid.get("margin_x", GRID_MARGIN_X))
    margin_y = float(grid.get("margin_y", GRID_MARGIN_Y))
    gap_x = float(grid.get("gap_x", GRID_GAP_X))
    gap_y = float(grid.get("gap_y", GRID_GAP_Y))
    b_w = float(map_data.get("brick_width", BRICK_WIDTH))
    b_h = float(map_data.get("brick_height", BRICK_HEIGHT))
    if "grid" not in map_data:
        coords = [b for b in map_data.get("bricks", []) if "x" in b and "y" in b]
        margin_x, gap_x = fit_axis([float(b["x"]) for b in coords], b_w, margin_x, gap_x)
        margin_y, gap_y = fit_axis([float(b["y"]) for b in coords], b_h, margin_y, gap_y)

    simplified_bricks: list[dict[str, Any]] = []
    max_row = 0
    for b in map_data.get("bricks", []):
        if "row" in b and "col" in b:
            r, c = int(b["row"]), int(b["col"])
        else:
            x, y = float(b.get("x", 0.0)), float(b.get("y", 0.0))
            c = int(round((x - margin_x) / (b_w + gap_x)))
            r = int(round((y - margin_y) / (b_h + gap_y)))
            if (margin_x + c * (b_w + gap_x), margin_y + r * (b_h + gap_y)) != (x, y):
                raise ValueError(f"Brick at ({x}, {y}) does not fit a regular grid")
        max_row = max(max_row, r)
        b_type = str(b.get("type", "red"))
        simplified_bricks.append({"row": r, "col": c, "type": b_type})

    return {
        "name": map_data.get("name", "Custom Stage"),
        "grid": {
            "cols": cols,
            "rows": max(max_row + 1, GRID_ROWS),
            "margin_x": margin_x,
            "margin_y": margin_y,
            "gap_x": gap_x,
            "gap_y": gap_y,
        },
        "brick_width": b_w,
        "brick_height": b_h,
        "bricks": simplified_bricks,
    }


def validate_map_winnable(map_data_or_path: dict[str, Any] | str) -> list[tuple[float, float]]:
    """Return coordinates of any unreachable destructible bricks."""
    from server.config import load_config, load_map_file
    cfg = load_config()
    if isinstance(map_data_or_path, str):
        map_data = load_map_file(map_data_or_path)
    else:
        map_data = map_data_or_path

    bricks = map_data.get("bricks", [])
    step = 4.0
    r = cfg.ball.radius
    w, h = cfg.bricks.width, cfg.bricks.height
    x0, x1 = r, cfg.screen.width - r
    y0, y1 = cfg.screen.ceiling_y + r, cfg.paddle.y - r
    cols, rows = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1

    def dist(cx: float, cy: float, b: dict[str, Any]) -> float:
        bx = float(b["x"])
        by = float(b["y"])
        return math.hypot(max(bx - cx, 0.0, cx - bx - w), max(by - cy, 0.0, cy - by - h))

    def blocked(cx: float, cy: float, live: list[dict[str, Any]]) -> bool:
        return any(dist(cx, cy, b) < r for b in live)

    live = list(bricks)
    while any(not b.get("indestructible", False) for b in live):
        seen: set[tuple[int, int]] = set()
        queue: deque[tuple[int, int]] = deque((c, rows - 1) for c in range(cols))
        seen.update(queue)
        while queue:
            c, rw = queue.popleft()
            for nc, nr in ((c + 1, rw), (c - 1, rw), (c, rw + 1), (c, rw - 1)):
                if (
                    0 <= nc < cols
                    and 0 <= nr < rows
                    and (nc, nr) not in seen
                    and not blocked(x0 + nc * step, y0 + nr * step, live)
                ):
                    seen.add((nc, nr))
                    queue.append((nc, nr))
        hit = []
        for b in live:
            if b.get("indestructible", False):
                continue
            if any(dist(x0 + c * step, y0 + rw * step, b) <= r + step for c, rw in seen):
                hit.append(b)
        if not hit:
            break
        live = [b for b in live if b not in hit]
    return [(float(b["x"]), float(b["y"])) for b in live if not b.get("indestructible", False)]


def run_gui(output_path: str = "maps/custom_level.json", initial_map: str | None = None) -> None:
    """Launch interactive Pygame level designer GUI."""
    import pygame
    from server.config import load_map_file

    pygame.init()
    screen_w, screen_h = 600, 800
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Arkanoid Level Designer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 14)
    big_font = pygame.font.SysFont("monospace", 16, bold=True)

    cols = GRID_COLS
    rows = 12
    margin_x = GRID_MARGIN_X
    margin_y = GRID_MARGIN_Y
    gap_x = GRID_GAP_X
    gap_y = GRID_GAP_Y
    b_w = BRICK_WIDTH
    b_h = BRICK_HEIGHT

    # Grid storage: [row][col] -> brick_type or None
    grid_cells: list[list[str | None]] = [[None for _ in range(cols)] for _ in range(rows)]
    level_name = "Custom Level"

    if initial_map and os.path.exists(initial_map):
        data = convert_map_to_grid(load_map_file(initial_map))
        level_name = str(data.get("name", "Custom Level"))
        grid = data["grid"]
        margin_x, margin_y, gap_x, gap_y = grid["margin_x"], grid["margin_y"], grid["gap_x"], grid["gap_y"]
        for b in data["bricks"]:
            r, c = int(b["row"]), int(b["col"])
            if 0 <= r < rows and 0 <= c < cols:
                grid_cells[r][c] = b.get("type", "red")

    palette = ["red", "blue", "green", "yellow", "metal", None]
    palette_labels = ["1:Red", "2:Blue", "3:Green", "4:Yellow", "M:Metal", "0:Clear"]
    selected_tool = "red"
    status_msg = "Controls: 1-4/M tool | Left click/drag to paint | S: Save | R: Check | Q: Quit"
    status_color = (216, 222, 233)

    painting = False
    erasing = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_1:
                    selected_tool = "red"
                elif event.key == pygame.K_2:
                    selected_tool = "blue"
                elif event.key == pygame.K_3:
                    selected_tool = "green"
                elif event.key == pygame.K_4:
                    selected_tool = "yellow"
                elif event.key in (pygame.K_m, pygame.K_5):
                    selected_tool = "metal"
                elif event.key in (pygame.K_0, pygame.K_SPACE, pygame.K_DELETE):
                    selected_tool = None
                elif event.key == pygame.K_s:
                    # Save map
                    bricks: list[dict[str, Any]] = []
                    for r in range(rows):
                        for c in range(cols):
                            bt = grid_cells[r][c]
                            if bt:
                                bricks.append({"row": r, "col": c, "type": bt})
                    out_data = {
                        "name": level_name,
                        "grid": {
                            "cols": cols,
                            "rows": rows,
                            "margin_x": margin_x,
                            "margin_y": margin_y,
                            "gap_x": gap_x,
                            "gap_y": gap_y,
                        },
                        "brick_width": b_w,
                        "brick_height": b_h,
                        "bricks": bricks,
                    }
                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(out_data, f, indent=2)
                    status_msg = f"Saved {len(bricks)} bricks to {output_path}!"
                    status_color = (163, 190, 140)
                elif event.key == pygame.K_r:
                    # Validate winnability
                    from server.config import load_map_file
                    bricks_raw = []
                    for r in range(rows):
                        for c in range(cols):
                            bt = grid_cells[r][c]
                            if bt:
                                bricks_raw.append({"row": r, "col": c, "type": bt})
                    test_map = {
                        "name": level_name,
                        "grid": {"margin_x": margin_x, "margin_y": margin_y, "gap_x": gap_x, "gap_y": gap_y},
                        "brick_width": b_w,
                        "brick_height": b_h,
                        "bricks": bricks_raw,
                    }
                    # Populate canvas coordinates for validator
                    for b in test_map["bricks"]:
                        b["x"] = margin_x + b["col"] * (b_w + gap_x)
                        b["y"] = margin_y + b["row"] * (b_h + gap_y)
                        b["indestructible"] = (b["type"] == "metal")
                    unreachable = validate_map_winnable(test_map)
                    if unreachable:
                        status_msg = f"WARNING: {len(unreachable)} unreachable bricks!"
                        status_color = (191, 97, 106)
                    else:
                        status_msg = "SUCCESS: All destructible bricks reachable!"
                        status_color = (163, 190, 140)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    painting = True
                elif event.button == 3:
                    erasing = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    painting = False
                elif event.button == 3:
                    erasing = False

        # Handle painting
        if painting or erasing:
            mx, my = pygame.mouse.get_pos()
            for r in range(rows):
                for c in range(cols):
                    bx = margin_x + c * (b_w + gap_x)
                    by = margin_y + r * (b_h + gap_y)
                    if bx <= mx <= bx + b_w and by <= my <= by + b_h:
                        grid_cells[r][c] = None if erasing else selected_tool

        # Draw frame
        screen.fill((46, 52, 64))  # nord0 dark background

        # Header info
        header_surf = big_font.render(f"ARKANOID LEVEL DESIGNER - {level_name}", True, (236, 239, 244))
        screen.blit(header_surf, (margin_x, 20))

        # Palette buttons at top
        px = margin_x
        py = 55
        for idx, (p_type, p_label) in enumerate(zip(palette, palette_labels)):
            btn_rect = pygame.Rect(px, py, 75, 24)
            color = TYPE_COLORS.get(p_type or "", (76, 86, 106))
            pygame.draw.rect(screen, color, btn_rect, border_radius=3)
            if selected_tool == p_type:
                pygame.draw.rect(screen, (236, 239, 244), btn_rect, 2, border_radius=3)
            lbl = font.render(p_label, True, (46, 52, 64) if p_type else (236, 239, 244))
            screen.blit(lbl, (px + 4, py + 4))
            px += 85

        # Arena ceiling line
        pygame.draw.line(screen, (76, 86, 106), (0, 82), (screen_w, 82), 1)

        # Draw grid cells
        for r in range(rows):
            for c in range(cols):
                bx = margin_x + c * (b_w + gap_x)
                by = margin_y + r * (b_h + gap_y)
                rect = pygame.Rect(int(bx), int(by), int(b_w), int(b_h))
                b_type = grid_cells[r][c]
                if b_type:
                    pygame.draw.rect(screen, TYPE_COLORS[b_type], rect, border_radius=2)
                    pygame.draw.rect(screen, (236, 239, 244), rect, 1, border_radius=2)
                else:
                    pygame.draw.rect(screen, (59, 66, 82), rect, 1, border_radius=2)

        # Status line at bottom
        status_surf = font.render(status_msg, True, status_color)
        screen.blit(status_surf, (margin_x, screen_h - 40))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def build_parser() -> argparse.ArgumentParser:
    """Create the command line parser for level designer."""
    parser = argparse.ArgumentParser(description="Arkanoid Level Designer & Map Utility")
    parser.add_argument("-o", "--output", type=str, default="maps/custom_level.json", help="Output map path")
    parser.add_argument("-i", "--input", type=str, default=None, help="Input map path (load/convert/validate)")
    parser.add_argument("-a", "--ascii", type=str, default=None, help="Generate from ASCII text file")
    parser.add_argument("-c", "--convert", action="store_true", help="Convert legacy x/y map to simplified grid JSON")
    parser.add_argument("-v", "--validate", action="store_true", help="Validate that all destructible bricks are reachable")
    parser.add_argument("-g", "--gui", action="store_true", help="Launch interactive Pygame level designer GUI")
    return parser


def main() -> None:
    """CLI entry point for level designer."""
    parser = build_parser()
    args = parser.parse_args()

    if args.validate and args.input:
        unreachable = validate_map_winnable(args.input)
        if unreachable:
            print(f"FAILED: {len(unreachable)} unreachable destructible bricks found in {args.input}: {unreachable}")
            sys.exit(1)
        else:
            print(f"SUCCESS: {args.input} is valid and winnable!")
            return

    if args.ascii:
        with open(args.ascii, encoding="utf-8") as f:
            lines = f.readlines()
        map_data = ascii_to_map("ASCII Level", lines)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(map_data, f, indent=2)
        print(f"Generated {args.output} from ASCII art.")
        return

    if args.convert and args.input:
        from server.config import load_map_file
        data = load_map_file(args.input)
        converted = convert_map_to_grid(data)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(converted, f, indent=2)
        print(f"Converted {args.input} -> {args.output}")
        return

    if args.gui or len(sys.argv) == 1:
        run_gui(output_path=args.output, initial_map=args.input)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
