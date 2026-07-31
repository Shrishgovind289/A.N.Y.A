<p align="center">
  <img src="web/anya-logo.png" alt="A.N.Y.A logo" width="140">
</p>

<h1 align="center">A.N.Y.A</h1>

<p align="center">
  <strong>Autonomous Neural savvY Assistant</strong>
</p>

<p align="center">
  A private, locally hosted AI assistant for home-server monitoring, file access,
  internet research, and future smart-device integration.
</p>

---

## Overview

A.N.Y.A is a self-hosted AI agent built with FastAPI, Ollama, and a responsive web interface.

It runs locally on a Linux home server and uses the `qwen2.5:3b` language model through Ollama. The assistant can answer general questions, inspect server health, read approved files, browse public webpages, and perform web searches through controlled tools.

A.N.Y.A is designed to remain private, lightweight, extensible, and accessible from desktop or mobile devices through a private network such as Tailscale.

## Features

- Local AI inference through Ollama
- FastAPI-based backend
- Responsive desktop and mobile web interface
- API-key authentication
- Multi-turn conversation support
- Server CPU, memory, disk, and uptime monitoring
- NVIDIA GPU monitoring
- Read-only filesystem tools
- Configurable allowed and denied paths
- Public web search
- Public webpage content extraction
- Protection against local-network webpage requests
- Configurable response length and temperature
- Automatic startup through systemd
- Tailscale-compatible remote access

## Technology Stack

| Component | Technology |
|---|---|
| AI model | Qwen 2.5 3B |
| Model runtime | Ollama |
| Backend | Python and FastAPI |
| Web server | Uvicorn |
| Frontend | HTML, CSS, and JavaScript |
| Authentication | API key |
| Remote access | Tailscale |
| Hardware monitoring | psutil and NVIDIA SMI |
| Web search | DDGS |
| Web extraction | HTTPX and Beautiful Soup |

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



