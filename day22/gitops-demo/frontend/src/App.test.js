import { render, screen } from '@testing-library/react';
import App from './App';

test('renders GitOps dashboard', () => {
  render(<App />);
  const linkElement = screen.getByText(/GitOps Dashboard/i);
  expect(linkElement).toBeInTheDocument();
});
