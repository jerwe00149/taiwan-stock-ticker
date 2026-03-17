import React, { useState, useEffect } from 'react'
import axios from 'axios'
import StockSelector from './components/StockSelector'
import CandlestickChart from './components/CandlestickChart'
import NewsPanel from './components/NewsPanel'

const API = '/api'

interface Stock {
  symbol: string
  name: string
  sector: string
  market: string
}

export default function App() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [selected, setSelected] = useState<string>('2330')
  const [ohlc, setOhlc] = useState<any[]>([])
  const [news, setNews] = useState<any[]>([])
  const [newsTimeline, setNewsTimeline] = useState<any[]>([])

  useEffect(() => {
    axios.get(`${API}/stocks`).then(r => setStocks(r.data))
  }, [])

  useEffect(() => {
    if (!selected) return
    axios.get(`${API}/stocks/${selected}/ohlc?limit=120`).then(r => setOhlc(r.data))
    axios.get(`${API}/news/${selected}?limit=50`).then(r => setNews(r.data))
    axios.get(`${API}/news/${selected}/timeline`).then(r => setNewsTimeline(r.data))
  }, [selected])

  const selectedStock = stocks.find(s => s.symbol === selected)

  return (
    <div className="app">
      <header className="header">
        <h1>📈 台股新聞追蹤器</h1>
        {selectedStock && (
          <span style={{ fontSize: 14, color: '#a0a0a0' }}>
            {selectedStock.symbol} {selectedStock.name} — {selectedStock.sector}
          </span>
        )}
      </header>
      
      <div className="sidebar">
        <StockSelector
          stocks={stocks}
          selected={selected}
          onSelect={setSelected}
        />
      </div>
      
      <div className="chart-area">
        <CandlestickChart data={ohlc} newsTimeline={newsTimeline} />
      </div>
      
      <div className="news-panel">
        <NewsPanel news={news} symbol={selected} />
      </div>
    </div>
  )
}
