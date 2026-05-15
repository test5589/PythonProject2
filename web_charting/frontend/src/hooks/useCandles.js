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
  const last1sTimestampRef = useRef(null)
  const noProgressCounterRef = useRef(0)
  const lastStallWarningRef = useRef(0)

  useEffect(() => {
    intervalRef.current = interval
  }, [interval])

  useEffect(() => {
    symbolRef.current = symbol
    backfillStartedRef.current = false
    setBackfillStatus('idle')
    setCurrentWindowCount(0)
  }, [symbol, interval])

  const startBackfillFromWeb = useCallback(async (initialOldestTimestamp) => {
    if (!initialOldestTimestamp) {
      return
    }

    if (backfillStartedRef.current) {
      return
    }

    backfillStartedRef.current = true
    setBackfillStatus('running')

    const batchLimit = 2000
    let endBefore = Math.floor(initialOldestTimestamp)

    try {
      while (true) {
        if (intervalRef.current !== 1) {
          console.log('   ⏹ 時間框架已切換，停止 Web 1 秒回補')
          break
        }

        const currentSymbol = symbolRef.current

        const params = new URLSearchParams({
          symbol: currentSymbol,
          limit: String(batchLimit),
          end_before: String(endBefore),
        })

        const url = `/api/charts/candles/1s-web-today?${params}`
        console.log('   回補 1 秒 Web 資料 URL:', url)

        const response = await fetch(url)
        console.log('   回補 1 秒 Web 資料狀態:', response.status, response.statusText)

        if (!response.ok) {
          console.error('❌ 回補 1 秒 Web 資料 HTTP 失敗:', response.status, response.statusText)
          break
        }

        const data = await response.json()
        if (!data.candles || data.candles.length === 0) {
          console.log('   ⏹ Web DB 無更多 1 秒資料可回補')
          break
        }

        setCandlesData((prev) => {
          const prevList = Array.isArray(prev) ? prev : []

          if (prevList.length === 0) {
            return data.candles
          }

          const prevTimestamps = new Set(prevList.map((c) => c.timestamp))
          const older = data.candles.filter((c) => !prevTimestamps.has(c.timestamp))

          if (older.length === 0) {
            return prevList
          }

          const merged = [...older, ...prevList]
          merged.sort((a, b) => a.timestamp - b.timestamp)
          console.log('   ✅ Web 回補後 K 線總數:', merged.length)
          return merged
        })

        const oldestInBatch = data.candles[0].timestamp

        if (data.candles.length < batchLimit) {
          console.log('   ⏹ Web 回補批次小於 batchLimit，視為已到最早可用資料')
          break
        }

        if (oldestInBatch >= endBefore) {
          console.log('   ⏹ Web 回補遇到邏輯邊界，停止迴圈')
          break
        }

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
  }, [])

  const loadCandles = useCallback(async () => {
    // 監控模式下且是 1 秒 timeframe，使用靜音模式減少日誌
    const isSubMinute = Number(interval) < 60
    const is1s = Number(interval) === 1
    const silentMode = monitoring && is1s

    if (!silentMode) {
      console.log('🔄 載入 K 線資料:', { symbol, interval, dataSource })
    }

    setLoading(monitoring ? false : true) // 監控模式下靜默加載，不轉圈圈
    try {
      // 監控模式下只抓取最近的資料進行增量更新
      const effectiveLimit = monitoring && isSubMinute ? 100 : 3000

      const params = new URLSearchParams({
        symbol,
        interval,
        limit: String(effectiveLimit),
      })

      if (monitoring && (Number(interval) === 60 || Number(interval) === 1)) {
        params.append('realtime', 'true')
      }

      if (dataSource !== 'all') {
        params.append('data_source', dataSource)
      }

      const url = `/api/charts/candles?${params}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      if (typeof data.interval === 'number' && data.interval !== intervalRef.current) {
        return
      }

      if (data.candles && data.candles.length > 0) {
        setCurrentWindowCount(data.candles.length)

        if (is1s && monitoring) {
          const latest = data.candles[data.candles.length - 1]
          const latestTs = latest?.timestamp
          if (latestTs) {
            if (last1sTimestampRef.current != null && latestTs <= last1sTimestampRef.current) {
              noProgressCounterRef.current += 1
            } else {
              last1sTimestampRef.current = latestTs
              noProgressCounterRef.current = 0
            }

            if (noProgressCounterRef.current >= 15) { // 稍微放寬警告閾值
              const now = Date.now()
              if (!lastStallWarningRef.current || now - lastStallWarningRef.current > 60000) {
                lastStallWarningRef.current = now
                message.warning('1 秒數據更新緩慢，請檢查後端監控狀態')
              }
            }
          }
        }

        // 增量更新邏輯：與現有資料合併，避免全量重新渲染
        setCandlesData((prev) => {
          const prevList = Array.isArray(prev) ? prev : []
          if (prevList.length === 0 || !monitoring) {
            return data.candles
          }

          // 只合併新資料
          const lastTsInPrev = prevList[prevList.length - 1].timestamp
          const newCandles = data.candles.filter(c => c.timestamp >= lastTsInPrev)
          
          if (newCandles.length === 0) return prevList

          // 使用 Map 進行去重合併，保持效能
          const candleMap = new Map(prevList.map(c => [c.timestamp, c]))
          newCandles.forEach(c => candleMap.set(c.timestamp, c))
          
          const merged = Array.from(candleMap.values()).sort((a, b) => a.timestamp - b.timestamp)
          
          // 保持資料長度，避免無限制增長
          return merged.slice(-3000)
        })

        if (is1s && !backfillStartedRef.current && !monitoring) {
          const oldest = data.candles[0]?.timestamp
          if (oldest) {
            startBackfillFromWeb(oldest)
          }
        }

        if (!monitoring) {
          message.success(`成功載入 ${data.count} 根K線`)
        }
      }
    } catch (error) {
      if (!monitoring) {
        console.error('❌ 載入K線失敗:', error.message)
        message.error('載入K線失敗: ' + error.message)
        setCandlesData([])
      }
    } finally {
      setLoading(false)
    }
  }, [symbol, interval, dataSource, monitoring])

  return {
    candlesData,
    loading,
    loadCandles,
    backfillStatus,
    currentWindowCount,
  }
}
