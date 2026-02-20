/**
 * Alpine.js stores and component functions for the CV Creator app.
 */

document.addEventListener('alpine:init', () => {

    // ── Toast Store ──
    Alpine.store('toast', {
        messages: [],
        show(text, type = 'info', duration = 4000) {
            const id = Date.now();
            this.messages.push({ id, text, type });
            setTimeout(() => {
                this.messages = this.messages.filter(m => m.id !== id);
            }, duration);
        },
        success(text) { this.show(text, 'success'); },
        error(text) { this.show(text, 'error', 6000); },
        info(text) { this.show(text, 'info'); },
    });

    // ── Auth Store ──
    Alpine.store('auth', {
        authenticated: false,
        user: null,
        showLogin: false,
        showRegister: false,
        showReset: false,
        showPassword: false,
        generatedPassword: '',
        loading: false,

        async checkSession() {
            try {
                const res = await Api.get('/api/auth/session');
                const data = await res.json();
                this.authenticated = data.authenticated;
                this.user = data.user || null;
                if (!this.authenticated) {
                    this.showLogin = true;
                }
            } catch {
                this.showLogin = true;
            }
        },

        async login(username, password) {
            this.loading = true;
            try {
                const res = await Api.post('/api/auth/login', { username, password });
                const data = await res.json();
                if (res.ok) {
                    this.authenticated = true;
                    this.user = data.user;
                    this.showLogin = false;
                    Alpine.store('toast').success('Logged in successfully');
                } else {
                    Alpine.store('toast').error(data.error || 'Login failed');
                }
            } catch {
                Alpine.store('toast').error('Login failed');
            } finally {
                this.loading = false;
            }
        },

        async register(username, email) {
            this.loading = true;
            try {
                const res = await Api.post('/api/auth/register', { username, email });
                const data = await res.json();
                if (res.ok) {
                    this.generatedPassword = data.password;
                    this.showRegister = false;
                    this.showPassword = true;
                    Alpine.store('toast').success('Registration successful');
                } else {
                    Alpine.store('toast').error(data.error || 'Registration failed');
                }
            } catch {
                Alpine.store('toast').error('Registration failed');
            } finally {
                this.loading = false;
            }
        },

        async logout() {
            await Api.post('/api/auth/logout');
            this.authenticated = false;
            this.user = null;
            this.showLogin = true;
            Alpine.store('toast').info('Logged out');
        },

        async resetRequest(email) {
            this.loading = true;
            try {
                const res = await Api.post('/api/auth/reset-request', { email });
                const data = await res.json();
                Alpine.store('toast').info(data.message);
                this.showReset = false;
                this.showLogin = true;
            } catch {
                Alpine.store('toast').error('Reset request failed');
            } finally {
                this.loading = false;
            }
        },

        async resetConfirm(token) {
            this.loading = true;
            try {
                const res = await Api.post('/api/auth/reset-confirm', { token });
                const data = await res.json();
                if (res.ok) {
                    this.generatedPassword = data.password;
                    this.showPassword = true;
                    this.showLogin = false;
                } else {
                    Alpine.store('toast').error(data.error || 'Reset failed');
                }
            } catch {
                Alpine.store('toast').error('Reset failed');
            } finally {
                this.loading = false;
            }
        },

        copyPassword() {
            navigator.clipboard.writeText(this.generatedPassword);
            Alpine.store('toast').success('Password copied to clipboard');
        },

        dismissPassword() {
            this.generatedPassword = '';
            this.showPassword = false;
            this.showLogin = true;
        },
    });

    // ── Navigation Store ──
    Alpine.store('nav', {
        current: 'about',
        tabs: [
            { id: 'about', label: 'About You' },
            { id: 'life', label: 'My Life' },
            { id: 'projects', label: 'Projects' },
            { id: 'job', label: 'Job Discussion' },
            { id: 'blurbs', label: 'Blurbs' },
            { id: 'generate', label: 'Generate CV' },
            { id: 'settings', label: 'Settings' },
        ],
        setTab(id) {
            this.current = id;
        },
    });
});

// ── Check for reset token in URL ──
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const resetToken = params.get('reset_token');
    if (resetToken) {
        window.history.replaceState({}, '', '/');
        // Wait for Alpine to initialize
        setTimeout(() => {
            Alpine.store('auth').resetConfirm(resetToken);
        }, 500);
    }
});

