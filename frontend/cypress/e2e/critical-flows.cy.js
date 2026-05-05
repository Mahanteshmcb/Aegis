describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('Should display login form with email and password fields', () => {
    cy.get('input[type="email"]').should('be.visible');
    cy.get('input[type="password"]').should('be.visible');
    cy.contains('button', /login|sign in/i).should('be.visible');
  });

  it('Should show validation error on empty submission', () => {
    cy.contains('button', /login|sign in/i).click();
    cy.get('input[type="email"]').should('have.attr', 'required');
  });

  it('Should login successfully with valid credentials', () => {
    cy.get('input[type="email"]').type('admin@aegis.local');
    cy.get('input[type="password"]').type('password123');
    cy.contains('button', /login|sign in/i).click();
    
    // Wait for redirect to dashboard
    cy.url().should('include', '/dashboard');
    cy.get('h1').should('contain', 'Dashboard');
  });

  it('Should show error on invalid credentials', () => {
    cy.get('input[type="email"]').type('invalid@test.com');
    cy.get('input[type="password"]').type('wrongpassword');
    cy.contains('button', /login|sign in/i).click();
    
    // Should see error message
    cy.contains(/invalid credentials|unauthorized|failed/i).should('be.visible');
  });

  it('Should navigate to signup from login', () => {
    cy.contains('a', /sign up|create account/i).click();
    cy.url().should('include', '/signup');
  });

  it('Should navigate to password reset from login', () => {
    cy.contains('a', /forgot password|reset password/i).click();
    cy.url().should('include', '/reset-password');
  });
});

describe('Signup Flow', () => {
  beforeEach(() => {
    cy.visit('/signup');
  });

  it('Should display signup form fields', () => {
    cy.get('input[type="email"]').should('be.visible');
    cy.get('input[type="password"]').should('be.visible');
    cy.contains('button', /sign up|register/i).should('be.visible');
  });

  it('Should validate password requirements', () => {
    const timestamp = Date.now();
    cy.get('input[type="email"]').type(`test${timestamp}@aegis.local`);
    cy.get('input[type="password"]').type('short');
    cy.contains('button', /sign up|register/i).click();
    
    // Should show validation error
    cy.contains(/password must be at least 8/i).should('be.visible');
  });

  it('Should require matching passwords', () => {
    const timestamp = Date.now();
    cy.get('input[type="email"]').type(`test${timestamp}@aegis.local`);
    cy.get('input[type="password"]').type('password123');
    cy.get('input[type="password"]').last().type('differentpassword');
    cy.contains('button', /sign up|register/i).click();
    
    // Should show mismatch error
    cy.contains(/password.*match|confirm.*password/i).should('be.visible');
  });

  it('Should create new user successfully', () => {
    const timestamp = Date.now();
    cy.get('input[type="email"]').type(`newuser${timestamp}@aegis.local`);
    cy.get('input[type="password"]').type('NewPassword123');
    cy.get('input[type="password"]').last().type('NewPassword123');
    cy.contains('button', /sign up|register/i).click();
    
    // Should redirect to login or show success
    cy.url().should('include', '/login');
  });
});

describe('Dashboard Navigation', () => {
  beforeEach(() => {
    // Login first
    cy.visit('/login');
    cy.get('input[type="email"]').type('admin@aegis.local');
    cy.get('input[type="password"]').type('password123');
    cy.contains('button', /login|sign in/i).click();
    cy.url().should('include', '/dashboard');
  });

  it('Should display dashboard metrics', () => {
    cy.contains(/dashboard|metrics/i).should('be.visible');
    cy.contains(/zones/i).should('be.visible');
    cy.contains(/sensors/i).should('be.visible');
    cy.contains(/audit logs/i).should('be.visible');
  });

  it('Should navigate to zones from dashboard', () => {
    cy.contains('a', /zones/i).first().click();
    cy.url().should('include', '/zones');
    cy.contains(/security zones/i).should('be.visible');
  });

  it('Should navigate to sensors from dashboard', () => {
    cy.contains('a', /sensors/i).first().click();
    cy.url().should('include', '/sensors');
    cy.contains(/sensor fleet/i).should('be.visible');
  });

  it('Should navigate to audit logs from dashboard', () => {
    cy.contains('a', /audit|logs/i).first().click();
    cy.url().should('include', '/audit-logs');
    cy.contains(/audit logs/i).should('be.visible');
  });

  it('Should navigate to profile from sidebar', () => {
    cy.contains('a', /profile/i).click();
    cy.url().should('include', '/profile');
    cy.contains(/profile/i).should('be.visible');
  });
});

