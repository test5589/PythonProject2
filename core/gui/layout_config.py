"""layout_config.py - GUI 版面與尺寸統一定義

集中管理各區塊的 padding / 高度 / 寬度，
讓需要調整版面時只修改這個檔案即可。

【使用說明】
- 一般來說「數值變大 = 空隙變大 / 區塊往下或往右移動」。
- 想讓區塊靠近一點，就把對應的 PADY / PADX 調小；想拉開距離就調大。
- 建議一次只改少量數值，改完重開 GUI 看效果。
"""

# ╔══════════════════════════════════════════════╗
# ║ ① 主控制區（整體上方控制列容器）           ║
# ╚══════════════════════════════════════════════╝
# MAIN_CONTROL_PADY：整個「時間 + 資產 + 快捷 + K線時間段」這一大塊距離上方/下方區域的垂直距離
#   調大：整塊控制區往下移、與上面的日誌區距離變大
#   調小：整塊控制區往上貼近日誌區
MAIN_CONTROL_PADY = 0

# MAIN_CONTROL_PADX：主控制區左右邊界的空隙
#   調大：整塊控制區往中間擠（左右留白變大）
#   調小：控制區更貼近視窗邊緣
MAIN_CONTROL_PADX = 0

# ╔══════════════════════════════════════════════╗
# ║ ② 時間選擇區（起始/結束時間）               ║
# ╚══════════════════════════════════════════════╝
# TIME_FRAME_PADY：整個「起始/結束時間」區塊，相對於上下其它區域的垂直距離
#   調大：時間區與其它控制區距離變大
#   調小：時間區與其它控制區更靠近
TIME_FRAME_PADY = 0

# TIME_FRAME_PADX：時間區整體的左右邊界空隙
#   調大：時間區內容整體往中間擠
#   調小：時間區更貼近左右邊界
TIME_FRAME_PADX = 0

# DATETIME_START_LABELFRAME_PADDING：起始時間 LabelFrame 內部文字與邊框的留白
#   調大：起始時間框看起來更「鬆」，框變胖一點
#   調小：起始時間框內容更貼近邊框
DATETIME_START_LABELFRAME_PADDING = 0

# DATETIME_START_LABELFRAME_PADY：起始時間框與時間區內部其他元素的垂直距離
#   目前是與結束時間框在同一排，主要影響這一排在 time_frame 裡的上下位置
DATETIME_START_LABELFRAME_PADY = 0

# DATETIME_END_LABELFRAME_PADDING：結束時間 LabelFrame 內部文字與邊框的留白
#   調大：結束時間框變得比較鬆、比較高
#   調小：內容更緊貼 LabelFrame 邊線
DATETIME_END_LABELFRAME_PADDING = 0

# DATETIME_END_LABELFRAME_PADY：結束時間框在 time_frame 裡的上下位置
#   通常和起始時間框保持一樣就好，要整排上移/下移可一起調整
DATETIME_END_LABELFRAME_PADY = 0

# DATETIME_END_LABELFRAME_PADX：起始時間框與結束時間框之間的水平間距
#   調大：兩個框中間空隙變大
#   調小：兩個框更靠近
DATETIME_END_LABELFRAME_PADX = 0

# ╔══════════════════════════════════════════════╗
# ║ ③ 資產分類與交易對區                         ║
# ╚══════════════════════════════════════════════╝
# ASSET_FRAME_PADY：整個「資產分類 + 交易對」這一排，與上下其他區域的垂直距離
#   調大：這一排與時間區 / 快捷按鈕的距離變大
#   調小：這一排與其它區塊更靠近
ASSET_FRAME_PADY = 0

# ASSET_FRAME_PADX：資產分類這一排左右邊界的空隙
#   調大：整排內容往中間擠
#   調小：整排內容更貼近左右邊
ASSET_FRAME_PADX = 0

# ╔══════════════════════════════════════════════╗
# ║ ④ 快捷時間按鈕區（現在 / 昨天→今天 / 最近一週） ║
# ╚══════════════════════════════════════════════╝
# QUICK_BUTTONS_FRAME_PADY：整個快捷按鈕區與上下其他區域的距離
#   調大：快捷按鈕與資產/時間/其他控制區拉開更多空間
#   調小：快捷按鈕貼近上下區塊
QUICK_BUTTONS_FRAME_PADY = 0

# QUICK_BUTTONS_FRAME_PADX：快捷按鈕區左右邊界空隙
#   調大：快捷按鈕列整體往中間擠
#   調小：更貼近左右邊
QUICK_BUTTONS_FRAME_PADX = 0

# QUICK_BUTTONS_PADY：每顆快捷按鈕自身的上下 padding（視覺上的「高度感」）
#   調大：按鈕看起來更厚、更高
#   調小：按鈕比較扁
QUICK_BUTTONS_PADY = 0

# ╔══════════════════════════════════════════════╗
# ║ ⑤ K線時間段配置區                            ║
# ╚══════════════════════════════════════════════╝
# CONFIG_FRAME_PADY：K線時間段那一排與上下區域的距離
#   調大：與快捷按鈕/後面按鈕列的距離變大
#   調小：各區塊更緊密
CONFIG_FRAME_PADY = 0