// ── Tab Component Functions ──

function aboutTab() {
    return {
        profile: { first_name: '', last_name: '', email_contact: '', phone: '', address: '', linkedin: '', website: '', bio: '' },
        photos: [],
        loading: false,
        photoUploading: false,

        async init() {
            await this.loadProfile();
            await this.loadPhotos();
        },

        async loadProfile() {
            try {
                const res = await Api.get('/api/profile');
                if (res.ok) this.profile = await res.json();
            } catch {}
        },

        async saveProfile() {
            this.loading = true;
            try {
                const res = await Api.put('/api/profile', this.profile);
                if (res.ok) Alpine.store('toast').success('Profile saved');
                else Alpine.store('toast').error('Failed to save profile');
            } catch {
                Alpine.store('toast').error('Failed to save profile');
            } finally {
                this.loading = false;
            }
        },

        async loadPhotos() {
            try {
                const res = await Api.get('/api/photos');
                if (res.ok) this.photos = await res.json();
            } catch {}
        },

        async uploadPhoto(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.photoUploading = true;
            try {
                const formData = new FormData();
                formData.append('photo', file);
                const res = await Api.post('/api/photos', formData);
                if (res.ok) {
                    await this.loadPhotos();
                    Alpine.store('toast').success('Photo uploaded');
                } else {
                    const data = await res.json();
                    Alpine.store('toast').error(data.error || 'Upload failed');
                }
            } catch {
                Alpine.store('toast').error('Upload failed');
            } finally {
                this.photoUploading = false;
                event.target.value = '';
            }
        },

        async deletePhoto(id) {
            if (!confirm('Delete this photo?')) return;
            try {
                const res = await Api.delete(`/api/photos/${id}`);
                if (res.ok) {
                    await this.loadPhotos();
                    Alpine.store('toast').success('Photo deleted');
                }
            } catch {
                Alpine.store('toast').error('Failed to delete photo');
            }
        },

        async setPrimary(id) {
            try {
                const res = await Api.put(`/api/photos/${id}/primary`);
                if (res.ok) await this.loadPhotos();
            } catch {}
        },

        photoUrl(id) {
            return `/api/photos/${id}/file`;
        },
    };
}

function lifeTab() {
    return {
        experiences: [],
        filter: 'all',
        editing: null,
        form: { category: 'work', title: '', organization: '', start_date: '', end_date: '', description: '', keywords: '' },
        showForm: false,
        loading: false,

        async init() {
            await this.load();
        },

        async load() {
            try {
                const res = await Api.get('/api/experiences');
                if (res.ok) this.experiences = await res.json();
            } catch {}
        },

        get filtered() {
            if (this.filter === 'all') return this.experiences;
            return this.experiences.filter(e => e.category === this.filter);
        },

        resetForm() {
            this.form = { category: 'work', title: '', organization: '', start_date: '', end_date: '', description: '', keywords: '' };
            this.editing = null;
            this.showForm = false;
        },

        editExperience(exp) {
            this.form = { ...exp };
            this.editing = exp.id;
            this.showForm = true;
        },

        async save() {
            this.loading = true;
            try {
                let res;
                if (this.editing) {
                    res = await Api.put(`/api/experiences/${this.editing}`, this.form);
                } else {
                    res = await Api.post('/api/experiences', this.form);
                }
                if (res.ok) {
                    await this.load();
                    this.resetForm();
                    Alpine.store('toast').success('Experience saved');
                } else {
                    const data = await res.json();
                    Alpine.store('toast').error(data.error || 'Save failed');
                }
            } catch {
                Alpine.store('toast').error('Save failed');
            } finally {
                this.loading = false;
            }
        },

        async deleteExperience(id) {
            if (!confirm('Delete this experience?')) return;
            try {
                const res = await Api.delete(`/api/experiences/${id}`);
                if (res.ok) {
                    await this.load();
                    Alpine.store('toast').success('Experience deleted');
                }
            } catch {
                Alpine.store('toast').error('Delete failed');
            }
        },
    };
}

