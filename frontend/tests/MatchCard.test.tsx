import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MatchCard } from '../src/components/MatchCard';
import { useMatchStore } from '../src/store/matchStore';

// Mock the match store
jest.mock('../src/store/matchStore');

const mockUseMatchStore = useMatchStore as unknown as jest.Mock;

const mockMatch = {
  id: 'match-1',
  user_id: 'user-123',
  name: 'Jane Doe',
  age: 28,
  bio: 'Love hiking and reading. Looking for meaningful connections.',
  photos: [
    'https://example.com/photo1.jpg',
    'https://example.com/photo2.jpg',
    'https://example.com/photo3.jpg',
  ],
  compatibility_score: 85,
  distance: 5,
};

describe('MatchCard Component', () => {
  let mockLikeMatch: jest.Mock;
  let mockPassMatch: jest.Mock;

  beforeEach(() => {
    mockLikeMatch = jest.fn();
    mockPassMatch = jest.fn();

    mockUseMatchStore.mockReturnValue({
      matches: [mockMatch],
      currentMatchIndex: 0,
      isLoading: false,
      error: null,
      fetchMatches: jest.fn(),
      likeMatch: mockLikeMatch,
      passMatch: mockPassMatch,
      nextMatch: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders match information', () => {
    render(<MatchCard match={mockMatch} />);

    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
    expect(screen.getByText(/Love hiking and reading/)).toBeInTheDocument();
    expect(screen.getByText('85% match')).toBeInTheDocument();
    expect(screen.getByText('📍 5 km away')).toBeInTheDocument();
  });

  test('displays first photo by default', () => {
    render(<MatchCard match={mockMatch} />);

    const image = screen.getByAlt('Jane Doe photo 1') as HTMLImageElement;
    expect(image).toBeInTheDocument();
    expect(image.src).toBe('https://example.com/photo1.jpg');
  });

  test('allows navigation between photos', () => {
    render(<MatchCard match={mockMatch} />);

    // Click next photo button
    const nextButton = screen.getAllByRole('button')[1]; // Second button should be next
    fireEvent.click(nextButton);

    const image = screen.getByAlt('Jane Doe photo 2') as HTMLImageElement;
    expect(image.src).toBe('https://example.com/photo2.jpg');

    // Click previous photo button
    const prevButton = screen.getAllByRole('button')[0]; // First button should be previous
    fireEvent.click(prevButton);

    const firstImage = screen.getByAlt('Jane Doe photo 1') as HTMLImageElement;
    expect(firstImage.src).toBe('https://example.com/photo1.jpg');
  });

  test('displays photo indicators', () => {
    render(<MatchCard match={mockMatch} />);

    // Should have 3 photo indicator dots
    const indicators = document.querySelectorAll('.rounded-full');
    // Filter for just the photo indicators (they're in the photo section)
    const photoIndicators = Array.from(indicators).filter(
      (el) => el.classList.contains('h-2')
    );
    expect(photoIndicators.length).toBe(3);
  });

  test('calls likeMatch when like button is clicked', async () => {
    render(<MatchCard match={mockMatch} />);

    const likeButton = screen.getByTitle('Like');
    fireEvent.click(likeButton);

    await waitFor(() => {
      expect(mockLikeMatch).toHaveBeenCalledWith('match-1');
    });
  });

  test('calls passMatch when pass button is clicked', async () => {
    render(<MatchCard match={mockMatch} />);

    const passButton = screen.getByTitle('Pass');
    fireEvent.click(passButton);

    await waitFor(() => {
      expect(mockPassMatch).toHaveBeenCalledWith('match-1');
    });
  });

  test('displays compatibility score as progress bar', () => {
    render(<MatchCard match={mockMatch} />);

    const progressBar = document.querySelector('.bg-gradient-to-r') as HTMLElement;
    expect(progressBar).toBeInTheDocument();
    expect(progressBar.style.width).toBe('85%');
  });

  test('handles match with no photos', () => {
    const matchWithoutPhotos = {
      ...mockMatch,
      photos: [],
    };

    render(<MatchCard match={matchWithoutPhotos} />);

    expect(screen.getByText('No photo available')).toBeInTheDocument();
  });

  test('handles match with no distance information', () => {
    const matchWithoutDistance = {
      ...mockMatch,
      distance: undefined,
    };

    render(<MatchCard match={matchWithoutDistance} />);

    expect(screen.queryByText(/km away/)).not.toBeInTheDocument();
  });

  test('renders all action buttons', () => {
    render(<MatchCard match={mockMatch} />);

    expect(screen.getByTitle('Pass')).toBeInTheDocument();
    expect(screen.getByTitle('Like')).toBeInTheDocument();
    expect(screen.getByTitle('Super Like')).toBeInTheDocument();
  });
});
