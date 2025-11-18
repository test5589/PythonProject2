import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

/**
 * 最簡單的圖表組件 - 用於測試
 */
function SimpleChart() {
  const chartContainerRef = useRef(null)

  useEffect(() => {
    console.log('🚀 SimpleChart useEffect 開始')
    console.log('📦 chartContainerRef.current:', chartContainerRef.current)

    if (!chartContainerRef.current) {
      console.error('❌ chartContainerRef.current 是 null!')
      return
    }

    const container = chartContainerRef.current
    console.log('📐 容器尺寸:', {
      clientWidth: container.clientWidth,
      clientHeight: container.clientHeight,
      offsetWidth: container.offsetWidth,
      offsetHeight: container.offsetHeight
    })

    try {
      console.log('📊 創建圖表...')
      const chart = createChart(container, {
        width: 800,
        height: 400,
        layout: {
          background: { color: '#222' },
          textColor: '#DDD',
        },
        grid: {
          vertLines: { color: '#444' },
          horzLines: { color: '#444' },
        },
      })
      console.log('✅ 圖表創建成功')

      console.log('📊 添加 Series...')
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      })
      console.log('✅ Series 添加成功')

      console.log('📝 設置數據...')
      const data = [
        { time: 1638360000, open: 100, high: 110, low: 95, close: 105 },
        { time: 1638360060, open: 105, high: 115, low: 100, close: 110 },
        { time: 1638360120, open: 110, high: 120, low: 105, close: 115 },
        { time: 1638360180, open: 115, high: 125, low: 110, close: 120 },
        { time: 1638360240, open: 120, high: 130, low: 115, close: 125 },
      ]
      candlestickSeries.setData(data)
      console.log('✅ 數據設置成功')

      chart.timeScale().fitContent()
      console.log('✅ 調整視圖完成')

      // 檢查 Canvas
      setTimeout(() => {
        const canvases = container.querySelectorAll('canvas')
        console.log(`🎨 找到 ${canvases.length} 個 Canvas 元素`)
        
        if (canvases.length === 0) {
          console.error('❌ 錯誤：Canvas 未創建！')
          console.log('容器 innerHTML:', container.innerHTML.substring(0, 200))
        } else {
          canvases.forEach((canvas, i) => {
            console.log(`Canvas ${i}:`, {
              width: canvas.width,
              height: canvas.height,
              offsetWidth: canvas.offsetWidth,
              offsetHeight: canvas.offsetHeight,
              display: window.getComputedStyle(canvas).display
            })
          })
        }
      }, 500)

      return () => {
        console.log('🧹 清理圖表')
        chart.remove()
      }
    } catch (error) {
      console.error('❌ 創建圖表時發生錯誤:', error)
      console.error('錯誤堆棧:', error.stack)
    }
  }, [])

  return (
    <div style={{ padding: '20px', background: '#1a1a1a', minHeight: '100vh' }}>
      <h1 style={{ color: 'lime', textAlign: 'center' }}>
        🧪 簡單圖表測試
      </h1>
      <div 
        ref={chartContainerRef} 
        style={{
          width: '800px',
          height: '400px',
          margin: '20px auto',
          border: '3px solid lime',
          background: '#2a2a2a'
        }}
      />
      <div style={{ color: 'white', textAlign: 'center', fontSize: '18px' }}>
        請打開 F12 Console 查看調試信息
      </div>
    </div>
  )
}

export default SimpleChart
