#!/usr/bin/env python3
"""Flask-powered Cryptographic Performance Simulator with WebSocket updates."""

from __future__ import annotations

import json
import logging
import os

from flask import Flask, render_template
from flask_sock import Sock

from benchmark import run_all_benchmarks

app = Flask(__name__, template_folder="templates", static_folder="static")
sock = Sock(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crypto-performance-simulator")


@app.route("/")
def index() -> str:
    """Serve the main simulator view."""
    return render_template("index.html")


@app.route("/health")
def health() -> dict:
    """Health check endpoint for deployment platforms."""
    return {"status": "healthy", "service": "crypto-simulator"}


@sock.route("/benchmark")
def benchmark_socket(ws) -> None:
    """
    WebSocket endpoint for running benchmarks with real-time progress updates.
    
    Expected message format:
    {
        "modes": ["classical", "pqc", "hybrid"],
        "latency": 50,
        "packetLoss": 2
    }
    """
    logger.info("✅ WebSocket connection established")

    def progress_callback(mode: str, iteration: int, total: int) -> None:
        """Send progress updates to client."""
        try:
            ws.send(
                json.dumps(
                    {
                        "type": "progress",
                        "mode": mode,
                        "iteration": iteration,
                        "total": total,
                    }
                )
            )
        except Exception as exc:
            logger.warning(f"Failed to send progress update: {exc}")

    try:
        while True:
            payload = ws.receive()
            if payload is None:
                break

            try:
                request = json.loads(payload)
                logger.info(f"Received benchmark request: {request}")
            except json.JSONDecodeError as exc:
                logger.error(f"Invalid JSON payload: {exc}")
                ws.send(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "Invalid request format. Expected JSON."
                        }
                    )
                )
                continue

            # Extract parameters with defaults
            modes = request.get("modes", ["classical", "pqc"])
            latency = float(request.get("latency", 0.0))
            packet_loss = float(request.get("packetLoss", 0.0))

            # Validate modes
            valid_modes = {"classical", "pqc", "hybrid"}
            modes = [m.lower() for m in modes if m.lower() in valid_modes]
            
            if not modes:
                ws.send(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "No valid modes selected. Choose from: classical, pqc, hybrid"
                        }
                    )
                )
                continue

            logger.info(
                f"Starting benchmark: modes={modes}, latency={latency}ms, "
                f"packet_loss={packet_loss}%"
            )

            try:
                # Run the benchmark with real-time progress
                results = run_all_benchmarks(
                    modes_to_run=modes,
                    latency_ms=latency,
                    packet_loss_percent=packet_loss,
                    progress_callback=progress_callback,
                )
                
                # Send final results
                ws.send(json.dumps({"type": "result", "data": results}))
                logger.info("✅ Benchmark completed successfully")
                
            except Exception as exc:
                logger.exception("❌ Benchmark execution failed")
                ws.send(
                    json.dumps(
                        {
                            "type": "error",
                            "message": f"Benchmark failed: {str(exc)}"
                        }
                    )
                )
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
    finally:
        logger.info("🔌 WebSocket connection closed")


def main() -> None:
    """Launch the simulator server."""
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    
    logger.info(
        f"🚀 Cryptographic Performance Simulator running on "
        f"http://{host}:{port}"
    )
    logger.info("Press Ctrl+C to stop the server")
    
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
