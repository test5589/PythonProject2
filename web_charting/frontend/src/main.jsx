import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  // 暫時關閉 StrictMode，因為它會導致雙重渲染，干擾 Lightweight Charts
  <App />
)
