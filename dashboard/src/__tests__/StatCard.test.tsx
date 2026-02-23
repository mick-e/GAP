import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatCard from '../components/StatCard'

describe('StatCard', () => {
  it('renders label and value', () => {
    render(<StatCard label="Test Metric" value={42} />)
    expect(screen.getByText('Test Metric')).toBeDefined()
    expect(screen.getByText('42')).toBeDefined()
  })

  it('shows positive change in green', () => {
    render(<StatCard label="Growth" value={100} change={15.5} />)
    expect(screen.getByText('+15.5%')).toBeDefined()
  })

  it('shows negative change in red', () => {
    render(<StatCard label="Decline" value={50} change={-10.2} />)
    expect(screen.getByText('-10.2%')).toBeDefined()
  })

  it('shows subtitle when provided', () => {
    render(<StatCard label="Repos" value={10} subtitle="3 private" />)
    expect(screen.getByText('3 private')).toBeDefined()
  })
})
