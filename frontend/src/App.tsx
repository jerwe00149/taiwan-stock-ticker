import React, { useState, useEffect } from 'react'
import axios from 'axios'
import StockSelector from './components/StockSelector'
import CandlestickChart from './components/CandlestickChart'
import NewsPanel from './components/NewsPanel'
import AnalysisPanel from './components/AnalysisPanel'
import AIReport from './components/AIReport'

const API = '/api'

interface Stock { symbol: string; name: string; sector: string; market: string }
type View = 'main' | 'analysis' | 'dashboard'

export default function App() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [selected, setSelected] = useState('2330')
  const [ohlc, setOhlc] = useState<any[]>([])
  const [news, setNews] = useState<any[]>([])
  const [newsTimeline, setNewsTimeline] = useState<any[]>([])
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [view, setView] = useState<View>('main')

  useEffect(() => { axios.get(`${API}/stocks`).then(r => setStocks(r.data)) }, [])

  useEffect(() => {
    if (!selected) return
    axios.get(`${API}/stocks/${selected}/ohlc?limit=500`).then(r => setOhlc(r.data))
    axios.get(`${API}/news/${selected}?limit=100`).then(r => setNews(r.data))
    axios.get(`${API}/news/${selected}/timeline`).then(r => setNewsTimeline(r.data))
    setSelectedDate(null)
  }, [selected])

  const selectedStock = stocks.find(s => s.symbol === selected)
  const filteredNews = selectedDate ? news.filter(n => n.published_at?.startsWith(selectedDate)) : news

  const tabStyle = (v: View) => ({
    padding: '4px 14px', borderRadius: 6, border: 'none', cursor: 'pointer' as const, fontSize: 13,
    background: view === v ? '#448aff' : '#1e2a3a',
    color: view === v ? '#fff' : '#a0a0a0',
  })

  return (
    <div className="app" style={{
      display: 'grid',
      gridTemplateColumns: view === 'main' ? '220px 1fr 320px' : '220px 1fr',
      gridTemplateRows: '50px 1fr',
      height: '100vh', gap: 1, background: '#0d1117',
    }}>
      <header style={{
        gridColumn: '1 / -1', background: '#16213e',
        display: 'flex', alignItems: 'center', padding: '0 16px', gap: 12,
      }}>
        <h1 style={{ fontSize: 16, color: '#448aff', margin: 0 }}>📈 台股追蹤器</h1>
        <div style={{ display: 'flex', gap: 4, marginLeft: 12 }}>
          <button onClick={() => setView('main')} style={tabStyle('main')}>📊 行情</button>
          <button onClick={() => setView('dashboard')} style={tabStyle('dashboard')}>📋 每日報告</button>
          <button onClick={() => setView('analysis')} style={tabStyle('analysis')}>🤖 多代理分析</button>
        </div>
        {selectedStock && (
          <span style={{ fontSize: 13, color: '#a0a0a0' }}>
            {selectedStock.symbol} {selectedStock.name} — {selectedStock.sector}
          </span>
        )}
        {selectedDate && (
          <span style={{ fontSize: 12, color: '#448aff', cursor: 'pointer', marginLeft: 'auto' }}
            onClick={() => setSelectedDate(null)}>📅 {selectedDate} ✕</span>
        )}
      </header>

      <div style={{ background: '#16213e', overflowY: 'auto', padding: 10 }}>
        <StockSelector stocks={stocks} selected={selected} onSelect={setSelected} />
      </div>

      {view === 'main' ? (
        <>
          <div style={{ background: '#1a1a2e', padding: 12, overflow: 'hidden' }}>
            <CandlestickChart data={ohlc} newsTimeline={newsTimeline}
              selectedDate={selectedDate}
              onDateClick={(date: string) => setSelectedDate(date === selectedDate ? null : date)} />
          </div>
          <div style={{ background: '#16213e', overflowY: 'auto', padding: 10 }}>
            <NewsPanel news={filteredNews} symbol={selected} selectedDate={selectedDate} />
          </div>
        </>
      ) : view === 'dashboard' ? (
        <div style={{ background: '#16213e', overflowY: 'auto', padding: 16 }}>
          <AIReport />
        </div>
      ) : (
        <div style={{ background: '#16213e', overflowY: 'auto', padding: 16 }}>
          <AnalysisPanel symbol={selected} />
        </div>
      )}
    </div>
  )
}
