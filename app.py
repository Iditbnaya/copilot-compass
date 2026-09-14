from __future__ import annotations

import html
import re
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from flask import Flask, jsonify, render_template


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

SOURCES = (
    {
        "name": "GitHub Changelog",
        "url": "https://github.blog/changelog/label/copilot/feed/",
        "kind": "Changelog",
    },
    {
        "name": "GitHub Blog",
        "url": "https://github.blog/ai-and-ml/github-copilot/feed/",
        "kind": "Blog",
    },
)

FEATURES = (
    {
        "title": "Code completion",
        "description": "Get inline suggestions for functions, tests, repetitive code, and documentation while you type.",
        "category": "Build",
        "icon": "spark",
        "url": "https://docs.github.com/en/copilot/get-started/features",
    },
    {
        "title": "Copilot Chat",
        "description": "Ask questions, explain unfamiliar code, debug failures, and explore implementation options in natural language.",
        "category": "Understand",
        "icon": "chat",
        "url": "https://docs.github.com/en/copilot/get-started/features",
    },
    {
        "title": "Agent mode",
        "description": "Delegate multi-step coding work that can inspect a project, edit files, and iterate on the result.",
        "category": "Automate",
        "icon": "agent",
        "url": "https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent",
    },
    {
        "title": "Copilot coding agent",
        "description": "Assign development tasks from GitHub and let Copilot create a pull request for human review.",
        "category": "Collaborate",
        "icon": "branch",
        "url": "https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent",
    },
    {
        "title": "Pull request assistance",
        "description": "Draft descriptions, summarize changes, and support code review directly in the GitHub workflow.",
        "category": "Review",
        "icon": "review",
        "url": "https://docs.github.com/en/copilot/get-started/features",
    },
    {
        "title": "Copilot CLI",
        "description": "Use Copilot from the terminal to understand repositories, edit code, and complete development tasks.",
        "category": "Build",
        "icon": "terminal",
        "url": "https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli",
    },
    {
        "title": "Custom instructions",
        "description": "Give Copilot repository-specific context, conventions, and guidance for more relevant responses.",
        "category": "Customize",
        "icon": "sliders",
        "url": "https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot",
    },
    {
        "title": "Extensions and MCP",
        "description": "Connect Copilot to external tools and context sources to support specialized workflows.",
        "category": "Extend",
        "icon": "plug",
        "url": "https://docs.github.com/en/copilot/customizing-copilot/extending-copilot-chat-with-mcp",
    },
)

BEST_PRACTICES = (
    {
        "number": "01",
        "title": "Start with a clear goal",
        "text": "Describe the outcome, relevant constraints, and what a successful answer should contain.",
    },
    {
        "number": "02",
        "title": "Provide useful context",
        "text": "Open relevant files, name the framework, and include examples or existing project conventions.",
    },
    {
        "number": "03",
        "title": "Break work into steps",
        "text": "Ask for focused changes and verify each meaningful stage instead of sending one oversized prompt.",
    },
    {
        "number": "04",
        "title": "Review every result",
        "text": "Treat suggestions as a draft. Check correctness, security, licensing, tests, and maintainability.",
    },
    {
        "number": "05",
        "title": "Keep humans accountable",
        "text": "Use Copilot to accelerate decisions, not replace engineering judgment or required approvals.",
    },
    {
        "number": "06",
        "title": "Protect sensitive data",
        "text": "Do not place secrets or confidential information in prompts, source files, or generated examples.",
    },
)

