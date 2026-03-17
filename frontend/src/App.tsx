import React, { useState, useEffect } from 'react'
import axios from 'axios'
import StockSelector from './components/StockSelector'
import CandlestickChart from './components/CandlestickChart'
import NewsPanel from './components/NewsPanel'
import AnalysisPanel from './components/AnalysisPanel'

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
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  useEffect(() => {
    axios.get(`${API}/stocks`).then(r => setStocks(r.data))
  }, [])

  useEffect(() => {
    if (!selected) return
    axios.get(`${API}/stocks/${selected}/ohlc?limit=250`).then(r => setOhlc(r.data))
    axios.get(`${API}/news/${selected}?limit=100`).then(r => setNews(r.data))
    axios.get(`${API}/news/${selected}/timeline`).then(r => setNewsTimeline(r.data))
    setSelectedDate(null)
  }, [selected])

  const selectedStock = stocks.find(s => s.symbol === selected)

  // Filter news by selected date
  const filteredNews = selectedDate
    ? news.filter(n => n.published_at?.startsWith(selectedDate))
    : news

  return (
    <div className="app">
      <header className="header">
        <h1>📈 台股新聞追蹤器</h1>
        {selectedStock && (
          <span style={{ fontSize: 14, color: '#a0a0a0' }}>
            {selectedStock.symbol} {selectedStock.name} — {selectedStock.sector}
          </span>
        )}
        {selectedDate && (
          <span 
            style={{ fontSize: 13, color: '#448aff', cursor: 'pointer', marginLeft: 'auto' }}
            onClick={() => setSelectedDate(null)}
          >
            📅 {selectedDate} ✕ 顯示全部
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
        <CandlestickChart 
          data={ohlc} 
          newsTimeline={newsTimeline}
          selectedDate={selectedDate}
          onDateClick={(date) => setSelectedDate(date === selectedDate ? null : date)}
        />
      </div>
      
      <div className="news-panel">
        <NewsPanel 
          news={filteredNews} 
          symbol={selected}
          selectedDate={selectedDate}
        />
      </div>
      
      <div className="news-panel">
        <h3 style={{ marginBottom: 12, fontSize: 15, color: '#448aff', padding: '0 8px' }}>
          🤖 多代理交易分析
        </h3>
        <AnalysisPanel symbol={selected} />
      </div>
    </div>
  )
}
