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
})
