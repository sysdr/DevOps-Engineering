import { render, screen } from '@testing-library/react';
import App from './App';

test('renders git workflows manager', () => {
  render(<App />);
  const linkElement = screen.getByText(/Git Workflows Manager/i);
  expect(linkElement).toBeInTheDocument();
});
