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
    
    console.log('📐 Chart container size:', { 
      width: containerWidth, 
      height: containerHeight 
    })

    if (containerWidth === 0 || containerHeight === 0) {
      console.error('❌ Chart container has zero size!')
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
      if (autoModeRef.current) {
        console.log('👆 使用者操作圖表（滾輪/拖拉），暫停自動視窗與自動跟隨最新 K 線')
      }
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
        console.log('🔄 強制調整圖表大小:', { width, height })
        chart.applyOptions({ width, height })
        
        // 檢查 canvas 是否存在
        const canvas = chartContainerRef.current.querySelector('canvas')
        if (canvas) {
          console.log('✅ Canvas 元素已找到:', {
            width: canvas.width,
            height: canvas.height,
            display: window.getComputedStyle(canvas).display,
            visibility: window.getComputedStyle(canvas).visibility
          })
        } else {
          console.error('❌ 找不到 Canvas 元素！')
        }
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
      // 啟動監控時，重置標記，允許自動跟隨
      userInteractedRef.current = false
      console.log('🎬 啟動監控模式，允許自動跟隨最新 K 線')
    } else {
      console.log('⏹ 停止監控模式')
    }
  }, [monitoring])

  useEffect(() => {
    if (!chartRef.current || !candlesData || candlesData.length === 0) {
      console.log('⚠️ No chart or data:', { 
        hasChart: !!chartRef.current, 
        dataLength: candlesData?.length 
      })
      return
    }

    console.log('📊 Processing candles data:', candlesData.length, 'candles')

    // 清除舊的series
    seriesMapRef.current.forEach(series => {
      chartRef.current.removeSeries(series)
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
        // 使用資料中的 timestamp（秒）作為圖表時間
        time: Math.floor(candle.timestamp),
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
      }

      // 將 real_no-trade-fill 視為 real，其餘維持 Aggregation / 低優先級分組
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

    console.log('📊 Grouped data:', {
      real: groupedData.real.length,
      Aggregation: groupedData.Aggregation.length,
      lowPriority: groupedData.lowPriority.length
    })

    const chart = chartRef.current

    // 選擇用來計算自動視窗的「主資料列」（優先 real，其次 Aggregation，再來 lowPriority）
    const primaryData =
      groupedData.real.length > 0
        ? groupedData.real
        : (groupedData.Aggregation.length > 0
            ? groupedData.Aggregation
            : groupedData.lowPriority)

    // 記錄主資料來源的最後一根 index，提供給視窗變化監聽用來判斷「距離最新多少根」
    if (primaryData && primaryData.length > 0) {
      lastLogicalIndexRef.current = primaryData.length - 1
    } else {
      lastLogicalIndexRef.current = null
    }

    // 主資料來源，用來決定在哪一個 series 上顯示「當前價格線」
    let primarySource = null
    if (groupedData.real.length > 0) {
      primarySource = 'real'
    } else if (groupedData.Aggregation.length > 0) {
      primarySource = 'Aggregation'
    } else if (groupedData.lowPriority.length > 0) {
      primarySource = 'lowPriority'
    }

    const applyAutoWindow = () => {
      if (!chart || !primaryData || primaryData.length === 0) return

      const n = primaryData.length
      const windowSize = targetWindowSizeRef.current || 100
      const size = Math.max(10, Math.min(windowSize, n))
      const lastIndex = n - 1
      const from = Math.max(lastIndex - size + 1, 0)
      const to = lastIndex + 1

      const ts = chart.timeScale()
      isProgrammaticChangeRef.current = true
      ts.setVisibleLogicalRange({ from, to })
      console.log('🎯 套用自動視窗:', { from, to, size, lastIndex })
      // isProgrammaticChangeRef 會在監聽器中自動重置
    }

    // 檢查 chart 實例是否有效（針對 v4 API：addCandlestickSeries）
    console.log('🔍 檢查 chart 實例:', {
      hasChartRef: !!chart,
      chartType: typeof chart,
      hasAddCandlestickSeries: typeof chart?.addCandlestickSeries,
      chartKeys: chart ? Object.keys(chart).slice(0, 10) : []
    })

    if (!chart || typeof chart.addCandlestickSeries !== 'function') {
      console.error('❌ Chart API 不支援 addCandlestickSeries，無法建立 K 線 series')
      console.error('   chartRef.current:', chart)
      return
    }

    // 創建不同的 candlestick series 並應用不同顏色
    Object.entries(groupedData).forEach(([source, data]) => {
      if (data.length === 0) return

      // 按時間排序（Lightweight Charts 要求）
      data.sort((a, b) => a.time - b.time)

      console.log(`📈 Creating ${source} series with ${data.length} candles`)
      if (data.length > 0) {
        console.log(`  First: time=${data[0].time}, OHLC=${data[0].open}/${data[0].high}/${data[0].low}/${data[0].close}`)
        console.log(`  Last: time=${data[data.length-1].time}`)
      }

      const colors = COLORS[source]

      // 只有主資料來源顯示「當前價格線」與最後價標籤
      const isPrimarySeries = source === primarySource

      let series
      try {
        // 使用 v4 API：chart.addCandlestickSeries(options)
        console.log('🧩 使用 addCandlestickSeries 建立 series')
        series = chart.addCandlestickSeries({
          upColor: colors.up,
          downColor: colors.down,
          borderUpColor: colors.up,
          borderDownColor: colors.down,
          wickUpColor: colors.up,
          wickDownColor: colors.down,
          // 僅在主 series 上顯示當前價格線與最後價標籤，其他來源保持關閉
          priceLineVisible: isPrimarySeries,
          lastValueVisible: isPrimarySeries,
          // 給當前價格線一個較明顯的顏色
          priceLineColor: isPrimarySeries ? '#FFD700' : undefined,
          priceLineWidth: isPrimarySeries ? 2 : undefined,
        })
      } catch (e) {
        console.error('❌ 建立 series 時發生錯誤:', e)
        return
      }

      try {
        series.setData(data)
        seriesMapRef.current.set(source, series)
        console.log(`✅ ${source} series created successfully`)
      } catch (error) {
        console.error(`❌ Error creating ${source} series:`, error)
      }
    })

    // 自動調整視圖：
    // - 第一次有數據時：分鐘以上用 fitContent，秒級別用「最後 N 根」視窗
    // - 之後：在監控模式 + 秒級別 + 自動模式下，維持最後 N 根視窗跟隨最新 K 線
    try {
      const isSubMinute = interval < 60

      if (!hasAutoFitRef.current) {
        if (isSubMinute) {
          // 秒級別首次載入改用簡單的 scrollToRealTime，避免視窗頻繁變動造成畫面亂飄
          if (chartRef.current) {
            chartRef.current.timeScale().scrollToRealTime()
          }
          hasAutoFitRef.current = true
          console.log('✅ Sub-minute chart initialized with scrollToRealTime (simple mode)')
        } else {
          chartRef.current.timeScale().fitContent()
          hasAutoFitRef.current = true
          console.log('✅ Chart rendered and auto-fitted once')
        }
      } else {
        // 只有在自動模式下才會根據最新 K 線調整視窗
        if (autoModeRef.current) {
          if (monitoring) {
            // 監控 + 自動模式：秒級別使用固定視窗寬度，並跟隨最新 K 線
            if (chartRef.current) {
              if (isSubMinute) {
                applyAutoWindow()
              }
              chartRef.current.timeScale().scrollToRealTime()
            }
            console.log('🔄 監控模式 + 自動模式：自動視窗 + 跟隨最新 K 線', { isSubMinute })
          } else if (!isSubMinute) {
            // 非監控模式：僅對分鐘以上 timeframe 嘗試跟隨
            if (chartRef.current) {
              chartRef.current.timeScale().scrollToRealTime()
            }
            console.log('🔄 非監控模式（分鐘以上）+ 自動模式：scrollToRealTime')
          } else {
            console.log('ℹ️ 非監控 + 秒級，自動模式下不強制跟隨')
          }
        } else {
          console.log('ℹ️ 手動瀏覽模式：不自動跟隨最新 K 線、不改變視窗寬度')
        }
      }

      // 強制更新一次大小以確保可見，但不再呼叫 fitContent
      setTimeout(() => {
        if (chartRef.current && chartContainerRef.current) {
          const width = chartContainerRef.current.clientWidth
          const height = chartContainerRef.current.clientHeight
          console.log('🔄 數據渲染後調整大小:', { width, height })
          chartRef.current.applyOptions({ width, height })
          
          // 最終檢查
          const canvases = chartContainerRef.current.querySelectorAll('canvas')
          console.log(`🎨 找到 ${canvases.length} 個 Canvas 元素`)
          canvases.forEach((canvas, i) => {
            console.log(`  Canvas ${i}:`, {
              width: canvas.width,
              height: canvas.height,
              offsetWidth: canvas.offsetWidth,
              offsetHeight: canvas.offsetHeight,
              visible: canvas.offsetWidth > 0 && canvas.offsetHeight > 0
            })
          })
        }
      }, 200)
    } catch (error) {
      console.error('❌ Error fitting content:', error)
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
