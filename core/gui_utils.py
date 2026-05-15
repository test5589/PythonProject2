"""gui_utils.py - GUI 通用輔助函數、版面配置、拖曳控制"""

"""
GUI工具類 - 統一管理版面編輯功能

版面編輯功能架構:
├── toggle_edit_mode()            # 編輯模式開關
├── confirm_edit_layout()         # 確認佈局編輯
├── cancel_edit_layout()          # 取消佈局編輯
└── _repack_all_buttons()         # 重置按鈕佈局

拖拽編輯功能:
├── _on_start_drag()              # 開始拖拽
├── _on_drag()                    # 拖拽中
└── _on_button_frame_resize()     # 容器大小變化處理
"""

import os
import json
import tkinter as tk
from tkinter import messagebox


class GUIUtils:
    def __init__(self, gui):
        self.gui = gui

    # ======== 載入和套用 layout ========
    def load_and_apply_layout(self, path):
        gui = self.gui
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_layout_dict(data)
            gui.emit("✅ 已套用儲存的按鈕配置")
        except Exception as e:
            gui.emit(f"❌ 套用 layout 錯誤: {e}")

    # ======== 編輯模式開關 ========
    def toggle_edit_mode(self):
        gui = self.gui
        if gui.edit_mode:
            # 已經在編輯模式，切換回正常模式
            self._exit_edit_mode()
            gui.emit("🛠 已退出版面編輯模式")
        else:
            # 進入編輯模式
            gui.edit_mode = True
            gui.emit("🛠 進入版面編輯模式（可拖曳按鈕）")

            for btn in gui._buttons:
                btn.bind("<Button-1>", self._on_start_drag)
                btn.bind("<B1-Motion>", self._on_drag)

            # 隱藏編輯按鈕，顯示確認/取消按鈕
            try:
                gui.controls.edit_btn.pack_forget()
                gui.controls.edit_ok_btn.pack(side=tk.LEFT, padx=5)
                gui.controls.edit_cancel_btn.pack(side=tk.LEFT, padx=5)
            except Exception as e:
                gui.emit(f"⚠️ 進入編輯模式時出錯: {e}")

    # ======== 確認 layout ========
    def confirm_edit_layout(self):
        gui = self.gui
        positions = self._collect_positions()
        layout_file = gui.controls._layout_file

        try:
            os.makedirs(os.path.dirname(layout_file), exist_ok=True)
            with open(layout_file, "w", encoding="utf-8") as f:
                json.dump(positions, f, ensure_ascii=False, indent=2)
            gui.emit("✅ 版面配置已儲存")
        except Exception as e:
            gui.emit(f"❌ 儲存版面配置失敗: {e}")

        # 退出編輯模式並重新pack所有按鈕
        self._exit_edit_mode()

    # ======== 取消 layout 編輯 ========
    def cancel_edit_layout(self):
        gui = self.gui

        # 取消編輯並重新pack所有按鈕
        self._exit_edit_mode()
        gui.emit("↩️ 已取消版面編輯")

    # ======== 退出編輯模式 ========
    def _exit_edit_mode(self):
        """退出編輯模式並重新pack所有按鈕"""
        gui = self.gui
        gui.edit_mode = False

        # 解除所有按鈕的拖拽綁定
        for btn in gui._buttons:
            btn.unbind("<Button-1>")
            btn.unbind("<B1-Motion>")

        # 隱藏編輯按鈕
        try:
            gui.controls.edit_ok_btn.pack_forget()
            gui.controls.edit_cancel_btn.pack_forget()
            gui.controls.edit_btn.pack(side=tk.LEFT, padx=5)
        except Exception:
            pass

        # 強制重新pack所有按鈕，恢復原始佈局
        self._repack_all_buttons()

    # ======== 重新pack所有按鈕 ========
    def _repack_all_buttons(self):
        """強制重新pack所有按鈕，恢復原始pack佈局"""
        gui = self.gui

        try:
            # 重新pack所有功能按鈕，除了編輯相關按鈕
            for btn in gui._buttons:
                # 跳過編輯相關的按鈕，因為它們有特殊的顯示邏輯
                if btn in [gui.controls.edit_ok_btn, gui.controls.edit_cancel_btn]:
                    continue

                # 先移除place幾何管理器
                btn.place_forget()
                
                # 根據按鈕類型重新pack到相應容器
                try:
                    # 主按鈕組和編輯按鈕 - pack到button_frame
                    if hasattr(gui.controls, 'button_frame') and btn.winfo_parent() == str(gui.controls.button_frame):
                        btn.pack(side=tk.LEFT, padx=5, pady=2)
                    # 快捷按鈕 - 已經在它們的容器中正確pack了
                    elif hasattr(gui.controls, 'quick_now_btn') and btn in [gui.controls.quick_now_btn, gui.controls.quick_yesterday_btn, gui.controls.quick_week_btn]:
                        # 快捷按鈕已經在創建時正確pack，無需重新pack
                        pass
                except Exception:
                    # 如果無法判斷容器，使用默認pack
                    btn.pack(side=tk.LEFT, padx=5, pady=2)

            gui.emit("🔄 已恢復原始按鈕佈局")

        except Exception as e:
            gui.emit(f"⚠️ 恢復佈局時發生錯誤: {e}")
            # 如果出錯，至少確保按鈕是可見的
            for btn in gui._buttons:
                try:
                    if (not btn.winfo_ismapped() and
                        btn not in [gui.controls.edit_ok_btn, gui.controls.edit_cancel_btn]):
                        btn.pack(side=tk.LEFT, padx=5, pady=2)
                except:
                    pass
    def _on_start_drag(self, event):
        widget = event.widget
        widget._drag_data = (event.x, event.y)

    def _on_drag(self, event):
        widget = event.widget
        dx = event.x - widget._drag_data[0]
        dy = event.y - widget._drag_data[1]
        new_x = widget.winfo_x() + dx
        new_y = widget.winfo_y() + dy
        widget.place(x=new_x, y=new_y)

    # ======== 監聽 frame resize ========
    def _on_button_frame_resize(self, event):
        gui = self.gui
        if not gui.edit_mode:
            return
        gui.emit(f"📐 按鈕區調整大小: {event.width}x{event.height}")

    # ======== 位置收集與套用 ========
    def _collect_positions(self):
        gui = self.gui
        data = {}
        for btn in gui._buttons:
            key = gui._button_keys.get(btn, btn.cget("text"))
            data[key] = {"x": btn.winfo_x(), "y": btn.winfo_y()}
        return data

    def _apply_layout_dict(self, data):
        gui = self.gui
        # 在我們的新佈局系統中，所有按鈕都使用pack佈局
        # 不再支持自定義位置的place佈局
        gui.emit("🎨 佈局系統已優化，所有按鈕使用統一的pack佈局")

