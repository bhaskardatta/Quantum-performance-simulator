# 🔐 Cryptographic Performance Simulator

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Post-Quantum](https://img.shields.io/badge/Post--Quantum-NIST--Approved-teal.svg)](https://csrc.nist.gov/projects/post-quantum-cryptography)

**Interactive web-based benchmarking tool for comparing Classical, Post-Quantum, and Hybrid cryptographic protocols**

---

## 📋 Overview

The **Cryptographic Performance Simulator** is a professional-grade benchmarking tool designed to evaluate and compare the performance characteristics of classical cryptographic algorithms against their post-quantum counterparts.

### Why This Matters

With the advent of quantum computing, traditional cryptographic methods (RSA, ECDH, ECDSA) face existential threats from algorithms like Shor's. This simulator helps developers, researchers, and security professionals:

- **Understand** the performance implications of migrating to post-quantum cryptography (PQC)
- **Benchmark** real-world handshake latencies under various network conditions
- **Visualize** the overhead introduced by larger PQC key sizes and signatures
- **Plan** migration strategies using hybrid approaches that combine classical + PQC

---

## ✨ Features

### Cryptographic Modes

| Mode | Key Exchange | Digital Signature | Use Case |
|------|-------------|-------------------|----------|
| **Classical** | ECDH P-256 | ECDSA | Baseline performance |
| **Post-Quantum** | Kyber768 | ML-DSA-65 | Quantum-resistant |
| **Hybrid** | ECDH + Kyber | ECDSA + ML-DSA | Maximum security |

### Benchmarking Capabilities

- ✅ **50 iterations per mode** for statistical accuracy
- ✅ **Configurable network simulation** (latency + packet loss)
- ✅ **Real-time progress tracking** via WebSocket
- ✅ **Comprehensive metrics**:
  - Handshake latency (milliseconds)
  - Public key sizes (bytes)
  - Signature sizes (bytes)
  - Statistical averages

### User Interface

- 🎨 **Professional design** with clean, modern aesthetics
- 💎 **Responsive layout** (desktop, tablet, mobile)
- ♿ **Accessible** keyboard navigation
- 📈 **Interactive charts** with hover tooltips
- 🎚️ **Live slider controls** for network parameters

---

## 🔧 Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **pip**: Latest version
- **Docker** (optional): For containerized deployment

### Dependencies

```bash
Flask==3.0.0
flask-sock==0.7.0
simple-websocket==1.0.0
cryptography==41.0.7
liboqs-python==0.14.1
```

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/bhaskardatta/Quantum-performance-simulator.git
cd Quantum-performance-simulator

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the simulator
python web_dashboard.py

# 5. Open browser
open http://localhost:8080
```

### Docker

```bash
# Build and run
docker-compose up --build

# Access at http://localhost:8080
```

---

## 📖 Usage

### 1. Select Benchmark Modes

Choose one or more:
- **Classical**: ECDH + ECDSA baseline
- **Post-Quantum**: Kyber768 + ML-DSA-65
- **Hybrid**: Combined approach

### 2. Configure Network Simulation

Adjust sliders:
- **Latency**: 0-200ms
- **Packet Loss**: 0-10%

### 3. Run Benchmark

Click **"Run Performance Benchmark"** and monitor real-time progress.

### 4. Analyze Results

View stat cards and interactive charts showing:
- Handshake latency comparison
- Public key size overhead
- Data overhead breakdown

---

## 🧪 Testing

```bash
# Test classical channel
pytest test_classical_channel.py -v

# Test PQC channel
pytest test_pqc_channel.py -v

# Run all tests
pytest -v
```

---

## 🌐 Deployment

### Docker Deployment

```bash
docker build -t crypto-simulator .
docker run -d -p 8080:8080 crypto-simulator
```

### Hugging Face Spaces

1. Create a new Space (Docker SDK)
2. Push your code:
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
   git push space main
   ```

---

## �� Performance Benchmarks

### Typical Results (No Network Simulation)

| Metric | Classical | Post-Quantum | Hybrid |
|--------|-----------|--------------|--------|
| **Handshake Time** | 5-10 ms | 8-15 ms | 12-20 ms |
| **Public Key Size** | 91 bytes | 1,184 bytes | 1,275 bytes |
| **Signature Size** | 71 bytes | 2,420 bytes | 2,491 bytes |

*Results vary based on hardware and network conditions*

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **NIST** - [Post-Quantum Cryptography Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- **Open Quantum Safe** - [liboqs library](https://github.com/open-quantum-safe/liboqs)

---

<div align="center">

**Built for a quantum-resistant future**

⭐ If you find this project useful, please star it!

</div>
