function truncate(str, max) {
  if (!str) return "";
  if (str.length <= max) return str;
  return str.slice(0, max - 1).trimEnd() + "…";
}

function formatTimeAgo(isoString) {
  if (!isoString) return "Never";
  
  const now = new Date();
  const past = new Date(isoString);
  const diffMs = now - past;
  
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  // For older dates, show the actual date
  return past.toLocaleDateString();
}

function updateLegendHighlighting(events) {
  // Clear existing highlighting
  document.querySelectorAll('.legend-item').forEach(item => {
    item.classList.remove('has-incident');
  });
  
  // Track providers with ongoing incidents
  const providersWithIncidents = new Set();
  
  for (const ev of events) {
    const description = (ev.description || "").toLowerCase();
    if (!description.includes("resolved") && !description.includes("completed") && !description.includes("scheduled")) {
      providersWithIncidents.add(ev.source.toLowerCase().replace(' ', '-'));
    }
  }
  
  // Apply highlighting to providers with ongoing incidents
  providersWithIncidents.forEach(provider => {
    const legendItem = document.getElementById(`legend-${provider}`);
    if (legendItem) {
      legendItem.classList.add('has-incident');
    }
  });
}

function renderTimeline(events) {
  const timelineEl = document.getElementById("timeline");
  timelineEl.innerHTML = "";
  
  // Apply filters
  let filteredEvents = events;
  
  // Apply provider filter if active
  if (activeProviderFilter) {
    filteredEvents = filteredEvents.filter(event => {
      const eventProvider = event.source.toLowerCase().replace(' ', '-');
      return eventProvider === activeProviderFilter;
    });
  }
  
  // Apply ongoing filter if active
  if (ongoingOnlyFilter) {
    filteredEvents = filteredEvents.filter(event => isOngoingIncident(event));
  }
  
  // Update legend highlighting based on current events
  updateLegendHighlighting(events);

  if (!filteredEvents.length) {
    const msg = document.createElement("div");
    msg.className = "empty-message";
    
    if (activeProviderFilter && ongoingOnlyFilter) {
      msg.textContent = "No ongoing incidents found for the selected provider.";
    } else if (activeProviderFilter) {
      msg.textContent = "No incidents found for the selected provider.";
    } else if (ongoingOnlyFilter) {
      msg.textContent = "No ongoing incidents found.";
    } else {
      msg.textContent = "No incidents or maintenance events in the last 24 hours.";
    }
    
    timelineEl.appendChild(msg);
    return;
  }

  const fragment = document.createDocumentFragment();

  for (const ev of filteredEvents) {
    const item = document.createElement("div");
    item.className = "timeline-item";

    const dot = document.createElement("div");
    dot.className = "timeline-dot";
    dot.style.borderColor = ev.color || "#555555";

    const card = document.createElement("div");
    card.className = "timeline-card";
    
    // Check if incident is resolved
    const description = (ev.description || "").toLowerCase();
    if (description.includes("resolved") || description.includes("completed") || description.includes("scheduled")) {
      card.classList.add("resolved");
    } else {
      card.classList.add("unresolved");
    }

    const meta = document.createElement("div");
    meta.className = "timeline-meta";

    const timeSpan = document.createElement("span");
    timeSpan.className = "timeline-time";
    const d = new Date(ev.pub_date);
    timeSpan.textContent = d.toLocaleString();

    const srcSpan = document.createElement("span");
    srcSpan.className = "timeline-source";
    srcSpan.style.color = ev.color || "#555555";
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

    const descDiv = document.createElement("div");
	descDiv.className = "timeline-description";
	// ev.description is HTML from the RSS; render it as HTML
	descDiv.innerHTML = ev.description || "";

	card.appendChild(meta);
	card.appendChild(titleDiv);
	if (ev.description) {
		card.appendChild(descDiv);
	}

    item.appendChild(dot);
    item.appendChild(card);

    fragment.appendChild(item);
  }

  timelineEl.appendChild(fragment);
}

