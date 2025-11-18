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
    console.log('🔄 開始載入 K 線資料...')
    console.log('   Symbol:', symbol, 'Interval:', interval, 'DataSource:', dataSource)

    setLoading(true)
    try {
      // 子分鐘 timeframe 且處於監控模式時，減少一次載入的 K 線數量，避免切回 1 秒時請求過大
      const isSubMinute = Number(interval) < 60
      const effectiveLimit = monitoring && isSubMinute ? 600 : 3000

      const params = new URLSearchParams({
        symbol,
        interval,
        limit: effectiveLimit,
      })

      // 在監控模式下，1 分鐘 timeframe 使用主 DB 的 1 秒資料即時聚合
      if (monitoring && (Number(interval) === 60 || Number(interval) === 1)) {
        params.append('realtime', 'true')
      }

      if (dataSource !== 'all') {
        params.append('data_source', dataSource)
      }

      const url = `/api/charts/candles?${params}`
      console.log('   請求 URL:', url)

      const response = await fetch(url)
      console.log('   響應狀態:', response.status, response.statusText)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      console.log('   收到數據:', {
        symbol: data.symbol,
        interval: data.interval,
        count: data.count,
        candlesLength: data.candles?.length,
        hasCandlesArray: !!data.candles,
      })

      // 如果這是舊 timeframe 的回應（例如之前的 1s），而目前已經切到別的 timeframe，就忽略
      if (typeof data.interval === 'number' && data.interval !== intervalRef.current) {
        console.log('   ⏭ 忽略舊 timeframe 回應:', 'response interval =', data.interval, 'current =', intervalRef.current)
        return
      }

      if (data.candles && data.candles.length > 0) {
        console.log('   ✅ 設置 K 線數據:', data.candles.length, '根')

        // 記錄這次查詢時間窗內實際回傳的 K 線數量（不包含右側空白區域）
        setCurrentWindowCount(data.candles.length)

        const is1s = Number(interval) === 1

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

            if (noProgressCounterRef.current >= 10) {
              const now = Date.now()
              if (!lastStallWarningRef.current || now - lastStallWarningRef.current > 30000) {
                lastStallWarningRef.current = now
                message.warning('1 秒監控已啟動，但最近一段時間 1 秒K線沒有更新，可能是 1 秒監控模組沒有持續寫入主資料庫')
              }
            }
          }
        }

        if (is1s && backfillStartedRef.current) {
          const chunk = data.candles
          setCandlesData((prev) => {
            const prevList = Array.isArray(prev) ? prev : []

            if (prevList.length === 0) {
              return chunk
            }

            // 以 timestamp 做集合合併：
            // - 同一秒只保留最新這批 chunk 的資料
            // - 其他時間點一律保留，避免相近資料被錯誤砍掉或亂接
            const chunkTimestamps = new Set(chunk.map((c) => c.timestamp))
            const filteredPrev = prevList.filter((c) => !chunkTimestamps.has(c.timestamp))
            const merged = filteredPrev.concat(chunk)
            merged.sort((a, b) => a.timestamp - b.timestamp)
            return merged
          })
        } else {
          setCandlesData(data.candles)

          if (is1s && !backfillStartedRef.current) {
            const oldest = data.candles[0]?.timestamp
            if (oldest) {
              startBackfillFromWeb(oldest)
            }
          }
        }

        if (!monitoring) {
          message.success(`成功載入 ${data.count} 根K線`)
        }
      } else {
        console.log('   ⚠️ 無 K 線數據')
        if (!monitoring) {
          message.warning('無K線資料，請先同步')
        }
      }
    } catch (error) {
      console.error('❌ 載入K線失敗:', error)
      console.error('   錯誤類型:', error.name)
      console.error('   錯誤訊息:', error.message)
      if (!monitoring) {
        message.error('載入K線失敗: ' + error.message)
        // 僅在非監控模式下清空數據；監控模式下保留最後一次成功的資料，避免圖表瞬間消失
        setCandlesData([])
      }
    } finally {
      setLoading(false)
      console.log('🔄 載入完成')
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
