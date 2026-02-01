import { z } from 'zod';

/**
 * Environment variable schema with validation.
 * This ensures all required environment variables are present and valid at runtime.
 */
const envSchema = z.object({
  // API Configuration
  NEXT_PUBLIC_API_BASE_URL: z
    .string()
    .url('API base URL must be a valid URL')
    .default('http://localhost:3000/api/bff'),

  // Feature Flags
  NEXT_PUBLIC_ENABLE_MSW: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),

  // Observability
  NEXT_PUBLIC_ENVIRONMENT: z
    .enum(['development', 'staging', 'production'])
    .default('development'),

  // Timeout Configuration
  NEXT_PUBLIC_REQUEST_TIMEOUT_MS: z
    .string()
    .default('30000')
    .transform((val) => parseInt(val, 10))
    .pipe(z.number().positive().max(120000)),

  NEXT_PUBLIC_TIMEOUT_RETRY_COUNT: z
    .string()
    .default('2')
    .transform((val) => parseInt(val, 10))
    .pipe(z.number().min(0).max(5)),

  NEXT_PUBLIC_RETRY_DELAY_MS: z
    .string()
    .default('2000')
    .transform((val) => parseInt(val, 10))
    .pipe(z.number().positive().max(10000)),
});

export type Env = z.infer<typeof envSchema>;

/**
 * Validate and parse environment variables.
 * Throws an error if validation fails.
 */
function validateEnv(): Env {
  const rawEnv = {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_ENABLE_MSW: process.env.NEXT_PUBLIC_ENABLE_MSW,
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT,
    NEXT_PUBLIC_REQUEST_TIMEOUT_MS: process.env.NEXT_PUBLIC_REQUEST_TIMEOUT_MS,
    NEXT_PUBLIC_TIMEOUT_RETRY_COUNT: process.env.NEXT_PUBLIC_TIMEOUT_RETRY_COUNT,
    NEXT_PUBLIC_RETRY_DELAY_MS: process.env.NEXT_PUBLIC_RETRY_DELAY_MS,
  };

  const result = envSchema.safeParse(rawEnv);

  if (!result.success) {
    console.error('❌ Invalid environment variables:');
    console.error(result.error.flatten().fieldErrors);
    throw new Error('Invalid environment variables');
  }

  return result.data;
}

/**
 * Validated environment variables.
 * Access this object throughout the application for type-safe env vars.
 */
export const env = validateEnv();

/**
 * Helper to check if we're in development mode
 */
export const isDev = env.NEXT_PUBLIC_ENVIRONMENT === 'development';

/**
 * Helper to check if we're in production mode
 */
export const isProd = env.NEXT_PUBLIC_ENVIRONMENT === 'production';

/**
 * Helper to check if MSW mocking is enabled
 */
export const isMswEnabled = env.NEXT_PUBLIC_ENABLE_MSW && typeof window !== 'undefined';
