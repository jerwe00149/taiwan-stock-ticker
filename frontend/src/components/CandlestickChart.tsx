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
}

export default function CandlestickChart({ data, newsTimeline }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!data.length || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const margin = { top: 20, right: 60, bottom: 60, left: 60 }
    const width = svgRef.current.clientWidth - margin.left - margin.right
    const height = svgRef.current.clientHeight * 0.7 - margin.top - margin.bottom
    const volHeight = svgRef.current.clientHeight * 0.2

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const x = d3.scaleBand()
      .domain(data.map(d => d.date))
      .range([0, width])
      .padding(0.3)

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
    g.append('g').attr('class', 'grid')
      .selectAll('line')
      .data(y.ticks(6))
      .join('line')
      .attr('x1', 0).attr('x2', width)
      .attr('y1', d => y(d)).attr('y2', d => y(d))
      .attr('stroke', '#1e2a3a').attr('stroke-dasharray', '2,2')

    // Candlesticks
    const candles = g.selectAll('.candle')
      .data(data)
      .join('g')
      .attr('class', 'candle')

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
      .attr('rx', 1)

    // Volume bars
    const volG = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top + height + 20})`)

    volG.selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', d => x(d.date)!)
      .attr('y', d => yVol(d.volume))
      .attr('width', x.bandwidth())
      .attr('height', d => volHeight - yVol(d.volume))
      .attr('fill', d => d.close >= d.open ? 'rgba(255,23,68,0.4)' : 'rgba(0,230,118,0.4)')

    // News dots
    const newsMap = new Map(newsTimeline.map(n => [n.date, n]))
    candles.each(function(d) {
      const n = newsMap.get(d.date)
      if (n && n.news_count > 0) {
        d3.select(this).append('circle')
          .attr('cx', x(d.date)! + x.bandwidth() / 2)
          .attr('cy', y(d.high) - 8)
          .attr('r', Math.min(4 + n.news_count, 8))
          .attr('fill', (n.avg_sentiment || 0) >= 0 ? '#ff174488' : '#00e67688')
          .attr('stroke', '#fff')
          .attr('stroke-width', 0.5)
      }
    })

    // Axes
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickValues(
        x.domain().filter((_, i) => i % Math.ceil(data.length / 10) === 0)
      ))
    xAxis.selectAll('text').attr('fill', '#a0a0a0').attr('font-size', 10)
      .attr('transform', 'rotate(-45)').attr('text-anchor', 'end')
    xAxis.selectAll('line,path').attr('stroke', '#333')

    const yAxis = g.append('g')
      .attr('transform', `translate(${width},0)`)
      .call(d3.axisRight(y).ticks(6).tickFormat(d3.format('.1f')))
    yAxis.selectAll('text').attr('fill', '#a0a0a0').attr('font-size', 11)
    yAxis.selectAll('line,path').attr('stroke', '#333')

  }, [data, newsTimeline])

  return (
    <svg
      ref={svgRef}
      style={{ width: '100%', height: '100%' }}
    />
  )
}
