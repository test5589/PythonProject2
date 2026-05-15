// 核心圖表實作，從原本的 CandlestickChart 抽出來，方便維護
import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import { Spin } from 'antd'
import './CandlestickChart.css'

// 顏色配置
const COLORS = {
  real: {
    up: '#089981',      // 專業綠
    down: '#f23645',    // 專業紅
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
  const autoModeRef = useRef(true) // 是否處於自動視窗/自動跟隨模式
  const targetWindowSizeRef = useRef(100) // 預設顯示的K線數量
  const isProgrammaticChangeRef = useRef(false) // 標記目前視窗變化是否由程式觸發
  const lastUserInteractionRef = useRef(0) // 最近一次使用者操作時間
  const autoResumeTimeoutRef = useRef(null) // 自動恢復預設模式的排程
  const lastLogicalIndexRef = useRef(null) // 目前主資料序列最後一根的 logical index

  useEffect(() => {
    if (!chartContainerRef.current) return

    const containerWidth = chartContainerRef.current.clientWidth
    const containerHeight = chartContainerRef.current.clientHeight
    
    // 創建圖表
    const chart = createChart(chartContainerRef.current, {
      width: containerWidth || 800,
      height: containerHeight || 600,
      layout: {
        background: { color: '#ffffff' }, // 白色背景
        textColor: '#131722', // 深色文字
      },
      grid: {
        vertLines: { color: '#f0f3fa' }, // 淺灰色網格
        horzLines: { color: '#f0f3fa' },
      },
      crosshair: {
        mode: 1,
      },
      timeScale: {
        borderColor: '#d1d4dc',
        timeVisible: true,
        secondsVisible: interval < 60,
        autoScale: true,
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
            if (interval < 60) return `${yyyy}-${MM}-${dd} ${hh}:${mm}:${ss}`
            return `${yyyy}-${MM}-${dd} ${hh}:${mm}`
          }
          return ''
        },
      },
      rightPriceScale: {
        borderColor: '#d1d4dc',
        autoScale: true,
        alignLabels: true,
      },
      handleScroll: true,
      handleScale: true,
    })

    chartRef.current = chart
    hasAutoFitRef.current = false
    autoModeRef.current = interval < 60 
    targetWindowSizeRef.current = 100

    const timeScale = chart.timeScale()

    // 監聽視窗變化
    const handleVisibleRangeChange = (newRange) => {
      if (!newRange) return
      if (isProgrammaticChangeRef.current) {
        isProgrammaticChangeRef.current = false
        return
      }
      const now = Date.now()
      lastUserInteractionRef.current = now
      autoModeRef.current = false
      if (autoResumeTimeoutRef.current) {
        clearTimeout(autoResumeTimeoutRef.current)
        autoResumeTimeoutRef.current = null
      }
      const visibleBars = newRange.to - newRange.from
      const lastIndex = lastLogicalIndexRef.current
      let distanceToLast = (typeof lastIndex === 'number') ? lastIndex - newRange.to : null
      const nearLast = distanceToLast !== null && Math.abs(distanceToLast) <= 5
      const smallWindow = visibleBars < 65

      if (nearLast && smallWindow) {
        const scheduledVisibleBars = visibleBars
        autoResumeTimeoutRef.current = setTimeout(() => {
          const idleMs = Date.now() - lastUserInteractionRef.current
          if (!autoModeRef.current && idleMs >= 5000) {
            autoModeRef.current = true
            targetWindowSizeRef.current = Math.max(10, Math.min(100, Math.round(scheduledVisibleBars)))
            if (chartRef.current) {
              isProgrammaticChangeRef.current = true
              chartRef.current.timeScale().scrollToRealTime()
            }
          }
        }, 5000)
      }
    }

    timeScale.subscribeVisibleLogicalRangeChange(handleVisibleRangeChange)

    // 響應式調整大小
    const resizeObserver = new ResizeObserver(entries => {
      if (entries.length === 0 || !chartRef.current) return
      const { width, height } = entries[0].contentRect
      chartRef.current.applyOptions({ width, height })
    })
    resizeObserver.observe(chartContainerRef.current)

    return () => {
      resizeObserver.disconnect()
      if (timeScale) {
        try { timeScale.unsubscribeVisibleLogicalRangeChange(handleVisibleRangeChange) } catch (e) {}
      }
      if (autoResumeTimeoutRef.current) clearTimeout(autoResumeTimeoutRef.current)
      chart.remove()
      chartRef.current = null
      seriesMapRef.current.clear()
    }
  }, [interval])

  // 當監控狀態改變時，重置自動模式標記
  useEffect(() => {
    if (monitoring) {
      autoModeRef.current = true
    } else {
      autoModeRef.current = interval < 60
    }
  }, [monitoring, interval])

  // 追蹤上一次渲染的參數
  const lastParamsRef = useRef({ symbol: null, interval: null })

  // 🛡️ 處理參數變化：切換交易對或時間框架時，立即清除圖表
  useEffect(() => {
    if (!chartRef.current) return
    const isParamsChanged = lastParamsRef.current.symbol !== symbol || lastParamsRef.current.interval !== interval
    if (isParamsChanged) {
      seriesMapRef.current.forEach(series => {
        try { chartRef.current.removeSeries(series) } catch (e) {}
      })
      seriesMapRef.current.clear()
      lastParamsRef.current = { symbol, interval }
      hasAutoFitRef.current = false 
      lastLogicalIndexRef.current = null 
    }
  }, [symbol, interval])

  useEffect(() => {
    if (!chartRef.current || !candlesData || candlesData.length === 0) return
    const chart = chartRef.current

    // 按資料來源分組
    const groupedData = { real: [], Aggregation: [], lowPriority: [] }
    candlesData.forEach(candle => {
      const data = {
        time: Math.floor(candle.timestamp),
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
      }
      const source = candle.data_source === 'real_no-trade-fill' ? 'real' : (candle.data_source || 'real')
      if (groupedData[source]) groupedData[source].push(data)
      else groupedData.lowPriority.push(data)
    })

    let primarySource = groupedData.real.length > 0 ? 'real' : (groupedData.Aggregation.length > 0 ? 'Aggregation' : 'lowPriority')
    const primaryData = groupedData[primarySource] || []
    if (primaryData.length > 0) lastLogicalIndexRef.current = primaryData.length - 1

    Object.entries(groupedData).forEach(([source, data]) => {
      if (data.length === 0) return
      data.sort((a, b) => a.time - b.time)
      let series = seriesMapRef.current.get(source)
      const isPrimary = source === primarySource
      if (!series) {
        const colors = COLORS[source] || COLORS.lowPriority
        series = chart.addCandlestickSeries({
          upColor: colors.up,
          downColor: colors.down,
          borderUpColor: colors.up,
          borderDownColor: colors.down,
          wickUpColor: colors.up,
          wickDownColor: colors.down,
          priceLineVisible: isPrimary,
          lastValueVisible: isPrimary,
          priceLineColor: isPrimary ? '#2962ff' : undefined,
          priceLineWidth: isPrimary ? 1 : undefined,
        })
        seriesMapRef.current.set(source, series)
      }
      series.setData(data)
    })

    const applyAutoWindow = () => {
      if (!chart || !primaryData.length) return
      const windowSize = 100
      const lastIndex = primaryData.length - 1
      const from = Math.max(lastIndex - windowSize + 1, 0)
      const to = lastIndex + 1
      isProgrammaticChangeRef.current = true
      chart.timeScale().setVisibleLogicalRange({ from, to })
    }

    try {
      if (!hasAutoFitRef.current) {
        applyAutoWindow()
        hasAutoFitRef.current = true
      } else if (autoModeRef.current && monitoring && interval < 60) {
        applyAutoWindow()
        chart.timeScale().scrollToRealTime()
      }
    } catch (error) {}
  }, [candlesData, symbol, interval, monitoring])

  return (
    <div className="chart-wrapper">
      <div ref={chartContainerRef} className="chart-container">
        {loading && (
          <div className="chart-loading-overlay">
            <Spin size="large" />
          </div>
        )}

        {/* 左上角 TradingView 風格一體化資訊窗 */}
        <div className="chart-overlay-info">
          <div className="overlay-row">
            <span className="overlay-symbol">{symbol}</span>
            <span className="overlay-interval">
              {interval < 60 ? `${interval}s` : interval < 3600 ? `${interval/60}m` : `${interval/3600}h`}
            </span>
            {candlesData.length > 0 && (
              <span className="overlay-count">累積 {candlesData.length} 根</span>
            )}
          </div>

          <div className="overlay-legend">
            {Object.keys(COLORS).map(source => (
              <div key={source} className="legend-item" style={{ fontSize: '10px' }}>
                <span className="legend-color" style={{background: COLORS[source].up, width: '10px', height: '2px'}}></span>
                <span style={{ color: 'var(--tv-text-dim)' }}>{source}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default BaseCandlestickChart
