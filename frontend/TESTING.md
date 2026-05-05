# Frontend Testing Guide - Day 21

## Overview
This document outlines the testing strategy for AEGIS frontend, including unit tests, component tests, integration tests, and end-to-end tests.

## Testing Stack
- **Jest**: Unit and component testing
- **React Testing Library**: Component testing utilities
- **Cypress**: End-to-end testing

## Running Tests

### Unit & Component Tests
```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test -- Button.test.js
```

### End-to-End Tests
```bash
# Open Cypress Test Runner
npm run cypress:open

# Run Cypress headless
npm run cypress:run

# Run specific test suite
npm run cypress:run -- --spec cypress/e2e/critical-flows.cy.js
```

## Test Structure

### 1. Unit Tests
Test individual components in isolation with mocked dependencies.

**Location:** `__tests__/`

**Examples:**
- Button component rendering
- Form validation logic
- Utility functions
- Hooks behavior

### 2. Component Tests
Test component interactions and state management.

**Location:** `__tests__/`

**Examples:**
- Form submission
- User interactions
- Conditional rendering
- Data display

### 3. Integration Tests
Test multiple components working together.

**Location:** `__tests__/integration/`

**Examples:**
- Login flow with authentication
- Zone creation with API
- Data fetching and display

### 4. End-to-End Tests
Test complete user workflows in a real browser environment.

**Location:** `cypress/e2e/`

**Suites:**
- `critical-flows.cy.js`: Authentication, Dashboard, Zone/Sensor management, Profile

## Test Coverage Goals

| Category | Target |
|----------|--------|
| Statements | 60%+ |
| Branches | 60%+ |
| Functions | 60%+ |
| Lines | 60%+ |

## Critical User Flows Tested

### 1. Authentication
- ✅ Login with valid credentials
- ✅ Error handling for invalid credentials
- ✅ Signup form validation
- ✅ Password reset flow
- ✅ Logout functionality

### 2. Dashboard
- ✅ Display metrics (Zones, Sensors, Users, Audit Logs)
- ✅ Navigation to all main sections
- ✅ 3D tactical map rendering
- ✅ Quick action links

### 3. Zone Management
- ✅ Display zones list
- ✅ Create new zone with validation
- ✅ Zone name and description required
- ✅ Success notifications
- ✅ Error handling

### 4. Sensor Management
- ✅ Display sensors fleet
- ✅ Filter by type
- ✅ Search by location
- ✅ Refresh data
- ✅ Auto-refresh toggle
- ✅ Status indicators (Online/Offline)

### 5. Audit Logs
- ✅ Display audit log table
- ✅ Filter by event type
- ✅ Search by event/hash
- ✅ Sort by newest/oldest
- ✅ Timestamp display

### 6. Profile
- ✅ Display user information
- ✅ Show role and permissions
- ✅ Back to dashboard button
- ✅ Change password form
- ✅ Password validation

### 7. Admin - User Management
- ✅ Display users list
- ✅ Search users by email
- ✅ Edit user role
- ✅ Delete user confirmation
- ✅ Success/error notifications

## Writing New Tests

### Jest/React Testing Library Example

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles user interactions', () => {
    render(<MyComponent />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(screen.getByText('Updated Text')).toBeInTheDocument();
  });
});
```

### Cypress Example

```javascript
describe('Feature Name', () => {
  beforeEach(() => {
    cy.visit('/path');
  });

  it('should do something', () => {
    cy.get('selector').click();
    cy.contains('expected text').should('be.visible');
  });
});
```

## Best Practices

1. **Test Behavior, Not Implementation**
   - Focus on what users see and do
   - Avoid testing internal state

2. **Use Meaningful Test Names**
   - "Should display error message when email is invalid"
   - Not "test1" or "check input"

3. **Keep Tests Isolated**
   - Each test should be independent
   - Use beforeEach for setup

4. **Mock External Dependencies**
   - API calls
   - localStorage
   - Third-party libraries

5. **Test Error Cases**
   - Invalid inputs
   - Network failures
   - Permission denied scenarios

## Debugging Tests

### Jest
```bash
# Run in debug mode
node --inspect-brk node_modules/.bin/jest --runInBand

# Run specific test
npm run test -- --testNamePattern="test name"
```

### Cypress
```bash
# Use pause() in test
cy.get('selector').pause();

# Debug in browser console
cy.debug();

# Print to console
cy.log('Message');
```

## Continuous Integration

Tests run automatically on:
- `git push` (pre-push hook)
- Pull requests (GitHub Actions)
- Scheduled nightly runs

See `.github/workflows/test.yml` for CI configuration.

## Performance Testing

Monitor with Lighthouse:
```bash
npm run lighthouse
```

Targets:
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+

## Accessibility Testing

Automated checks with jest-axe:
```javascript
import { axe } from 'jest-axe';

it('should have no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  expect(await axe(container)).toHaveNoViolations();
});
```

## Common Issues & Solutions

### Issue: Tests timeout
**Solution:** Increase timeout in jest.config.js or use `--testTimeout`

### Issue: Components not rendering
**Solution:** Mock router and context providers in test setup

### Issue: Cypress can't find element
**Solution:** Add `cy.wait()` or check selector specificity

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Cypress Documentation](https://docs.cypress.io/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Version Info

- Jest: ^29.0.0
- React Testing Library: ^14.0.0
- Cypress: ^13.0.0
- Node.js: ^18.0.0
- React: ^18.2.0
