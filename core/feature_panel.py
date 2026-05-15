"""
feature_panel.py - 進階功能面板統一管理
使用模組化結構管理進階功能
"""

from .panels.advanced_panel import AdvancedPanel

class FeaturePanel:
    """進階功能面板統一管理器"""
    
    def __init__(self, root, main_gui):
        # 使用新的模組化結構
        self.advanced_panel = AdvancedPanel(root, main_gui)
        
        # 保持向後相容性
        self.main_gui = main_gui
        self.query_win = None
        
        # 複製屬性以保持向後相容性
        self.panel = self.advanced_panel.panel
        self.symbol_combobox = self.advanced_panel.symbol_combobox
        
    # 向後相容性方法
    def _on_symbol_select(self, event):
        """貨幣對選擇事件處理"""
        return self.advanced_panel._on_symbol_select(event)
        
    def open_db(self):
        """開啟資料庫"""
        return self.advanced_panel.open_database()
        
    def query_data(self):
        """查詢資料"""
        return self.advanced_panel.open_query_window()
        
    def analyze_data(self):
        """分析資料"""
        return self.advanced_panel.open_analyze_window()
