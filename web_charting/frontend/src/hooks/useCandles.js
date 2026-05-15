import { useState, useCallback, useRef, useEffect } from 'react'
import { message } from 'antd'

// 負責載入 K 線資料的共用 hook，集中處理 /api/charts/candles 的呼叫與錯誤處理
export function useCandles({ symbol, interval, dataSource, monitoring }) {
  const [candlesData, setCandlesData] = useState([])
  const [loading, setLoading] = useState(false)
  const [backfillStatus, setBackfillStatus] = useState('idle') // 'idle' | 'running' | 'done'
  const [currentWindowCount, setCurrentWindowCount] = useState(0)

  // 追蹤目前實際使用中的 timeframe，避免舊回應覆蓋新 timeframe 的資料
  const intervalRef = useRef(interval)
  const symbolRef = useRef(symbol)
  const backfillStartedRef = useRef(false)

  // 當 symbol 或 interval 變化時，立即重置狀態
  useEffect(() => {
    if (symbol !== symbolRef.current || interval !== intervalRef.current) {
      symbolRef.current = symbol
      intervalRef.current = interval
      backfillStartedRef.current = false
      setBackfillStatus('idle')
      setCandlesData([]) // 立即清空，配合 BaseCandlestickChart 的重置邏輯
      setCurrentWindowCount(0)
    }
  }, [symbol, interval])

  const startBackfillFromWeb = useCallback(async (initialOldestTimestamp) => {
    if (!initialOldestTimestamp || backfillStartedRef.current) return

    backfillStartedRef.current = true
    setBackfillStatus('running')

    const batchLimit = 2000
    let endBefore = Math.floor(initialOldestTimestamp)

    try {
      while (true) {
        // 檢查是否已切換，避免在回補過程中切換了交易對或時間框架
        if (intervalRef.current !== 1 || symbolRef.current !== symbol) {
          console.log('   ⏹ 參數已切換，停止 Web 1 秒回補')
          break
        }

        const params = new URLSearchParams({
          symbol: symbolRef.current,
          limit: String(batchLimit),
          end_before: String(endBefore),
        })

        const url = `/api/charts/candles/1s-web-today?${params}`
        const response = await fetch(url)

        if (!response.ok) {
          console.error('❌ 回補 1 秒 Web 資料 HTTP 失敗:', response.status)
          break
        }

        const data = await response.json()
        if (!data.candles || data.candles.length === 0) {
          console.log('   ⏹ Web DB 無更多 1 秒資料可回補')
          break
        }

        setCandlesData((prev) => {
          // 再次檢查確保還在 1 秒模式
          if (intervalRef.current !== 1) return prev
          
          const prevList = Array.isArray(prev) ? prev : []
          if (prevList.length === 0) return data.candles

          const prevTimestamps = new Set(prevList.map((c) => c.timestamp))
          const older = data.candles.filter((c) => !prevTimestamps.has(c.timestamp))

          if (older.length === 0) return prevList

          const merged = [...older, ...prevList]
          merged.sort((a, b) => a.timestamp - b.timestamp)
          return merged
        })

        const oldestInBatch = data.candles[0].timestamp
        if (data.candles.length < batchLimit || oldestInBatch >= endBefore) break
        endBefore = oldestInBatch
      }
      
      if (intervalRef.current === 1) {
        setBackfillStatus('done')
        console.log('✅ Web 1 秒當日資料分批回補完成')
      }
    } catch (error) {
      console.error('❌ 回補 1 秒 Web 資料時發生錯誤:', error)
      setBackfillStatus('idle')
    }
  }, [symbol])

  const loadCandles = useCallback(async () => {
    const is1s = Number(interval) === 1
    const isSubMinute = Number(interval) < 60
    const silentMode = monitoring

    if (!silentMode) {
      console.log('🔄 載入 K 線資料:', { symbol, interval, dataSource })
    }

    // 抓取目前的參數，用於稍後核對回傳結果是否過時
    const requestSymbol = symbol
    const requestInterval = interval

    setLoading(monitoring ? false : true)
    try {
      // 增加監控模式下的 1s 抓取數量，確保有足夠蠟燭顯示
      const effectiveLimit = monitoring && is1s ? 500 : (monitoring && isSubMinute ? 300 : 3000)

      const params = new URLSearchParams({
        symbol: requestSymbol,
        interval: String(requestInterval),
        limit: String(effectiveLimit),
      })

      // 只要是監控模式或 1s，都嘗試 realtime 模式（從主 DB 抓最新）
      if (monitoring || is1s) {
        params.append('realtime', 'true')
      }

      if (dataSource !== 'all') {
        params.append('data_source', dataSource)
      }

      const url = `/api/charts/candles?${params}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      // 核對請求參數是否仍與當前一致，避免舊回應覆蓋新狀態
      if (requestSymbol !== symbolRef.current || requestInterval !== intervalRef.current) {
        return
      }

      if (data.candles && data.candles.length > 0) {
        setCurrentWindowCount(data.candles.length)

        setCandlesData((prev) => {
          const prevList = Array.isArray(prev) ? prev : []
          
          // 如果是第一次載入或非監控模式，直接使用
          if (prevList.length === 0 || !monitoring) {
            return data.candles
          }

          // 增量合併邏輯
          const lastTsInPrev = prevList[prevList.length - 1].timestamp
          const newCandles = data.candles.filter(c => c.timestamp >= lastTsInPrev)
          
          if (newCandles.length === 0) return prevList

          const candleMap = new Map(prevList.map(c => [c.timestamp, c]))
          newCandles.forEach(c => candleMap.set(c.timestamp, c))
          
          const merged = Array.from(candleMap.values()).sort((a, b) => a.timestamp - b.timestamp)
          return merged.slice(-5000) // 保留多一點歷史，避免縮放時全白
        })

        // 1s 模式下且非監控時啟動回補
        if (is1s && !backfillStartedRef.current && !monitoring) {
          const oldest = data.candles[0]?.timestamp
          if (oldest) {
            startBackfillFromWeb(oldest)
          }
        }
      } else {
        // 如果是 1s 監控模式卻沒數據，可能是後端還沒準備好或沒交易
        if (is1s && monitoring) {
          setCurrentWindowCount(0)
        }
      }
    } catch (error) {
      if (!monitoring) {
        console.error('❌ 載入K線失敗:', error.message)
        message.error('載入K線失敗: ' + error.message)
      }
    } finally {
      setLoading(false)
    }
  }, [symbol, interval, dataSource, monitoring, startBackfillFromWeb])

  return {
    candlesData,
    loading,
    loadCandles,
    backfillStatus,
    currentWindowCount,
  }
}
