#!/usr/bin/env python3
"""
Unpaywall MCP Server for Claude Desktop

Provides Claude Desktop with tools to look up open-access availability
for scholarly articles, search by title, and export citations.

Unpaywall API docs: https://unpaywall.org/products/api
"""

import os
from typing import Optional
from mcp.server.fastmcp import FastMCP
import httpx

# ── Configuration ──────────────────────────────────────────────────────────

EMAIL = os.environ.get("UNPAYWALL_EMAIL", "")
BASE_URL = "https://api.unpaywall.org/v2"

mcp = FastMCP("Unpaywall")


# ── Helpers ────────────────────────────────────────────────────────────────

async def _get(url: str, params: dict = None) -> dict:
    """Make a GET request to the Unpaywall API."""
    p = params or {}
    p["email"] = EMAIL
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=p)
        resp.raise_for_status()
        return resp.json()


def _get_authors(data: dict) -> str:
    """Extract author names from an Unpaywall record."""
    authors = data.get("z_authors") or []
    names = []
    for a in authors:
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{family}, {given}".strip(", ") if family else given
        if name:
            names.append(name)
    return "; ".join(names) if names else "Unknown"


def _format_location(loc: dict) -> str:
    """Format a single OA location."""
    host = loc.get("host_type", "")
    url = loc.get("url_for_pdf") or loc.get("url_for_landing_page") or loc.get("url", "")
    version = loc.get("version", "")
    license_ = loc.get("license", "")
    source = loc.get("evidence", "")

    line = f"  - [{host}]"
    if version:
        line += f" {version}"
    if license_:
        line += f" ({license_})"
    if url:
        line += f"\n    {url}"
    if source:
        line += f"\n    Evidence: {source}"
    return line


def _format_result(i: int, data: dict) -> str:
    """Format a single Unpaywall record as readable text."""
    title = data.get("title", "Untitled")
    authors = _get_authors(data)
    year = data.get("year", "")
    doi = data.get("doi", "")
    journal = data.get("journal_name", "")
    publisher = data.get("publisher", "")
    is_oa = data.get("is_oa", False)
    oa_status = data.get("oa_status", "")

    line = f"{i}. {title}"
    line += f"\n   Authors: {authors}"
    if journal:
        line += f"\n   Journal: {journal}"
    if year:
        line += f"\n   Year: {year}"
    if publisher:
        line += f"\n   Publisher: {publisher}"
    if doi:
        line += f"\n   DOI: https://doi.org/{doi}"
    line += f"\n   Open Access: {'Yes' if is_oa else 'No'}"
    if oa_status:
        line += f" ({oa_status})"

    best = data.get("best_oa_location")
    if best:
        pdf = best.get("url_for_pdf", "")
        landing = best.get("url_for_landing_page", "")
        license_ = best.get("license", "")
        if pdf:
            line += f"\n   PDF: {pdf}"
        elif landing:
            line += f"\n   URL: {landing}"
        if license_:
            line += f"\n   License: {license_}"

    return line


def _format_lookup(data: dict) -> str:
    """Format a full DOI lookup response."""
    title = data.get("title", "Untitled")
    authors = _get_authors(data)
    year = data.get("year", "")
    doi = data.get("doi", "")
    journal = data.get("journal_name", "")
    publisher = data.get("publisher", "")
    is_oa = data.get("is_oa", False)
    oa_status = data.get("oa_status", "")
    genre = data.get("genre", "")
    published_date = data.get("published_date", "")
    journal_is_oa = data.get("journal_is_oa", False)
    journal_issns = data.get("journal_issns", "")

    output = f"Title: {title}\n"
    output += f"Authors: {authors}\n"
    if journal:
        output += f"Journal: {journal}"
        if journal_issns:
            output += f" (ISSN: {journal_issns})"
        output += "\n"
        if journal_is_oa:
            output += "Journal is fully OA: Yes\n"
    if year:
        output += f"Year: {year}\n"
    if published_date:
        output += f"Published: {published_date}\n"
    if genre:
        output += f"Type: {genre}\n"
    if publisher:
        output += f"Publisher: {publisher}\n"
    if doi:
        output += f"DOI: https://doi.org/{doi}\n"

    output += f"\nOpen Access: {'Yes' if is_oa else 'No'}"
    if oa_status:
        output += f" (status: {oa_status})"
    output += "\n"

    # Best OA location
    best = data.get("best_oa_location")
    if best:
        output += f"\nBest OA Location:\n{_format_location(best)}\n"

    # All OA locations
    locations = data.get("oa_locations") or []
    if len(locations) > 1:
        output += f"\nAll OA Locations ({len(locations)}):\n"
        for loc in locations:
            output += f"{_format_location(loc)}\n"

    return output


