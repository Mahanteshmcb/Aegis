import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../Button';

describe('Button Component', () => {
  it('renders button with text', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByText('Click Me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('can be disabled', () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByText('Disabled');
    expect(button).toBeDisabled();
  });

  it('applies variant styles', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByText('Secondary');
    expect(button).toHaveClass('bg-slate-600');
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByText('Loading');
    expect(button).toBeDisabled();
  });
});
