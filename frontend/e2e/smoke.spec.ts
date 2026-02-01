import { test, expect } from '@playwright/test';

test.describe('IRIS Portal Smoke Tests', () => {
  test('homepage loads and shows title', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('IRIS Digital Invoicing Portal');
  });

  test('can navigate to login page', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Sign In');
    await expect(page).toHaveURL('/login');
    await expect(page.locator('h2')).toContainText('Sign in');
  });

  test('can navigate to dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('login form validates required fields', async ({ page }) => {
    await page.goto('/login');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=NTN is required')).toBeVisible();
    await expect(page.locator('text=Password is required')).toBeVisible();
  });

  test('can access settings page', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.locator('h1')).toContainText('Settings');
    await expect(page.locator('text=Seller Identity')).toBeVisible();
  });

  test('can access new invoice page', async ({ page }) => {
    await page.goto('/invoices/new');
    await expect(page.locator('h1')).toContainText('New Sale Invoice');
  });

  test('can access attempts page', async ({ page }) => {
    await page.goto('/attempts');
    await expect(page.locator('h1')).toContainText('Attempt Ledger');
  });
});