function projectsTab() {
    return {
        projects: [],
        editing: null,
        form: { title: '', description: '', keywords: '' },
        showForm: false,
        loading: false,

        async init() {
            await this.load();
        },

        async load() {
            try {
                const res = await Api.get('/api/projects');
                if (res.ok) this.projects = await res.json();
            } catch {}
        },

        resetForm() {
            this.form = { title: '', description: '', keywords: '' };
            this.editing = null;
            this.showForm = false;
        },

        editProject(proj) {
            this.form = { ...proj };
            this.editing = proj.id;
            this.showForm = true;
        },

        async save() {
            this.loading = true;
            try {
                let res;
                if (this.editing) {
                    res = await Api.put(`/api/projects/${this.editing}`, this.form);
                } else {
                    res = await Api.post('/api/projects', this.form);
                }
                if (res.ok) {
                    await this.load();
                    this.resetForm();
                    Alpine.store('toast').success('Project saved');
                } else {
                    const data = await res.json();
                    Alpine.store('toast').error(data.error || 'Save failed');
                }
            } catch {
                Alpine.store('toast').error('Save failed');
            } finally {
                this.loading = false;
            }
        },

        async deleteProject(id) {
            if (!confirm('Delete this project?')) return;
            try {
                const res = await Api.delete(`/api/projects/${id}`);
                if (res.ok) {
                    await this.load();
                    Alpine.store('toast').success('Project deleted');
                }
            } catch {
                Alpine.store('toast').error('Delete failed');
            }
        },
    };
}

function jobTab() {
    return {
        analyses: [],
        jobDescription: '',
        analyzing: false,
        loading: false,

        async init() {
            await this.load();
        },

        async load() {
            try {
                const res = await Api.get('/api/job/analyses');
                if (res.ok) this.analyses = await res.json();
            } catch {}
        },

        async analyze() {
            if (!this.jobDescription.trim()) {
                Alpine.store('toast').error('Please enter a job description');
                return;
            }
            this.analyzing = true;
            try {
                const res = await Api.post('/api/job/analyze', { job_description: this.jobDescription });
                if (res.ok) {
                    await this.load();
                    this.jobDescription = '';
                    Alpine.store('toast').success('Job analyzed successfully');
                } else {
                    const data = await res.json();
                    Alpine.store('toast').error(data.error || 'Analysis failed');
                }
            } catch {
                Alpine.store('toast').error('Analysis failed');
            } finally {
                this.analyzing = false;
            }
        },

        async activate(id) {
            try {
                const res = await Api.put(`/api/job/analyses/${id}/activate`);
                if (res.ok) await this.load();
            } catch {}
        },

        async deleteAnalysis(id) {
            if (!confirm('Delete this analysis?')) return;
            try {
                const res = await Api.delete(`/api/job/analyses/${id}`);
                if (res.ok) {
                    await this.load();
                    Alpine.store('toast').success('Analysis deleted');
                }
            } catch {}
        },

        parseJSON(str) {
            try { return JSON.parse(str); } catch { return []; }
        },
    };
}

