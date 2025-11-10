"""
Benchmark routines for classical, PQC, and hybrid handshakes with network simulation.
Enhanced for professional-grade performance analysis and visualization.
"""

from __future__ import annotations

import json
import random
import socket
import statistics
import threading
import time
from typing import Callable, Dict, List, Optional

from oqs import oqs
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from client_classical import ClassicalClient
from client_pqc import PQCClient
from server_classical import ClassicalServer
from server_pqc import PQCServer

ITERATIONS_PER_MODE = 50


def _get_free_port() -> int:
    """Find an available port dynamically."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def _simulate_network_penalties(
    elapsed_ms: float, latency_ms: float, packet_loss_percent: float
) -> float:
    """Apply latency and packet loss adjustments to raw timings."""
    adjusted = elapsed_ms + max(latency_ms, 0.0)
    if packet_loss_percent > 0.0:
        adjusted *= 1.0 + (packet_loss_percent / 100.0)
        jitter = adjusted * (packet_loss_percent / 500.0)
        adjusted += random.uniform(0.0, jitter)
    return adjusted


def measure_classical_handshake(
    latency_ms: float = 0.0,
    packet_loss_percent: float = 0.0,
    *,
    port: int = None,
) -> float:
    """Measure a single classical ECDH handshake with network simulation."""
    if port is None:
        port = _get_free_port()
    
    server = ClassicalServer(host="0.0.0.0", port=port)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(0.1)  # Give server more time to start

    client = ClassicalClient(host="127.0.0.1", port=port)
    try:
        start_time = time.perf_counter()
        if not client.connect():
            raise RuntimeError("Classical handshake failed to connect")
        client.disconnect()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    finally:
        client.disconnect()
        server.stop()
        server_thread.join(timeout=2.0)
        time.sleep(0.05)  # Brief pause between tests

    return _simulate_network_penalties(elapsed_ms, latency_ms, packet_loss_percent)


def measure_pqc_handshake(
    latency_ms: float = 0.0,
    packet_loss_percent: float = 0.0,
    *,
    port: int = None,
) -> float:
    """Measure a single PQC handshake (Kyber768 + ML-DSA-65) with network simulation."""
    if port is None:
        port = _get_free_port()
    
    server = PQCServer(host="0.0.0.0", port=port)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(0.1)  # Give server more time to start

    client = PQCClient(host="127.0.0.1", port=port)
    try:
        start_time = time.perf_counter()
        if not client.connect():
            raise RuntimeError("PQC handshake failed to connect")
        client.disconnect()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    finally:
        client.disconnect()
        server.stop()
        server_thread.join(timeout=2.0)
        time.sleep(0.05)  # Brief pause between tests

    return _simulate_network_penalties(elapsed_ms, latency_ms, packet_loss_percent)


def measure_hybrid_handshake(
    latency_ms: float = 0.0, 
    packet_loss_percent: float = 0.0
) -> float:
    """Measure hybrid handshake (Classical + PQC sequential)."""
    classical_time = measure_classical_handshake(latency_ms, packet_loss_percent)
    pqc_time = measure_pqc_handshake(latency_ms, packet_loss_percent)
    return classical_time + pqc_time


def get_classical_key_size() -> int:
    """Return size of a classical ECDH public key in bytes."""
    private_key = ec.generate_private_key(ec.SECP384R1())
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return len(public_bytes)


def get_pqc_key_sizes() -> Dict[str, int]:
    """Return sizes of Kyber768 public key and ML-DSA-65 signature in bytes."""
    with oqs.KeyEncapsulation("Kyber768") as kem:
        with oqs.Signature("ML-DSA-65") as sig:
            kem_public_key = kem.generate_keypair()
            sig.generate_keypair()
            dummy_message = b"benchmark"
            signature = sig.sign(dummy_message)
    return {
        "kem_public_key_bytes": len(kem_public_key),
        "signature_bytes": len(signature),
    }


def run_all_benchmarks(
    modes_to_run: Optional[List[str]] = None,
    latency_ms: float = 0.0,
    packet_loss_percent: float = 0.0,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> Dict[str, Dict[str, float]]:
    """Run comprehensive benchmarking suite with configurable modes."""
    if modes_to_run is None:
        modes_to_run = ['classical', 'pqc', 'hybrid']
    
    modes_to_run = [mode.lower() for mode in modes_to_run]
    latency_ms = max(float(latency_ms), 0.0)
    packet_loss_percent = max(float(packet_loss_percent), 0.0)

    samples: Dict[str, List[float]] = {}

    if 'classical' in modes_to_run:
        samples['classical'] = []
        for iteration in range(1, ITERATIONS_PER_MODE + 1):
            samples['classical'].append(measure_classical_handshake(latency_ms, packet_loss_percent))
            if progress_callback:
                progress_callback("Classical", iteration, ITERATIONS_PER_MODE)

    if 'pqc' in modes_to_run:
        samples['pqc'] = []
        for iteration in range(1, ITERATIONS_PER_MODE + 1):
            samples['pqc'].append(measure_pqc_handshake(latency_ms, packet_loss_percent))
            if progress_callback:
                progress_callback("PQC", iteration, ITERATIONS_PER_MODE)

    if 'hybrid' in modes_to_run:
        samples['hybrid'] = []
        for iteration in range(1, ITERATIONS_PER_MODE + 1):
            samples['hybrid'].append(measure_hybrid_handshake(latency_ms, packet_loss_percent))
            if progress_callback:
                progress_callback("Hybrid", iteration, ITERATIONS_PER_MODE)

    classical_key_size = get_classical_key_size()
    pqc_sizes = get_pqc_key_sizes()

    results = {
        "settings": {
            "modes": modes_to_run,
            "latency_ms": latency_ms,
            "packet_loss_percent": packet_loss_percent,
            "iterations": ITERATIONS_PER_MODE,
        },
        "handshake_time_ms": {},
        "handshake_samples": samples,
        "public_key_bytes": {
            "classical": classical_key_size,
            "pqc": pqc_sizes["kem_public_key_bytes"],
            "hybrid": classical_key_size + pqc_sizes["kem_public_key_bytes"],
        },
        "signature_bytes": {
            "pqc": pqc_sizes["signature_bytes"],
            "hybrid": pqc_sizes["signature_bytes"],
        },
    }
    
    for mode in modes_to_run:
        if mode in samples and samples[mode]:
            results["handshake_time_ms"][mode] = statistics.mean(samples[mode])
    
    return results


if __name__ == "__main__":
    results = run_all_benchmarks(modes_to_run=['classical', 'pqc', 'hybrid'], latency_ms=30.0, packet_loss_percent=2.0)
    print(json.dumps(results, indent=2))
