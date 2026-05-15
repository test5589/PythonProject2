import React from 'react'
import { Select, Space, Tooltip, Badge } from 'antd'
import { 
  BarChartOutlined, 
  SettingOutlined, 
  PlayCircleOutlined, 
  StopOutlined, 
  SyncOutlined,
  GlobalOutlined,
  ReloadOutlined,
  LinkOutlined,
  CloudSyncOutlined,
  DashboardOutlined
} from '@ant-design/icons'
import CandlestickChart from './components/CandlestickChart'
import './ProfessionalTheme.css'
import dayjs from 'dayjs'

const TIMEFRAME_LABELS = {
  1: '1s', 2: '2s', 5: '5s', 10: '10s', 15: '15s', 30: '30s',
  60: '1m', 300: '5m', 600: '10m', 1800: '30m', 3600: '1h',
  14400: '4h', 28800: '8h',
}

function ProfessionalLayout({
  symbol,
  onSymbolChange,
  symbols,
  interval,
  onIntervalChange,
  monitoring,
  onStartMonitoring,
  onStopMonitoring,
  loading,
  syncLoading,
  onSync,
  onRefresh,
  candlesData,
  currentWindowCount,
  dataSource,
  onDataSourceChange,
  lastSyncTime,
  onGapFillFrom1m,
  backfillStatus,
  monitorSymbols,
}) {
  const is1s = Number(interval) === 1
  const backfillDone = backfillStatus === 'done'

  return (
    <div className="pro-theme-container">
      {/* 頂部導覽列 */}
      <div className="pro-toolbar">
        <div className="pro-logo">
          <BarChartOutlined style={{ fontSize: '20px' }} />
          <span>PRO TERMINAL</span>
        </div>
        
        <div className="pro-divider"></div>
        
        <div className="symbol-selector-wrapper" style={{ minWidth: '130px', flexShrink: 0 }}>
          <Select
            value={symbol}
            onChange={onSymbolChange}
            options={symbols.map(s => ({ label: s, value: s }))}
            showSearch
            placeholder="搜尋交易對"
            bordered={false}
            style={{ width: '100%' }}
          />
        </div>

        <div className="pro-divider"></div>

        <div className="pro-timeframes">
          {[1, 60, 300, 3600, 14400].map(tf => (
            <button 
              key={tf} 
              className={`pro-btn ${interval === tf ? 'active' : ''}`}
              onClick={() => onIntervalChange(tf)}
            >
              {TIMEFRAME_LABELS[tf] || `${tf}s`}
            </button>
          ))}
          <Select
            value={TIMEFRAME_LABELS[interval] ? undefined : interval}
            placeholder="更多"
            onChange={onIntervalChange}
            options={Object.entries(TIMEFRAME_LABELS)
              .filter(([sec]) => ![1, 60, 300, 3600, 14400].includes(Number(sec)))
              .map(([sec, label]) => ({ label, value: Number(sec) }))
            }
            bordered={false}
            style={{ width: 80 }}
          />
        </div>

        <div className="pro-divider"></div>

        <div className="pro-data-source">
          <Select
            value={dataSource}
            onChange={onDataSourceChange}
            options={[
              { label: '全部來源', value: 'all' },
              { label: 'Real Only', value: 'real' },
              { label: 'Aggregated', value: 'Aggregation' },
            ]}
            bordered={false}
            style={{ width: 110 }}
          />
        </div>

        <div className="pro-divider"></div>

        <div style={{ display: 'flex', gap: '4px' }}>
          <Tooltip title="同步當前資料">
            <button className="pro-btn" onClick={onSync} disabled={syncLoading}>
              <CloudSyncOutlined spin={syncLoading} />
              <span>{syncLoading ? '同步中' : '同步'}</span>
            </button>
          </Tooltip>
          <Tooltip title="重新整理圖表">
            <button className="pro-btn" onClick={onRefresh} disabled={loading}>
              <ReloadOutlined spin={loading} />
            </button>
          </Tooltip>
          {is1s && (
            <Tooltip title="補齊最新1分鐘缺口">
              <button 
                className={`pro-btn ${backfillDone ? '' : 'danger'}`} 
                onClick={onGapFillFrom1m}
                disabled={!backfillDone || loading}
              >
                <LinkOutlined />
                <span>串接</span>
              </button>
            </Tooltip>
          )}
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
          {!monitoring ? (
            <button className="pro-btn primary" onClick={onStartMonitoring}>
              <PlayCircleOutlined />
              <span>START MONITOR</span>
            </button>
          ) : (
            <button className="pro-btn danger active" onClick={onStopMonitoring}>
              <StopOutlined />
              <span>STOP MONITOR</span>
            </button>
          )}
          <button className="pro-btn">
            <SettingOutlined />
          </button>
        </div>
      </div>

      {/* 圖表主區域 */}
      <div className="pro-chart-area">
        <CandlestickChart 
          symbol={symbol}
          interval={interval}
          candlesData={candlesData}
          loading={loading}
          monitoring={monitoring}
          currentWindowCount={currentWindowCount}
        />
      </div>

      {/* 底部狀態列 */}
      <div className="pro-statusbar">
        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="pro-status-item">
            <div className={`pro-status-dot ${monitoring ? 'online' : 'offline'}`}></div>
            <span>
              1s 監控: {monitoring ? `運行中 (${monitorSymbols?.length || 0} 對)` : '已停止'}
            </span>
          </div>
          {is1s && (
            <div className="pro-status-item">
              <DashboardOutlined />
              <span>當前視窗: {currentWindowCount} 根蠟燭</span>
            </div>
          )}
          <div className="pro-status-item">
            <GlobalOutlined />
            <span>資料來源: {dataSource === 'all' ? '混合' : dataSource}</span>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '20px' }}>
          {lastSyncTime && (
            <span>最後同步: {dayjs(lastSyncTime).format('HH:mm:ss')}</span>
          )}
          <span style={{ color: '#2962ff', fontWeight: 'bold' }}>v2.1.0-STABLE</span>
        </div>
      </div>
    </div>
  )
}

export default ProfessionalLayout
