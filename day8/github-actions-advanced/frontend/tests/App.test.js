import { render, screen } from '@testing-library/react';
import App from '../src/App';

test('renders DevOps Dashboard', () => {
  render(<App />);
  const linkElement = screen.getByText(/DevOps Dashboard/i);
  expect(linkElement).toBeInTheDocument();
});

test('renders Day 8 subtitle', () => {
  render(<App />);
  const subtitleElement = screen.getByText(/Day 8: GitHub Actions Advanced Patterns/i);
  expect(subtitleElement).toBeInTheDocument();
});
