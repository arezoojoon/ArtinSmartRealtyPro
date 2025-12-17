# ArtinSmartRealty Pro

**Enterprise-Grade Real Estate CRM with AI-Powered WhatsApp & Telegram Bots**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

---

## 🚀 Overview

ArtinSmartRealty Pro is a **multi-tenant SaaS platform** for real estate agencies, featuring:

- 🤖 **AI Chatbots** (WhatsApp & Telegram) powered by Google Gemini 2.0
- 📊 **Advanced CRM** with lead scoring and psychological profiling
- 📈 **ROI Calculator** with automated PDF reports
- 🎯 **Smart Follow-up Engine** with 7-stage Ghost Protocol
- 🏢 **Multi-tenant Architecture** with role-based access control
- 📱 **Modern React Admin Panel** with real-time analytics

---

## ✨ Key Features

### 🤖 **AI-Powered Conversational Bots**

- **Multi-channel**: WhatsApp (WAHA/Twilio) & Telegram
- **Multi-language**: English, Persian, Arabic, Russian
- **Smart Context**: Remembers conversation history via Redis
- **Voice Support**: Processes voice messages with Gemini 2.0
- **Image Analysis**: Analyzes property photos sent by users

### 📊 **Lead Management**

- **Lead Scoring**: BANT + Engagement + Response Time (0-100 scale)
- **Psychological Profiling**: Hot/Warm/Cold classification
- **Follow-up Automation**: 7-stage Ghost Protocol with FOMO triggers
- **Smart Routing**: Auto-assign leads to available agents

### 💰 **ROI Calculator**

- **Dynamic Calculations**: Purchase price, rental income, ROI, Golden Visa eligibility
- **PDF Generation**: Professional branded reports with charts
- **Multi-currency**: AED, USD, EUR support

---

## 🚀 Quick Start

### **Prerequisites**

- Docker 20.10+ & Docker Compose 2.0+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- Telegram Bot Token ([Create bot via @BotFather](https://t.me/BotFather))

### **1. Clone & Configure**

```bash
git clone https://github.com/arezoojoon/ArtinSmartRealtyPro.git
cd ArtinSmartRealtyPro
cp .env.example .env
# Edit .env with your API keys
```

### **2. Deploy**

```bash
./deploy.sh prod
```

### **3. Access**

- **Admin Panel**: `http://localhost`
- **API Docs**: `http://localhost/docs`

---

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Bot Workflows](docs/BOT_WORKFLOWS.md)

---

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.11 + SQLAlchemy
- **AI**: Google Gemini 2.0 Flash
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Frontend**: React 18 + Vite + Material-UI
- **Infrastructure**: Docker + Nginx

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Built with ❤️ for Real Estate Professionals**
