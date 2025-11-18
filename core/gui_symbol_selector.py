"""
gui_symbol_selector.py - 貨幣對選擇器
支持多選、分類顯示、搜索過濾
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.trading_config import TradingConfig


class SymbolSelectorDialog:
    """貨幣對選擇器對話框"""
    
    def __init__(self, parent, category="crypto", current_selection=None):
        """
        初始化選擇器
        
        Args:
            parent: 父窗口
            category: 資產分類 ('crypto' 或 'stock')
            current_selection: 當前已選擇的貨幣對列表
        """
        self.parent = parent
        self.category = category.lower()
        self.result = None  # 用戶選擇的結果
        self.current_selection = current_selection or []
        
        # 創建對話框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"選擇回補貨幣對 - {self.get_category_name()}")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 獲取可選貨幣對
        self.available_symbols = self.get_available_symbols()
        
        # 創建UI
        self.create_ui()
        
        # 載入當前選擇
        self.load_current_selection()
        
        # 居中顯示
        self.center_dialog()
    
    def get_category_name(self):
        """獲取分類名稱"""
        return "加密貨幣" if self.category == "crypto" else "股票"
    
    def get_available_symbols(self):
        """獲取可用的貨幣對列表"""
        if self.category == "crypto":
            return TradingConfig.CRYPTO_SYMBOLS
        elif self.category == "stock":
            return TradingConfig.STOCK_SYMBOLS
        else:
            return []
    
    def create_ui(self):
        """創建UI組件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 頂部控制區
        self.create_top_controls(main_frame)
        
        # 中間列表區
        self.create_symbol_list(main_frame)
        
        # 底部按鈕區
        self.create_bottom_buttons(main_frame)
    
    def create_top_controls(self, parent):
        """創建頂部控制區"""
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 搜索框
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="🔍 搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 選中數量顯示
        self.count_label = ttk.Label(top_frame, text="已選: 0/15", foreground="blue")
        self.count_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 快速操作按鈕
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(button_frame, text="🗹 全選", command=self.select_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="☐ 清除", command=self.clear_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="↻ 反選", command=self.invert_selection, width=8).pack(side=tk.LEFT, padx=2)
    
    def create_symbol_list(self, parent):
        """創建貨幣對列表"""
        # 列表框架
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 說明標籤
        info_text = f"💡 提示：最多選擇 {TradingConfig.MAX_BACKFILL_SYMBOLS} 個貨幣對進行回補"
        ttk.Label(list_frame, text=info_text, foreground="gray").pack(anchor=tk.W, pady=(0, 5))
        
        # 創建帶滾動條的Canvas
        canvas_frame = ttk.Frame(list_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(canvas_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas
        self.canvas = tk.Canvas(canvas_frame, yscrollcommand=scrollbar.set, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)
        
        # 內部框架（放置 Checkbutton）
        self.checkbutton_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.checkbutton_frame, anchor='nw')
        
        # 綁定滾輪事件（只綁定在此 Canvas，避免視窗關閉後仍收到全域事件）
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        # 創建 Checkbutton 列表
        self.checkbox_vars = {}
        self.checkbuttons = {}
        self.create_checkbuttons()
        
        # 更新滾動區域
        self.checkbutton_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # 綁定窗口大小變化
        self.canvas.bind('<Configure>', self.on_canvas_configure)
    
    def create_checkbuttons(self):
        """創建所有 Checkbutton"""
        # 按分類顯示
        current_category = None
        row = 0
        col = 0
        max_cols = 4  # 每行顯示4個
        
        for symbol in self.available_symbols:
            # 提取分類（從註釋中）
            category = self.get_symbol_category(symbol)
            
            # 如果是新分類，添加分類標題
            if category != current_category:
                if col > 0:  # 如果不是第一行，換行
                    row += 1
                    col = 0
                    
                # 分類標題（跨越所有列）
                category_label = ttk.Label(
                    self.checkbutton_frame, 
                    text=category, 
                    font=('Arial', 9, 'bold'),
                    foreground='#0066cc'
                )
                category_label.grid(row=row, column=0, columnspan=max_cols, sticky=tk.W, pady=(10, 5), padx=5)
                row += 1
                col = 0
                current_category = category
            
            # 創建 Checkbox
            var = tk.BooleanVar(value=False)
            self.checkbox_vars[symbol] = var
            
            # 簡化顯示名稱（移除USDT）
            display_name = symbol.replace('USDT', '')
            
            cb = ttk.Checkbutton(
                self.checkbutton_frame,
                text=display_name,
                variable=var,
                command=self.on_selection_change
            )
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.checkbuttons[symbol] = cb
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def get_symbol_category(self, symbol):
        """獲取貨幣對的分類"""
        # 根據 CRYPTO_SYMBOLS 中的註釋分類
        if symbol in ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "TRXUSDT", "LINKUSDT", "AVAXUSDT"]:
            return "💎 主流幣"
        elif symbol in ["WBETHUSDT"]:
            return "🔒 質押代幣"
        elif symbol in ["WBTCUSDT", "WBTUSDT", "LBTCUSDT", "FBTCUSDT", "CLBTCUSDT", "SOLVBTCUSDT"]:
            return "🎁 Wrapped代幣"
        elif symbol in ["ARBUSDT", "OPUSDT", "STRKUSDT", "SEIUSDT", "SUIUSDT", "APTUSDT", "NEARUSDT", "ICPUSDT", "INJUSDT", "ATOMUSDT", "DOTUSDT", "XLMUSDT", "VETUSDT", "ALGOUSDT", "FILUSDT", "HBARUSDT", "QNTUSDT", "KASUSDT", "XTZUSDT", "STXUSDT", "TONUSDT", "XDCUSDT"]:
            return "⛓️ Layer1/2"
        elif symbol in ["UNIUSDT", "AAVEUSDT", "CRVUSDT", "CAKEUSDT", "GRTUSDT", "JUPUSDT", "JUPSOLUSDT", "JITOSOLUSDT", "JLPUSDT"]:
            return "🏦 DeFi"
        elif symbol in ["SHIBUSDT", "PEPEUSDT", "BONKUSDT", "WLDUSDT", "FLRUSDT"]:
            return "🐸 Meme"
        elif symbol in ["TAOUSDT", "FETUSDT", "ENAUSDT", "VIRTUALUSDT", "HYPEUSDT", "TIAUSDT"]:
            return "🤖 AI/新概念"
        elif symbol in ["OKBUSDT", "BGBUSDT", "HTXUSDT", "KCSUSDT", "GTUSDT", "LEOUSDT", "CROUSDT"]:
            return "🏢 交易所幣"
        elif symbol in ["XMRUSDT", "ZECUSDT", "DASHUSDT"]:
            return "🔐 隱私幣"
        elif symbol in ["LTCUSDT", "BCHUSDT", "ETCUSDT"]:
            return "📜 老牌幣"
        elif symbol in ["XAUTUSDT", "PAXGUSDT"]:
            return "🏆 貴金屬"
        else:
            return "🌟 其他"
    
    def load_current_selection(self):
        """載入當前選擇"""
        for symbol in self.current_selection:
            if symbol in self.checkbox_vars:
                self.checkbox_vars[symbol].set(True)
        self.update_count()
    
    def on_selection_change(self):
        """選擇改變時的回調"""
        selected_count = sum(1 for var in self.checkbox_vars.values() if var.get())
        
        # 檢查是否超過限制
        if selected_count > TradingConfig.MAX_BACKFILL_SYMBOLS:
            messagebox.showwarning(
                "選擇超限",
                f"最多只能選擇 {TradingConfig.MAX_BACKFILL_SYMBOLS} 個貨幣對！\n"
                f"請取消一些選擇。"
            )
            # 取消最後一個選擇
            for symbol, var in self.checkbox_vars.items():
                if var.get():
                    var.set(False)
                    break
        
        self.update_count()
    
    def update_count(self):
        """更新選中數量顯示"""
        selected_count = sum(1 for var in self.checkbox_vars.values() if var.get())
        self.count_label.config(
            text=f"已選: {selected_count}/{TradingConfig.MAX_BACKFILL_SYMBOLS}",
            foreground="red" if selected_count > TradingConfig.MAX_BACKFILL_SYMBOLS else "blue"
        )
    
    def select_all(self):
        """全選"""
        # 獲取當前可見的（未被搜索過濾的）貨幣對
        visible_symbols = [symbol for symbol in self.available_symbols if self.checkbuttons[symbol].winfo_ismapped()]
        
        # 計算可以選擇多少個
        can_select = min(len(visible_symbols), TradingConfig.MAX_BACKFILL_SYMBOLS)
        
        if len(visible_symbols) > TradingConfig.MAX_BACKFILL_SYMBOLS:
            messagebox.showinfo(
                "全選提示",
                f"當前可見 {len(visible_symbols)} 個貨幣對，\n"
                f"但最多只能選擇 {TradingConfig.MAX_BACKFILL_SYMBOLS} 個。\n\n"
                f"將選擇前 {can_select} 個。"
            )
        
        # 全選前 can_select 個
        selected = 0
        for symbol in visible_symbols:
            if selected < can_select:
                self.checkbox_vars[symbol].set(True)
                selected += 1
            else:
                self.checkbox_vars[symbol].set(False)
        
        self.update_count()
    
    def clear_all(self):
        """清除所有選擇"""
        for var in self.checkbox_vars.values():
            var.set(False)
        self.update_count()
    
    def invert_selection(self):
        """反選"""
        current_selected = sum(1 for var in self.checkbox_vars.values() if var.get())
        visible_symbols = [symbol for symbol in self.available_symbols if self.checkbuttons[symbol].winfo_ismapped()]
        
        # 計算反選後的數量
        will_be_selected = len(visible_symbols) - current_selected
        
        if will_be_selected > TradingConfig.MAX_BACKFILL_SYMBOLS:
            messagebox.showwarning(
                "反選超限",
                f"反選後將有 {will_be_selected} 個貨幣對被選中，\n"
                f"超過限制 {TradingConfig.MAX_BACKFILL_SYMBOLS} 個！\n\n"
                f"請先清除一些選擇後再反選。"
            )
            return
        
        for symbol in visible_symbols:
            var = self.checkbox_vars[symbol]
            var.set(not var.get())
        
        self.update_count()
    
    def on_search_change(self, *args):
        """搜索框內容改變"""
        search_text = self.search_var.get().upper()
        
        for symbol, cb in self.checkbuttons.items():
            if search_text in symbol.upper():
                cb.grid()  # 顯示
            else:
                cb.grid_remove()  # 隱藏
        
        # 更新滾動區域
        self.checkbutton_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def on_mousewheel(self, event):
        """滾輪事件"""
        try:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            # Canvas 可能已被銷毀或 Tk 已關閉（對話框關閉後的殘留事件），忽略即可
            pass
    
    def on_canvas_configure(self, event):
        """Canvas大小改變"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def center_dialog(self):
        """居中對話框"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_bottom_buttons(self, parent):
        """創建底部按鈕"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="✓ 確定", command=self.on_confirm, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✗ 取消", command=self.on_cancel, width=15).pack(side=tk.RIGHT)
    
    def on_confirm(self):
        """確認選擇"""
        selected = [symbol for symbol, var in self.checkbox_vars.items() if var.get()]
        
        if not selected:
            messagebox.showwarning("未選擇", "請至少選擇一個貨幣對！")
            return
        
        if len(selected) > TradingConfig.MAX_BACKFILL_SYMBOLS:
            messagebox.showerror(
                "選擇超限",
                f"選擇了 {len(selected)} 個貨幣對，\n"
                f"超過限制 {TradingConfig.MAX_BACKFILL_SYMBOLS} 個！"
            )
            return
        
        self.result = selected
        try:
            # 關閉前解除滾輪綁定，避免銷毀後還有殘留事件
            self.canvas.unbind("<MouseWheel>")
        except Exception:
            pass
        self.dialog.destroy()
    
    def on_cancel(self):
        """取消選擇"""
        self.result = None
        try:
            # 關閉前解除滾輪綁定，避免銷毀後還有殘留事件
            self.canvas.unbind("<MouseWheel>")
        except Exception:
            pass
        self.dialog.destroy()
    
    def get_result(self):
        """獲取選擇結果"""
        self.dialog.wait_window()
        return self.result


def select_symbols_for_backfill(parent, category="crypto", current_selection=None):
    """
    打開貨幣對選擇器並返回用戶選擇
    
    Args:
        parent: 父窗口
        category: 資產分類 ('crypto' 或 'stock')
        current_selection: 當前已選擇的貨幣對列表
    
    Returns:
        list: 用戶選擇的貨幣對列表，如果取消則返回 None
    """
    selector = SymbolSelectorDialog(parent, category, current_selection)
    return selector.get_result()
