import React from 'react'

interface NewsItem {
  id: string
  title: string
  description: string
  publisher: string
  published_at: string
  article_url: string
  sentiment: string | null
  sentiment_score: number | null
  summary: string | null
  reason_growth: string | null
  reason_decrease: string | null
  return_t1: number | null
  return_t5: number | null
}

interface Props {
  news: NewsItem[]
  symbol: string
  selectedDate: string | null
}

export default function NewsPanel({ news, symbol, selectedDate }: Props) {
  const sentimentEmoji = (s: string | null) => {
    if (s === 'positive') return '🟢'
    if (s === 'negative') return '🔴'
    return '⚪'
  }

  const formatReturn = (r: number | null) => {
    if (r == null) return '-'
    const pct = (r * 100).toFixed(1)
    return r >= 0 ? `+${pct}%` : `${pct}%`
  }

  return (
    <div>
      <h3 style={{ marginBottom: 12, fontSize: 15, color: '#448aff' }}>
        📰 {symbol} 新聞 
        {selectedDate 
          ? <span style={{ fontSize: 12 }}>（{selectedDate}，{news.length} 篇）</span>
          : <span style={{ fontSize: 12 }}>（共 {news.length} 篇）</span>
        }
      </h3>

      {selectedDate && news.length === 0 && (
        <div style={{ color: '#a0a0a0', textAlign: 'center', padding: 30, background: '#0f3460', borderRadius: 8 }}>
          📅 {selectedDate} 無相關新聞
          <br/><small style={{ color: '#666' }}>點擊其他 K 線或「顯示全部」</small>
        </div>
      )}
      
      {!selectedDate && news.length === 0 && (
        <div style={{ color: '#a0a0a0', textAlign: 'center', padding: 40 }}>
          尚無新聞資料
        </div>
      )}
      
      {news.map(item => (
        <a
          key={item.id}
          href={item.article_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ textDecoration: 'none', color: 'inherit' }}
        >
          <div className="news-card" style={{ transition: 'background 0.2s' }}
               onMouseEnter={e => (e.currentTarget.style.background = '#1a3a6e')}
               onMouseLeave={e => (e.currentTarget.style.background = '')}
          >
            <div className="title">
              {sentimentEmoji(item.sentiment)} {item.title}
            </div>
            
            {item.summary && (
              <div style={{ fontSize: 12, color: '#c0c0c0', marginBottom: 4 }}>
                {item.summary}
              </div>
            )}
            
            {item.description && !item.summary && (
              <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                {item.description.slice(0, 100)}...
              </div>
            )}
            
            {(item.reason_growth || item.reason_decrease) && (
              <div style={{ fontSize: 11, marginBottom: 4 }}>
                {item.reason_growth && (
                  <span className="sentiment-positive">▲ {item.reason_growth}</span>
                )}
                {item.reason_growth && item.reason_decrease && ' | '}
                {item.reason_decrease && (
                  <span className="sentiment-negative">▼ {item.reason_decrease}</span>
                )}
              </div>
            )}
            
            <div className="meta">
              <span>{item.publisher}</span>
              <span style={{ margin: '0 8px' }}>•</span>
              <span>{item.published_at?.slice(0, 10)}</span>
              {item.return_t1 != null && (
                <>
                  <span style={{ margin: '0 8px' }}>•</span>
                  <span style={{ color: (item.return_t1 || 0) >= 0 ? '#ff1744' : '#00e676' }}>
                    T+1: {formatReturn(item.return_t1)}
                  </span>
                </>
              )}
            </div>
          </div>
        </a>
      ))}
    </div>
  )
}
