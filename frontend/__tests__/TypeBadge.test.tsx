import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { TypeBadge } from '@/components/TypeBadge'

describe('TypeBadge', () => {
  it('renders plant badge', () => {
    render(<TypeBadge type="plant" />)
    expect(screen.getByText('Plant')).toBeDefined()
  })

  it('renders tree badge', () => {
    render(<TypeBadge type="tree" />)
    expect(screen.getByText('Tree')).toBeDefined()
  })

  it('renders shrub badge', () => {
    render(<TypeBadge type="shrub" />)
    expect(screen.getByText('Shrub')).toBeDefined()
  })

  it('renders other badge', () => {
    render(<TypeBadge type="other" />)
    expect(screen.getByText('Other')).toBeDefined()
  })
})
