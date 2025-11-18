import { Button, Radio, Space, Tag } from 'antd'
import { SyncOutlined, ReloadOutlined, ClockCircleOutlined, PlayCircleOutlined, StopOutlined, LinkOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import './ControlPanel.css'

function ControlPanel({ 
  dataSource, 
  onDataSourceChange, 
  onSync, 
  onRefresh, 
  loading, 
  syncLoading,
  lastSyncTime,
  monitoring,
  monitorLoading,
  monitorSymbols,
  onStartMonitoring,
  onStopMonitoring,
  interval,
  backfillStatus,
  onGapFillFrom1m,
}) {
  const is1s = Number(interval) === 1
  const backfillDone = backfillStatus === 'done'

  return (
    <div className="control-panel">
      <div className="control-section">
        <div className="control-label">資料來源：</div>
        <Radio.Group value={dataSource} onChange={e => onDataSourceChange(e.target.value)}>
          <Radio.Button value="all">全部</Radio.Button>
          <Radio.Button value="real">Real</Radio.Button>
          <Radio.Button value="Aggregation">Aggregation</Radio.Button>
        </Radio.Group>
      </div>

      <div className="control-section">
        <Space>
          <Button
            type="primary"
            icon={<SyncOutlined spin={loading} />}
            onClick={onSync}
            loading={syncLoading}
          >
            同步資料
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={onRefresh}
            loading={loading}
          >
            重新整理
          </Button>
          <Button
            icon={<LinkOutlined />}
            onClick={onGapFillFrom1m}
            disabled={!is1s || !backfillDone || loading}
          >
            最新1分鐘串接（缺口）
          </Button>
          <Button
            type={monitoring ? 'default' : 'primary'}
            icon={<PlayCircleOutlined />}
            onClick={onStartMonitoring}
            loading={monitorLoading}
            disabled={monitoring}
          >
            啟動 1秒監控
          </Button>
          <Button
            danger
            icon={<StopOutlined />}
            onClick={onStopMonitoring}
            loading={monitorLoading}
            disabled={!monitoring}
          >
            停止 1秒監控
          </Button>
        </Space>
      </div>

      <div className="control-section">
        {lastSyncTime && (
          <Tag icon={<ClockCircleOutlined />} color="success" style={{ marginRight: 8 }}>
            最後同步: {dayjs(lastSyncTime).format('YYYY-MM-DD HH:mm:ss')}
          </Tag>
        )}
        <Tag color={monitoring ? 'processing' : 'default'}>
          1秒監控：{monitoring ? '運行中' : '已停止'}
          {monitoring && Array.isArray(monitorSymbols) && (
            <>（{monitorSymbols.length} 個貨幣對）</>
          )}
        </Tag>
      </div>
    </div>
  )
}

export default ControlPanel
