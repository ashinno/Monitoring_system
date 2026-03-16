import datetime
import logging
import os
import socket
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import psutil
import requests

from schemas import InterceptionConfig


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrafficInterceptor")


@dataclass(frozen=True)
class FlowRecord:
    local_ip: str
    remote_ip: str
    remote_port: int
    protocol: str


class TrafficInterceptor:
    def __init__(self):
        self._config = InterceptionConfig()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._stats = {
            "packets_intercepted": 0,
            "bytes_intercepted": 0,
            "errors": 0,
        }

        self._last_io_snapshot: Dict[str, Tuple[int, int]] = {}
        self._interface_ip_map: Dict[str, Set[str]] = {}

        self.api_url = os.getenv("TRAFFIC_INGEST_URL", "http://127.0.0.1:8000/traffic")
        parsed = urlparse(self.api_url)
        self._ingest_host = parsed.hostname or "127.0.0.1"
        self._ingest_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._last_access_denied_log_at = 0.0
        self._access_denied_log_interval_seconds = max(
            1,
            int(os.getenv("TRAFFIC_ACCESS_DENIED_LOG_INTERVAL_SECONDS", "30")),
        )

    def get_available_interfaces(self) -> List[str]:
        return sorted(psutil.net_if_addrs().keys())

    def start(self, config: InterceptionConfig):
        if self._config.is_running:
            self.stop()

        self._refresh_interface_ip_map()

        selected_interface = config.interface or None
        if selected_interface and selected_interface not in self._interface_ip_map:
            raise ValueError(f"Interface '{selected_interface}' was not found")

        protocols = [p.upper() for p in (config.protocols or ["TCP", "UDP"])]
        protocols = [p for p in protocols if p in {"TCP", "UDP"}]
        if not protocols:
            protocols = ["TCP", "UDP"]

        poll_interval_ms = min(10000, max(200, config.poll_interval_ms))

        self._config = InterceptionConfig(
            is_running=True,
            interface=selected_interface,
            protocols=protocols,
            include_loopback=config.include_loopback,
            poll_interval_ms=poll_interval_ms,
        )

        self._stats = {
            "packets_intercepted": 0,
            "bytes_intercepted": 0,
            "errors": 0,
        }

        self._last_io_snapshot = self._get_interface_counters()
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Traffic interception started with config=%s", self._config.model_dump())

    def stop(self):
        if not self._config.is_running:
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

        self._config.is_running = False
        logger.info("Traffic interception stopped")

    def get_status(self):
        return {
            "is_running": self._config.is_running,
            "config": self._config,
            "stats": self._stats,
        }

    def _run(self):
        while not self._stop_event.is_set():
            started_at = time.monotonic()
            try:
                self._capture_cycle()
            except Exception as exc:
                self._stats["errors"] += 1
                logger.exception("Interception cycle failed: %s", exc)

            elapsed = time.monotonic() - started_at
            sleep_time = max(0.0, (self._config.poll_interval_ms / 1000.0) - elapsed)
            self._stop_event.wait(timeout=sleep_time)

    def _capture_cycle(self):
        flows = self._collect_flows()
        if not flows:
            self._compute_bytes_delta()
            return

        max_flows_per_cycle = 100
        flows = flows[:max_flows_per_cycle]

        total_bytes = self._compute_bytes_delta()
        if total_bytes <= 0:
            return

        bytes_per_flow = total_bytes // len(flows) if flows else 0
        remainder = total_bytes % len(flows) if flows else 0

        for idx, flow in enumerate(flows):
            bytes_for_flow = bytes_per_flow + (1 if idx < remainder else 0)
            packet = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.now().isoformat(),
                "source_ip": flow.local_ip,
                "destination_ip": flow.remote_ip,
                "port": flow.remote_port,
                "protocol": flow.protocol,
                "bytes_transferred": bytes_for_flow,
                "packet_count": max(1, bytes_for_flow // 1200) if bytes_for_flow else 1,
                "latency": 0,
                "is_anomalous": False,
            }

            if self._ingest_packet(packet):
                self._stats["packets_intercepted"] += 1
                self._stats["bytes_intercepted"] += bytes_for_flow

    def _collect_flows(self) -> List[FlowRecord]:
        self._refresh_interface_ip_map()
        selected_interface_ips = self._interface_ip_map.get(self._config.interface or "", set())

        unique_flows: Dict[Tuple[str, str, int, str], FlowRecord] = {}

        try:
            connections = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, psutil.Error) as exc:
            self._stats["errors"] += 1
            self._log_access_denied(exc)
            return []

        for conn in connections:
            if not conn.laddr or not conn.raddr:
                continue

            local_ip = getattr(conn.laddr, "ip", None)
            remote_ip = getattr(conn.raddr, "ip", None)
            remote_port = getattr(conn.raddr, "port", 0)

            if not local_ip or not remote_ip or not remote_port:
                continue

            if self._is_ingest_connection(remote_ip, remote_port):
                continue

            protocol = self._resolve_protocol(conn.type)
            if protocol not in self._config.protocols:
                continue

            if selected_interface_ips and local_ip not in selected_interface_ips:
                continue

            if not self._config.include_loopback and (self._is_loopback(local_ip) or self._is_loopback(remote_ip)):
                continue

            key = (local_ip, remote_ip, remote_port, protocol)
            unique_flows[key] = FlowRecord(
                local_ip=local_ip,
                remote_ip=remote_ip,
                remote_port=remote_port,
                protocol=protocol,
            )

        return list(unique_flows.values())

    def _compute_bytes_delta(self) -> int:
        current_snapshot = self._get_interface_counters()

        if self._config.interface:
            interface_names = [self._config.interface]
        else:
            interface_names = list(current_snapshot.keys())

        total_delta = 0
        for interface_name in interface_names:
            if interface_name not in current_snapshot:
                continue

            if not self._config.include_loopback and interface_name.lower().startswith("lo"):
                continue

            sent_now, recv_now = current_snapshot[interface_name]
            sent_prev, recv_prev = self._last_io_snapshot.get(interface_name, (sent_now, recv_now))

            total_delta += max(0, sent_now - sent_prev)
            total_delta += max(0, recv_now - recv_prev)

        self._last_io_snapshot = current_snapshot
        return total_delta

    def _refresh_interface_ip_map(self):
        interface_ip_map: Dict[str, Set[str]] = {}
        for interface_name, addresses in psutil.net_if_addrs().items():
            ips: Set[str] = set()
            for addr in addresses:
                if addr.family in (socket.AF_INET, socket.AF_INET6):
                    if addr.address:
                        ips.add(addr.address)
            interface_ip_map[interface_name] = ips

        self._interface_ip_map = interface_ip_map

    def _get_interface_counters(self) -> Dict[str, Tuple[int, int]]:
        snapshot = {}
        for interface_name, counters in psutil.net_io_counters(pernic=True).items():
            snapshot[interface_name] = (counters.bytes_sent, counters.bytes_recv)
        return snapshot

    @staticmethod
    def _resolve_protocol(socket_type: int) -> str:
        if socket_type == socket.SOCK_STREAM:
            return "TCP"
        if socket_type == socket.SOCK_DGRAM:
            return "UDP"
        return "UNKNOWN"

    @staticmethod
    def _is_loopback(ip_address: str) -> bool:
        return ip_address.startswith("127.") or ip_address == "::1"

    def _is_ingest_connection(self, remote_ip: str, remote_port: int) -> bool:
        if remote_port != self._ingest_port:
            return False

        if remote_ip == self._ingest_host:
            return True

        if self._ingest_host in {"localhost", "127.0.0.1", "::1"} and self._is_loopback(remote_ip):
            return True

        return False

    def _log_access_denied(self, exc: Exception):
        now = time.monotonic()
        if (now - self._last_access_denied_log_at) < self._access_denied_log_interval_seconds:
            return
        self._last_access_denied_log_at = now
        logger.warning(
            "Connection listing denied: %s. Grant elevated privileges to list host connections.",
            exc,
        )

    def _ingest_packet(self, packet: Dict[str, object]) -> bool:
        try:
            response = requests.post(
                self.api_url,
                json=packet,
                timeout=5,
                proxies={"http": None, "https": None},
            )
            if response.status_code >= 400:
                self._stats["errors"] += 1
                logger.error("Traffic ingest failed with status=%s", response.status_code)
                return False
            return True
        except Exception as exc:
            self._stats["errors"] += 1
            logger.error("Traffic ingest request failed: %s", exc)
            return False


interceptor = TrafficInterceptor()