async function loadLastUpdate() {
  try {
    const res = await fetch("/api/last-update");
    if (res.ok) {
      const data = await res.json();
      const lastUpdateEl = document.getElementById("last-update");
      lastUpdateEl.textContent = `Last update: ${formatTimeAgo(data.last_update)}`;
    }
  } catch (e) {
    console.error("Failed to load last update time:", e);
    document.getElementById("last-update").textContent = "Last update: Unknown";
  }
}

async function loadEvents() {
  const timelineEl = document.getElementById("timeline");
  timelineEl.innerHTML = "<div class='empty-message'>Loading…</div>";

  try {
    const res = await fetch("/api/events");
    if (!res.ok) {
      throw new Error("HTTP " + res.status);
    }
    const data = await res.json();
    allEvents = data; // Store for filtering
    renderTimeline(data);
    loadLastUpdate();
  } catch (e) {
    console.error(e);
    timelineEl.innerHTML =
      "<div class='error-message'>Error loading events: " + e.message + "</div>";
  }
}

async function manualRefresh() {
  const btn = document.getElementById("refresh-btn");
  btn.disabled = true;
  btn.textContent = "Refreshing…";

  try {
    const res = await fetch("/refresh", { method: "POST" });
    if (!res.ok) {
      throw new Error("HTTP " + res.status);
    }
    await loadEvents();
  } catch (e) {
    alert("Refresh failed: " + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Refresh now";
  }
}

// Filter state management
let activeProviderFilter = null;
let ongoingOnlyFilter = false;
let allEvents = [];

function isOngoingIncident(event) {
  const description = (event.description || "").toLowerCase();
  return !description.includes("resolved") && 
         !description.includes("completed") && 
         !description.includes("scheduled");
}

function setProviderFilter(provider) {
  activeProviderFilter = provider;
  renderTimeline(allEvents);
  updateFilterStates();
}

function clearProviderFilter() {
  activeProviderFilter = null;
  renderTimeline(allEvents);
  updateFilterStates();
}

function toggleOngoingFilter() {
  ongoingOnlyFilter = !ongoingOnlyFilter;
  renderTimeline(allEvents);
  updateFilterStates();
}

function clearAllFilters() {
  activeProviderFilter = null;
  ongoingOnlyFilter = false;
  renderTimeline(allEvents);
  updateFilterStates();
}

function updateFilterStates() {
  // Update legend states
  document.querySelectorAll('.legend-item').forEach(item => {
    item.classList.remove('active', 'filtered');
    
    if (activeProviderFilter) {
      const provider = item.id.replace('legend-', '');
      if (provider === activeProviderFilter) {
        item.classList.add('active');
      } else {
        item.classList.add('filtered');
      }
    }
  });
  
  // Update ongoing filter button
  const ongoingBtn = document.getElementById('ongoing-filter-btn');
  if (ongoingOnlyFilter) {
    ongoingBtn.classList.add('active');
  } else {
    ongoingBtn.classList.remove('active');
  }
  
  // Show/hide the "Show All" button
  const showAllBtn = document.getElementById('show-all-btn');
  if (activeProviderFilter || ongoingOnlyFilter) {
    showAllBtn.style.display = 'inline-block';
  } else {
    showAllBtn.style.display = 'none';
  }
}

function setupLegendClickHandlers() {
  document.querySelectorAll('.legend-item').forEach(item => {
    item.addEventListener('click', function() {
      const provider = this.id.replace('legend-', '');
      
      if (activeProviderFilter === provider) {
        // Click on already active filter - clear it
        clearProviderFilter();
      } else {
        // Set new filter
        setProviderFilter(provider);
      }
    });
  });
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById("refresh-btn").addEventListener("click", manualRefresh);
  document.getElementById("show-all-btn").addEventListener("click", clearAllFilters);
  document.getElementById("ongoing-filter-btn").addEventListener("click", toggleOngoingFilter);
  
  // Setup legend click handlers
  setupLegendClickHandlers();
  
  // Initial load
  loadEvents();
  
  // Update the "time ago" display every minute
  setInterval(loadLastUpdate, 60000);
});