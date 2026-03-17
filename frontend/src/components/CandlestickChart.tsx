import React, { useRef, useEffect, useState, useCallback } from 'react'
import * as d3 from 'd3'

interface OHLCData {
  date: string; open: number; high: number; low: number; close: number; volume: number
}

interface Props {
  data: OHLCData[]
  newsTimeline: any[]
  selectedDate: string | null
  onDateClick: (date: string) => void
}

export default function CandlestickChart({ data, newsTimeline, selectedDate, onDateClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [range, setRange] = useState<[number, number]>([0, 0])

  // Initialize range when data changes
  useEffect(() => {
    if (data.length > 0) {
      const start = Math.max(0, data.length - 60)
      setRange([start, data.length])
    }
  }, [data])

  // Scroll zoom handler
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault()
    const [start, end] = range
    const visible = end - start
    const delta = e.deltaY > 0 ? Math.ceil(visible * 0.15) : -Math.ceil(visible * 0.15)
    
    // Zoom centered
    const newStart = Math.max(0, start - delta)
    const newEnd = Math.min(data.length, end + delta)
    
    // Min 10 candles, max all data
    if (newEnd - newStart >= 10 && newEnd - newStart <= data.length) {
      setRange([newStart, newEnd])
    }
  }, [range, data.length])

  useEffect(() => {
    const svg = svgRef.current
    if (!svg) return
    svg.addEventListener('wheel', handleWheel, { passive: false })
    return () => svg.removeEventListener('wheel', handleWheel)
  }, [handleWheel])

  useEffect(() => {
    if (!data.length || !svgRef.current || range[1] === 0) return

    const visibleData = data.slice(range[0], range[1])
    if (!visibleData.length) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const margin = { top: 20, right: 60, bottom: 50, left: 10 }
    const width = svgRef.current.clientWidth - margin.left - margin.right
    const height = svgRef.current.clientHeight * 0.65 - margin.top - margin.bottom
    const volHeight = svgRef.current.clientHeight * 0.18

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    const x = d3.scaleBand().domain(visibleData.map(d => d.date)).range([0, width]).padding(0.2)
    const y = d3.scaleLinear()
      .domain([d3.min(visibleData, d => d.low)! * 0.998, d3.max(visibleData, d => d.high)! * 1.002])
      .range([height, 0])
    const yVol = d3.scaleLinear()
      .domain([0, d3.max(visibleData, d => d.volume)!])
      .range([volHeight, 0])

    // Grid
    g.selectAll('.grid-line').data(y.ticks(5)).join('line')
      .attr('x1', 0).attr('x2', width)
      .attr('y1', d => y(d)).attr('y2', d => y(d))
      .attr('stroke', '#1e2a3a').attr('stroke-dasharray', '2,2')

    const newsMap = new Map(newsTimeline.map(n => [n.date, n]))

    // Candles
    const candles = g.selectAll('.candle').data(visibleData).join('g').attr('class', 'candle').style('cursor', 'pointer')

    // Click area
    candles.append('rect')
      .attr('x', d => x(d.date)! - 1).attr('y', 0)
      .attr('width', x.bandwidth() + 2).attr('height', height)
      .attr('fill', 'transparent')
      .on('click', (_, d) => onDateClick(d.date))

    // Selected highlight
    candles.append('rect')
      .attr('x', d => x(d.date)! - 2).attr('y', 0)
      .attr('width', x.bandwidth() + 4).attr('height', height)
      .attr('fill', d => d.date === selectedDate ? 'rgba(68,138,255,0.12)' : 'transparent')

    // Wicks
    candles.append('line')
      .attr('x1', d => x(d.date)! + x.bandwidth() / 2)
      .attr('x2', d => x(d.date)! + x.bandwidth() / 2)
      .attr('y1', d => y(d.high)).attr('y2', d => y(d.low))
      .attr('stroke', d => d.close >= d.open ? '#ff1744' : '#00e676')

    // Bodies
    candles.append('rect')
      .attr('x', d => x(d.date)!)
      .attr('y', d => y(Math.max(d.open, d.close)))
      .attr('width', x.bandwidth())
      .attr('height', d => Math.max(1, Math.abs(y(d.open) - y(d.close))))
      .attr('fill', d => d.close >= d.open ? '#ff1744' : '#00e676')
      .attr('stroke', d => d.date === selectedDate ? '#fff' : 'none')
      .attr('stroke-width', d => d.date === selectedDate ? 1.5 : 0)
      .attr('rx', 1)

    // News dots
    candles.each(function(d) {
      const n = newsMap.get(d.date)
      if (n && n.news_count > 0) {
        d3.select(this).append('circle')
          .attr('cx', x(d.date)! + x.bandwidth() / 2)
          .attr('cy', y(d.high) - 8)
          .attr('r', Math.min(3 + n.news_count, 7))
          .attr('fill', (n.avg_sentiment || 0) >= 0 ? '#ff174488' : '#00e67688')
          .attr('stroke', '#ffffff44').attr('stroke-width', 0.5)
      }
    })

    // Tooltip
    const tooltip = svg.append('g').style('display', 'none')
    const tooltipBg = tooltip.append('rect').attr('fill', '#16213eee').attr('rx', 6).attr('stroke', '#333')
    const tooltipText = tooltip.append('text').attr('fill', '#e8e8e8').attr('font-size', 11)

    candles.on('mouseenter', function(event, d) {
      const xPos = Math.min(x(d.date)! + margin.left + x.bandwidth() + 8, width - 200)
      tooltip.style('display', null).attr('transform', `translate(${xPos},${margin.top + 10})`)
      const change = ((d.close - d.open) / d.open * 100).toFixed(2)
      const nInfo = newsMap.get(d.date)
      const lines = [
        `📅 ${d.date}`,
        `開 ${d.open.toFixed(1)} 收 ${d.close.toFixed(1)} (${Number(change) >= 0 ? '+' : ''}${change}%)`,
        `高 ${d.high.toFixed(1)} 低 ${d.low.toFixed(1)}${nInfo ? ` 📰${nInfo.news_count}` : ''}`,
      ]
      tooltipText.selectAll('tspan').remove()
      lines.forEach((line, i) => {
        tooltipText.append('tspan').attr('x', 8).attr('dy', i === 0 ? 16 : 15).text(line)
      })
      tooltipBg.attr('width', 240).attr('height', lines.length * 17 + 10)
    }).on('mouseleave', () => tooltip.style('display', 'none'))

    // Volume
    const volG = svg.append('g').attr('transform', `translate(${margin.left},${margin.top + height + 25})`)
    volG.selectAll('rect').data(visibleData).join('rect')
      .attr('x', d => x(d.date)!).attr('y', d => yVol(d.volume))
      .attr('width', x.bandwidth()).attr('height', d => volHeight - yVol(d.volume))
      .attr('fill', d => d.close >= d.open ? 'rgba(255,23,68,0.25)' : 'rgba(0,230,118,0.25)')
      .style('cursor', 'pointer').on('click', (_, d) => onDateClick(d.date))

    // Axes
    const tickInterval = Math.max(1, Math.ceil(visibleData.length / 8))
    const xAxis = g.append('g').attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickValues(x.domain().filter((_, i) => i % tickInterval === 0)))
    xAxis.selectAll('text').attr('fill', '#888').attr('font-size', 9)
      .attr('transform', 'rotate(-40)').attr('text-anchor', 'end')
    xAxis.selectAll('line,path').attr('stroke', '#333')

    g.append('g').attr('transform', `translate(${width},0)`)
      .call(d3.axisRight(y).ticks(5).tickFormat(d3.format('.0f')))
      .selectAll('text').attr('fill', '#888').attr('font-size', 10)

    // Zoom info
    svg.append('text')
      .attr('x', margin.left + 5).attr('y', margin.top + height + volHeight + 48)
      .attr('fill', '#555').attr('font-size', 10)
      .text(`顯示 ${visibleData.length}/${data.length} 根 ⟠ 滾輪縮放`)

  }, [data, newsTimeline, selectedDate, range])

  return <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
}
