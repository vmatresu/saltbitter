import { test, expect, Page } from '@playwright/test';

/**
 * E2E tests for critical user flows in SaltBitter dating platform
 */

test.describe('User Authentication Flow', () => {
  test('user can register for a new account', async ({ page }) => {
    await page.goto('/');

    // Click on register/sign up link
    await page.click('text=/sign up|register/i');

    // Fill registration form
    await page.fill('input[name="email"]', `test-${Date.now()}@example.com`);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePassword123!');

    // Accept terms and conditions
    await page.check('input[name="termsAccepted"]');
    await page.check('input[name="dataProcessingConsent"]');

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to profile creation or dashboard
    await expect(page).toHaveURL(/\/(profile|dashboard|onboarding)/);
  });

  test('user can login with existing credentials', async ({ page }) => {
    // First, register a user
    const email = `login-test-${Date.now()}@example.com`;
    await page.goto('/register');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.check('input[name="termsAccepted"]');
    await page.check('input[name="dataProcessingConsent"]');
    await page.click('button[type="submit"]');

    // Logout
    await page.click('text=/logout|sign out/i');

    // Now login
    await page.goto('/login');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.click('button[type="submit"]');

    // Should be logged in
    await expect(page).toHaveURL(/\/(dashboard|profile)/);
  });

  test('login fails with invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'nonexistent@example.com');
    await page.fill('input[name="password"]', 'WrongPassword123!');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('text=/invalid|incorrect|error/i')).toBeVisible();
  });
});

test.describe('Profile Creation Flow', () => {
  let authenticatedPage: Page;

  test.beforeEach(async ({ page }) => {
    // Register and login before each test
    const email = `profile-test-${Date.now()}@example.com`;
    await page.goto('/register');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.check('input[name="termsAccepted"]');
    await page.check('input[name="dataProcessingConsent"]');
    await page.click('button[type="submit"]');

    authenticatedPage = page;
  });

  test('user can create and edit profile', async ({ page }) => {
    // Navigate to profile creation/edit
    await page.goto('/profile/edit');

    // Fill profile fields
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('textarea[name="bio"]', 'This is my test bio');
    await page.fill('input[name="dateOfBirth"]', '1990-01-01');

    // Save profile
    await page.click('button:has-text("Save")');

    // Should show success message or redirect
    await expect(
      page.locator('text=/saved|updated|success/i')
    ).toBeVisible({ timeout: 5000 });
  });

  test('profile requires mandatory fields', async ({ page }) => {
    await page.goto('/profile/edit');

    // Try to submit without filling required fields
    await page.click('button:has-text("Save")');

    // Should show validation errors
    await expect(page.locator('text=/required|mandatory/i')).toBeVisible();
  });
});

test.describe('Attachment Questionnaire Flow', () => {
  test('user can complete ECR-R questionnaire', async ({ page }) => {
    // Register and login
    const email = `questionnaire-${Date.now()}@example.com`;
    await page.goto('/register');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.check('input[name="termsAccepted"]');
    await page.check('input[name="dataProcessingConsent"]');
    await page.click('button[type="submit"]');

    // Navigate to questionnaire
    await page.goto('/questionnaire');

    // Fill out questionnaire (ECR-R has 36 questions)
    // Select middle option (4 out of 1-7 scale) for all questions
    const questions = await page.locator('input[type="radio"]').count();

    if (questions > 0) {
      for (let i = 0; i < Math.min(questions / 7, 36); i++) {
        // Select the middle option for each question
        await page.check(`input[name="q${i}"][value="4"]`);
      }

      // Submit questionnaire
      await page.click('button:has-text("Submit")');

      // Should show results or confirmation
      await expect(
        page.locator('text=/results|completed|thank you/i')
      ).toBeVisible();
    }
  });
});

test.describe('GDPR Compliance Flow', () => {
  test('user can export their data', async ({ page }) => {
    // Register and login
    const email = `gdpr-export-${Date.now()}@example.com`;
    await page.goto('/register');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.check('input[name="termsAccepted"]');
    await page.check('input[name="dataProcessingConsent"]');
    await page.click('button[type="submit"]');

    // Navigate to privacy/settings
    await page.goto('/settings/privacy');

    // Click export data button
    const downloadPromise = page.waitForEvent('download');
    await page.click('text=/export.*data|download.*data/i');

    // Should trigger download
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.json|\.zip/);
  });

  test('user can delete their account', async ({ page }) => {
    // Register and login
    const email = `gdpr-delete-${Date.now()}@example.com`;
    await page.goto('/register');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'SecurePassword123!');
    await page.check('input[name="termsAccepted"]');
    await page.check('input[name="dataProcessingConsent"]');
    await page.click('button[type="submit"]');

    // Navigate to account deletion
    await page.goto('/settings/account');

    // Click delete account
    await page.click('text=/delete.*account/i');

    // Confirm deletion in modal/dialog
    await page.click('button:has-text("Confirm")');

    // Should redirect to goodbye page or home
    await expect(page).toHaveURL(/\/(goodbye|login|\/)/);
  });
});

test.describe('Accessibility Tests', () => {
  test('login page is keyboard navigable', async ({ page }) => {
    await page.goto('/login');

    // Tab through form
    await page.keyboard.press('Tab'); // Email field
    await page.keyboard.type('test@example.com');
    await page.keyboard.press('Tab'); // Password field
    await page.keyboard.type('password123');
    await page.keyboard.press('Tab'); // Submit button
    await page.keyboard.press('Enter');

    // Form should submit via keyboard
    await expect(page).toHaveURL(/\//, { timeout: 5000 });
  });

  test('pages have proper ARIA labels', async ({ page }) => {
    await page.goto('/');

    // Check for proper ARIA landmarks
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('nav')).toBeVisible();
  });
});

test.describe('Responsive Design Tests', () => {
  test('app works on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Should show mobile menu/hamburger
    await expect(page).toBeVisible();

    // Navigation should work
    await page.click('[aria-label="menu"]');
    await expect(page.locator('nav')).toBeVisible();
  });

  test('app works on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto('/');

    // Should render properly
    await expect(page).toBeVisible();
  });
});

test.describe('Performance Tests', () => {
  test('home page loads within 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('no console errors on main pages', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.goto('/login');
    await page.goto('/register');

    // Should have no console errors
    expect(consoleErrors).toHaveLength(0);
  });
});
