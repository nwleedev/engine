import json
import re
import sys
from pathlib import Path

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "kubernetes": ["kubernetes", "kubectl", "k8s", "pod", "pods", "deployment", "namespace", "helm", "ingress", "configmap", "replicaset"],
    "docker": ["docker", "dockerfile", "container", "containers", "compose", "registry"],
    "terraform": ["terraform", "hcl", "provider", "resource", "module", "tfstate"],
    "aws": ["aws", "s3", "ec2", "lambda", "iam", "cloudformation", "dynamodb", "vpc"],
    "finance": ["dcf", "valuation", "equity", "bond", "option", "hedge", "portfolio", "roi", "irr", "ebitda", "wacc"],
    "sql": ["select", "join", "index", "transaction", "migration", "constraint", "schema"],
    "react": ["react", "jsx", "hook", "component", "props", "useeffect", "usestate", "redux"],
    "python": ["asyncio", "decorator", "generator", "comprehension", "virtualenv", "pytest"],
}

THRESHOLD = 3


def extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [c.get("text", "").strip() for c in content
                 if isinstance(c, dict) and c.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def parse_transcript(path: str) -> list[dict]:
    messages = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = entry.get("message")
                if not msg:
                    continue
                text = extract_text(msg.get("content", ""))
                if text:
                    messages.append({
                        "role": msg.get("role", ""),
                        "text": text,
                        "uuid": entry.get("uuid", ""),
                    })
    except (FileNotFoundError, OSError):
        pass
    return messages


def detect_domains(messages: list[dict], threshold: int = THRESHOLD) -> list[str]:
    text = " ".join(m.get("text", "").lower() for m in messages)
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        count = sum(
            len(re.findall(r"\b" + re.escape(kw) + r"\b", text))
            for kw in keywords
        )
        if count >= threshold:
            domains.append(domain)
    return domains


def detect_domains_from_transcript(transcript_path: str, threshold: int = THRESHOLD) -> list[str]:
    messages = parse_transcript(transcript_path)
    return detect_domains(messages, threshold)
