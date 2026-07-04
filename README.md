# Unpaywall MCP Server

An MCP (Model Context Protocol) server for the [Unpaywall](https://unpaywall.org/) API — open-access availability for 120M+ scholarly articles.

Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk).

## Tools

| Tool | Description |
|------|-------------|
| `unpaywall_lookup` | Look up open-access availability by DOI — returns OA status, PDF/landing page URLs, license, all OA locations |
| `unpaywall_search` | Search 120M+ article titles with OA filtering and pagination |
| `unpaywall_export_ris` | Export results as RIS (for Zotero, EndNote, etc.) |
| `unpaywall_export_bibtex` | Export results as BibTeX |

## What you get

- Open-access status and OA type (gold, green, hybrid, bronze)
- Best OA location with direct PDF link
- All OA locations across repositories and publishers
- Journal OA status, ISSN, publisher info
- Author lists, publication dates, DOIs
- License information per location

## Setup

### 1. Get your email ready

Unpaywall requires an email address as your API identifier (no API key needed). See the [Unpaywall API docs](https://unpaywall.org/products/api).

### 2. Install

```bash
cd unpaywall-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Add to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "unpaywall": {
      "command": "/path/to/unpaywall-mcp-server/venv/bin/python",
      "args": ["/path/to/unpaywall-mcp-server/server.py"],
      "env": {
        "UNPAYWALL_EMAIL": "your-email@example.com"
      }
    }
  }
}
```

Or if using Claude Code CLI:

```bash
claude mcp add unpaywall \
  /path/to/unpaywall-mcp-server/venv/bin/python \
  /path/to/unpaywall-mcp-server/server.py \
  -e UNPAYWALL_EMAIL=your-email@example.com
```

## Usage examples

- "Is there an open-access version of DOI 10.1038/nature12373?"
- "Search Unpaywall for open-access papers on CRISPR gene editing"
- "Export these results as RIS for Zotero"
- "Find OA articles about climate change mitigation"

## License

MIT
