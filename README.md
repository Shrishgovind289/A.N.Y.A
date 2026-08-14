<p align="center">
  <img src="web/anya-logo.png" alt="A.N.Y.A logo" width="140">
</p>

<h1 align="center">A.N.Y.A</h1>

<p align="center">
  <strong>Autonomous Neural savvY Assistant</strong>
</p>

<p align="center">
  A private, self-hosted AI assistant for local inference, home-server monitoring, file and image analysis, web research, GitHub access, and personal AI workflows.
</p>

---

## Overview

A.N.Y.A is a self-hosted AI assistant built with **FastAPI**, **Ollama**, and a responsive web interface.

It runs locally on a Linux home server and supports multiple Ollama models, allowing models to be selected at runtime depending on the task. A.N.Y.A can maintain persistent conversations, organize chats into projects, inspect server health, monitor NVIDIA GPU resources, analyze uploaded files and images, search the public web, read webpages, and inspect GitHub repositories through controlled read-only tools.

A.N.Y.A also includes automatic factual verification for common fact-based questions and correction requests, helping reduce repeated hallucinations by grounding responses with web-search results when verification is appropriate.

The system is designed to remain **private, lightweight, extensible, and secure**, while remaining accessible from desktop and mobile devices through a private network such as Tailscale.

## Features

* Local AI inference through Ollama
* Runtime model switching
* Multi-turn persistent chat history
* Project-based chat organization
* Secure file uploads with ClamAV scanning
* Text and PDF content extraction
* Image analysis through vision-capable models
* Automatic vision-model routing
* Server CPU, memory, disk, and uptime monitoring
* NVIDIA GPU monitoring
* Combined system health reporting
* Read-only filesystem access with path restrictions
* Public web search
* Public webpage content extraction
* Automatic factual verification for factual questions and corrections
* Read-only GitHub repository access
* GitHub repository, branch, file, commit, issue, and pull-request inspection
* KaTeX mathematical expression rendering
* API-key authentication
* Responsive desktop and mobile web interface
* Tailscale-compatible remote access
* Automatic startup through systemd

## Technology Stack

| Component           | Technology             |
| ------------------- | ---------------------- |
| Local AI runtime    | Ollama                 |
| Default model       | Qwen 2.5 3B            |
| Backend             | Python + FastAPI       |
| API server          | Uvicorn                |
| Frontend            | HTML, CSS, JavaScript  |
| Database            | SQLite                 |
| Authentication      | API key                |
| Remote access       | Tailscale              |
| Hardware monitoring | psutil + NVIDIA SMI    |
| Web search          | DDGS                   |
| Web extraction      | HTTPX + Beautiful Soup |
| PDF extraction      | pypdf                  |
| Malware scanning    | ClamAV                 |
| GitHub access       | GitHub REST API        |
| Math rendering      | KaTeX                  |

## Project Structure

```text
A.N.Y.A/
├── app/
│   ├── __init__.py
│   ├── agent_tools.py
│   ├── database.py
│   ├── factual_verification.py
│   ├── file_content.py
│   ├── file_storage.py
│   ├── filesystem_tools.py
│   ├── github_tools.py
│   ├── internet_tools.py
│   ├── main.py
│   └── tools.py
├── data/
├── projects/
├── web/
│   ├── anya-logo.png
│   ├── app.js
│   ├── index.html
│   └── style.css
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
