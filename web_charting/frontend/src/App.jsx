import { useState, useEffect } from 'react'
import { Layout, message } from 'antd'
import Header from './components/Header'
import TimeframeSelector from './components/TimeframeSelector'
import CandlestickChart from './components/CandlestickChart'
import ControlPanel from './components/ControlPanel'
import './App.css'
import { useCandles } from './hooks/useCandles'
import { useMonitoring } from './hooks/useMonitoring'

const { Header: AntHeader, Content } = Layout

function App() {
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [interval, setInterval] = useState(60) // 1分鐘
  const [dataSource, setDataSource] = useState('all') // 'all', 'real', 'Aggregation'
  const [lastSyncTime, setLastSyncTime] = useState(null)
  const [syncLoading, setSyncLoading] = useState(false)

  // 使用共用 hook 管理監控狀態與 /api/monitor/* 呼叫
  const {
    monitoring,
    monitorLoading,
    monitorSymbols,
    fetchMonitorStatus,
    startMonitoring: startMonitoringCore,
    stopMonitoring: stopMonitoringCore,
  } = useMonitoring()

  // 使用共用 hook 管理 K 線資料載入邏輯（需要監控狀態做錯誤處理判斷）
  const { candlesData, loading, loadCandles, backfillStatus, currentWindowCount } = useCandles({
    symbol,
    interval,
    dataSource,
    monitoring,
  })

  const handleIntervalChange = (newInterval) => {
    setInterval(newInterval)
  }

  // 缺口補齊：從主 DB 1 分鐘資料推導缺口 1s/2s/5s 寫入 Web Chart DB
  const handleGapFillFrom1m = async () => {
    try {
      const response = await fetch('/api/sync/gap-fill/from-1m', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          category: 'crypto',
          intervals: [1, 2, 5],
        }),
      })

      const data = await response.json()

      if (!response.ok || data.status !== 'success') {
        throw new Error(data.error || data.detail || data.message || '缺口補齊失敗')
      }

      message.success(data.message || '缺口補齊完成')

      // 補齊完成後重新載入當前 timeframe 的 K 線
      await loadCandles()
    } catch (error) {
      console.error('缺口補齊失敗:', error)
      message.error('缺口補齊失敗: ' + error.message)
    }
  }

  // 包一層，讓 timeframe 切換邏輯仍在 App 中，監控本身交給 hook 處理
  const startMonitoring = async () => {
    // 啟動監控時，強制切到 1 秒 timeframe
    setInterval(1)
    // [DESIGN NOTE] 這裡使用當前頁面的 symbol 來啟動 /api/monitor/start，
    // 使 Web 端 1 秒監控只關注單一交易對；若未來支援多 symbol 或不同 timeframe，需要一起調整 useMonitoring 與 backend。 
    await startMonitoringCore(symbol)
  }

  const stopMonitoring = async () => {
    await stopMonitoringCore()
    // 關閉 1 秒監控後，自動退回 1 分鐘時間框架，避免停在 1 秒卻沒有監控的混亂狀態
    setInterval(60)
  }

  // 同步資料
  const syncData = async () => {
    setSyncLoading(true)
    try {
      const is1s = Number(interval) === 1

      let response
      if (is1s) {
        // 1 秒 timeframe 使用專用端點，只同步當日 1 秒資料
        response = await fetch('/api/sync/subminute/1s', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            symbol,
            category: 'crypto',
            overwrite: false,
          }),
        })
      } else {
        // 其他 timeframe 使用通用同步端點
        response = await fetch('/api/sync/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            symbol,
            interval,
            category: 'crypto',
            overwrite: false,
          }),
        })
      }

      const data = await response.json()

      if (data.status === 'success') {
        const count = typeof data.records_synced === 'number' ? data.records_synced : 0
        message.success(data.message || `同步成功！獲取 ${count} 根K線`)
        setLastSyncTime(new Date())
        // 同步後自動載入
        await loadCandles()
      } else {
        message.error('同步失敗: ' + (data.error || data.detail || data.message || '未知錯誤'))
      }
    } catch (error) {
      console.error('同步失敗:', error)
      message.error('同步失敗: ' + error.message)
    } finally {
      setSyncLoading(false)
    }
  }

  // 初始載入和參數變化時重新載入
  useEffect(() => {
    loadCandles()
    fetchMonitorStatus()
  }, [loadCandles, fetchMonitorStatus])

  useEffect(() => {
    // 監控模式下 1 秒刷新一次
    // 非監控模式下 30 秒刷新一次，確保 1 分鐘 K 線也會隨時間更新
    const refreshInterval = monitoring ? 1000 : 30000

    const id = window.setInterval(() => {
      loadCandles()
    }, refreshInterval)

    return () => {
      window.clearInterval(id)
    }
  }, [monitoring, loadCandles])

  return (
    <Layout style={{ height: '100vh' }}>
      <AntHeader style={{ 
        padding: '0 24px', 
        display: 'flex', 
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <Header 
          symbol={symbol}
          onSymbolChange={setSymbol}
        />
      </AntHeader>
      
      <Content style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* 時間框架選擇器 */}
        <TimeframeSelector 
          interval={interval}
          onIntervalChange={handleIntervalChange}
        />
        
        {/* K線圖 */}
        <div style={{ 
          flex: 1, 
          minHeight: '500px',
          height: 'calc(100vh - 300px)',
          display: 'flex'
        }}>
          <CandlestickChart 
            symbol={symbol}
            interval={interval}
            candlesData={candlesData}
            loading={loading}
            monitoring={monitoring}
            currentWindowCount={currentWindowCount}
          />
        </div>
        
        {/* 控制面板 */}
        <ControlPanel 
          dataSource={dataSource}
          onDataSourceChange={setDataSource}
          onSync={syncData}
          onRefresh={loadCandles}
          loading={loading}
          syncLoading={syncLoading}
          lastSyncTime={lastSyncTime}
          monitoring={monitoring}
          monitorLoading={monitorLoading}
          monitorSymbols={monitorSymbols}
          onStartMonitoring={startMonitoring}
          onStopMonitoring={stopMonitoring}
          interval={interval}
          backfillStatus={backfillStatus}
          onGapFillFrom1m={handleGapFillFrom1m}
        />
      </Content>
    </Layout>
  )
}

export default App
