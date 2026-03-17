import React, { useState } from 'react'

interface Props {
  stocks: any[]
  selected: string
  onSelect: (sym: string) => void
}

export default function StockSelector({ stocks, selected, onSelect }: Props) {
  const [search, setSearch] = useState('')
  
  const filtered = stocks.filter(s =>
    s.symbol.includes(search) || s.name.includes(search)
  )

  return (
    <div>
      <input
        type="text"
        placeholder="🔍 搜尋股票..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{
          width: '100%', padding: '8px 12px', borderRadius: 6,
          border: '1px solid #333', background: '#0f3460', color: '#e8e8e8',
          marginBottom: 8, fontSize: 13,
        }}
      />
      {filtered.map(s => (
        <div
          key={s.symbol}
          className={`stock-item ${s.symbol === selected ? 'active' : ''}`}
          onClick={() => onSelect(s.symbol)}
        >
          <div>
            <div className="symbol">{s.symbol}</div>
            <div className="name">{s.name}</div>
          </div>
          <div className="name">{s.sector}</div>
        </div>
      ))}
    </div>
  )
}
