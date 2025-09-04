# Developer Onboarding Guide

**Status: [ACTIVE]** – Read this first when joining the project.

Welcome to **Autocoder4_CC**!  This guide walks you through setting up your development environment, understanding the repository layout, and finding key resources.

---

## 1. Clone & Install

```bash
# Clone the repo
git clone https://github.com/your-org/autocoder4_cc.git
cd autocoder4_cc

# Install Python deps
python -m pip install --upgrade pip
pip install -r requirements.txt

# (Optional) Docs & Dev tools
pip install mkdocs-material
```

> 💡  Tip: Use a Python virtual-env or Conda environment.

---

## 2. Explore the Repo

| Path | Purpose |
|------|---------|
| `autocoder_cc/` | Core Python package – generators, analysis, healing, etc. |
| `examples/` | Working reference systems you can run locally |
| `docs/` | Source for all project documentation (served via MkDocs) |
| `tools/` | Utility scripts, CI helpers, validation tools |

Full architecture docs live under **Architecture** in the left-hand nav.

---

## 3. Run Your First Generation

```bash
# Quick test generation
autocoder generate examples/test_working_system/health_check_api/config/system_config.yaml

# Run locally with hot-reload
autocoder runlocal examples/test_working_system/health_check_api/config/system_config.yaml --watch
```

See the **[Quickstart Guide](../quickstart.md)** for detailed walkthrough.

---

## 4. Serve Interactive Docs Locally

```bash
# Inside repo root
mkdocs serve

# Open http://localhost:8000 in your browser
```

You’ll get the same left-hand navigation you see on GitHub Pages but live-reloaded as you edit markdown.

---

## 5. Contribute Code or Docs

1. Read `docs/development/contributing.md`
2. Create a feature branch: `git checkout -b feat/my-change`
3. Run `pytest` and `python tools/documentation/enhanced_doc_health_dashboard.py`
4. Push and open a PR – the Docs validation workflow will run automatically.

---

## 6. Common Commands Cheat-Sheet

| Task | Command |
|------|---------|
| Run unit tests | `pytest tests/` |
| Lint code | `flake8` + `black --check` |
| Docs health check | `python tools/documentation/enhanced_doc_health_dashboard.py` |
| Roadmap lint | `python tools/scripts/roadmap_lint.py` |
| Serve docs | `mkdocs serve` |

---

## 7. Getting Help

• **Slack/Discord**: #autocoder-dev channel  
• **Issues**: Use GitHub issues for bugs & feature requests  
• **Discussions**: Ask architecture questions in GitHub Discussions  

Welcome aboard!  🚀 