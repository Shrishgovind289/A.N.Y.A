<p align="center">
  <img src="web/anya-logo.png" alt="A.N.Y.A logo" width="140">
</p>

<h1 align="center">A.N.Y.A</h1>

<p align="center">
  <strong>Autonomous Neural savvY Assistant</strong>
</p>

<p align="center">
  A private, locally hosted AI assistant for home-server monitoring, file access, internet research, and future smart-device integration.
</p>

---

## Overview

A.N.Y.A is a self-hosted AI agent built with FastAPI, Ollama, and a responsive web interface.

It runs locally on a Linux home server and uses the `qwen2.5:3b` language model through Ollama. The assistant can answer general questions, inspect server health, read approved files, browse public webpages, and perform web searches through controlled tools.

A.N.Y.A is designed to remain private, lightweight, extensible, and accessible from desktop or mobile devices through a private network such as Tailscale.

## Features

- Local AI inference through Ollama
- Runtime model switching
- Multi-turn persistent chat history
- Project-based chat organization
- Secure file uploads with ClamAV scanning
- Text and PDF content extraction
- Image analysis through vision-capable models
- Automatic vision-model routing
- Server CPU, memory, disk, and uptime monitoring
- NVIDIA GPU monitoring
- Combined system health reporting
- Read-only filesystem access with path restrictions
- Public web search
- Public webpage content extraction
- Automatic factual verification for factual questions and corrections
- Read-only GitHub repository access
- GitHub branches, files, commits, issues, and pull requests
- KaTeX mathematical expression rendering
- API-key authentication
- Responsive desktop and mobile web interface
- Tailscale-compatible remote access
- Automatic startup through systemd

## Technology Stack

| Component | Technology |
|---|---|
| Local AI runtime | Ollama |
| Default model | Qwen 2.5 3B |
| Backend | Python + FastAPI |
| API server | Uvicorn |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| Authentication | API key |
| Remote access | Tailscale |
| Hardware monitoring | psutil + NVIDIA SMI |
| Web search | DDGS |
| Web extraction | HTTPX + Beautiful Soup |
| PDF extraction | pypdf |
| Malware scanning | ClamAV |
| GitHub access | GitHub REST API |
| Math rendering | KaTeX |

## Project Structure

```text
A.N.Y.A/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agent_tools.py
│   ├── filesystem_tools.py
│   ├── internet_tools.py
│   └── tools.py
├── web/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── anya-logo.png
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md



