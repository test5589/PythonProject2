"""gui_backfill.py - 回補功能模組，包含回補資料、覆蓋確認對話框、暫停/停止控制"""

import time
import threading
from datetime import datetime, timezone, timedelta
from tkinter import ttk, messagebox, Toplevel, StringVar
from config.trading_config import TradingConfig
from modules.utils.backfill.backfill_data import smart_backfill, slow_background_seconds, fetch_and_insert
from modules.utils.backfill.backfill_state import backfill_state_manager
from modules.utils.exceptions import BackfillInsertError, BackfillConfigurationError
from modules.utils.data.backfill_monitoring_utils import validate_symbol_binding
from core.async_backfill_runner import AsyncBackfillRunner


class GUIBackfill:
    def __init__(self, gui):
        self.gui = gui

    # ======== 開始回補 ========
    def backfill_data(self):
        gui = self.gui
        
        # 0. 強制切換到模板 C（回補摘要模板）
        if getattr(gui, "current_template", None) != "C":
            if hasattr(gui, "set_monitor_template"):
                gui.set_monitor_template("C")
                gui.log("💡 已自動切換至【模板 C】顯示回補任務摘要")

        # 檢查是否有暫停中的回補任務
        state = backfill_state_manager.get_state()
        if state.is_running and state.is_paused:
            result = messagebox.askyesno(
                "偵測到暫停的回補任務",
                "目前有一個暫停中的回補任務。\n\n"
                "要開始新的回補，將自動停止舊任務。\n\n"
                "是否繼續？\n\n"
                "（點「是」將停止舊任務並開始新回補）\n"
                "（點「否」將取消操作）"
            )
            if result:
                # 用戶同意，自動停止舊任務
                backfill_state_manager.stop_backfill()
                # 重置按鈕狀態
                gui.controls.pause_resume_btn.config(state="disabled", text="⏸️ 暫時停止回補")
                gui.controls.stop_backfill_btn.config(state="disabled")
                gui.log("🔄 正在停止暫停中的舊任務...")
                
                # 等待資料庫鎖被釋放（最多10秒）
                from modules.utils.database.data_manager import _db_operation_lock
                wait_start = time.time()
                max_wait = 10  # 最多等待10秒
                
                while time.time() - wait_start < max_wait:
                    # 嘗試獲取鎖（非阻塞）
                    if _db_operation_lock.acquire(blocking=False):
                        # 成功獲取，立即釋放（我們只是測試）
                        _db_operation_lock.release()
                        gui.log("✅ 舊任務已停止，資料庫鎖已釋放")
                        break
                    # 沒獲取到，短暫等待後重試
                    time.sleep(0.5)
                else:
                    # 超時了
                    gui.log("⚠️ 警告：舊任務可能未完全停止（超時10秒）")
                    gui.log("💡 如果下一步出現鎖超時，請重啟GUI")
                
                gui.log("✅ 準備開始新的回補")
            else:
                # 用戶取消
                gui.log("❌ 取消開始新回補")
                return
        elif state.is_running:
            # 如果任務正在運行（非暫停），不允許開始新任務
            messagebox.showwarning(
                "回補任務運行中",
                "目前有回補任務正在運行。\n\n"
                "請先暫停或停止當前任務，\n"
                "然後才能開始新的回補。"
            )
            return
        
        cat = gui.controls.category_entry.get()
        sym = gui.controls.symbol_entry.get().strip()

        if not cat:
            messagebox.showerror("錯誤", "請填寫資產分類")
            return

        try:
            s = datetime(int(gui.controls.sy.get()), int(gui.controls.sM.get()), int(gui.controls.sd.get()),
                         int(gui.controls.sh.get()), int(gui.controls.su.get()), int(gui.controls.ss.get()))
            e = datetime(int(gui.controls.ey.get()), int(gui.controls.eM.get()), int(gui.controls.ed.get()),
                         int(gui.controls.eh.get()), int(gui.controls.eu.get()), int(gui.controls.es.get()))
        except Exception:
            messagebox.showerror("錯誤", "請完整選擇起訖時間")
            return

        taipei = timezone(timedelta(hours=8))
        s_aware = s.replace(tzinfo=taipei)
        e_aware = e.replace(tzinfo=taipei)

        if s_aware >= e_aware:
            messagebox.showerror("錯誤", "起始時間必須早於結束時間")
            return

        mapping = {
            "1分": "1m", "5分": "5m", "15分": "15m", "30分": "30m",
            "1小時": "1h", "4小時": "4h", "8小時": "8h", "12小時": "12h", "24小時": "1d"
        }
        interval = mapping.get(gui.controls.backfill_interval_combo.get() or "1分", "1m")

        # ========== 新增：貨幣對選擇器 ==========
        from core.gui_symbol_selector import select_symbols_for_backfill
        
        # 彈出選擇器讓用戶選擇要回補的貨幣對
        gui.log(f"💡 請選擇要回補的貨幣對（最多{TradingConfig.MAX_BACKFILL_SYMBOLS}個）...")
        
        target_symbols = select_symbols_for_backfill(
            parent=gui.root,
            category=cat,
            current_selection=None  # 可以傳入上次的選擇作為預設
        )
        
        if not target_symbols:
            # 用戶取消了選擇
            gui.log("❌ 已取消回補")
            return
        
        # 驗證選擇的貨幣對是否都是有效的
        try:
            validate_symbol_binding(target_symbols)
        except BackfillConfigurationError as binding_error:
            gui.log(f"❌ 貨幣對驗證失敗: {binding_error}")
            messagebox.showerror("驗證錯誤", str(binding_error))
            return

        gui.log(f"🧩 本次回補貨幣對: {', '.join(target_symbols[:5])}{'...' if len(target_symbols) > 5 else ''} (共{len(target_symbols)}個)")
        gui.log(f"⏳ 開始補齊 {cat} 資料 [間隔: {interval}]...")

        gui.controls.backfill_btn.config(state="disabled")
        gui.controls.pause_resume_btn.config(state="normal")
        gui.controls.stop_backfill_btn.config(state="normal")

        backfill_state_manager.start_backfill(target_symbols[0], interval, len(target_symbols), gui.log)

        # ========== 階段3：使用異步架構 ==========
        # 創建異步回補執行器（完全分離數據處理和GUI更新）
        async_runner = AsyncBackfillRunner(gui)
        
        # 顯示進度條
        gui.progress_bar.show()
        
        # 定義回補工作函數（在子線程中執行）
        def backfill_worker(message_sender):
            """回補工作函數（在子線程運行）"""
            lock_acquired = False
            
            # ========== 追蹤已完成/未完成的貨幣對 ==========
            completed_symbols = []  # 成功完成的貨幣對
            failed_symbols = []     # 失敗的貨幣對
            skipped_symbols = []    # 跳過的貨幣對（停止或錯誤後）
            # 回補風險與摘要：記錄每個貨幣對的狀態與錯誤類型
            backfill_summary = {}   # symbol -> {status, validation, risk, note}
            validation_error_count = 0
            insert_error_count = 0
            other_error_count = 0
            
            try:
                # 獲取全域資料庫操作鎖
                from modules.utils.database.data_manager import _db_operation_lock

                if not _db_operation_lock.acquire(blocking=False):
                    message_sender.info('', "⏳ 資料庫操作進行中，請等待其他操作完成...")
                    if not _db_operation_lock.acquire(timeout=30):
                        message_sender.error('', "無法獲取資料庫鎖，操作超時（30秒）")
                        message_sender.warning('', "可能原因：暫停的任務未完全停止，或其他操作正在進行")
                        message_sender.warning('', "建議：稍後再試，或重啟GUI")
                        backfill_state_manager.set_error("資料庫鎖獲取超時")
                        return
                    message_sender.info('', "✅ 資料庫操作鎖已獲取，繼續回補資料")
                
                lock_acquired = True  # 標記鎖已成功獲取

                try:
                    for index, symbol in enumerate(target_symbols, 1):
                        message_sender.info('', f"📍 進度: {index}/{len(target_symbols)} - 正在處理 {symbol}")
                        try:
                            backfill_state_manager.set_current_target(symbol, interval)
                            symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
                            message_sender.info(symbol, f"📊 正在回補 {symbol}@{interval}，data_source=real")
                            message_sender.info(symbol, 
                                f"⏰ 時間範圍: {s_aware.strftime('%Y-%m-%d %H:%M:%S')} → {e_aware.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)")

                            # 使用 smart_backfill，傳遞 message_sender
                            result = smart_backfill(
                                cat, symbol, interval, 
                                start_time=s_aware, 
                                end_time=e_aware,
                                progress_cb=None,  # 不再使用舊的 progress_cb
                                overwrite_callback=self.overwrite_real_callback,
                                gui_logger=None,  # 不再使用舊的 gui_logger
                                message_sender=message_sender  # 使用新的訊息發送器
                            )

                            if result:
                                message_sender.info(symbol, f"✅ {symbol} 回補成功，資料完整性驗證通過")
                                completed_symbols.append(symbol)  # 記錄成功
                                backfill_summary[symbol] = {
                                    "status": "SUCCESS",
                                    "validation": "PASS",
                                    "risk": "OK",
                                    "note": "回補成功，資料完整性驗證通過",
                                }
                            else:
                                message_sender.warning(symbol, f"⚠️ {symbol} 回補結果未知")
                                failed_symbols.append(symbol)  # 記錄失敗
                                other_error_count += 1
                                backfill_summary[symbol] = {
                                    "status": "FAILED",
                                    "validation": "WARN",
                                    "risk": "結果未知",
                                    "note": "回補結果未知",
                                }
                            
                            state = backfill_state_manager.get_state()
                            if state.is_stopped:
                                message_sender.warning(symbol, "⏹️ 偵測到停止指令，中止剩餘貨幣對")
                                # 記錄剩餘未處理的貨幣對
                                remaining = target_symbols[index:]
                                skipped_symbols.extend(remaining)
                                backfill_summary[symbol] = {
                                    "status": "SKIPPED",
                                    "validation": "WARN",
                                    "risk": "任務被停止",
                                    "note": "回補已被停止",
                                }
                                break

                        except InterruptedError:
                            message_sender.warning(symbol, "⏹️ 回補已被停止")
                            failed_symbols.append(symbol)  # 記錄失敗
                            # 記錄剩餘未處理的貨幣對
                            remaining = target_symbols[index:]
                            skipped_symbols.extend(remaining)
                            backfill_summary[symbol] = {
                                "status": "SKIPPED",
                                "validation": "WARN",
                                "risk": "任務被停止",
                                "note": "回補已被停止",
                            }
                            break
                        except BackfillInsertError as critical:
                            message_sender.error(symbol, f"回補錯誤: {critical}")
                            failed_symbols.append(symbol)  # 記錄失敗
                            insert_error_count += 1
                            backfill_summary[symbol] = {
                                "status": "FAILED",
                                "validation": "WARN",
                                "risk": "插入錯誤",
                                "note": str(critical)[:60],
                            }
                            backfill_state_manager.set_error(str(critical))
                            gui.root.after(0, lambda e=critical: messagebox.showerror("回補錯誤", str(e)))
                            # 記錄剩餘未處理的貨幣對
                            remaining = target_symbols[index:]
                            skipped_symbols.extend(remaining)
                            break
                        except Exception as e:
                            failed_symbols.append(symbol)  # 記錄失敗
                            msg_text = str(e)

                            if "資料驗證失敗" in msg_text or "資料驗證錯誤" in msg_text:
                                validation_error_count += 1
                                risk_label = "驗證錯誤"
                                message_sender.error(symbol, f"資料驗證失敗: {e}")
                                message_sender.warning(symbol, "回補操作已被終止，請檢查資料完整性")
                                
                                # 特別處理：如果是 API 返回0筆（可能是交易對不存在）
                                if "API返回少筆 (0 <" in msg_text or "實際0筆" in msg_text:
                                    message_sender.warning(symbol, f"⚠️ {symbol} 可能不存在或已下架，建議從配置中移除")
                                    message_sender.info('', f"💡 提示：可以在 config/trading_config.py 中移除 {symbol}")
                                    risk_label = "可能不存在或已下架"
                                
                                gui.root.after(0, lambda e=e: messagebox.showerror("資料驗證失敗",
                                    f"資料完整性檢查未通過:\n\n{str(e)}\n\n請檢查:\n• 網路連線是否正常\n• API是否正常運作\n• 時間範圍設定是否正確\n• 貨幣對是否存在"))
                            else:
                                other_error_count += 1
                                risk_label = "其他異常"
                                import traceback
                                message_sender.error(symbol, f"回補錯誤: {e}")
                                message_sender.info(symbol, f"詳細錯誤: {traceback.format_exc()}")
                                backfill_state_manager.set_error(str(e))

                            backfill_summary[symbol] = {
                                "status": "FAILED",
                                "validation": "WARN",
                                "risk": risk_label,
                                "note": msg_text[:60],
                            }
                            
                            # 記錄剩餘未處理的貨幣對
                            remaining = target_symbols[index:]
                            skipped_symbols.extend(remaining)
                            break

                finally:
                    if lock_acquired:
                        _db_operation_lock.release()
                        message_sender.info('', "🔓 資料庫操作鎖已釋放")
                    else:
                        message_sender.warning('', "⚠️ 未獲取鎖，無需釋放")

            finally:
                # ========== 顯示回補摘要 ==========
                message_sender.info('', "")
                message_sender.info('', "=" * 60)
                message_sender.info('', "📊 回補任務摘要")
                message_sender.info('', "=" * 60)
                message_sender.info('', f"🎯 總數: {len(target_symbols)} 個貨幣對")
                message_sender.info('', f"✅ 成功: {len(completed_symbols)} 個")
                message_sender.info('', f"❌ 失敗: {len(failed_symbols)} 個")
                message_sender.info('', f"⏭️ 跳過: {len(skipped_symbols)} 個")
                message_sender.info('', "")
                
                if completed_symbols:
                    message_sender.info('', "✅ 已完成的貨幣對:")
                    for sym in completed_symbols:
                        message_sender.info('', f"   • {sym}")
                    message_sender.info('', "")
                
                if failed_symbols:
                    message_sender.info('', "❌ 失敗的貨幣對:")
                    for sym in failed_symbols:
                        message_sender.info('', f"   • {sym}")
                    message_sender.info('', "")
                
                if skipped_symbols:
                    message_sender.info('', "⏭️ 跳過的貨幣對:")
                    for sym in skipped_symbols:
                        message_sender.info('', f"   • {sym}")
                    message_sender.info('', "")
                
                message_sender.info('', "=" * 60)

                # ========== 將本次回補摘要提供給模板 C 顯示 ==========
                try:
                    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

                    try:
                        finished_at = _dt.now(tz=_tz(_td(hours=8)))
                    except Exception:
                        finished_at = None

                    summary_payload = {
                        "total": len(target_symbols),
                        "success": len(completed_symbols),
                        "failed": len(failed_symbols),
                        "skipped": len(skipped_symbols),
                        "validation_errors": validation_error_count,
                        "insert_errors": insert_error_count,
                        "other_errors": other_error_count,
                        "finished_at": finished_at,
                        "symbols": backfill_summary,
                    }

                    if hasattr(gui, "update_backfill_template"):
                        gui.root.after(0, lambda s=summary_payload: gui.update_backfill_template(s))
                except Exception:
                    # 回補摘要失敗不影響主要流程
                    pass
                
                # 完成時恢復按鈕狀態
                gui.root.after(0, lambda: gui.controls.backfill_btn.config(state="normal"))
                gui.root.after(0, lambda: gui.controls.pause_resume_btn.config(state="disabled"))
                gui.root.after(0, lambda: gui.controls.stop_backfill_btn.config(state="disabled"))
                backfill_state_manager.finish_backfill()
                
                state = backfill_state_manager.get_state()
                success = len(completed_symbols) > 0 and len(failed_symbols) == 0
                
                if success:
                    message_sender.info('', f"✅ 回補任務完成：{len(completed_symbols)}/{len(target_symbols)} 個貨幣對成功")
                elif len(completed_symbols) > 0:
                    message_sender.warning('', f"⚠️ 回補部分完成：{len(completed_symbols)}/{len(target_symbols)} 個成功，{len(failed_symbols)} 個失敗")
                else:
                    message_sender.warning('', "❌ 回補任務失敗：所有貨幣對處理失敗或被停止")
        
        # 啟動異步回補
        async_runner.start_backfill(backfill_worker)

    # ======== 抓取最新 1 分鐘資料（多貨幣對） ========
    def fetch_latest(self):
        gui = self.gui
        
        # 0. 強制切換到模板 B（狀態模板）
        if getattr(gui, "current_template", None) != "B":
            if hasattr(gui, "set_monitor_template"):
                gui.set_monitor_template("B")
                gui.log("💡 已自動切換至【模板 B】顯示批量抓取狀態")
                
        cat = gui.controls.category_entry.get()

        if not cat:
            messagebox.showerror("錯誤", "請填寫資產分類")
            return

        # 計算台灣時間今天 00:00:00 到現在
        taipei_tz = timezone(timedelta(hours=8))
        now_taipei = datetime.now(tz=taipei_tz)
        today_start = now_taipei.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 顯示時間範圍（台灣時間）
        gui.log(f"📥 開始批量抓取所有貨幣對最新 1 分鐘資料...")
        gui.log(f"⏰ 時間範圍: {today_start.strftime('%Y-%m-%d %H:%M:%S')} → {now_taipei.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)")

        def gui_safe_log(msg):
            gui.root.after(0, lambda: gui.log(msg))

        def run():
            try:
                from modules.monitors.multi_symbol_monitor import fetch_all_symbols_latest_minute
                success = fetch_all_symbols_latest_minute(cat, progress_cb=gui_safe_log)

                # 嘗試取得本次「最新 1 分鐘批量抓取」的驗證摘要，更新模板 B
                try:
                    from modules.utils.data.IMPORTANT_VALIDATION_MODULE import get_latest_daily_1m_summary
                    from modules.utils.api.api_client import get_kline_fetch_stats, get_api_retry_stats
                    from modules.utils.logger import get_log_rotation_stats

                    summary = get_latest_daily_1m_summary()
                    fetch_calls, total_rows = get_kline_fetch_stats()
                    conn_retries, timeout_retries = get_api_retry_stats()
                    rotation_count, _ = get_log_rotation_stats()

                    if summary is not None and hasattr(gui, "update_latest_1m_template"):
                        gui.root.after(
                            0,
                            lambda s=summary,
                                   fc=fetch_calls,
                                   tr=total_rows,
                                   cr=conn_retries,
                                   to=timeout_retries,
                                   rc=rotation_count: gui.update_latest_1m_template(s, fc, tr, cr, to, rc),
                        )
                except Exception:
                    # 摘要更新失敗不影響主要批量抓取流程
                    pass

                if success:
                    gui.root.after(0, lambda: gui.log(f"✅ 批量抓取完成 - 時間範圍: {today_start.strftime('%Y-%m-%d')} (UTC+8)"))
                    gui.root.after(0, lambda: gui.log(f"🔍 請檢查上方日誌中各交易對的插入結果"))
                else:
                    gui.root.after(0, lambda: gui.log("❌ 批量抓取失敗"))
            except Exception as e:
                gui.root.after(0, lambda: gui.log(f"❌ 批量抓取錯誤: {e}"))

        threading.Thread(target=run, daemon=True).start()

    # ======== 暫停與恢復 ========
    def toggle_pause_resume(self):
        gui = self.gui
        state = backfill_state_manager.get_state()
        
        if state.is_paused:
            # 當前已暫停，要恢復
            if backfill_state_manager.resume_backfill():
                gui.controls.pause_resume_btn.config(text="⏸️ 暫時停止回補")
                # 恢復時重新禁用開始按鈕（因為任務又在運行了）
                gui.controls.backfill_btn.config(state="disabled")
                gui.log("▶️ 回補資料已恢復")
        else:
            # 當前運行中，要暫停
            if backfill_state_manager.pause_backfill():
                gui.controls.pause_resume_btn.config(text="▶️ 回補資料重新開始")
                # ✨ 關鍵改進：暫停時啟用開始按鈕，允許用戶調整設定後開始新回補
                gui.controls.backfill_btn.config(state="normal")
                gui.log("⏸️ 回補資料已暫停")
                gui.log("💡 暫停期間，您可以：")
                gui.log("   1. 點擊「▶️ 回補資料重新開始」恢復回補")
                gui.log("   2. 點擊「⏹️ 完全停止回補」終止任務")
                gui.log("   3. 調整設定後點擊「開始資料圍捕」開始新的回補")

    # ======== 完全停止 ========
    def stop_backfill(self):
        gui = self.gui
        
        # 立即禁用停止和暫停按鈕，避免重複點擊
        gui.controls.stop_backfill_btn.config(state="disabled")
        gui.controls.pause_resume_btn.config(state="disabled")
        
        # 發送停止信號
        backfill_state_manager.stop_backfill()
        gui.log("⏹️ 已發送停止信號，正在安全終止回補...")
        gui.log("💡 請等待當前批次處理完成（最多5秒）")
        
        # 添加漸進式按鈕恢復機制
        def restore_buttons_gradually():
            """漸進式恢復按鈕狀態"""
            # 2秒後檢查一次
            time.sleep(2)
            state = backfill_state_manager.get_state()
            if not state.is_running:
                gui.root.after(0, lambda: gui.controls.backfill_btn.config(state="normal"))
                gui.root.after(0, lambda: gui.log("🔄 停止成功，按鈕已恢復"))
                return
            
            # 如果還在運行，再等3秒強制恢復
            gui.root.after(0, lambda: gui.log("⏳ 正在等待批次處理完成..."))
            time.sleep(3)
            
            # 5秒後強制恢復所有按鈕
            gui.root.after(0, lambda: gui.controls.backfill_btn.config(state="normal"))
            gui.root.after(0, lambda: gui.controls.pause_resume_btn.config(state="disabled"))
            gui.root.after(0, lambda: gui.controls.stop_backfill_btn.config(state="disabled"))
            
            state = backfill_state_manager.get_state()
            if state.is_running:
                gui.root.after(0, lambda: gui.log("⚠️ 回補線程可能未正常結束，已強制恢復按鈕"))
                gui.root.after(0, lambda: gui.log("💡 如果需要，可以重新開始回補"))
            else:
                gui.root.after(0, lambda: gui.log("✅ 回補已完全停止，按鈕已恢復"))
        
        # 啟動超時保護線程
        threading.Thread(target=restore_buttons_gradually, daemon=True).start()

    # ======== 覆蓋 real 資料詢問 ========
    def overwrite_real_callback(self, symbol, interval, time_str):
        gui = self.gui
        if gui.overwrite_real_preference is not None:
            return gui.overwrite_real_preference

        gui.overwrite_asked_count += 1
        dialog = Toplevel(gui.root)
        dialog.title("⚠️ 發現 Real 資料衝突")
        dialog.geometry("600x350")
        dialog.minsize(600, 350)
        dialog.transient(gui.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 300
        y = (dialog.winfo_screenheight() // 2) - 175
        dialog.geometry(f"600x350+{x}+{y}")

        result = {"choice": False}
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ttk.Label(main_frame, text="⚠️ 發現已存在的 Real 資料",
                                font=("Arial", 16, "bold"), foreground="#ff6600")
        title_label.pack(pady=(0, 15))

        info_frame = ttk.LabelFrame(main_frame, text="資料資訊", padding=10)
        info_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(info_frame, text=f"交易對：{symbol}", font=("Arial", 12)).pack(anchor="w", pady=3)
        ttk.Label(info_frame, text=f"間隔：{interval}", font=("Arial", 12)).pack(anchor="w", pady=3)
        ttk.Label(info_frame, text=f"時間：{time_str}", font=("Arial", 12)).pack(anchor="w", pady=3)

        question_frame = ttk.LabelFrame(main_frame, text="請選擇處理方式", padding=10)
        question_frame.pack(fill="both", expand=True, pady=(0, 15))
        option_var = StringVar(value="skip_once")

        options = [
            ("once", "✅ 只覆蓋這一筆（下次遇到再詢問）"),
            ("all", "✅✅ 覆蓋所有（本次會話不再詢問）"),
            ("skip_once", "⏭️ 跳過這一筆（下次遇到再詢問）"),
            ("skip_all", "⏭️⏭️ 跳過所有（本次會話不再詢問）")
        ]

        for value, text in options:
            rb = ttk.Radiobutton(question_frame, text=text, variable=option_var, value=value)
            rb.pack(anchor="w", pady=4, padx=10)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        def on_confirm():
            choice = option_var.get()
            if choice == "once":
                result["choice"] = True
            elif choice == "all":
                result["choice"] = True
                gui.overwrite_real_preference = True
                gui.root.after(0, lambda: gui.log("✅ 已設定：覆蓋所有 Real 資料（直到重啟 GUI）"))
            elif choice == "skip_once":
                result["choice"] = False
            elif choice == "skip_all":
                result["choice"] = False
                gui.overwrite_real_preference = False
                gui.root.after(0, lambda: gui.log("⏭️ 已設定：跳過所有 Real 資料（直到重啟 GUI）"))
            dialog.destroy()

        def on_cancel():
            result["choice"] = False
            dialog.destroy()

        confirm_btn = ttk.Button(btn_frame, text="✅ 確認", command=on_confirm)
        confirm_btn.pack(side="left", padx=5, expand=True, fill="x")
        cancel_btn = ttk.Button(btn_frame, text="❌ 取消", command=on_cancel)
        cancel_btn.pack(side="left", padx=5, expand=True, fill="x")

        confirm_btn.focus_set()
        dialog.bind('<Return>', lambda e: on_confirm())
        dialog.bind('<Escape>', lambda e: on_cancel())

        gui.root.wait_window(dialog)
        return result["choice"]

    def _get_symbol_entry_value(self):
        entry = getattr(self.gui.controls, 'symbol_entry', None)
        if hasattr(entry, 'get'):
            return entry.get().strip().upper()
        if hasattr(entry, 'getvalue'):
            return entry.getvalue().strip().upper()
        return ""

    # _resolve_target_symbols() 已移除
    # 現在通過 gui_symbol_selector.py 中的選擇器獲取貨幣對