COST_PRACTICES = (
    {
        "number": "01",
        "title": "Use automatic model selection",
        "text": "Let Copilot route routine work to an efficient model instead of manually choosing a costly reasoning model for every task.",
        "saving": "Lower model cost",
        "url": "https://docs.github.com/en/copilot/tutorials/optimize-ai-usage",
    },
    {
        "number": "02",
        "title": "Match the model to the task",
        "text": "Use lighter models for explanations, small edits, and boilerplate. Reserve advanced reasoning models for genuinely complex problems.",
        "saving": "Fewer AI credits",
        "url": "https://docs.github.com/en/copilot/tutorials/optimize-ai-usage",
    },
    {
        "number": "03",
        "title": "Keep prompts and context focused",
        "text": "Share only relevant files, requirements, and examples. Smaller context reduces token usage and helps Copilot reach the answer faster.",
        "saving": "Less token usage",
        "url": "https://docs.github.com/en/copilot/tutorials/optimize-ai-usage",
    },
    {
        "number": "04",
        "title": "Prefer included coding assistance",
        "text": "Use code completions and next edit suggestions for everyday coding when they fit; these features do not consume GitHub AI Credits.",
        "saving": "Included usage",
        "url": "https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/",
    },
    {
        "number": "05",
        "title": "Set budgets before overages",
        "text": "Create enterprise, organization, cost-center, and user budgets so extra usage cannot become an unexpected bill.",
        "saving": "Predictable spend",
        "url": "https://docs.github.com/en/copilot/concepts/billing/budgets-for-usage-based-billing",
    },
    {
        "number": "06",
        "title": "Review usage and licenses monthly",
        "text": "Track usage by user and feature, investigate unusual consumption, and reassign seats that are inactive or delivering little value.",
        "saving": "Remove waste",
        "url": "https://docs.github.com/en/copilot/how-tos/manage-and-track-spending/manage-company-spending",
    },
)

_cache_lock = threading.Lock()
_cache = {"items": [], "updated_at": None, "expires_at": 0.0, "errors": []}
CACHE_SECONDS = 15 * 60
USER_AGENT = "Copilot-Compass/1.0 (+local educational app)"


@app.after_request
def disable_local_browser_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def _text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return child.text.strip() if child is not None and child.text else ""


def _clean_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _iso_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            return ""


def _fetch_feed(source: dict[str, str]) -> list[dict[str, str]]:
    request = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=10) as response:
        root = ET.fromstring(response.read())

    entries = root.findall(".//item")
    if not entries:
        atom = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//atom:entry", atom)

    items = []
    for entry in entries:
        title = _text(entry, "title") or _text(entry, "{http://www.w3.org/2005/Atom}title")
        description = (
            _text(entry, "description")
            or _text(entry, "{http://purl.org/rss/1.0/modules/content/}encoded")
            or _text(entry, "{http://www.w3.org/2005/Atom}summary")
        )
        link = _text(entry, "link")
        if not link:
            link_node = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        published = (
            _text(entry, "pubDate")
            or _text(entry, "{http://www.w3.org/2005/Atom}published")
            or _text(entry, "{http://www.w3.org/2005/Atom}updated")
        )
        searchable = f"{title} {_clean_markup(description)}".lower()
        if "copilot" not in searchable:
            continue
        items.append(
            {
                "title": title,
                "summary": _clean_markup(description)[:280],
                "url": link,
                "published_at": _iso_date(published),
                "source": source["name"],
                "kind": source["kind"],
            }
        )
    return items


def get_updates(force: bool = False) -> dict:
    now = time.time()
    with _cache_lock:
        if not force and _cache["items"] and now < _cache["expires_at"]:
            return dict(_cache)

        items = []
        errors = []
        for source in SOURCES:
            try:
                items.extend(_fetch_feed(source))
            except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError) as exc:
                errors.append(f'{source["name"]}: {type(exc).__name__}')

        unique = {}
        for item in items:
            unique[item["url"] or item["title"]] = item
        items = sorted(
            unique.values(),
            key=lambda item: item["published_at"] or "",
            reverse=True,
        )[:18]

        if items:
            _cache["items"] = items
            _cache["updated_at"] = datetime.now(timezone.utc).isoformat()
        _cache["errors"] = errors
        _cache["expires_at"] = now + CACHE_SECONDS
        return dict(_cache)


@app.get("/")
def index():
    return render_template(
        "index.html",
        features=FEATURES,
        best_practices=BEST_PRACTICES,
        cost_practices=COST_PRACTICES,
        updates_endpoint="/api/updates",
    )


@app.get("/api/updates")
def updates():
    data = get_updates()
    return jsonify(
        {
            "items": data["items"],
            "updated_at": data["updated_at"],
            "stale": bool(data["errors"]),
            "source_errors": data["errors"],
        }
    )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
