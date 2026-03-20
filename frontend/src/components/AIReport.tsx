
import React, { useState, useEffect } from "react"
import axios from "axios"

export default function AIReport() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get("/api/ai-dashboard").then(r => {
      setData(r.data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div style={{padding:24,textAlign:"center",color:"#888"}}>載入中...</div>
  if (!data || !data.ai_dashboard) return <div style={{padding:24,textAlign:"center",color:"#888"}}>尚無分析報告（每日 14:30 自動更新）</div>

  return (
    <div style={{padding:16,maxWidth:900,margin:"0 auto"}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
        <h2 style={{fontSize:18,color:"#448aff",margin:0}}>📊 每日決策儀表板</h2>
        <span style={{fontSize:13,color:"#666"}}>{data.date}</span>
      </div>
      
      {/* Market Overview */}
      {data.market && (
        <div style={{background:"#0a1628",borderRadius:10,padding:16,marginBottom:12,border:"1px solid #1e2a3a"}}>
          <div style={{fontSize:14,fontWeight:600,color:"#ff9100",marginBottom:8}}>📈 大盤復盤</div>
          <pre style={{fontSize:13,color:"#c0c0c0",whiteSpace:"pre-wrap",lineHeight:1.7,margin:0}}>{data.market}</pre>
        </div>
      )}
      
      {/* Stock Scores */}
      {Object.keys(data.stocks || {}).length > 0 && (
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8,marginBottom:12}}>
          {Object.entries(data.stocks).map(([sym, info]: [string, any]) => (
            <div key={sym} style={{
              background:"#0f1a2e",borderRadius:8,padding:12,
              border:"1px solid " + (info.signal?.includes("買") ? "#ff174433" : info.signal?.includes("賣") ? "#00e67633" : "#1e2a3a")
            }}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <span style={{fontWeight:600,fontSize:14}}>{sym}</span>
                <span style={{
                  fontSize:12,padding:"2px 8px",borderRadius:10,
                  background: info.signal?.includes("買") ? "#ff174422" : info.signal?.includes("賣") ? "#00e67622" : "#ffb74d22",
                  color: info.signal?.includes("買") ? "#ff1744" : info.signal?.includes("賣") ? "#00e676" : "#ffb74d"
                }}>{info.signal || "觀望"}</span>
              </div>
              <div style={{fontSize:20,fontWeight:700,marginTop:4}}>{info.score?.toFixed(1) || "-"}</div>
              <div style={{fontSize:11,color:"#888",marginTop:4}}>{info.summary?.substring(0,40) || ""}</div>
            </div>
          ))}
        </div>
      )}
      
      {/* AI Dashboard */}
      <div style={{background:"#0a1628",borderRadius:10,padding:16,border:"1px solid #1e2a3a"}}>
        <div style={{fontSize:14,fontWeight:600,color:"#00e5ff",marginBottom:8}}>🤖 AI 決策分析</div>
        <pre style={{fontSize:13,color:"#c0c0c0",whiteSpace:"pre-wrap",lineHeight:1.7,margin:0}}>{data.ai_dashboard}</pre>
      </div>
    </div>
  )
}
