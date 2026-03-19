import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/client', () => ({
  clearToken: vi.fn(),
}))

import Layout from '../components/Layout'

function renderLayout() {
  return render(
    <MemoryRouter>
      <Layout />
    </MemoryRouter>
  )
}

describe('Layout', () => {
  it('renders sidebar with navigation links', () => {
    renderLayout()
    expect(screen.getByText('GAP')).toBeDefined()
    expect(screen.getByText('Dashboard')).toBeDefined()
    expect(screen.getByText('Repos')).toBeDefined()
    expect(screen.getByText('Contributors')).toBeDefined()
    expect(screen.getByText('Trends')).toBeDefined()
    expect(screen.getByText('Teams')).toBeDefined()
    expect(screen.getByText('Reports')).toBeDefined()
    expect(screen.getByText('Settings')).toBeDefined()
  })

  it('renders logout button', () => {
    renderLayout()
    expect(screen.getByText('Logout')).toBeDefined()
  })
})
