"""
gui_controls.py - GUI控制項統一管理
使用模組化結構管理所有GUI控制項
"""

from .gui.controls_base import ControlsBase
from .gui.datetime_controls import DateTimeControls  
from .gui.button_controls import ButtonControls
from .gui.quick_controls import QuickControls

class GUIControls:
    """GUI控制項統一管理器"""
    
    def __init__(self, gui):
        self.gui = gui
        root = gui.root
        
        # 初始化各個控制項管理器
        self.controls_base = ControlsBase(gui)
        self.datetime_controls = DateTimeControls(gui)
        self.button_controls = ButtonControls(gui)
        self.quick_controls = QuickControls(gui, self.datetime_controls)
        
        # 創建控制項
        self._create_controls(root)
        
    def _create_controls(self, root):
        """創建所有控制項"""
        self.gui._layout_groups = {}
        control_frame = self.controls_base.create_main_control_frame(root)
        self.datetime_controls.create_datetime_selectors(control_frame)
        quick_buttons = self.quick_controls.create_quick_buttons(control_frame)
        quick_button_keys = self.quick_controls.get_quick_button_keys()
        self.controls_base.create_config_controls(control_frame)
        button_frame = self.button_controls.create_button_frame(root)
        main_buttons = self.button_controls.create_main_buttons(button_frame)
        edit_buttons = self.button_controls.create_edit_buttons(button_frame)
        self.button_controls.setup_button_lists()
        self.button_controls.add_quick_buttons_to_list(quick_buttons)
        self.button_controls.add_quick_buttons_to_keys(quick_button_keys)
        self._copy_attributes_to_main()
        self.controls_base.apply_saved_layout()
        self.button_controls.setup_button_frame_bindings()
        self.controls_base.create_backfill_controls(root)
        self.controls_base.create_weight_controls(root)
        
    def _copy_attributes_to_main(self):
        """複製屬性到主類"""
        # 時間控制項
        for attr in ['sy', 'sM', 'sd', 'sh', 'su', 'ss', 'ey', 'eM', 'ed', 'eh', 'eu', 'es', 'category_entry', 'symbol_entry']:
            if hasattr(self.datetime_controls, attr):
                setattr(self, attr, getattr(self.datetime_controls, attr))
        # 按鈕控制項
        for attr in ['button_frame', 'fetch_btn', 'ws_start_btn', 'ws_stop_btn', 'edit_btn', 'edit_ok_btn', 'edit_cancel_btn']:
            if hasattr(self.button_controls, attr):
                setattr(self, attr, getattr(self.button_controls, attr))
        # 快捷按鈕
        for attr in ['quick_now_btn', 'quick_yesterday_btn', 'quick_week_btn']:
            if hasattr(self.quick_controls, attr):
                setattr(self, attr, getattr(self.quick_controls, attr))
        # 基礎控制項
        for attr in ['backfill_interval_combo', 'backfill_control_frame', 'backfill_btn', 'pause_resume_btn', 'stop_backfill_btn', 'weight_control_frame', 'weight_status_btn', 'reset_weight_btn', 'test_weight_btn', 'stop_weight_test_btn']:
            if hasattr(self.controls_base, attr):
                setattr(self, attr, getattr(self.controls_base, attr))
        self._layout_file = self.controls_base._layout_file
        
    # 向後相容性方法
    def toggle_edit_mode(self): self.button_controls.toggle_edit_mode()
    def _confirm_edit(self): self.button_controls.confirm_edit()
    def _cancel_edit(self): self.button_controls.cancel_edit()
    def show_weight_status(self): self.controls_base.show_weight_status()
    def reset_all_weights(self): self.controls_base.reset_all_weights()
    def test_weight_system(self): self.controls_base.test_weight_system()
    def stop_weight_test(self): self.controls_base.stop_weight_test()
    def _convert_interval_to_api_format(self, interval_display: str) -> str: return self.controls_base.convert_interval_to_api_format(interval_display)
    def _apply_saved_layout(self): self.controls_base.apply_saved_layout()
    def _set_current_time(self): self.datetime_controls.set_current_time()
    def _set_yesterday_to_today(self): self.datetime_controls.set_yesterday_to_today()
    def _set_last_week(self): self.datetime_controls.set_last_week()
    def _add_one_hour(self): self.datetime_controls.add_one_hour()
    def _add_one_day(self): self.datetime_controls.add_one_day()
