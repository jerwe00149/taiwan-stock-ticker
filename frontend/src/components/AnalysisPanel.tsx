import React, { useState, useEffect } from 'react'
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
      const r = await axios.get(`/api/analysis/${symbol}`)
      setAnalysis(r.data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const actionColor = (a: string) => {
    if (a === 'BUY') return '#ff1744'
    if (a === 'SELL') return '#00e676'
    return '#a0a0a0'
  }

  const actionEmoji = (a: string) => {
    if (a === 'BUY') return '🔴 買入'
    if (a === 'SELL') return '🟢 賣出'
    return '⚪ 觀望'
  }

  const conclusionBadge = (c: string) => {
    if (c === 'bullish') return '🟢多'
    if (c === 'bearish' || c === 'extreme_fear') return '🔴空'
    return '⚪中'
  }

  if (!analysis) {
    return (
      <div style={{ padding: 16, textAlign: 'center' }}>
        <button
          onClick={runAnalysis}
          disabled={loading}
          style={{
            padding: '12px 24px', borderRadius: 8,
            background: loading ? '#333' : '#448aff', color: '#fff',
            border: 'none', cursor: loading ? 'wait' : 'pointer',
            fontSize: 14, fontWeight: 600, width: '100%',
          }}
        >
          {loading ? '⏳ 分析中...' : '🤖 啟動多代理分析'}
        </button>
      </div>
    )
  }

  const td = analysis.Trade_Decision
  const reports = analysis.Analysis_Reports
  const agents = analysis.Agent_Conclusions

  return (
    <div style={{ padding: 8 }}>
      {/* Trade Decision Card */}
      <div style={{
        background: '#0a1628', borderRadius: 10, padding: 16, marginBottom: 12,
        border: `1px solid ${actionColor(td.Action)}44`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 20, fontWeight: 700, color: actionColor(td.Action) }}>
            {actionEmoji(td.Action)}
          </span>
          <span style={{ fontSize: 13, color: '#a0a0a0' }}>
            信心：{td.Confidence_Level}
          </span>
        </div>
        
        <div style={{ fontSize: 12, color: '#c0c0c0', marginBottom: 8 }}>{td.Reasoning}</div>
        
        {/* Fear/Greed gauge */}
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>
            恐懼 ← {analysis.Fear_Greed_Score}/100 → 貪婪
          </div>
          <div style={{ background: '#1a1a2e', borderRadius: 4, height: 8, overflow: 'hidden' }}>
            <div style={{
              width: `${analysis.Fear_Greed_Score}%`, height: '100%',
              background: `linear-gradient(90deg, #00e676, #ffeb3b, #ff1744)`,
              borderRadius: 4,
            }} />
          </div>
        </div>
        
        {/* Agent conclusions */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
          {Object.entries(agents).map(([key, val]) => (
            <span key={key} style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 12,
              background: '#16213e', color: '#e0e0e0',
            }}>
              {key === 'fundamental' ? '基本' : key === 'technical' ? '技術' :
               key === 'positioning' ? '籌碼' : '情緒'} {conclusionBadge(val as string)}
            </span>
          ))}
        </div>
        
        <div style={{ fontSize: 11, color: '#888' }}>
          ⚠️ {td.Risk_Management}
        </div>
      </div>

      {/* Expandable Agent Reports */}
      {Object.entries(reports).map(([key, report]) => {
        const label = key === 'Fundamental' ? '🕵️ 基本面' :
                      key === 'Technical' ? '📈 技術面' :
                      key === 'Positioning_and_Chips' ? '🎲 籌碼面' : '🔥 情緒面'
        const isExpanded = expanded === key
        return (
          <div key={key} style={{
            background: '#0f1a2e', borderRadius: 8, marginBottom: 4,
            overflow: 'hidden',
          }}>
            <div
              onClick={() => setExpanded(isExpanded ? null : key)}
              style={{
                padding: '8px 12px', cursor: 'pointer', fontSize: 13,
                display: 'flex', justifyContent: 'space-between',
                color: '#c0c0c0',
              }}
            >
              <span>{label}</span>
              <span>{isExpanded ? '▼' : '▶'}</span>
            </div>
            {isExpanded && (
              <pre style={{
                padding: '8px 12px', fontSize: 11, color: '#a0a0a0',
                whiteSpace: 'pre-wrap', lineHeight: 1.6, margin: 0,
                borderTop: '1px solid #1e2a3a',
              }}>
                {report as string}
              </pre>
            )}
          </div>
        )
      })}

      {/* Bull/Bear Debate */}
      {analysis.Bull_Bear_Debate && (
        <div style={{
          background: '#1a0a0a', borderRadius: 8, padding: 12, marginTop: 8,
          border: '1px solid #ff174433',
        }}>
          <pre style={{ fontSize: 11, color: '#c0c0c0', whiteSpace: 'pre-wrap', margin: 0 }}>
            {analysis.Bull_Bear_Debate}
          </pre>
        </div>
      )}

      <button
        onClick={runAnalysis}
        style={{
          marginTop: 8, padding: '8px 16px', borderRadius: 6,
          background: '#16213e', color: '#448aff', border: '1px solid #448aff33',
          cursor: 'pointer', fontSize: 12, width: '100%',
        }}
      >
        🔄 重新分析
      </button>
    </div>
  )
}
