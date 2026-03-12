"""
Dynamic Keyword Clustering from Ghost CMS Blog

Generates security-relevant keywords dynamically based on blog content
to keep the monitoring system up-to-date with current threats.
"""

import os
import re
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import threading


@dataclass
class KeywordCluster:
    """A cluster of related security keywords."""
    name: str
    keywords: Set[str]
    source: str  # "ghost", "manual", "ml"
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0


class GhostCMSFetcher:
    """Fetches posts from Ghost CMS to extract keywords."""

    def __init__(self, ghost_url: str = None, ghost_api_key: str = None):
        self.ghost_url = ghost_url or os.getenv("GHOST_URL")
        self.ghost_api_key = ghost_api_key or os.getenv("GHOST_API_KEY")

    def get_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent posts from Ghost CMS."""
        if not self.ghost_url:
            return []

        try:
            import httpx
            # Ghost API v3 uses Content API
            # API key format: {id}:{api_key}
            if self.ghost_api_key:
                # Basic auth for Ghost Admin API
                import base64
                auth = base64.b64encode(f"{self.ghost_api_key}:".encode()).decode()

            # Try to fetch from Ghost site
            url = f"{self.ghost_url.rstrip('/')}/ghost/api/content/posts/?limit={limit}&include=tags"

            # For public Ghost sites, try without auth first
            try:
                response = httpx.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("posts", [])
            except:
                pass

            # Try with API key
            if self.ghost_api_key:
                headers = {"Authorization": f"Ghost {auth}"}
                response = httpx.get(url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("posts", [])

        except Exception as e:
            print(f"Ghost CMS fetch error: {e}")

        return []

    def extract_keywords_from_posts(self, posts: List[Dict[str, Any]]) -> List[str]:
        """Extract security-relevant keywords from blog posts."""
        keywords = []

        # Security-related patterns
        security_patterns = [
            r'\b(phishing|malware|ransomware|spyware|trojan|worm|virus)\b',
            r'\b(breach|leak|exploit|vulnerability|CVE|zero-day)\b',
            r'\b(injection|SQLi|XSS|csrf|ssrf|buffer overflow)\b',
            r'\b(ddos|botnet|ddos|amplification)\b',
            r'\b(cryptocurrency|crypto|wallet|mining|monero)\b',
            r'\b(credential|password|token|authentication|authorization)\b',
            r'\b(backdoor|rootkit|keylogger|stealer)\b',
            r'\b(mitigation|prevention|detection|response)\b',
            r'\b(security|cyber|threat|attack|defense)\b',
            r'\b(apt|advanced persistent threat|insider)\b',
        ]

        combined_pattern = '|'.join(security_patterns)

        for post in posts:
            # Get title and plaintext content
            title = post.get("title", "")
            html = post.get("html", "")
            plain_text = post.get("plaintext", "")

            # Also get tags
            tags = post.get("tags", [])
            for tag in tags:
                if isinstance(tag, dict):
                    keywords.append(tag.get("name", "").lower())

            # Extract from title
            if title:
                matches = re.findall(combined_pattern, title, re.IGNORECASE)
                keywords.extend([m.lower() for m in matches])

            # Extract from content
            content = html + " " + plain_text
            if content:
                matches = re.findall(combined_pattern, content, re.IGNORECASE)
                keywords.extend([m.lower() for m in matches])

        return keywords


class DynamicKeywordCluster:
    """Dynamically clusters and manages security keywords."""

    def __init__(self):
        self.clusters: Dict[str, KeywordCluster] = {}
        self.lock = threading.RLock()
        self._initialize_default_clusters()

    def _initialize_default_clusters(self):
        """Initialize default security keyword clusters."""
        default_clusters = {
            "malware": {
                "ransomware", "malware", "spyware", "trojan", "worm", "virus",
                "backdoor", "rootkit", "keylogger", "stealer", "adware", "cryptominer"
            },
            "phishing": {
                "phishing", "spear phishing", "whaling", "vishing", "smishing",
                "email spoofing", "domain spoofing", "credential harvesting"
            },
            "web_attacks": {
                "sql injection", "sqli", "xss", "cross-site scripting", "csrf",
                "ssrf", "path traversal", "lfi", "rfi", "deserialization"
            },
            "network_attacks": {
                "ddos", "dos", "syn flood", "ping of death", "mitm", "arp spoofing",
                "dns poisoning", "port scanning", "reconnaissance"
            },
            "privilege_escalation": {
                "privilege escalation", "vertical escalation", "horizontal escalation",
                "root", "sudo", "passwd", "shadow", "etc/passwd"
            },
            "data_exfiltration": {
                "data exfiltration", "data breach", "data leak", "upload", "download",
                "file transfer", "external ip", "c2", "command and control"
            },
            "insider_threat": {
                "insider", "malicious insider", "privilege abuse", "data theft",
                "sabotage", "fraud", "unauthorized access"
            },
            "emerging_threats": {
                "ai attack", "deepfake", "prompt injection", "llm jailbreak",
                "supply chain", "log4shell", "spring4shell", "zero-day"
            }
        }

        for name, keywords in default_clusters.items():
            self.clusters[name] = KeywordCluster(
                name=name,
                keywords=keywords,
                source="manual"
            )

    def update_from_ghost(self, ghost_url: str = None, ghost_api_key: str = None):
        """Update keywords from Ghost CMS blog."""
        fetcher = GhostCMSFetcher(ghost_url, ghost_api_key)
        posts = fetcher.get_posts(limit=20)

        if not posts:
            return False

        keywords = fetcher.extract_keywords_from_posts(posts)

        if keywords:
            with self.lock:
                # Add to emerging_threats cluster
                if "emerging_threats" not in self.clusters:
                    self.clusters["emerging_threats"] = KeywordCluster(
                        name="emerging_threats",
                        keywords=set(),
                        source="ghost"
                    )

                self.clusters["emerging_threats"].keywords.update(keywords)
                self.clusters["emerging_threats"].last_updated = datetime.now().isoformat()
                self.clusters["emerging_threats"].source = "ghost"

        return True

    def get_all_keywords(self) -> List[str]:
        """Get all keywords from all clusters."""
        with self.lock:
            all_keywords = set()
            for cluster in self.clusters.values():
                all_keywords.update(cluster.keywords)
            return sorted(list(all_keywords))

    def get_keywords_for_matching(self) -> Dict[str, Set[str]]:
        """Get keywords formatted for log matching."""
        with self.lock:
            return {name: cluster.keywords for name, cluster in self.clusters.items()}

    def add_cluster(self, name: str, keywords: List[str], source: str = "manual"):
        """Add a new keyword cluster."""
        with self.lock:
            self.clusters[name] = KeywordCluster(
                name=name,
                keywords=set(kw.lower() for kw in keywords),
                source=source
            )

    def get_cluster(self, name: str) -> Optional[KeywordCluster]:
        """Get a specific cluster."""
        with self.lock:
            return self.clusters.get(name)

    def match_keywords(self, text: str) -> Dict[str, List[str]]:
        """Match text against all clusters, return matched clusters and keywords."""
        text_lower = text.lower()
        matches = {}

        with self.lock:
            for name, cluster in self.clusters.items():
                matched = [kw for kw in cluster.keywords if kw in text_lower]
                if matched:
                    matches[name] = matched

        return matches


# Global instance
keyword_cluster = DynamicKeywordCluster()


def get_dynamic_keywords() -> List[str]:
    """Get all dynamic keywords."""
    return keyword_cluster.get_all_keywords()


def match_text_keywords(text: str) -> Dict[str, List[str]]:
    """Match text against dynamic keyword clusters."""
    return keyword_cluster.match_keywords(text)


def update_keywords_from_ghost(ghost_url: str = None, ghost_api_key: str = None):
    """Update keywords from Ghost CMS."""
    return keyword_cluster.update_from_ghost(ghost_url, ghost_api_key)


def get_matching_clusters() -> Dict[str, Set[str]]:
    """Get all clusters for matching."""
    return keyword_cluster.get_keywords_for_matching()
