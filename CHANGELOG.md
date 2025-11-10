# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-11-11

### Added
- Initial release of Quantum-Resistant Cryptography Performance Simulator
- Interactive web-based UI with real-time WebSocket updates
- Support for three cryptographic modes:
  - Classical (ECDH P-256 + ECDSA)
  - Post-Quantum (Kyber768 + ML-DSA-65)
  - Hybrid (combined classical + PQC)
- Network simulation capabilities:
  - Configurable latency (0-200ms)
  - Configurable packet loss (0-10%)
- Real-time progress tracking during benchmarks
- Interactive Chart.js visualizations:
  - Handshake latency comparison
  - Public key size comparison
  - Data overhead analysis
- Professional UI features:
  - Animated gradient backgrounds
  - Glass morphism design
  - Responsive layout (mobile, tablet, desktop)
  - Accessible keyboard navigation
- Comprehensive benchmarking:
  - 50 iterations per mode for statistical accuracy
  - Statistical analysis (mean calculation)
  - Detailed metric reporting
- Docker support for containerized deployment
- Health check endpoint for monitoring
- Unit tests for classical and PQC channels
- Professional documentation:
  - README.md with usage instructions
  - CONTRIBUTING.md with development guidelines
  - LICENSE (MIT)

### Technical Details
- **Backend**: Flask 3.0 + gevent + WebSocket support
- **Frontend**: Vanilla JavaScript + Tailwind CSS + Chart.js
- **Cryptography**: 
  - Python `cryptography` library for classical algorithms
  - `liboqs` (Open Quantum Safe) for NIST-approved PQC algorithms
- **Testing**: pytest with comprehensive unit test coverage
- **Deployment**: Docker-ready with Hugging Face Spaces support

---

## [Unreleased]

### Planned Features
- [ ] Additional PQC algorithms (NTRU, SABER, FrodoKEM)
- [ ] Export results to CSV/JSON format
- [ ] Historical benchmark comparison dashboard
- [ ] RESTful API for programmatic access
- [ ] CLI mode for headless benchmarking
- [ ] Multi-threaded concurrent benchmarks
- [ ] Database integration for result persistence

---

## Release Notes

### Version 1.0.0 - Initial Release

This is the first stable release of the Quantum-Resistant Cryptography Performance Simulator. The tool provides a professional, interactive environment for benchmarking classical vs. post-quantum cryptographic protocols.

**Key Highlights:**
- Real-time WebSocket-based benchmarking
- Beautiful, responsive UI with animated visualizations
- Support for NIST-approved PQC algorithms (Kyber768, ML-DSA-65)
- Network simulation for realistic performance testing
- Docker deployment ready

**Known Limitations:**
- Limited to Kyber768 and ML-DSA-65 (more algorithms coming)
- Single-threaded benchmarking (sequential mode execution)
- No result persistence (results lost on page refresh)

**Supported Platforms:**
- macOS (tested on macOS 14+)
- Linux (tested on Ubuntu 22.04+)
- Windows (via Docker)
- Web browsers: Chrome 90+, Firefox 88+, Safari 14+

---

For detailed changes and contributions, see the [commit history](https://github.com/bhaskardatta/Quantum-performance-simulator/commits/main).
