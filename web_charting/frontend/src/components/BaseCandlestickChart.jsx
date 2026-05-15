// 核心圖表實作，從原本的 CandlestickChart 抽出來，方便維護
import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import { Spin } from 'antd'
import './CandlestickChart.css'

// 顏色配置（保持與原本 CandlestickChart 完全一致）
const COLORS = {
  real: {
    up: '#00C853',      // 深綠色
    down: '#D50000',    // 深紅色
  },
  Aggregation: {
    up: '#69F0AE',      // 淺綠色
    down: '#FF5252',    // 淺紅色
  },
  lowPriority: {
    up: '#9E9E9E',      // 灰色
    down: '#757575',    // 深灰色
  }
}

function BaseCandlestickChart({ symbol, interval, candlesData, loading, monitoring, currentWindowCount }) {
  const chartContainerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesMapRef = useRef(new Map()) // 存儲不同資料來源的series
  const hasAutoFitRef = useRef(false) // 控制只在首次有數據時自動 fitContent
  const userInteractedRef = useRef(false) // 追蹤使用者是否手動操作過圖表（目前保留，不再作為主要判斷依據）
  const autoModeRef = useRef(true) // 是否處於自動視窗/自動跟隨模式
  const targetWindowSizeRef = useRef(100) // 預設顯示的K線數量（秒級先用100根）
  const isProgrammaticChangeRef = useRef(false) // 標記目前視窗變化是否由程式觸發
  const lastUserInteractionRef = useRef(0) // 最近一次使用者操作時間（毫秒）
  const autoResumeTimeoutRef = useRef(null) // 自動恢復預設模式的排程
  const lastLogicalIndexRef = useRef(null) // 目前主資料序列最後一根的 logical index

  useEffect(() => {
    if (!chartContainerRef.current) return

    const containerWidth = chartContainerRef.current.clientWidth
    const containerHeight = chartContainerRef.current.clientHeight
    
    if (containerWidth === 0 || containerHeight === 0) {
      return
    }

    // 創建圖表
    const chart = createChart(chartContainerRef.current, {
      width: containerWidth,
      height: containerHeight,
      layout: {
        background: { color: '#161b22' },
        textColor: '#c9d1d9',
      },
      grid: {
        vertLines: { color: '#30363d' },
        horzLines: { color: '#30363d' },
      },
      crosshair: {
        mode: 1,
      },
      timeScale: {
        borderColor: '#30363d',
        timeVisible: true,
        secondsVisible: interval < 60,
        autoScale: true, // 確保時間軸自適應
      },
      localization: {
        locale: 'zh-TW',
        timeFormatter: (time) => {
          if (typeof time === 'number') {
            const date = new Date(time * 1000)
            const yyyy = date.getFullYear()
            const MM = String(date.getMonth() + 1).padStart(2, '0')
            const dd = String(date.getDate()).padStart(2, '0')
            const hh = String(date.getHours()).padStart(2, '0')
            const mm = String(date.getMinutes()).padStart(2, '0')
            const ss = String(date.getSeconds()).padStart(2, '0')

            // 秒級別 timeframe 顯示到秒；分鐘以上只顯示到分
            if (interval < 60) {
              return `${yyyy}-${MM}-${dd} ${hh}:${mm}:${ss}`
            }
            return `${yyyy}-${MM}-${dd} ${hh}:${mm}`
          }

          // BusinessDay 格式備援（目前未使用，但保險保留）
          const { year, month, day } = time
          const MM = String(month).padStart(2, '0')
          const dd = String(day).padStart(2, '0')
          return `${year}-${MM}-${dd}`
        },
      },
      rightPriceScale: {
        borderColor: '#30363d',
        autoScale: true, // 啟用價格軸自動縮放，避免蠟燭變扁
        alignLabels: true,
      },
      handleScroll: true,
      handleScale: true,
    })

    chartRef.current = chart
    hasAutoFitRef.current = false
    userInteractedRef.current = false // 重置使用者互動標記
    autoModeRef.current = interval < 60 // 秒級別預設啟用自動視窗模式
    targetWindowSizeRef.current = 100

    const timeScale = chart.timeScale()

    // 監聽視窗變化，用來判斷使用者是否打破預設視窗範圍 / 是否回到當前區域
    const handleVisibleRangeChange = (newRange) => {
      if (!newRange) return

      // 程式主動改視窗時，不視為使用者操作
      if (isProgrammaticChangeRef.current) {
        // 下一次變化再恢復正常判斷
        isProgrammaticChangeRef.current = false
        return
      }

      const now = Date.now()
      lastUserInteractionRef.current = now

      // 任何手動操作都先關閉自動模式與自動跟隨
      autoModeRef.current = false

      // 有新的操作就取消之前排程的自動恢復
      if (autoResumeTimeoutRef.current) {
        clearTimeout(autoResumeTimeoutRef.current)
        autoResumeTimeoutRef.current = null
      }

      const visibleBars = newRange.to - newRange.from
      if (!Number.isFinite(visibleBars) || visibleBars <= 0) {
        return
      }

      const lastIndex = lastLogicalIndexRef.current
      let distanceToLast = null
      if (typeof lastIndex === 'number' && Number.isFinite(lastIndex)) {
        distanceToLast = lastIndex - newRange.to
      }

      // 視窗的尾端靠近最後一根 K 線（容許前後 5 根的誤差）
      const nearLast =
        distanceToLast !== null &&
        distanceToLast <= 5 &&
        distanceToLast >= -5

      // 使用者目前視窗寬度小於 65 根
      const smallWindow = visibleBars < 65

      // 使用者已經把視窗拉回接近最新 K 線，且視窗寬度小於 65 根時，
      // 若接下來 5 秒內沒有任何操作，就自動恢復預設的自動模式（固定視窗寬度 + 跟隨最新 K 線）。
      if (nearLast && smallWindow) {
        const scheduledVisibleBars = visibleBars
        autoResumeTimeoutRef.current = setTimeout(() => {
          const idleMs = Date.now() - lastUserInteractionRef.current
          if (!autoModeRef.current && idleMs >= 5000) {
            autoModeRef.current = true
            const size = Math.max(10, Math.min(100, Math.round(scheduledVisibleBars)))
            targetWindowSizeRef.current = size
            console.log(
              '⏱ 5 秒內無操作且已回到最新附近，恢復自動視窗與自動跟隨；固定視窗寬度 =',
              size,
              '根 K 線'
            )

            if (chartRef.current) {
              const ts = chartRef.current.timeScale()
              isProgrammaticChangeRef.current = true
              ts.scrollToRealTime()
            }
          }
        }, 5000)
      }
    }

    timeScale.subscribeVisibleLogicalRangeChange(handleVisibleRangeChange)

    // 強制調整一次大小確保 canvas 渲染
    setTimeout(() => {
      if (chartContainerRef.current && chart) {
        const width = chartContainerRef.current.clientWidth
        const height = chartContainerRef.current.clientHeight
        chart.applyOptions({ width, height })
      }
    }, 100)

    // 響應式調整大小
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (timeScale && handleVisibleRangeChange) {
        try {
          timeScale.unsubscribeVisibleLogicalRangeChange(handleVisibleRangeChange)
        } catch (e) {
          console.warn('⚠️ 解除 timeScale 監聽失敗:', e)
        }
      }
      if (autoResumeTimeoutRef.current) {
        clearTimeout(autoResumeTimeoutRef.current)
        autoResumeTimeoutRef.current = null
      }
      chart.remove()
      chartRef.current = null
      seriesMapRef.current.clear()
    }
  }, [interval])

  // 當監控狀態改變時，重置使用者互動標記
  useEffect(() => {
    if (monitoring) {
      autoModeRef.current = true
    } else {
      autoModeRef.current = false
    }
  }, [monitoring])

  useEffect(() => {
    if (!chartRef.current || !candlesData || candlesData.length === 0) {
      return
    }

    const is1s = Number(interval) === 1
    const silentMode = monitoring

    // 🛡️ [尊重原始邏輯] 每次數據發生重大變化或切換時，先清除舊的 series 避免衝突
    seriesMapRef.current.forEach(series => {
      try {
        chartRef.current.removeSeries(series)
      } catch (e) {
        // 忽略移除失敗（可能已被移除）
      }
    })
    seriesMapRef.current.clear()

    // 按資料來源分組
    const groupedData = {
      real: [],
      Aggregation: [],
      lowPriority: []
    }

    candlesData.forEach(candle => {
      const data = {
        time: Math.floor(candle.timestamp),
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
      }

      const source =
        candle.data_source === 'real_no-trade-fill'
          ? 'real'
          : (candle.data_source || 'real')

      if (source === 'real') {
        groupedData.real.push(data)
      } else if (source === 'Aggregation') {
        groupedData.Aggregation.push(data)
      } else {
        groupedData.lowPriority.push(data)
      }
    })

    const chart = chartRef.current

    // 選擇主資料來源
    let primarySource = null
    if (groupedData.real.length > 0) primarySource = 'real'
    else if (groupedData.Aggregation.length > 0) primarySource = 'Aggregation'
    else if (groupedData.lowPriority.length > 0) primarySource = 'lowPriority'

    const primaryData = groupedData[primarySource] || []
    if (primaryData.length > 0) {
      lastLogicalIndexRef.current = primaryData.length - 1
    }

    const applyAutoWindow = () => {
      if (!chart || !primaryData || primaryData.length === 0) return
      // 固定顯示最後 100 根，這樣蠟燭大小才清楚
      const windowSize = 100 
      const n = primaryData.length
      const lastIndex = n - 1
      const from = Math.max(lastIndex - windowSize + 1, 0)
      const to = lastIndex + 1

      const ts = chart.timeScale()
      isProgrammaticChangeRef.current = true
      ts.setVisibleLogicalRange({ from, to })
    }

    // 核心優化：如果 series 已經存在，則使用增量更新
    const updateOrSetSeries = (source, data) => {
      if (data.length === 0) return
      data.sort((a, b) => a.time - b.time)

      let series = seriesMapRef.current.get(source)
      const isPrimarySeries = source === primarySource
      const isSubMinute = interval < 60

      if (!series) {
        const colors = COLORS[source]
        series = chart.addCandlestickSeries({
          upColor: colors.up,
          downColor: colors.down,
          borderUpColor: colors.up,
          borderDownColor: colors.down,
          wickUpColor: colors.up,
          wickDownColor: colors.down,
          priceLineVisible: isPrimarySeries,
          lastValueVisible: isPrimarySeries,
          priceLineColor: isPrimarySeries ? '#FFD700' : undefined,
          priceLineWidth: isPrimarySeries ? 2 : undefined,
        })
        series.setData(data)
        seriesMapRef.current.set(source, series)
      } else {
        // 僅在「秒級監控」模式下使用增量更新，分鐘級別或非監控模式使用 setData 確保數據完整
        if (monitoring && isSubMinute) {
          const lastFew = data.slice(-2)
          lastFew.forEach(d => series.update(d))
        } else {
          series.setData(data)
        }
      }
    }

    Object.entries(groupedData).forEach(([source, data]) => {
      updateOrSetSeries(source, data)
    })

    try {
      const isSubMinute = interval < 60

      if (!hasAutoFitRef.current) {
        // 首次載入：套用 100 根視窗
        applyAutoWindow()
        hasAutoFitRef.current = true
      } else if (autoModeRef.current) {
        // 監控模式下，僅當數據有更新時才嘗試跟隨最新 K 線
        if (monitoring && isSubMinute) {
          applyAutoWindow()
          chart.timeScale().scrollToRealTime()
        }
      }
    } catch (error) {
      if (!silentMode) console.error('❌ Error updating chart view:', error)
    }
  }, [candlesData])

  return (
    <div className="chart-wrapper" style={{ position: 'relative' }}>
      {loading && (
        <div className="chart-loading-overlay">
          <Spin size="large" />
        </div>
      )}

      <div className="chart-info" style={{ background: '#0d1117', padding: '12px' }}>
        <span className="symbol-name">{symbol}</span>
        <span className="interval-label">
          {interval < 60 ? `${interval}s` : 
           interval < 3600 ? `${interval/60}m` : 
           `${interval/3600}h`}
        </span>
        {candlesData.length > 0 && (
          <span className="candles-count">
            累積 1 秒 K 線總數（從最早一筆到目前）：{candlesData.length} 根
          </span>
        )}
        {interval === 1 && currentWindowCount > 0 && (
          <span className="candles-count" style={{ marginLeft: '12px' }}>
            當前 1 秒時間窗實際 K 線數（不含右側空白）：{currentWindowCount} 根
          </span>
        )}
        {candlesData.length === 0 && (
          <span style={{ color: 'red', fontWeight: 'bold' }}>
            ⚠️ 無數據
          </span>
        )}
      </div>
      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color" style={{background: COLORS.real.up}}></span>
          <span>Real 上漲</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{background: COLORS.real.down}}></span>
          <span>Real 下跌</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{background: COLORS.Aggregation.up}}></span>
          <span>Aggregation 上漲</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{background: COLORS.Aggregation.down}}></span>
          <span>Aggregation 下跌</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{background: COLORS.lowPriority.up}}></span>
          <span>低優先級</span>
        </div>
      </div>
      <div 
        ref={chartContainerRef} 
        className="chart-container"
        style={{
          position: 'relative'
        }}
      />
    </div>
  )
}

export default BaseCandlestickChart