def _result_to_ris(data: dict) -> str:
    """Convert an Unpaywall record to RIS format."""
    genre = (data.get("genre") or "").lower()
    ris_type = "JOUR" if "journal" in genre else "GEN"
    lines = [f"TY  - {ris_type}"]

    if data.get("title"):
        lines.append(f"TI  - {data['title']}")

    for a in (data.get("z_authors") or []):
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{family}, {given}".strip(", ") if family else given
        if name:
            lines.append(f"AU  - {name}")

    if data.get("journal_name"):
        lines.append(f"JO  - {data['journal_name']}")
    if data.get("year"):
        lines.append(f"PY  - {data['year']}")
    if data.get("doi"):
        lines.append(f"DO  - {data['doi']}")
    if data.get("publisher"):
        lines.append(f"PB  - {data['publisher']}")
    if data.get("journal_issns"):
        lines.append(f"SN  - {data['journal_issns']}")

    best = data.get("best_oa_location") or {}
    url = best.get("url_for_pdf") or best.get("url_for_landing_page") or ""
    if url:
        lines.append(f"UR  - {url}")

    lines.append("ER  - ")
    return "\n".join(lines)


def _result_to_bibtex(data: dict) -> str:
    """Convert an Unpaywall record to BibTeX format."""
    genre = (data.get("genre") or "").lower()
    bib_type = "article" if "journal" in genre else "misc"

    authors_raw = data.get("z_authors") or []
    first_family = "unknown"
    if authors_raw and authors_raw[0].get("family"):
        first_family = authors_raw[0]["family"].replace(" ", "")
    year = data.get("year", "nd")
    key = f"{first_family}{year}"

    author_names = []
    for a in authors_raw:
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{family}, {given}".strip(", ") if family else given
        if name:
            author_names.append(name)

    lines = [f"@{bib_type}{{{key},"]
    if data.get("title"):
        lines.append(f"  title = {{{data['title']}}},")
    if author_names:
        lines.append(f"  author = {{{' and '.join(author_names)}}},")
    if data.get("journal_name"):
        lines.append(f"  journal = {{{data['journal_name']}}},")
    if year != "nd":
        lines.append(f"  year = {{{year}}},")
    if data.get("doi"):
        lines.append(f"  doi = {{{data['doi']}}},")
    if data.get("publisher"):
        lines.append(f"  publisher = {{{data['publisher']}}},")
    lines.append("}")
    return "\n".join(lines)


# ── Store last results for export ─────────────────────────────────────────

_last_results: list = []


# ── Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def unpaywall_lookup(doi: str) -> str:
    """
    Look up open-access availability for a scholarly article by DOI.

    Returns OA status, best OA location (PDF/landing page URL, license),
    all OA locations, journal info, authors, and publication details.

    Args:
        doi: The DOI to look up (e.g. "10.1038/nature12373")
    """
    global _last_results
    try:
        data = await _get(f"{BASE_URL}/{doi}")
        _last_results = [data]
        return _format_lookup(data)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"DOI not found: {doi}"
        return f"Unpaywall API error: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def unpaywall_search(
    query: str,
    is_oa: Optional[bool] = None,
    page: int = 1,
) -> str:
    """
    Search Unpaywall for scholarly articles by title.

    Searches across 120M+ article titles. Supports AND (default),
    quoted phrases, OR, and negation (-term). Returns up to 50 results per page.

    Args:
        query: Search terms for article titles (e.g. "machine learning")
        is_oa: Filter by open-access status (true = OA only, false = closed only, omit for all)
        page: Page number for pagination (50 results per page, default 1)
    """
    global _last_results
    params = {"query": query, "page": page}
    if is_oa is not None:
        params["is_oa"] = str(is_oa).lower()

    try:
        data = await _get(f"{BASE_URL}/search/", params)
        results = data.get("results", [])
        elapsed = data.get("elapsed_seconds", "")

        docs = [r.get("response", {}) for r in results]
        _last_results = docs

        if not docs:
            return f"No results found for: {query}"

        header = f"Unpaywall Search: {len(docs)} results (page {page})"
        if elapsed:
            header += f" in {elapsed:.2f}s"
        header += f"\nQuery: {query}\n"
        header += "=" * 60 + "\n\n"

        formatted = "\n\n".join(
            _format_result(i, doc) for i, doc in enumerate(docs, 1)
        )
        return header + formatted
    except httpx.HTTPStatusError as e:
        return f"Unpaywall API error: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def unpaywall_export_ris() -> str:
    """
    Export the most recent unpaywall_lookup or unpaywall_search results as RIS format.
    Save output as a .ris file and import into Zotero: File -> Import.
    """
    if not _last_results:
        return "No results to export. Run unpaywall_lookup or unpaywall_search first."
    records = [_result_to_ris(doc) for doc in _last_results]
    count = len(records)
    return f"RIS Export ({count} records) — Save as .ris and import into Zotero:\n\n" + "\n\n".join(records)


@mcp.tool()
async def unpaywall_export_bibtex() -> str:
    """
    Export the most recent unpaywall_lookup or unpaywall_search results as BibTeX format.
    """
    if not _last_results:
        return "No results to export. Run unpaywall_lookup or unpaywall_search first."
    records = [_result_to_bibtex(doc) for doc in _last_results]
    count = len(records)
    return f"BibTeX Export ({count} records):\n\n" + "\n\n".join(records)


# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
