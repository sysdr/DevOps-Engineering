import { render, screen } from '@testing-library/react';
import CDNDashboard from './CDNDashboard';

const mockMetrics = {
  overview: {
    total_requests: 1234,
    cache_hit_rate: 85.5,
    avg_response_time: 125,
    total_cost_usd: 12.34
  },
  regional_data: [
    {
      region: 'us-east',
      requests: 500,
      avg_response_time: 120,
      cache_hit_rate: 88,
      cost_usd: 5.50
    }
  ],
  cost_breakdown: {
    'us-east': 5.50,
    'eu-west': 3.20
  }
};

test('renders dashboard with metrics', () => {
  render(<CDNDashboard metrics={mockMetrics} />);
  
  expect(screen.getByText('1,234')).toBeInTheDocument();
  expect(screen.getByText('85.5%')).toBeInTheDocument();
  expect(screen.getByText('125ms')).toBeInTheDocument();
  expect(screen.getByText('$12.34')).toBeInTheDocument();
});

test('shows loading when no metrics', () => {
  render(<CDNDashboard metrics={null} />);
  expect(screen.getByText('Loading CDN metrics...')).toBeInTheDocument();
});
