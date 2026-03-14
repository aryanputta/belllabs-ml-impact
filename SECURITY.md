# Security & Repository Protection

This project does not intentionally store secrets. To keep it that way:

- Keep API keys and credentials in `.env` files (ignored by `.gitignore`).
- Never commit private keys (`*.pem`, `*.key`) or raw credentials.
- Use GitHub branch protection on `main`:
  - require pull request reviews,
  - require status checks,
  - block force-pushes,
  - block direct pushes.

## Local checks before push

```bash
python scripts/verify_environment.py
python -m py_compile src/similarity/paper_similarity.py src/researcher/researcher_analysis.py
```
