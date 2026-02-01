import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('Environment Validation', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
  });

  it('should use default values when env vars are not set', async () => {
    // Clear all env vars
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_ENABLE_MSW;
    delete process.env.NEXT_PUBLIC_ENVIRONMENT;
    delete process.env.NEXT_PUBLIC_REQUEST_TIMEOUT_MS;
    delete process.env.NEXT_PUBLIC_TIMEOUT_RETRY_COUNT;
    delete process.env.NEXT_PUBLIC_RETRY_DELAY_MS;

    const { env } = await import('../env');

    expect(env.NEXT_PUBLIC_API_BASE_URL).toBe('http://localhost:3000/api/bff');
    expect(env.NEXT_PUBLIC_ENABLE_MSW).toBe(false);
    expect(env.NEXT_PUBLIC_ENVIRONMENT).toBe('development');
    expect(env.NEXT_PUBLIC_REQUEST_TIMEOUT_MS).toBe(30000);
    expect(env.NEXT_PUBLIC_TIMEOUT_RETRY_COUNT).toBe(2);
    expect(env.NEXT_PUBLIC_RETRY_DELAY_MS).toBe(2000);
  });

  it('should parse boolean env vars correctly', async () => {
    process.env.NEXT_PUBLIC_ENABLE_MSW = 'true';

    const { env } = await import('../env');

    expect(env.NEXT_PUBLIC_ENABLE_MSW).toBe(true);
  });

  it('should parse numeric env vars correctly', async () => {
    process.env.NEXT_PUBLIC_REQUEST_TIMEOUT_MS = '60000';
    process.env.NEXT_PUBLIC_TIMEOUT_RETRY_COUNT = '3';
    process.env.NEXT_PUBLIC_RETRY_DELAY_MS = '5000';

    const { env } = await import('../env');

    expect(env.NEXT_PUBLIC_REQUEST_TIMEOUT_MS).toBe(60000);
    expect(env.NEXT_PUBLIC_TIMEOUT_RETRY_COUNT).toBe(3);
    expect(env.NEXT_PUBLIC_RETRY_DELAY_MS).toBe(5000);
  });
});
