import React, { useRef, useEffect } from 'react'
import * as d3 from 'd3'

interface OHLCData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface Props {
  data: OHLCData[]
  newsTimeline: any[]
  selectedDate: string | null
  onDateClick: (date: string) => void
}

export default function CandlestickChart({ data, newsTimeline, selectedDate, onDateClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!data.length || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const margin = { top: 20, right: 60, bottom: 60, left: 60 }
    const width = svgRef.current.clientWidth - margin.left - margin.right
    const height = svgRef.current.clientHeight * 0.65 - margin.top - margin.bottom
    const volHeight = svgRef.current.clientHeight * 0.2

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const x = d3.scaleBand()
      .domain(data.map(d => d.date))
      .range([0, width])
      .padding(0.2)

    const y = d3.scaleLinear()
      .domain([
        d3.min(data, d => d.low)! * 0.995,
        d3.max(data, d => d.high)! * 1.005,
      ])
      .range([height, 0])

    const yVol = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.volume)!])
      .range([volHeight, 0])

    // Grid
    g.append('g')
      .selectAll('line')
      .data(y.ticks(6))
      .join('line')
      .attr('x1', 0).attr('x2', width)
      .attr('y1', d => y(d)).attr('y2', d => y(d))
      .attr('stroke', '#1e2a3a').attr('stroke-dasharray', '2,2')

    // News map
    const newsMap = new Map(newsTimeline.map(n => [n.date, n]))

    // Candlesticks
    const candles = g.selectAll('.candle')
      .data(data)
      .join('g')
      .attr('class', 'candle')
      .style('cursor', 'pointer')

    // Click handler - invisible rect for easier clicking
    candles.append('rect')
      .attr('x', d => x(d.date)! - 2)
      .attr('y', 0)
      .attr('width', x.bandwidth() + 4)
      .attr('height', height)
      .attr('fill', 'transparent')
      .on('click', (_, d) => onDateClick(d.date))

    // Selected date highlight
    candles.append('rect')
      .attr('x', d => x(d.date)! - 3)
      .attr('y', 0)
      .attr('width', x.bandwidth() + 6)
      .attr('height', height)
      .attr('fill', d => d.date === selectedDate ? 'rgba(68,138,255,0.15)' : 'transparent')
      .attr('rx', 3)

    // High-Low lines
    candles.append('line')
      .attr('x1', d => x(d.date)! + x.bandwidth() / 2)
      .attr('x2', d => x(d.date)! + x.bandwidth() / 2)
      .attr('y1', d => y(d.high))
      .attr('y2', d => y(d.low))
      .attr('stroke', d => d.close >= d.open ? '#ff1744' : '#00e676')
      .attr('stroke-width', 1)

    // Bodies
    candles.append('rect')
      .attr('x', d => x(d.date)!)
      .attr('y', d => y(Math.max(d.open, d.close)))
      .attr('width', x.bandwidth())
      .attr('height', d => Math.max(1, Math.abs(y(d.open) - y(d.close))))
      .attr('fill', d => d.close >= d.open ? '#ff1744' : '#00e676')
      .attr('stroke', d => d.date === selectedDate ? '#fff' : 'none')
      .attr('stroke-width', d => d.date === selectedDate ? 2 : 0)
      .attr('rx', 1)

    // News dots (on candles that have news)
    candles.each(function(d) {
      const n = newsMap.get(d.date)
      if (n && n.news_count > 0) {
        d3.select(this).append('circle')
          .attr('cx', x(d.date)! + x.bandwidth() / 2)
          .attr('cy', y(d.high) - 10)
          .attr('r', Math.min(3 + n.news_count * 1.5, 9))
          .attr('fill', (n.avg_sentiment || 0) >= 0 ? '#ff174499' : '#00e67699')
          .attr('stroke', d.date === selectedDate ? '#fff' : '#ffffff44')
          .attr('stroke-width', d.date === selectedDate ? 2 : 0.5)
        
        // News count label
        if (n.news_count > 1) {
          d3.select(this).append('text')
            .attr('x', x(d.date)! + x.bandwidth() / 2)
            .attr('y', y(d.high) - 7)
            .attr('text-anchor', 'middle')
            .attr('font-size', 8)
            .attr('fill', '#fff')
            .attr('font-weight', 'bold')
            .text(n.news_count)
        }
      }
    })

    // Tooltip on hover
    const tooltip = svg.append('g').style('display', 'none')
    const tooltipBg = tooltip.append('rect')
      .attr('fill', '#16213e').attr('rx', 6).attr('stroke', '#333')
    const tooltipText = tooltip.append('text')
      .attr('fill', '#e8e8e8').attr('font-size', 11)

    candles.on('mouseenter', function(event, d) {
      const xPos = x(d.date)! + margin.left + x.bandwidth() + 10
      const yPos = margin.top + 20
      tooltip.style('display', null).attr('transform', `translate(${xPos},${yPos})`)
      
      const change = ((d.close - d.open) / d.open * 100).toFixed(2)
      const changeStr = d.close >= d.open ? `+${change}%` : `${change}%`
      const newsInfo = newsMap.get(d.date)
      const newsStr = newsInfo ? ` | 📰${newsInfo.news_count}篇` : ''
      
      const lines = [
        `📅 ${d.date}`,
        `開 ${d.open.toFixed(1)} | 收 ${d.close.toFixed(1)} (${changeStr})`,
        `高 ${d.high.toFixed(1)} | 低 ${d.low.toFixed(1)}${newsStr}`,
      ]
      
      tooltipText.selectAll('tspan').remove()
      lines.forEach((line, i) => {
        tooltipText.append('tspan')
          .attr('x', 8).attr('dy', i === 0 ? 16 : 16)
          .text(line)
      })
      
      tooltipBg.attr('width', 260).attr('height', lines.length * 18 + 12)
    })
    .on('mouseleave', () => tooltip.style('display', 'none'))

    // Volume bars
    const volG = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top + height + 30})`)

    volG.selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', d => x(d.date)!)
      .attr('y', d => yVol(d.volume))
      .attr('width', x.bandwidth())
      .attr('height', d => volHeight - yVol(d.volume))
      .attr('fill', d => d.close >= d.open ? 'rgba(255,23,68,0.3)' : 'rgba(0,230,118,0.3)')
      .style('cursor', 'pointer')
      .on('click', (_, d) => onDateClick(d.date))

    // Axes
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickValues(
        x.domain().filter((_, i) => i % Math.ceil(data.length / 8) === 0)
      ))
    xAxis.selectAll('text').attr('fill', '#a0a0a0').attr('font-size', 10)
      .attr('transform', 'rotate(-45)').attr('text-anchor', 'end')
    xAxis.selectAll('line,path').attr('stroke', '#333')

    const yAxis = g.append('g')
      .attr('transform', `translate(${width},0)`)
      .call(d3.axisRight(y).ticks(6).tickFormat(d3.format('.0f')))
    yAxis.selectAll('text').attr('fill', '#a0a0a0').attr('font-size', 11)
    yAxis.selectAll('line,path').attr('stroke', '#333')

  }, [data, newsTimeline, selectedDate])

  return (
    <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
  )
}
