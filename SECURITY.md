# Security Policy

QuantRisk++ is a numerical C++20/Python library for pricing, Monte Carlo simulation, portfolio optimization, risk measurement, and stress testing. Please report security issues privately so maintainers can investigate before details become public.

## Reporting a vulnerability

**Do not post exploitable details in a public issue or discussion.**

1. If the repository's GitHub **Security** tab supports private vulnerability reporting, use that channel.
2. Otherwise, contact the maintainer privately through the GitHub profile and request a secure reporting channel.
3. Include the affected commit or release, environment/toolchain, impact, and minimal reproduction steps. Use synthetic data and a small proof of concept whenever possible.

Do not include API keys, credentials, private market-data feeds, customer data, or other confidential material in a report.

## In-scope examples

- Memory-safety issues, undefined behavior, unsafe native bindings, or exploitable parsing/input handling.
- Incorrect validation that can turn malformed or non-finite inputs into unsafe execution or misleadingly certified outputs.
- Dependency or build-pipeline vulnerabilities that materially affect consumers of the package.
- Secret leakage or unsafe handling of external data in optional integrations.

Numerical disagreements, model assumptions, performance regressions, and financial-methodology questions are generally better reported as ordinary issues unless they create a security impact. When uncertain, ask privately first.

## Safe testing

- Test only systems and data you are authorized to use.
- Prefer deterministic unit tests and synthetic inputs; do not use private customer data.
- Avoid destructive tests or denial-of-service testing against shared infrastructure.
- Record compiler, platform, dependency versions, random seed, and exact reproduction command for numerical or native-code findings.

## Coordinated disclosure

The maintainer will assess the report, determine affected versions, and coordinate a fix or mitigation before public disclosure where practical. No response-time guarantee is implied by this policy.

QuantRisk++ is a research and numerical-computing library, not a trading system or investment recommendation service. This policy does not change that scope.
