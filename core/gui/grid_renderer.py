"""grid_renderer.py - 專責處理 MainGUI 的 Grid 畫面渲染與更新邏輯"""

import tkinter as tk


class GridRenderer:
    """負責管理 MainGUI 的 grid_lines 與重繪邏輯的輔助類別。

    說明：
    - 所有實際狀態仍掛在 gui 物件上（grid_lines、_dirty_rows、_render_pending 等），
      這個類別只負責封裝演算法，讓 gui_main.py 比較精簡。
    """

    def __init__(self, gui):
        self.gui = gui

    # ===== 初始化與基本寫入 =====
    def init_grid(self):
        gui = self.gui
        gui.grid_lines = [" " * gui.grid_cols for _ in range(gui.grid_rows)]
        gui._dirty_rows = set(range(gui.grid_rows))

    def set_row(self, row_index, text):
        gui = self.gui
        if not (0 <= row_index < gui.grid_rows):
            return
        if text is None:
            text = ""
        if len(text) > gui.grid_cols:
            line = text[: gui.grid_cols]
        else:
            line = text.ljust(gui.grid_cols)
        gui.grid_lines[row_index] = line
        if hasattr(gui, "_dirty_rows"):
            gui._dirty_rows.add(row_index)

    def set_segment(self, row_index, col_start, text):
        gui = self.gui
        if not (0 <= row_index < gui.grid_rows):
            return
        if text is None:
            return
        if col_start < 0 or col_start >= gui.grid_cols:
            return
        row = gui.grid_lines[row_index]
        if len(row) < gui.grid_cols:
            row = row.ljust(gui.grid_cols)
        chars = list(row)
        for i, ch in enumerate(text):
            cidx = col_start + i
            if cidx >= gui.grid_cols:
                break
            chars[cidx] = ch
        gui.grid_lines[row_index] = "".join(chars)
        if hasattr(gui, "_dirty_rows"):
            gui._dirty_rows.add(row_index)

    # ===== 實際渲染到 Text 控制項 =====
    def render_grid(self):
        gui = self.gui
        if not hasattr(gui, "log_text"):
            return

        try:
            y_start, _ = gui.log_text.yview()
        except Exception:
            y_start = None

        dirty_rows = getattr(gui, "_dirty_rows", None)
        if not dirty_rows:
            return

        gui.log_text.configure(state="normal")

        try:
            total_lines = int(gui.log_text.index("end-1c").split(".")[0])
        except Exception:
            total_lines = 0

        if total_lines < gui.grid_rows:
            for _ in range(gui.grid_rows - total_lines):
                gui.log_text.insert(tk.END, "\n")

        for idx in sorted(dirty_rows):
            if not (0 <= idx < gui.grid_rows):
                continue
            row = idx + 1
            start_index = f"{row}.0"
            end_index = f"{row}.end"
            line = gui.grid_lines[idx]
            gui.log_text.delete(start_index, end_index)
            gui.log_text.insert(start_index, line)

        gui._dirty_rows.clear()

        if y_start is not None:
            try:
                gui.log_text.yview_moveto(y_start)
            except Exception:
                pass

        gui.log_text.configure(state="disabled")

    # ===== 重繪排程 =====
    def schedule_render(self):
        gui = self.gui
        if getattr(gui, "_render_pending", False):
            return
        gui._render_pending = True
        try:
            gui.root.after(gui._render_interval_ms, self.flush_render)
        except Exception:
            gui._render_pending = False

    def flush_render(self):
        gui = self.gui
        gui._render_pending = False
        self.render_grid()
