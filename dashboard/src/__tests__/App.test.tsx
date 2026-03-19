import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/client', () => ({
  isAuthenticated: vi.fn(() => false),
  setToken: vi.fn(),
  clearToken: vi.fn(),
  auth: { me: vi.fn(), login: vi.fn(), register: vi.fn(), listApiKeys: vi.fn(), createApiKey: vi.fn(), deleteApiKey: vi.fn() },
  org: { summary: vi.fn(), repos: vi.fn() },
  trends: { overview: vi.fn(), sparklines: vi.fn(), metric: vi.fn(), compare: vi.fn() },
  teams: { metrics: vi.fn(), dora: vi.fn(), compare: vi.fn() },
  contributors: { list: vi.fn(), get: vi.fn(), activity: vi.fn(), rankings: vi.fn() },
  schedules: { list: vi.fn(), create: vi.fn(), delete: vi.fn(), run: vi.fn() },
  repo: { commits: vi.fn(), pulls: vi.fn(), issues: vi.fn(), releases: vi.fn(), security: vi.fn(), workflows: vi.fn() },
  reports: { activity: vi.fn(), quality: vi.fn(), releases: vi.fn() },
}))

import App from '../App'
import * as client from '../api/client'

function renderApp(route = '/') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('App routing', () => {
  beforeEach(() => {
    vi.mocked(client.isAuthenticated).mockReturnValue(false)
  })

  it('redirects to login when not authenticated', async () => {
    renderApp('/')
    await waitFor(() => {
      expect(screen.getByText('GAP')).toBeDefined()
    })
    expect(screen.getByText('GitHub Analytics Dashboard')).toBeDefined()
  })

  it('shows login page at /login', async () => {
    renderApp('/login')
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Email')).toBeDefined()
    })
    expect(screen.getByPlaceholderText('Password')).toBeDefined()
  })

  it('shows register link on login page', async () => {
    renderApp('/login')
    await waitFor(() => {
      expect(screen.getByText('Register')).toBeDefined()
    })
  })
})
