/**
 * Trusted LibreChat tool-approval hook for the Issue #24 synthetic demo.
 *
 * The hook can only tighten the static YAML policy: high-risk prod remediation
 * without a DEMO-* ticket becomes deny; a valid ticket remains ask.
 */
module.exports = () => () => async (input) => {
  const args = input?.toolInput ?? {};
  if (args.environment === 'prod' && !/^DEMO-[0-9]+$/.test(String(args.ticket ?? '').trim())) {
    return {
      decision: 'deny',
      reason: 'High-risk prod remediation requires a DEMO-* ticket.',
    };
  }
  return {};
};
