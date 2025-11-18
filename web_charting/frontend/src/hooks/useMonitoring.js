import { useState, useCallback } from 'react'
import { message } from 'antd'

// 管理 1 秒監控狀態與 API 呼叫的共用 hook
export function useMonitoring() {
  const [monitoring, setMonitoring] = useState(false)
  const [monitorLoading, setMonitorLoading] = useState(false)
  const [monitorSymbols, setMonitorSymbols] = useState([])

  // 查詢目前監控狀態（不在這裡改 timeframe，由呼叫端決定）
  const fetchMonitorStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/monitor/status')
      if (!response.ok) {
        console.warn('取得監控狀態失敗，HTTP 狀態碼:', response.status)
        return
      }

      const data = await response.json()
      const isMonitoring = !!data.monitoring
      setMonitoring(isMonitoring)
      setMonitorSymbols(Array.isArray(data.symbols) ? data.symbols : [])
    } catch (error) {
      console.error('❌ 取得監控狀態失敗:', error)
    }
  }, [])

  // 啟動 1 秒監控（僅處理監控本身，不處理 timeframe 切換）
  const startMonitoring = useCallback(async () => {
    setMonitorLoading(true)
    try {
      const response = await fetch('/api/monitor/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: 'crypto',
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      setMonitoring(!!data.monitoring)
      setMonitorSymbols(Array.isArray(data.symbols) ? data.symbols : [])
      message.success('已啟動 1 秒監控')
    } catch (error) {
      console.error('啟動監控失敗:', error)
      message.error('啟動監控失敗: ' + error.message)
    } finally {
      setMonitorLoading(false)
    }
  }, [])

  // 停止 1 秒監控（前端一律視為停止輪詢，timeframe 切換仍交給呼叫端）
  const stopMonitoring = useCallback(async () => {
    setMonitorLoading(true)
    try {
      const response = await fetch('/api/monitor/stop', {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      const isMonitoring = !!data.monitoring
      // 使用者既然按了「停止」，前端就停止每秒輪詢
      setMonitoring(false)
      setMonitorSymbols(Array.isArray(data.symbols) ? data.symbols : [])
      message.success('已停止 1 秒監控')
    } catch (error) {
      console.error('停止監控失敗:', error)
      message.error('停止監控失敗: ' + error.message)
    } finally {
      setMonitorLoading(false)
    }
  }, [])

  return {
    monitoring,
    monitorLoading,
    monitorSymbols,
    fetchMonitorStatus,
    startMonitoring,
    stopMonitoring,
  }
}