# CONFIG_FRAME_PADX：K線時間段這一排左右邊界空隙
#   調大：整排往中間擠
#   調小：靠近左右邊
CONFIG_FRAME_PADX = 10

# ╔══════════════════════════════════════════════╗
# ║ ⑥ 主 LOG 日誌視窗（顯示所有訊息的文字框）    ║
# ╚══════════════════════════════════════════════╝
# LOG_TEXT_PADX：LOG 視窗外側左右邊界的空隙（pack padx）
#   調大：LOG 整塊往中間擠，左右留白變大
#   調小：LOG 更貼近視窗左右邊
LOG_TEXT_PADX = 10

# LOG_TEXT_PADY：LOG 視窗外側上下邊界的空隙（pack pady）
#   調大：LOG 與上下區塊之間空隙變大（看起來更鬆）
#   調小：LOG 更貼近上下區塊，空白區域變少
LOG_TEXT_PADY = 0

# LOG_TEXT_HEIGHT：LOG 視窗顯示的文字行數高度
#   調大：LOG 視窗變高，可以同時看到比較多行訊息
#   調小：LOG 視窗變矮，下面的控制區會有更多空間
LOG_TEXT_HEIGHT = 25

# LOG_TEXT_WIDTH：LOG 視窗每行大約可以容納的字元數（配合等寬字型）
#   調大：LOG 視窗變寬，每行可以顯示更多字
#   調小：LOG 視窗變窄
LOG_TEXT_WIDTH = 90

# LOG_TEXT_FONT_FAMILY：LOG 視窗使用的字型（建議用等寬字型，例如 Consolas / Courier New）
LOG_TEXT_FONT_FAMILY = "Consolas"

# LOG_TEXT_FONT_SIZE：LOG 視窗字體大小
#   調大：字變大、可讀性好但可見行數會感覺變少
#   調小：字變小、同一高度內可以塞更多內容
LOG_TEXT_FONT_SIZE = 10

# ╔══════════════════════════════════════════════╗
# ║ ⑦ 主要功能按鈕列（抓取 / 監控 / 編輯版面）    ║
# ╚══════════════════════════════════════════════╝
# BUTTON_FRAME_PADY：整排主要按鈕（抓取 / 啟動監控 / 停止監控 / 編輯版面）
#   與上下區塊的垂直距離
#   調大：按鈕列與上方 K線時間段 / 下方回補控制之間空隙變大
#   調小：按鈕列更貼近上下區塊
BUTTON_FRAME_PADY = 5

# BUTTON_FRAME_PADX：主要按鈕列左右邊界空隙
#   調大：整排按鈕往中間擠
#   調小：按鈕更靠近左右邊
BUTTON_FRAME_PADX = 0

# BUTTON_FRAME_HEIGHT：主要按鈕列的固定高度
#   調大：這一整排區域變高，按鈕周圍留白變多
#   調小：整排變扁（注意太小可能讓文字看起來擠）
BUTTON_FRAME_HEIGHT = 30

# ╔══════════════════════════════════════════════╗
# ║ ⑧ 回補控制區                                 ║
# ╚══════════════════════════════════════════════╝
# BACKFILL_FRAME_PADY：整個「回補資料控制」LabelFrame 與上下區塊的距離
#   調大：回補控制區與按鈕列、API 權重區距離變大
#   調小：回補控制區更靠近其它區塊
BACKFILL_FRAME_PADY = 5

# BACKFILL_FRAME_PADX：回補控制區左右邊界空隙
#   調大：整個回補控制區往中間擠
#   調小：貼近左右邊
BACKFILL_FRAME_PADX = 0

# BACKFILL_BUTTON_PADY：回補區內每顆按鈕的上下 padding（高度感）
#   調大：按鈕看起來更厚
#   調小：按鈕看起來較扁
BACKFILL_BUTTON_PADY = 5

# BACKFILL_BUTTON_PADX：回補區內按鈕左右間距
#   調大：三顆按鈕之間距離變大
#   調小：按鈕更靠近
BACKFILL_BUTTON_PADX = 0

# ╔══════════════════════════════════════════════╗
# ║ ⑨ API 權重控制區                             ║
# ╚══════════════════════════════════════════════╝
# WEIGHT_FRAME_PADY：整個「API 權重評估系統」LabelFrame 與上下區塊的距離
#   調大：權重區與回補控制 / 下方其他元件之間空隙變大
#   調小：權重區更緊貼其他區塊
WEIGHT_FRAME_PADY = 0

# WEIGHT_FRAME_PADX：權重控制區左右邊界空隙
#   調大：整個權重控制區往中間擠
#   調小：靠近左右邊
WEIGHT_FRAME_PADX = 0

# WEIGHT_BUTTON_PADY：權重區內按鈕的上下 padding
#   調大：按鈕更高、更有空間
#   調小：按鈕較扁
WEIGHT_BUTTON_PADY = 5

# WEIGHT_BUTTON_PADX：權重區內按鈕之間的左右間距
#   調大：按鈕彼此之間空隙變大
#   調小：按鈕排得更緊密
WEIGHT_BUTTON_PADX = 0
