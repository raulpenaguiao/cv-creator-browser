
# Project Structure

```
cv-creator-browser/
    requirements.txt                    # Python dependencies
    config.py                           # Dev/Prod/Test config classes
    run.py                              # Entry point (python run.py)
    instance/                           # Gitignored runtime data
        cv_creator.db                   #   SQLite database
        uploads/                        #   User-uploaded photos
        generated/                      #   Compiled PDF/TEX output
    app/
        __init__.py                     # create_app() factory, blueprint registration
        database.py                     # get_db(), close_db(), init_db(), init_test_db()
        schema.sql                      # CREATE TABLE statements (9 tables + indexes)
        models.py                       # User class (Flask-Login UserMixin)
        extensions.py                   # LoginManager, CSRFProtect, Mail, Limiter instances
        blueprints/
            main.py                     # Serves index.html at /
            auth.py                     # /api/auth -- register, login, logout, password reset
            profile.py                  # /api/profile -- about-you CRUD
            photo.py                    # /api/photos -- upload, delete, set-primary, serve
            experience.py               # /api/experiences -- CRUD + reorder
            project.py                  # /api/projects -- CRUD + reorder
            job.py                      # /api/job -- job description analysis via OpenAI
            blurb.py                    # /api/blurbs -- AI blurb generation + accept/modify/reject
            generate.py                 # /api/generate -- LaTeX compile, PDF/TEX download
            settings.py                 # /api/settings -- user prefs, API key, template list
            data.py                     # /api/data -- JSON export/import
        services/
            auth_service.py             # Registration (auto-gen password), bcrypt, reset tokens
            crypto_service.py           # Fernet encrypt/decrypt for OpenAI API keys
            openai_service.py           # Job analysis + blurb generation prompts
            template_service.py         # CV template listing and config loading
            latex_service.py            # sanitize_latex(), Jinja2 rendering, pdflatex compilation
            data_service.py             # Full JSON export/import of user data
            email_service.py            # SMTP password reset emails
        cv_templates/
            classic/
                config.json             # Template metadata, section definitions, field configs
                template.tex            # Jinja2-flavored LaTeX (\VAR{}, \BLOCK{} delimiters)
        templates/
            index.html                  # Single-page Alpine.js app (all tabs + auth modals)
            email/
                reset_password.html     # Password reset email template
        static/
            css/main.css                # Custom CSS (no framework)
            js/api.js                   # Fetch wrapper with CSRF + 401 handling
            js/app.js                   # Alpine.js stores + tab component functions
    tests/
        conftest.py                     # Fixtures (app, client, db) + helpers
        test_auth.py                    # Auth flow tests (register, login, logout, reset)
        test_profile.py                 # Profile CRUD tests
        test_experiences.py             # Experience CRUD + reorder tests
        test_projects.py                # Project CRUD + reorder tests
        test_job.py                     # Job analysis tests
        test_blurbs.py                  # Blurb lifecycle tests
        test_generate.py                # PDF/TEX download tests
        test_settings.py                # Settings + template listing tests
        test_data.py                    # Export/import tests
        test_crypto.py                  # Fernet roundtrip tests
        test_latex_sanitize.py          # LaTeX special character escaping tests
```

# Database Schema

9 tables with foreign keys and indexes:

- **users** -- id, username (unique), email (unique), password_hash (bcrypt), timestamps
- **user_settings** -- 1:1 with users; openai_api_key_enc (Fernet blob), selected_template, sentences_per_field, font_size
- **password_reset_tokens** -- token_hash (SHA-256), expires_at (1hr), used flag
- **about_you** -- 1:1 with users; first_name, last_name, contact fields, bio
- **photos** -- per user; filename, storage_path, mime_type, is_primary, sort_order
- **experiences** -- per user; category (work/education/hobby), title, organization, dates, description, keywords
- **projects** -- per user; title, description, keywords, sort_order
- **job_analyses** -- per user; job_description, extracted_keywords (JSON), focus_suggestions (JSON), alignment_data (JSON), is_active
- **blurbs** -- per user; template_name, field_key, suggestion_text, status (pending/accepted/modified/rejected), user_text

# Frontend Architecture

Single-page Alpine.js app with no build step. All JavaScript in two files:

- **api.js** -- `Api` object wrapping `fetch()` with automatic CSRF token injection and 401 redirect
- **app.js** -- three Alpine stores (`auth`, `nav`, `toast`) and seven tab component functions:
  - `aboutTab()` -- profile form + photo upload/management
  - `lifeTab()` -- experience list with work/education/hobby filter, inline add/edit/delete
  - `projectsTab()` -- project list with inline add/edit/delete
  - `jobTab()` -- job description textarea, analyze button, results with keywords and suggestions
  - `blurbsTab()` -- per-field blurb generation, accept/edit/reject cards with color states
  - `generateTab()` -- compile button, PDF/TEX download links
  - `settingsTab()` -- API key, template, preferences, data export/import

# CV Template System

Templates live under `app/cv_templates/<name>/` with two files:

- **config.json** -- metadata, header fields, sections array where each section is either:
  - `type: "blurb"` -- AI-generated text; has `prompt_context`, `max_chars`, `min/max_sentences`
  - `type: "data"` -- pulled from DB; has `data_source`, `filter`, `sort`
- **template.tex** -- Jinja2 with custom delimiters to avoid LaTeX brace conflicts:
  - `\VAR{variable}` for values
  - `\BLOCK{if/for/endif/endfor}` for logic

All user text is sanitized via `sanitize_latex()` before rendering. Compilation uses `pdflatex --no-shell-escape` in an isolated temp directory with a configurable timeout.

# How It Works

1. User registers, receives an auto-generated password (shown once)
2. User fills in profile, experiences, projects across the tabbed interface
3. User enters their OpenAI API key in Settings (encrypted with Fernet at rest)
4. User pastes a job description; AI extracts keywords, suggests focus areas, scores alignment
5. User generates blurbs per CV field; AI returns suggestions the user can accept, edit, or reject
6. User compiles the CV; accepted/modified blurbs + data are rendered into LaTeX and compiled to PDF
7. User downloads the PDF or TEX source

# Security Notes

- Parameterized SQL queries throughout (no string interpolation)
- Fernet encryption for API keys, derived from SECRET_KEY via HKDF
- CSRF protection on all state-changing endpoints
- Rate limiting on auth endpoints (Flask-Limiter)
- Photo uploads validated by extension whitelist + MIME type check + size limit
- Password reset tokens are SHA-256 hashed, expire in 1 hour, single-use
- No email enumeration on reset endpoint (always returns generic success)
