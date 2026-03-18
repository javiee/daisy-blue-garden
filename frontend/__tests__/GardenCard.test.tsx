import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { GardenCard } from '@/components/GardenCard'
import type { GardenItem } from '@/lib/types'

const mockItem: GardenItem = {
  id: 1,
  name: 'Red Rose',
  type: 'plant',
  description: 'A beautiful red rose',
  cares: 'Water weekly',
  photo: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('GardenCard', () => {
  it('renders plant name', () => {
    render(<GardenCard item={mockItem} />)
    expect(screen.getByText('Red Rose')).toBeDefined()
  })

  it('renders description', () => {
    render(<GardenCard item={mockItem} />)
    expect(screen.getByText('A beautiful red rose')).toBeDefined()
  })

  it('shows generating text when no description', () => {
    render(<GardenCard item={{ ...mockItem, description: '' }} />)
    expect(screen.getByText(/Generating care guide/i)).toBeDefined()
  })

  it('links to plant detail page', () => {
    render(<GardenCard item={mockItem} />)
    const link = screen.getByRole('link')
    expect(link.getAttribute('href')).toBe('/garden/1')
  })

  it('renders type badge', () => {
    render(<GardenCard item={mockItem} />)
    expect(screen.getByText('Plant')).toBeDefined()
  })
})
