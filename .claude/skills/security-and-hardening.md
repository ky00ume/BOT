# Security and Hardening

## Core Philosophy
The document establishes that **"Security isn't a phase — it's a constraint on every line of code"** touching user data, authentication, or external systems.

## Three-Tier Boundary System

**Always Do (No Exceptions):**
- Validate all external input at system boundaries
- Use parameterized database queries
- Encode output to prevent XSS attacks
- Implement HTTPS for all external communication
- Hash passwords with bcrypt/scrypt/argon2
- Configure security headers (CSP, HSTS, etc.)
- Use secure cookie attributes (httpOnly, secure, sameSite)
- Run dependency audits before releases

**Ask First (Requires Approval):**
- New authentication flows
- Storing sensitive data categories
- External service integrations
- CORS configuration changes
- File upload handlers
- Rate limiting modifications
- Permission/role changes

**Never Do:**
- Commit secrets to version control
- Log sensitive data
- Trust client-side validation for security
- Use `eval()` or `innerHTML` with user input
- Store auth tokens in localStorage
- Expose stack traces to users

## OWASP Top 10 Coverage
The guide provides practical TypeScript examples addressing injection prevention, password hashing, XSS protection, access control, security headers, data exposure prevention, input validation schemas, file upload safety, and rate limiting implementations.

## Additional Safeguards
- Secrets management via environment variables
- npm audit triage decision framework
- Security review checklist
- Common rationalization rebuttals
- Red flag indicators for code review

The document emphasizes building security into initial development rather than retrofitting later, treating all external data as potentially hostile.
