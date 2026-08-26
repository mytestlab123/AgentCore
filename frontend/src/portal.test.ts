import { describe, expect, it } from 'vitest';
import { ALLOWED_MODEL_ID, DENIED_MODEL_ID, models, routeFromHash, routes } from './portal';

describe('Issue 4 route contract', () => {
  it('contains only the three MVP views', () => {
    expect(routes.map((route) => route.id)).toEqual(['home', 'playground', 'logs']);
    expect(routeFromHash('#/playground')).toBe('playground');
    expect(routeFromHash('#/unknown')).toBe('home');
  });
});

describe('Issue 4 model policy', () => {
  it('shows exactly one allowed and one denied model', () => {
    expect(models).toEqual([
      { id: ALLOWED_MODEL_ID, name: 'Amazon Nova Lite', access: 'Allowed' },
      { id: DENIED_MODEL_ID, name: 'Premium model', access: 'Not allowed' },
    ]);
  });
});