function blurbsTab() {
    return {
        blurbs: [],
        templates: [],
        selectedTemplate: 'classic',
        templateConfig: null,
        generating: {},
        loading: false,
        editingBlurb: null,
        editText: '',

        async init() {
            await this.loadTemplates();
            await this.load();
        },

        async loadTemplates() {
            try {
                const res = await Api.get('/api/settings/templates');
                if (res.ok) {
                    const data = await res.json();
                    this.templates = data.templates || [];
                    if (this.templates.length > 0) {
                        this.templateConfig = this.templates.find(t => t.name === this.selectedTemplate) || this.templates[0];
                    }
                }
            } catch {}
        },

        async load() {
            try {
                const res = await Api.get(`/api/blurbs?template_name=${this.selectedTemplate}`);
                if (res.ok) this.blurbs = await res.json();
            } catch {}
        },

        getBlurbsForField(fieldKey) {
            return this.blurbs.filter(b => b.field_key === fieldKey);
        },

        blurbFields() {
            if (!this.templateConfig || !this.templateConfig.sections) return [];
            return this.templateConfig.sections.filter(s => s.type === 'blurb');
        },

        async generate(fieldKey) {
            this.generating[fieldKey] = true;
            try {
                const res = await Api.post('/api/blurbs/generate', {
                    field_key: fieldKey,
                    template_name: this.selectedTemplate,
                });
                if (res.ok) {
                    await this.load();
                    Alpine.store('toast').success('Blurbs generated');
                } else {
                    const data = await res.json();
                    Alpine.store('toast').error(data.error || 'Generation failed');
                }
            } catch {
                Alpine.store('toast').error('Generation failed');
            } finally {
                this.generating[fieldKey] = false;
            }
        },

        async updateBlurb(id, status, userText) {
            try {
                const res = await Api.put(`/api/blurbs/${id}`, { status, user_text: userText || '' });
                if (res.ok) await this.load();
            } catch {
                Alpine.store('toast').error('Update failed');
            }
        },

        startEdit(blurb) {
            this.editingBlurb = blurb.id;
            this.editText = blurb.user_text || blurb.suggestion_text;
        },

        async saveEdit(id) {
            await this.updateBlurb(id, 'modified', this.editText);
            this.editingBlurb = null;
            this.editText = '';
        },

        cancelEdit() {
            this.editingBlurb = null;
            this.editText = '';
        },

        statusClass(status) {
            return {
                'accepted': 'blurb-accepted',
                'modified': 'blurb-modified',
                'rejected': 'blurb-rejected',
                'pending': 'blurb-pending',
            }[status] || '';
        },
    };
}

function generateTab() {
    return {
        compiling: false,
        compiled: false,
        error: null,

        async compile() {
            this.compiling = true;
            this.error = null;
            this.compiled = false;
            try {
                const res = await Api.post('/api/generate/compile');
                if (res.ok) {
                    this.compiled = true;
                    Alpine.store('toast').success('CV compiled successfully');
                } else {
                    const data = await res.json();
                    this.error = data.error || 'Compilation failed';
                    Alpine.store('toast').error(this.error);
                }
            } catch {
                this.error = 'Compilation failed';
                Alpine.store('toast').error(this.error);
            } finally {
                this.compiling = false;
            }
        },

        downloadPDF() {
            window.open('/api/generate/download/pdf', '_blank');
        },

        downloadTEX() {
            window.open('/api/generate/download/tex', '_blank');
        },
    };
}

function settingsTab() {
    return {
        settings: { openai_api_key_set: false, selected_template: 'classic', sentences_per_field: 3, font_size: 11 },
        apiKey: '',
        templates: [],
        loading: false,
        importing: false,

        async init() {
            await this.loadSettings();
            await this.loadTemplates();
        },

        async loadSettings() {
            try {
                const res = await Api.get('/api/settings');
                if (res.ok) this.settings = await res.json();
            } catch {}
        },

        async loadTemplates() {
            try {
                const res = await Api.get('/api/settings/templates');
                if (res.ok) {
                    const data = await res.json();
                    this.templates = data.templates || [];
                }
            } catch {}
        },

        async saveSettings() {
            this.loading = true;
            try {
                const payload = {
                    selected_template: this.settings.selected_template,
                    sentences_per_field: this.settings.sentences_per_field,
                    font_size: this.settings.font_size,
                };
                if (this.apiKey) {
                    payload.openai_api_key = this.apiKey;
                }
                const res = await Api.put('/api/settings', payload);
                if (res.ok) {
                    this.apiKey = '';
                    await this.loadSettings();
                    Alpine.store('toast').success('Settings saved');
                } else {
                    const data = await res.json();
                    Alpine.store('toast').error(data.error || 'Save failed');
                }
            } catch {
                Alpine.store('toast').error('Save failed');
            } finally {
                this.loading = false;
            }
        },

        async exportData() {
            window.open('/api/data/export', '_blank');
        },

        async importData(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.importing = true;
            try {
                const formData = new FormData();
                formData.append('file', file);
                const res = await Api.post('/api/data/import', formData);
                if (res.ok) {
                    Alpine.store('toast').success('Data imported successfully');
                } else {
                    const data = await res.json();
                    Alpine.store('toast').error(data.error || 'Import failed');
                }
            } catch {
                Alpine.store('toast').error('Import failed');
            } finally {
                this.importing = false;
                event.target.value = '';
            }
        },
    };
}
