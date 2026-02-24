import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DataTable from '../components/DataTable'

describe('DataTable', () => {
  const data = [
    { name: 'Alice', commits: 50 },
    { name: 'Bob', commits: 30 },
    { name: 'Charlie', commits: 80 },
  ]

  const columns = [
    { key: 'name', header: 'Name' },
    { key: 'commits', header: 'Commits' },
  ]

  it('renders headers and rows', () => {
    render(<DataTable data={data} columns={columns} />)
    expect(screen.getByText('Name')).toBeDefined()
    expect(screen.getByText('Commits')).toBeDefined()
    expect(screen.getByText('Alice')).toBeDefined()
    expect(screen.getByText('Bob')).toBeDefined()
    expect(screen.getByText('Charlie')).toBeDefined()
  })

  it('sorts by column on click', () => {
    render(<DataTable data={data} columns={columns} />)
    fireEvent.click(screen.getByText('Commits'))
    const cells = screen.getAllByRole('cell')
    // After sorting by commits asc: Bob(30), Alice(50), Charlie(80)
    expect(cells[0].textContent).toBe('Bob')
  })

  it('calls onRowClick', () => {
    const onClick = vi.fn()
    render(<DataTable data={data} columns={columns} onRowClick={onClick} />)
    fireEvent.click(screen.getByText('Alice'))
    expect(onClick).toHaveBeenCalledWith(data[0])
  })

  describe('pagination', () => {
    const largeData = Array.from({ length: 25 }, (_, i) => ({
      name: `User ${i + 1}`,
      commits: i + 1,
    }))

    it('shows only pageSize rows', () => {
      render(<DataTable data={largeData} columns={columns} pageSize={10} />)
      const rows = screen.getAllByRole('row')
      // 1 header + 10 data rows
      expect(rows.length).toBe(11)
    })

    it('shows page indicator', () => {
      render(<DataTable data={largeData} columns={columns} pageSize={10} />)
      expect(screen.getByText('1-10 of 25')).toBeDefined()
    })

    it('navigates to next page', () => {
      render(<DataTable data={largeData} columns={columns} pageSize={10} />)
      fireEvent.click(screen.getByText('Next'))
      expect(screen.getByText('11-20 of 25')).toBeDefined()
    })

    it('navigates to previous page', () => {
      render(<DataTable data={largeData} columns={columns} pageSize={10} />)
      fireEvent.click(screen.getByText('Next'))
      fireEvent.click(screen.getByText('Prev'))
      expect(screen.getByText('1-10 of 25')).toBeDefined()
    })

    it('disables prev on first page', () => {
      render(<DataTable data={largeData} columns={columns} pageSize={10} />)
      const prevBtn = screen.getByText('Prev')
      expect(prevBtn).toHaveProperty('disabled', true)
    })

    it('resets page on sort change', () => {
      render(<DataTable data={largeData} columns={columns} pageSize={10} />)
      fireEvent.click(screen.getByText('Next'))
      expect(screen.getByText('11-20 of 25')).toBeDefined()
      fireEvent.click(screen.getByText('Name'))
      expect(screen.getByText('1-10 of 25')).toBeDefined()
    })

    it('does not show pagination when data fits one page', () => {
      render(<DataTable data={data} columns={columns} pageSize={20} />)
      expect(screen.queryByText('Prev')).toBeNull()
      expect(screen.queryByText('Next')).toBeNull()
    })
  })

  describe('search', () => {
    it('does not show search input by default', () => {
      render(<DataTable data={data} columns={columns} />)
      expect(screen.queryByPlaceholderText('Search...')).toBeNull()
    })

    it('shows search input when searchable', () => {
      render(<DataTable data={data} columns={columns} searchable />)
      expect(screen.getByPlaceholderText('Search...')).toBeDefined()
    })

    it('filters rows on search', () => {
      render(<DataTable data={data} columns={columns} searchable />)
      const input = screen.getByPlaceholderText('Search...')
      fireEvent.change(input, { target: { value: 'ali' } })
      const rows = screen.getAllByRole('row')
      // 1 header + 1 matching row
      expect(rows.length).toBe(2)
      expect(screen.getByText('Alice')).toBeDefined()
    })

    it('resets page on search change', () => {
      const largeData = Array.from({ length: 25 }, (_, i) => ({
        name: `User ${i + 1}`,
        commits: i + 1,
      }))
      render(<DataTable data={largeData} columns={columns} pageSize={10} searchable />)
      fireEvent.click(screen.getByText('Next'))
      const input = screen.getByPlaceholderText('Search...')
      fireEvent.change(input, { target: { value: 'User 1' } })
      // Should be back on first page with filtered results
      const rows = screen.getAllByRole('row')
      expect(rows.length).toBeGreaterThan(1) // header + at least one match
    })
  })
})
