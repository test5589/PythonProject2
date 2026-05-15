import BaseCandlestickChart from './BaseCandlestickChart'

// 薄包裝：保留原本的元件名稱與對外介面，實作搬到 BaseCandlestickChart
function CandlestickChart(props) {
  return <BaseCandlestickChart {...props} />
}

export default CandlestickChart
