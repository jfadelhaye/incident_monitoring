from flask import Flask, request, Response
import requests

app = Flask(__name__)


INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Status Timeline - Last 24h</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      --bg: #f5f5f5;
      --card-bg: #ffffff;
      --text-main: #222222;
      --text-muted: #555555;
      --border: #dddddd;
      --github: #24292e;
      --docker: #0db7ed;
      --cloudflare: #f38020;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                   sans-serif;
      background: var(--bg);
      color: var(--text-main);
      padding: 1.5rem;
    }

    h1 {
      font-size: 1.4rem;
      margin-bottom: 0.5rem;
    }

    #status-summary {
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }

    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 1.2rem;
    }

    .legend-item {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }

    #timeline-container {
      max-width: 800px;
      margin: 0.5rem auto 0;
      position: relative;
    }

    #timeline {
      border-left: 2px solid var(--border);
      padding-left: 1.5rem;
      position: relative;
    }

    .timeline-item {
      position: relative;
      margin-bottom: 1rem;
    }

    .timeline-dot {
      position: absolute;
      left: -7px;
      top: 0.6rem;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--card-bg);
      border: 3px solid var(--border);
    }

    .timeline-card {
      background: var(--card-bg);
      border-radius: 6px;
      padding: 0.75rem 0.9rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }

    .timeline-meta {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 0.4rem;
      font-size: 0.8rem;
      margin-bottom: 0.35rem;
      color: var(--text-muted);
    }

    .timeline-source {
      font-weight: 600;
    }

    .timeline-title {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 0.35rem;
    }

    .timeline-title a {
      color: inherit;
      text-decoration: none;
      border-bottom: 1px solid transparent;
    }

    .timeline-title a:hover {
      border-bottom-color: currentColor;
    }

    .timeline-description {
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.4;
      white-space: pre-line;
    }

    .empty-message,
    .error-message {
      padding: 0.6rem 0.8rem;
      font-size: 0.9rem;
      color: var(--text-muted);
    }

    .error-message {
      color: #b00020;
    }

    @media (max-width: 600px) {
      body {
        padding: 1rem;
      }
    }
  </style>
