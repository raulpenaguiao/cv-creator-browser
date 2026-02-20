# CV Creator Browser

A browser-based CV creator powered by Flask and OpenAI. Input your personal info, work experience, projects, and a target job description. AI analyzes the job, generates tailored CV sentences, and the final output is a LaTeX-compiled PDF.

## Prerequisites

- Python 3.10+
- TeX Live (or MiKTeX on Windows) for PDF compilation:
  - Debian/Ubuntu: `sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended`
- libmagic for file type validation:
  - Debian/Ubuntu: `sudo apt install libmagic1`
- SMTP server for password reset emails (optional, a debug server works for local dev)

## Setup

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd cv-creator-browser
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate (or .\.venv\Scripts\Activate.ps1 on Windows)
   pip install -r requirements.txt
   ```

3. (Optional) Configure environment variables in a `.env` file:

   ```
   SECRET_KEY=your-secret-key-here
   MAIL_SERVER=localhost
   MAIL_PORT=1025
   ```

4. Start the application:

   ```bash
   python run.py
   ```

5. Open `http://localhost:5000` in your browser.

## Running Tests

```bash
pytest tests/
```

For coverage:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Architecture

| Component | Choice |
|-----------|--------|
| Backend | Flask with Blueprint-based API |
| Database | SQLite (raw `sqlite3`, no ORM) |
| Auth | Flask-Login + session cookies, auto-generated passwords |
| Frontend | Alpine.js single-page app (no build step) |
| CSS | Custom CSS, no framework |
| API keys | Per-user, Fernet-encrypted at rest |
| Password reset | SMTP with SHA-256 hashed tokens, 1hr expiry |
| CV output | Jinja2-rendered LaTeX compiled via `pdflatex` |
| OpenAI | `response_format={"type": "json_object"}` for structured output |

## API Endpoints

All state-changing requests require CSRF token via `X-CSRFToken` header.

| Blueprint | Prefix | Endpoints |
|-----------|--------|-----------|
| Auth | `/api/auth` | `GET /session`, `POST /register`, `POST /login`, `POST /logout`, `POST /reset-request`, `POST /reset-confirm` |
| Profile | `/api/profile` | `GET`, `PUT` |
| Photos | `/api/photos` | `GET`, `POST` (upload), `DELETE /<id>`, `PUT /<id>/primary`, `GET /<id>/file` |
| Experiences | `/api/experiences` | `GET`, `POST`, `PUT /<id>`, `DELETE /<id>`, `PUT /reorder` |
| Projects | `/api/projects` | `GET`, `POST`, `PUT /<id>`, `DELETE /<id>`, `PUT /reorder` |
| Job | `/api/job` | `GET /analyses`, `POST /analyze`, `PUT /analyses/<id>/activate`, `DELETE /analyses/<id>` |
| Blurbs | `/api/blurbs` | `GET ?template_name=`, `POST /generate`, `PUT /<id>`, `DELETE /<id>` |
| Generate | `/api/generate` | `POST /compile`, `GET /download/pdf`, `GET /download/tex` |
| Settings | `/api/settings` | `GET`, `PUT`, `GET /templates` |
| Data | `/api/data` | `GET /export`, `POST /import` |

## Workflow

1. **Register** -- server returns an auto-generated password (shown once, copy it)
2. **About You** -- fill in personal info and upload a photo
3. **My Life** -- add work experience, education, and hobbies
4. **Projects** -- add projects and achievements
5. **Settings** -- enter your OpenAI API key (encrypted at rest, never returned)
6. **Job Discussion** -- paste a job description, AI extracts keywords and alignment data
7. **Blurbs** -- generate AI blurb suggestions per CV field, accept/edit/reject each one
8. **Generate CV** -- compile to PDF and download

## Security

- LaTeX injection prevention: `sanitize_latex()` escapes all 10 special characters; `pdflatex --no-shell-escape`; compilation in isolated temp directory with timeout
- API key encryption: Fernet key derived from `SECRET_KEY` via HKDF; never returned to frontend
- CSRF: Flask-WTF CSRFProtect; token in `<meta>` tag; sent via `X-CSRFToken` header
- Sessions: HttpOnly, SameSite=Lax, Secure in production
- Uploads: extension whitelist, MIME type check (python-magic), 5MB limit, `secure_filename` + UUID prefix
- SQL injection: parameterized queries only
- Password reset tokens: SHA-256 hashed in DB, 1hr expiry, single-use, no email enumeration
- Rate limiting: Flask-Limiter on auth endpoints (register, login, reset)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for the API powering CV generation
- Flask for the web framework
- Contributors: Carolin Warnecke, Zheng Gong, and others



# TODO

- we need a favicon