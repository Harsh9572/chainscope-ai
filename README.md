<div align="center">

# 🚀 ChainScope AI

**A Real-Time Blockchain Intelligence Platform**

Full-stack crypto analytics — live prices, wallet intelligence, whale tracking, AI-generated insights, and token risk scoring, all in one interactive dashboard.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render&logoColor=white)](https://render.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Harsh9572/chainscope-ai?style=social)](https://github.com/Harsh9572/chainscope-ai)

[Live Frontend](https://chainscope-ai-b3hrzzz4t4enjnfcoayzfn.streamlit.app/) · [API Docs](https://chainscope-ai-ljoa.onrender.com/docs) · [Report Bug](../../issues) · [Request Feature](../../issues)

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Live Demo](#-live-demo)
- [Architecture](#️-architecture)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Backend Highlights](#-backend-highlights)
- [Screenshots](#️-screenshots)
- [Deployment](#-deployment)
- [Challenges Solved](#-challenges-solved)
- [What I Learned](#-what-i-learned)
- [Roadmap](#-roadmap)
- [Author](#-author)

---

## 🧭 Overview

**ChainScope AI** is a full-stack blockchain analytics platform that delivers real-time cryptocurrency market intelligence, wallet analysis, whale transaction tracking, AI-generated insights, and token risk assessment through an interactive web dashboard.

Built to demonstrate modern backend development, API integration, cloud deployment, and production-ready engineering practices.

---

## ✨ Features

| Category | Capabilities |
|---|---|
| 📈 **Market Dashboard** | Live BTC & ETH prices, interactive visualizations, real-time crypto overview |
| 🔍 **Wallet Intelligence** | Ethereum wallet analysis, recent transaction history, activity monitoring |
| 📊 **Token Analytics** | Live price, market cap, trading volume, 24h stats |
| 🐋 **Whale Tracker** | Large wallet monitoring, recent whale transactions, activity visualization |
| 🤖 **AI Market Insights** | Automated token analysis, trading interpretation, behavior insights |
| 🛡️ **Risk Assessment** | Market-cap analysis, volume-based risk evaluation, token risk classification |

---

## 🌍 Live Demo

| Layer | Link |
|---|---|
| 🖥️ Frontend (Streamlit) | [chainscope-ai-b3hrzzz4t4enjnfcoayzfn.streamlit.app](https://chainscope-ai-b3hrzzz4t4enjnfcoayzfn.streamlit.app/) |
| ⚙️ Backend API Docs | [chainscope-ai-ljoa.onrender.com/docs](https://chainscope-ai-ljoa.onrender.com/docs) |

> **Note:** The backend is hosted on Render's free tier and may take up to a minute to spin up after inactivity.

---

## 🏗️ Architecture

```
                     User
                       │
                       ▼
             Streamlit Dashboard
                       │
                       ▼
               FastAPI Backend
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
  Binance API   CoinGecko API   Etherscan API
         │             │              │
         └─────────────┼──────────────┘
                       ▼
           Blockchain Intelligence
```

---

## 🛠️ Tech Stack

**Backend**
`Python` · `FastAPI` · `REST APIs` · `Requests` · `python-dotenv`

**Frontend**
`Streamlit` · `Plotly` · `Pandas`

**Blockchain APIs**
`Binance API` · `CoinGecko API` · `Etherscan API V2`

**Deployment**
`Render` · `Streamlit Community Cloud`

**Version Control**
`Git` · `GitHub`

---

## 📂 Project Structure

```
chainscope-ai
│
├── backend
│   ├── app
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
│
├── frontend
│   ├── app.py
│   └── requirements.txt
│
├── screenshots
│
├── README.md
└── LICENSE
```

---

## ⚡ Getting Started

### Prerequisites
- Python 3.10+
- API keys for Etherscan (and any other services used)

### 1. Clone the repository
```bash
git clone https://github.com/Harsh9572/chainscope-ai.git
cd chainscope-ai
```

### 2. Set up the backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:
```env
ETHERSCAN_API_KEY=your_api_key_here
```

Run the API:
```bash
uvicorn app.main:app --reload
```
The backend will be available at `http://127.0.0.1:8000` with docs at `http://127.0.0.1:8000/docs`.

### 3. Set up the frontend
```bash
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔥 Backend Highlights

The backend follows production-ready practices including:

- Modular API architecture
- Centralized helper functions
- Input validation
- Ethereum wallet validation
- Structured logging
- Environment variable management
- Robust exception handling
- API timeout management
- Health monitoring endpoint
- Graceful third-party API failure handling
- Consistent JSON responses
- RESTful API design

---

## 🖼️ Screenshots

<details>
<summary><b>Click to expand</b></summary>

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Main UI
![Main UI](screenshots/ui%20chaincodeai.png)

### Wallet Analyzer
![Wallet Analyzer](screenshots/wallet%20analyzer.png)

### Token Analytics
![Token Analytics](screenshots/token%20analytics.png)

### Solana Analytics
![Solana Analytics](screenshots/salona%20analytics.png)

### Whale Tracker
![Whale Tracker](screenshots/whale%20tracker.png)

### Whale Analytics
![Whale Analytics](screenshots/whale%20analytics.png)

### AI Insights
![AI Insights](screenshots/ai%20insights.png)

### Risk Assessment
![Risk Assessment](screenshots/risk%20assesment.png)

</details>

---

## 🚀 Deployment

| Service | Platform |
|---|---|
| Frontend | Streamlit Community Cloud |
| Backend | Render |
| Version Control | GitHub |

---

## 💡 Challenges Solved

During development, several real-world engineering challenges were addressed:

- Third-party API integration
- Production deployment issues
- API rate-limit handling
- Invalid input validation
- Cloud deployment debugging
- Backend reliability improvements
- Error handling for external services
- Frontend-backend communication

---

## 📚 What I Learned

This project strengthened my practical understanding of:

- Backend Engineering
- REST API Development
- FastAPI
- Blockchain APIs
- Cloud Deployment
- Data Visualization
- API Integration
- Production Debugging
- Error Handling
- Git & GitHub Workflow

---

## 🚀 Roadmap

- [ ] Multi-chain blockchain support
- [ ] Portfolio tracker
- [ ] WebSocket-based live prices
- [ ] User authentication
- [ ] Historical analytics
- [ ] AI-based price prediction
- [ ] Notification system

---

## 👨‍💻 Author

**Harsh Kumar**
🎓 B.Tech Information Technology

[![Email](https://img.shields.io/badge/Email-hk.16.12264%40gmail.com-D14836?logo=gmail&logoColor=white)](mailto:hk.16.12264@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-Harsh9572-181717?logo=github&logoColor=white)](https://github.com/Harsh9572)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Harsh%20Kumar-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/harsh-kumar-b9b9a3298)

---

<div align="center">

### ⭐ Support

If you found this project useful, please consider starring the repository!

</div>
