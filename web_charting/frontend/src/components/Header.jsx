import { Select } from 'antd'
import { useEffect, useState } from 'react'
import './Header.css'

function Header({ symbol, onSymbolChange }) {
  const [symbols, setSymbols] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // 獲取可用的交易對列表
    const fetchSymbols = async () => {
      setLoading(true)
      try {
        const response = await fetch('/api/charts/symbols')
        const data = await response.json()
        if (data.symbols) {
          setSymbols(data.symbols)
        }
      } catch (error) {
        console.error('獲取交易對失敗:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchSymbols()
  }, [])

  const symbolOptions = symbols.map(sym => ({
    label: sym,
    value: sym
  }))

  return (
    <div className="header-container">
      <div className="logo">
        <span className="logo-icon">📊</span>
        <span className="logo-text">Web Charting</span>
      </div>
      
      <div className="symbol-selector">
        <label>交易對：</label>
        <Select
          value={symbol}
          onChange={onSymbolChange}
          options={symbolOptions}
          loading={loading}
          showSearch
          placeholder="選擇交易對"
          style={{ width: 180 }}
          filterOption={(input, option) =>
            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
          }
        />
      </div>
    </div>
  )
}

export default Header
