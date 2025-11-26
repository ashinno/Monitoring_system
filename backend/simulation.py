import threading
import time
import random
import uuid
import datetime
import requests
import logging
from typing import Optional
from schemas import SimulationConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrafficSimulator")

class TrafficSimulator:
    def __init__(self):
        self._config = SimulationConfig(
            is_running=False,
            traffic_type="HTTP",
            volume="medium",
            pattern="steady",
            packet_size_range=[500, 1500],
            error_rate=0.0,
            latency=0
        )
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._stats = {
            "packets_generated": 0,
            "bytes_generated": 0,
            "errors_simulated": 0
        }
        self.api_url = "http://localhost:8000/traffic"  # Self-referencing

    def start(self, config: SimulationConfig):
        if self._config.is_running:
            self.stop()
        
        self._config = config
        self._config.is_running = True
        self._stop_event.clear()
        
        # Reset stats on start
        self._stats = {
            "packets_generated": 0,
            "bytes_generated": 0,
            "errors_simulated": 0
        }

        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
        logger.info(f"Simulation started with config: {config.model_dump()}")

    def stop(self):
        if self._config.is_running:
            self._stop_event.set()
            if self._thread:
                self._thread.join(timeout=2)
            self._config.is_running = False
            logger.info("Simulation stopped.")

    def get_status(self):
        return {
            "is_running": self._config.is_running,
            "config": self._config,
            "stats": self._stats
        }

    def _run(self):
        while not self._stop_event.is_set():
            try:
                # 1. Determine delay based on volume
                delay = 1.0
                if self._config.volume == "low":
                    delay = random.uniform(0.5, 1.5)
                elif self._config.volume == "medium":
                    delay = random.uniform(0.1, 0.5)
                elif self._config.volume == "high":
                    delay = random.uniform(0.01, 0.1)
                
                # 2. Adjust for pattern
                if self._config.pattern == "bursty":
                    if random.random() < 0.2: # 20% chance of burst
                        delay = delay / 10
                    elif random.random() < 0.1: # 10% chance of pause
                        time.sleep(1)
                        continue
                elif self._config.pattern == "random":
                    delay = delay * random.uniform(0.1, 2.0)

                # 3. Simulate Traffic
                if random.random() < self._config.error_rate:
                    self._stats["errors_simulated"] += 1
                    # Log error or drop packet (just sleep/skip)
                    time.sleep(delay)
                    continue

                self._generate_packet()
                time.sleep(delay)

            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                time.sleep(1)

    def _generate_packet(self):
        # Generate random IPs
        source_ip = f"192.168.1.{random.randint(2, 254)}"
        
        # 80% chance of external destination, 20% internal
        if random.random() < 0.8:
            dest_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        else:
            dest_ip = f"192.168.1.{random.randint(2, 254)}"

        # Ports based on protocol
        protocol = self._config.traffic_type
        port = 80
        if protocol == "HTTP":
            port = random.choice([80, 443, 8080])
            protocol = "TCP" # HTTP is over TCP
        elif protocol == "TCP":
            port = random.randint(1024, 65535)
        elif protocol == "UDP":
            port = random.randint(1024, 65535)

        bytes_transferred = random.randint(self._config.packet_size_range[0], self._config.packet_size_range[1])
        
        # Inject anomalies occasionally (5% chance)
        is_anomalous = False
        if random.random() < 0.05:
            # Generate anomaly
            anomaly_type = random.choice(["high_transfer", "port_scan"])
            if anomaly_type == "high_transfer":
                bytes_transferred = random.randint(100 * 1024 * 1024, 500 * 1024 * 1024)
                is_anomalous = True # Logic in analysis.py will flag it, but we can mark it here too if needed? 
                # Actually analysis.py calculates is_anomalous. 
                # The input schema allows setting is_anomalous, but analysis.py overrides/detects it.
                # Let's set it to False and let analysis detect it, OR set it to True if we want to force it.
                # The current system relies on analysis.py to flag it.
            elif anomaly_type == "port_scan":
                # To simulate port scan, we need multiple requests.
                # This single function call generates one packet.
                # Port scan simulation needs a loop. 
                # For simplicity, we just generate a single random packet here.
                # Real port scan logic requires stateful generation which is complex for this simple loop.
                pass

        # Simulate latency based on config + jitter
        base_latency = self._config.latency
        jitter = random.randint(-5, 5) # +/- 5ms jitter
        simulated_latency = max(0, base_latency + jitter)

        packet_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "source_ip": source_ip,
            "destination_ip": dest_ip,
            "port": port,
            "protocol": protocol,
            "bytes_transferred": bytes_transferred,
            "packet_count": random.randint(1, 100),
            "latency": simulated_latency,
            "is_anomalous": is_anomalous
        }

        # Send to API
        try:
            # We need a token? The API requires authentication?
            # main.py: create_traffic_log depends on get_db. 
            # It DOES NOT depend on current_user in the definition:
            # @app.post("/traffic", response_model=schemas.NetworkTraffic)
            # async def create_traffic_log(traffic: schemas.NetworkTrafficCreate, db: Session = Depends(get_db)):
            # So no auth required for this endpoint based on current main.py code.
            
            requests.post(self.api_url, json=packet_data, timeout=1)
            
            self._stats["packets_generated"] += 1
            self._stats["bytes_generated"] += bytes_transferred
            
        except Exception as e:
            logger.error(f"Failed to send packet: {e}")

# Global instance
simulator = TrafficSimulator()
