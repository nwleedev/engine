import fcntl
import json
import os
import subprocess
from pathlib import Path

SKILL_MD_PATH = Path(__file__).parent.parent / "skills" / "domain-professor" / "SKILL.md"


def find_project_root(cwd: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    path = Path(cwd)
    for candidate in [path] + list(path.parents):
        if (candidate / ".claude").is_dir():
            return str(candidate)
    return cwd


def read_skill_content() -> str:
    try:
        return SKILL_MD_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def call_claude(prompt: str) -> str:
    env = {**os.environ, "CLAUDE_WRITING_CONTEXT": "1"}
    try:
        r = subprocess.run(
            ["claude", "-p", "--no-session-persistence", "--output-format", "json"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if r.returncode != 0:
            return ""
        data = json.loads(r.stdout)
        return data.get("result", "")
    except Exception:
        return ""


def get_existing_concepts(domain_dir: Path) -> list[str]:
    return [p.stem for p in domain_dir.rglob("*.md") if p.name != "INDEX.md"]


def ensure_index(domain_dir: Path, domain: str) -> None:
    index_path = domain_dir / "INDEX.md"
    if index_path.exists():
        return
    index_path.write_text(
        f"# {domain.capitalize()} Textbook\n\n"
        f"## Overview\n- [Getting Started](./01-overview/what-is-{domain}.md)\n\n"
        f"## Core Concepts\n\n## Advanced\n",
        encoding="utf-8",
    )


def update_index(domain_dir: Path, rel_path: str, concept_name: str, stage: str) -> None:
    index_path = domain_dir / "INDEX.md"
    stage_heading = {
        "01-overview": "## Overview",
        "02-core-concepts": "## Core Concepts",
        "03-advanced": "## Advanced",
    }.get(stage, "## Core Concepts")
    link = f"- [{concept_name}](./{rel_path})\n"
    if not index_path.exists():
        index_path.write_text("", encoding="utf-8")
    with open(index_path, "r+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            content = f.read()
            if link.strip() in content:
                return
            if stage_heading in content:
                content = content.replace(stage_heading + "\n", stage_heading + "\n" + link)
            else:
                content += f"\n{stage_heading}\n{link}"
            f.seek(0)
            f.write(content)
            f.truncate()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def generate_file(
    domain: str, stage: str, concept: str, domain_dir: Path, skill_content: str
) -> bool:
    stage_dir = domain_dir / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    slug = concept.lower().replace(" ", "-")
    file_path = stage_dir / f"{slug}.md"
    if file_path.exists():
        return False
    prereq = ""
    if stage == "02-core-concepts":
        prereq = f"prerequisites: [01-overview/what-is-{domain}.md]"
    elif stage == "03-advanced":
        prereq = f"prerequisites: [02-core-concepts/{slug}.md]"
    prompt = (
        f"You are a domain teaching expert. Follow these educational principles:\n\n"
        f"{skill_content}\n\n"
        f'Generate a textbook markdown file for the concept "{concept}" in the domain "{domain}".\n\n'
        f"Output ONLY the markdown content (no explanation), following this exact template:\n\n"
        f"---\nstage: {stage}\n{prereq}\nrelated: []\n---\n\n"
        f"# {concept}\n\n[← 목차로](../INDEX.md)\n\n"
        f"## 한 줄 설명\n\n## 핵심 개념\n\n## 실제 예시\n\n## 연관 개념\n"
    )
    content = call_claude(prompt)
    if not content:
        return False
    file_path.write_text(content.strip() + "\n", encoding="utf-8")
    rel_path = str(file_path.relative_to(domain_dir))
    update_index(domain_dir, rel_path, concept, stage)
    return True


def generate_overview(domain: str, project_root: str, skill_content: str) -> None:
    domain_dir = Path(project_root) / ".claude" / "textbooks" / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    ensure_index(domain_dir, domain)
    generate_file(domain, "01-overview", f"what-is-{domain}", domain_dir, skill_content)


def generate_for_domains(domains: list[str], project_root: str) -> None:
    skill_content = read_skill_content()
    for domain in domains:
        domain_dir = Path(project_root) / ".claude" / "textbooks" / domain
        if not domain_dir.exists():
            generate_overview(domain, project_root, skill_content)