describe('Zone Management', () => {
  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('admin@aegis.local');
    cy.get('input[type="password"]').type('password123');
    cy.contains('button', /login|sign in/i).click();
    cy.visit('/zones');
  });

  it('Should display zones list', () => {
    cy.contains(/security zones/i).should('be.visible');
  });

  it('Should open create zone form', () => {
    cy.contains('button', /new zone/i).click();
    cy.contains(/create new zone/i).should('be.visible');
    cy.get('input[placeholder*="Warehouse"]').should('be.visible');
  });

  it('Should validate zone creation', () => {
    cy.contains('button', /new zone/i).click();
    cy.contains('button', /create zone/i).click();
    cy.contains(/zone name is required/i).should('be.visible');
  });

  it('Should create zone successfully', () => {
    cy.contains('button', /new zone/i).click();
    cy.get('input[placeholder*="Warehouse"]').type('Test Zone');
    cy.get('textarea').type('Test description');
    cy.contains('button', /create zone/i).click();
    
    // Should see success message
    cy.contains(/created successfully/i).should('be.visible');
  });
});

describe('Sensor Management', () => {
  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('admin@aegis.local');
    cy.get('input[type="password"]').type('password123');
    cy.contains('button', /login|sign in/i).click();
    cy.visit('/sensors');
  });

  it('Should display sensors fleet', () => {
    cy.contains(/sensor fleet/i).should('be.visible');
  });

  it('Should filter sensors by type', () => {
    cy.get('select').contains('All Types').parent().select('temperature');
    cy.get('table').should('be.visible');
  });

  it('Should search sensors by location', () => {
    cy.get('input[placeholder*="location"]').type('Warehouse');
    cy.get('table tbody').should('be.visible');
  });

  it('Should refresh sensors data', () => {
    cy.contains('button', /refresh/i).click();
    cy.contains(/loading sensors/i).should('be.visible');
  });

  it('Should toggle auto-refresh', () => {
    cy.contains('label', /auto-refresh/i).click();
    cy.contains(/auto-refreshing/i).should('be.visible');
  });
});

describe('Profile & Security', () => {
  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('admin@aegis.local');
    cy.get('input[type="password"]').type('password123');
    cy.contains('button', /login|sign in/i).click();
    cy.visit('/profile');
  });

  it('Should display user profile information', () => {
    cy.contains(/account identity/i).should('be.visible');
    cy.contains(/admin@aegis.local/).should('be.visible');
  });

  it('Should show back to dashboard button', () => {
    cy.contains('button', /back to dashboard/i).should('be.visible');
  });

  it('Should navigate back to dashboard', () => {
    cy.contains('button', /back to dashboard/i).click();
    cy.url().should('include', '/dashboard');
  });

  it('Should open password change form', () => {
    cy.contains('button', /change password/i).click();
    cy.contains(/current password/i).should('be.visible');
    cy.contains(/new password/i).should('be.visible');
  });

  it('Should validate password change', () => {
    cy.contains('button', /change password/i).click();
    cy.contains('button', /update password/i).click();
    cy.contains(/all fields are required/i).should('be.visible');
  });
});

describe('Logout Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('admin@aegis.local');
    cy.get('input[type="password"]').type('password123');
    cy.contains('button', /login|sign in/i).click();
    cy.url().should('include', '/dashboard');
  });

  it('Should logout successfully', () => {
    cy.contains('a', /logout/i).click();
    cy.url().should('include', '/login');
  });

  it('Should redirect to login when accessing protected route after logout', () => {
    cy.contains('a', /logout/i).click();
    cy.visit('/profile');
    cy.url().should('include', '/login');
  });
});

describe('Admin User Management', () => {
  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('admin@aegis.local');
    cy.get('input[type="password"]').type('password123');
    cy.contains('button', /login|sign in/i).click();
    cy.visit('/admin/users');
  });

  it('Should display users list for admin', () => {
    cy.contains(/user management/i).should('be.visible');
  });

  it('Should search users by email', () => {
    cy.get('input[placeholder*="Search users"]').type('test@');
    cy.get('table').should('be.visible');
  });

  it('Should refresh users list', () => {
    cy.contains('button', /refresh/i).click();
  });

  it('Should open edit role dialog', () => {
    cy.contains('button', /edit/i).first().click();
    cy.get('select').should('be.visible');
  });
});
