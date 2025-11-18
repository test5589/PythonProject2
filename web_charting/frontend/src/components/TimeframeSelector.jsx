import { Button } from 'antd'
import { useEffect, useState } from 'react'
import './TimeframeSelector.css'

const TIMEFRAME_LABELS = {
  1: '1s',
  2: '2s',
  5: '5s',
  10: '10s',
  15: '15s',
  30: '30s',
  60: '1m',
  300: '5m',
  600: '10m',
  1800: '30m',
  3600: '1h',
  14400: '4h',
  28800: '8h',
}

function TimeframeSelector({ interval, onIntervalChange }) {
  const [timeframes, setTimeframes] = useState([])

  useEffect(() => {
    // 獲取支持的時間框架
    const fetchTimeframes = async () => {
      try {
        const response = await fetch('/api/charts/timeframes')
        const data = await response.json()
        if (data.timeframes) {
          setTimeframes(data.timeframes)
        }
      } catch (error) {
        console.error('獲取時間框架失敗:', error)
        // 使用預設值
        setTimeframes(
          Object.entries(TIMEFRAME_LABELS).map(([seconds, label]) => ({
            seconds: parseInt(seconds),
            label
          }))
        )
      }
    }
    fetchTimeframes()
  }, [])

  return (
    <div className="timeframe-selector">
      <div className="timeframe-label">時間框架：</div>
      <div className="timeframe-buttons">
        {timeframes.map(({ seconds, label }) => (
          <Button
            key={seconds}
            type={interval === seconds ? 'primary' : 'default'}
            onClick={() => onIntervalChange(seconds)}
            className={interval === seconds ? 'active' : ''}
          >
            {label}
          </Button>
        ))}
      </div>
    </div>
  )
}

export default TimeframeSelector
