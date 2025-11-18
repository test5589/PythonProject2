import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

function ChartDebug() {
  const chartContainerRef = useRef(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    console.log('🔍 Debug: Creating test chart')
    console.log('Container:', chartContainerRef.current)
    console.log('Size:', {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      offsetWidth: chartContainerRef.current.offsetWidth,
      offsetHeight: chartContainerRef.current.offsetHeight
    })

    const chart = createChart(chartContainerRef.current, {
      width: 800,
      height: 400,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#000000',
      }
    })

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    // 測試數據
    const testData = [
      { time: 1638360000, open: 100, high: 110, low: 95, close: 105 },
      { time: 1638360060, open: 105, high: 115, low: 100, close: 110 },
      { time: 1638360120, open: 110, high: 120, low: 105, close: 115 },
      { time: 1638360180, open: 115, high: 125, low: 110, close: 120 },
      { time: 1638360240, open: 120, high: 130, low: 115, close: 125 },
    ]

    console.log('Setting test data:', testData)
    candlestickSeries.setData(testData)
    console.log('✅ Test chart created')

    return () => {
      chart.remove()
    }
  }, [])

  return (
    <div style={{ padding: '20px' }}>
      <h2>Chart Debug Test</h2>
      <div 
        ref={chartContainerRef} 
        style={{ 
          width: '800px', 
          height: '400px', 
          border: '2px solid red',
          background: '#f0f0f0'
        }} 
      />
      <p>If you see a chart above, Lightweight Charts is working!</p>
    </div>
  )
}

export default ChartDebug