</head>
<body>
  <h1>Service Status Timeline (Last 24 hours)</h1>
  <div id="status-summary">
    Aggregating incidents & maintenance from GitHub, Docker, and Cloudflare
    status pages (RSS).
  </div>

  <div class="legend">
    <span class="legend-item">
      <span class="legend-dot" style="background: var(--github);"></span>GitHub
    </span>
    <span class="legend-item">
      <span class="legend-dot" style="background: var(--docker);"></span>Docker
    </span>
    <span class="legend-item">
      <span class="legend-dot" style="background: var(--cloudflare);"></span>Cloudflare
    </span>
  </div>

  <div id="timeline-container">
    <div id="timeline"></div>
  </div>

  <script>
    // --- CONFIG -------------------------------------------------------------

    const FEEDS = [
      {
        name: "GitHub",
        url: "https://www.githubstatus.com/history.rss",
        color: "var(--github)",
      },
      {
        name: "Docker",
        url: "https://www.dockerstatus.com/pages/533c6539221ae15e3f000031/rss",
        color: "var(--docker)",
      },
      {
        name: "Cloudflare",
        url: "https://www.cloudflarestatus.com/history.rss",
        color: "var(--cloudflare)",
      },
    ];

    // Our own Flask proxy
    const PROXY_BASE = "/proxy?url=";

    // Time window (ms) – last 24h
    const WINDOW_MS = 24 * 60 * 60 * 1000;

    // --- HELPERS -----------------------------------------------------------

    function proxiedUrl(url) {
      return PROXY_BASE + encodeURIComponent(url);
    }

    function parseDateFromItem(item) {
      const fields = ["pubDate", "updated", "published", "dc\\\\:date", "date"];
      for (const name of fields) {
        const el = item.querySelector(name);
        if (el && el.textContent.trim()) {
          const d = new Date(el.textContent.trim());
          if (!isNaN(d.getTime())) return d;
        }
      }
      return null;
    }

    function getText(el) {
      return el ? el.textContent.trim() : "";
    }

    function stripHtml(str) {
      return str.replace(/<[^>]*>/g, "");
    }

    function truncate(str, max) {
      if (str.length <= max) return str;
      return str.slice(0, max - 1).trimEnd() + "…";
    }

    // --- RSS FETCH & PARSE -------------------------------------------------

    async function fetchFeed(feed) {
      const response = await fetch(proxiedUrl(feed.url));
      if (!response.ok) {
        throw new Error("HTTP " + response.status + " for " + feed.name);
      }
      const text = await response.text();

      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(text, "application/xml");

      let items = Array.from(xmlDoc.querySelectorAll("item"));
      if (!items.length) {
        // Atom fallback
        items = Array.from(xmlDoc.querySelectorAll("entry"));
      }

      const events = [];

      for (const item of items) {
        const title = getText(item.querySelector("title")) || "(no title)";
        const linkEl = item.querySelector("link");
        let link = "";
        if (linkEl) {
          link = linkEl.getAttribute("href") || getText(linkEl);
        }

        const descEl =
          item.querySelector("description") ||
          item.querySelector("summary") ||
          item.querySelector("content");
        let description = descEl ? descEl.textContent : "";
        description = stripHtml(description).trim();

        const date = parseDateFromItem(item);
        if (!date) continue; // skip items without valid date

        events.push({
          source: feed.name,
          color: feed.color,
          title,
          link,
          description,
          date,
        });
      }

      return events;
    }

    // --- RENDERING ---------------------------------------------------------

    function renderTimeline(events) {
      const timelineEl = document.getElementById("timeline");
      timelineEl.innerHTML = "";

      if (!events.length) {
        const msg = document.createElement("div");
        msg.className = "empty-message";
        msg.textContent = "No incidents or maintenance events in the last 24 hours.";
        timelineEl.appendChild(msg);
        return;
      }

      const fragment = document.createDocumentFragment();

      for (const ev of events) {
        const item = document.createElement("div");
        item.className = "timeline-item";

        const dot = document.createElement("div");
        dot.className = "timeline-dot";
        dot.style.borderColor = ev.color;

        const card = document.createElement("div");
        card.className = "timeline-card";

        const meta = document.createElement("div");
        meta.className = "timeline-meta";

        const timeSpan = document.createElement("span");
        timeSpan.className = "timeline-time";
        timeSpan.textContent = ev.date.toLocaleString();

        const srcSpan = document.createElement("span");
        srcSpan.className = "timeline-source";
        srcSpan.style.color = ev.color;
        srcSpan.textContent = ev.source;

        meta.appendChild(timeSpan);
        meta.appendChild(srcSpan);

        const titleDiv = document.createElement("div");
        titleDiv.className = "timeline-title";

        if (ev.link) {
          const a = document.createElement("a");
          a.href = ev.link;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.textContent = ev.title;
          titleDiv.appendChild(a);
        } else {
          titleDiv.textContent = ev.title;
        }

        const descP = document.createElement("p");
        descP.className = "timeline-description";
        descP.textContent = truncate(ev.description || "", 280);

        card.appendChild(meta);
        card.appendChild(titleDiv);
        if (ev.description) {
          card.appendChild(descP);
        }

        item.appendChild(dot);
        item.appendChild(card);

        fragment.appendChild(item);
      }

      timelineEl.appendChild(fragment);
    }

    function renderError(error) {
      const timelineEl = document.getElementById("timeline");
      timelineEl.innerHTML = "";
      const msg = document.createElement("div");
      msg.className = "error-message";
      msg.textContent =
        "Error while loading feeds: " + (error && error.message
          ? error.message
          : String(error));
      timelineEl.appendChild(msg);
    }

    // --- MAIN --------------------------------------------------------------

    (async function main() {
      const now = new Date();
      const cutoff = new Date(now.getTime() - WINDOW_MS);
      const cutafter = new Date(now.getTime());

      try {
        const allEventsArrays = await Promise.all(
          FEEDS.map((feed) =>
            fetchFeed(feed).catch((err) => {
              console.error("Failed to fetch feed", feed.name, err);
              return []; // ignore failing feed, keep others
            })
          )
        );

        let events = allEventsArrays.flat();

        // Filter for last 24h
        events = events.filter((ev) => ev.date >= cutoff);
        events = events.filter((ev) => ev.date < cutafter);

        // Sort chronologically (newest at top)
        events.sort((a, b) => b.date - a.date);

        renderTimeline(events);
      } catch (err) {
        console.error(err);
        renderError(err);
      }
    })();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    # Serve the HTML directly from the string to keep everything in one file
    return Response(INDEX_HTML, mimetype="text/html")


@app.route("/proxy")
def proxy():
    """
    Very small server-side proxy to bypass CORS issues.

    Usage: GET /proxy?url=<encoded RSS URL>
    """
    url = request.args.get("url")
    if not url:
        return Response("Missing 'url' parameter", status=400)

    try:
        # You can add small hardening here if you like:
        # - restrict to known domains
        # - check scheme, etc.
        resp = requests.get(url, timeout=10)
    except requests.RequestException as e:
        return Response(f"Error fetching URL: {e}", status=502)

    # Pass through content with permissive CORS
    flask_resp = Response(
        resp.content,
        status=resp.status_code,
        mimetype=resp.headers.get("Content-Type", "application/xml"),
    )
    flask_resp.headers["Access-Control-Allow-Origin"] = "*"
    return flask_resp


if __name__ == "__main__":
    # Simple dev server
    app.run(host="0.0.0.0", port=5000, debug=True)

