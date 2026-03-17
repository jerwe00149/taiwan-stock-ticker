import React, { useState } from 'react'
import axios from 'axios'

interface Props {
  symbol: string
}

export default function AnalysisPanel({ symbol }: Props) {
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState<string | null>(null)

  const runAnalysis = async () => {
    setLoading(true)
    try {
      const r = await axios.get(`/api/analysis/${symbol}?days=500`)
      setAnalysis(r.data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const actionColor = (a: string) => a === 'BUY' ? '#ff1744' : a === 'SELL' ? '#00e676' : '#a0a0a0'
  const actionEmoji = (a: string) => a === 'BUY' ? '🔴 買入' : a === 'SELL' ? '🟢 賣出' : '⚪ 觀望'
  const conclusionBadge = (c: string) => c === 'bullish' ? '🟢多' : (c === 'bearish' || c === 'extreme_fear') ? '🔴空' : '⚪中'

  if (!analysis) {
    return (
      <div style={{ maxWidth: 700, margin: '80px auto', textAlign: 'center' }}>
        <div style={{ fontSize: 64, marginBottom: 20 }}>🤖</div>
        <h2 style={{ color: '#e0e0e0', marginBottom: 12, fontSize: 26 }}>多代理市場情緒交易分析</h2>
        <p style={{ color: '#888', fontSize: 16, marginBottom: 32, lineHeight: 1.8 }}>
          四位專業 AI 分析師（基本面、技術面、籌碼面、市場情緒）<br/>
          並行分析後，由交易經理綜合產出決策報告。<br/>
          使用最近 500 個交易日（約2年）的數據進行分析。
        </p>
        <button
          onClick={runAnalysis}
          disabled={loading}
          style={{
            padding: '16px 48px', borderRadius: 12,
            background: loading ? '#333' : 'linear-gradient(135deg, #448aff, #1565c0)',
            color: '#fff', border: 'none', cursor: loading ? 'wait' : 'pointer',
            fontSize: 18, fontWeight: 600, boxShadow: '0 4px 15px rgba(68,138,255,0.3)',
          }}
        >
          {loading ? '⏳ 4位分析師分析中...' : '🚀 啟動多代理分析'}
        </button>
      </div>
    )
  }

  const td = analysis.Trade_Decision
  const reports = analysis.Analysis_Reports
  const agents = analysis.Agent_Conclusions

  const reportEntries = [
    { key: 'Fundamental', label: '🕵️ Agent 1: 基本面分析師', color: '#448aff' },
    { key: 'Technical', label: '📈 Agent 2: 技術面分析師', color: '#ff9100' },
    { key: 'Positioning_and_Chips', label: '🎲 Agent 3: 籌碼與結構分析師', color: '#e040fb' },
    { key: 'Market_Sentiment', label: '🔥 Agent 4: 市場情緒分析師', color: '#ff1744' },
  ]

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      {/* Trade Decision Hero */}
      <div style={{
        background: `linear-gradient(135deg, #0a1628, ${actionColor(td.Action)}11)`,
        borderRadius: 14, padding: 28, marginBottom: 20,
        border: `1px solid ${actionColor(td.Action)}33`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 14, color: '#888', marginBottom: 6 }}>⚖️ 交易經理決策</div>
            <span style={{ fontSize: 34, fontWeight: 700, color: actionColor(td.Action) }}>
              {actionEmoji(td.Action)}
            </span>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 14, color: '#888' }}>信心度</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#e0e0e0' }}>{td.Confidence_Level}</div>
          </div>
        </div>
        
        <div style={{ fontSize: 16, color: '#c0c0c0', marginBottom: 16, lineHeight: 1.7 }}>{td.Reasoning}</div>
        
        {/* Fear/Greed Bar */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#888', marginBottom: 6 }}>
            <span>😱 恐懼</span>
            <span style={{ color: '#e0e0e0', fontWeight: 600, fontSize: 18 }}>{analysis.Fear_Greed_Score}/100</span>
            <span>🤑 貪婪</span>
          </div>
          <div style={{ background: '#1a1a2e', borderRadius: 8, height: 14, overflow: 'hidden' }}>
            <div style={{
              width: `${analysis.Fear_Greed_Score}%`, height: '100%',
              background: 'linear-gradient(90deg, #00e676, #ffeb3b, #ff9100, #ff1744)',
              borderRadius: 8, transition: 'width 0.5s',
            }} />
          </div>
        </div>
        
        {/* Agent badges */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
          {Object.entries(agents).map(([key, val]) => (
            <span key={key} style={{
              fontSize: 15, padding: '5px 14px', borderRadius: 14,
              background: '#16213e', color: '#e0e0e0',
            }}>
              {key === 'fundamental' ? '基本面' : key === 'technical' ? '技術面' :
               key === 'positioning' ? '籌碼面' : '情緒面'} {conclusionBadge(val as string)}
            </span>
          ))}
        </div>

        <div style={{ fontSize: 15, color: '#ff9100', background: '#1a0e00', padding: 12, borderRadius: 8, lineHeight: 1.6 }}>
          ⚠️ {td.Risk_Management}
        </div>
      </div>

      {/* Bull/Bear Debate */}
      {analysis.Bull_Bear_Debate && (
        <div style={{
          background: '#0f0a1e', borderRadius: 12, padding: 20, marginBottom: 20,
          border: '1px solid #e040fb22',
        }}>
          <div style={{ fontSize: 17, fontWeight: 600, color: '#e040fb', marginBottom: 12 }}>⚔️ 多空辯論</div>
          <pre style={{ fontSize: 15, color: '#c0c0c0', whiteSpace: 'pre-wrap', margin: 0, lineHeight: 1.7 }}>
            {analysis.Bull_Bear_Debate}
          </pre>
        </div>
      )}

      {/* Agent Reports */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {reportEntries.map(({ key, label, color }) => {
          const isExpanded = expanded === key
          return (
            <div key={key} style={{
              background: '#0f1a2e', borderRadius: 12, overflow: 'hidden',
              border: `1px solid ${color}22`,
              gridColumn: isExpanded ? '1 / -1' : undefined,
            }}>
              <div
                onClick={() => setExpanded(isExpanded ? null : key)}
                style={{
                  padding: '14px 18px', cursor: 'pointer', fontSize: 16,
                  display: 'flex', justifyContent: 'space-between',
                  color: color, fontWeight: 600,
                }}
              >
                <span>{label}</span>
                <span style={{ color: '#888' }}>{isExpanded ? '▼' : '▶'}</span>
              </div>
              {isExpanded && (
                <pre style={{
                  padding: '14px 18px', fontSize: 15, color: '#b0b0b0',
                  whiteSpace: 'pre-wrap', lineHeight: 1.8, margin: 0,
                  borderTop: `1px solid ${color}22`, background: '#0a1020',
                }}>
                  {reports[key]}
                </pre>
              )}
            </div>
          )
        })}
      </div>

      <button
        onClick={runAnalysis}
        disabled={loading}
        style={{
          marginTop: 20, padding: '12px 24px', borderRadius: 10,
          background: '#16213e', color: '#448aff', border: '1px solid #448aff33',
          cursor: loading ? 'wait' : 'pointer', fontSize: 16, width: '100%',
        }}
      >
        {loading ? '⏳ 分析中...' : '🔄 重新分析'}
      </button>
    </div>
  )
}
