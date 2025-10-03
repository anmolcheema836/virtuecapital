import logging
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, List

from .config import config_manager

# Setup logging
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- Pydantic Models for API Validation ---
class StreamAddModel(BaseModel):
    name: str
    url: str
    format: str = "mp3"

class StreamConfigModel(BaseModel):
    name: str
    url: str
    format: str
    enabled: bool

# --- In-memory Status Tracking ---
stream_statuses: Dict[str, Dict[str, Any]] = {}

def update_stream_status(stream_name: str, status: str, last_message: str):
    """Updates the status of a stream for the GUI."""
    if stream_name not in stream_statuses:
        stream_statuses[stream_name] = {}
    stream_statuses[stream_name]['status'] = status
    stream_statuses[stream_name]['last_message'] = last_message
    stream_statuses[stream_name]['last_update'] = datetime.datetime.utcnow().isoformat()

# --- API Endpoints ---
@app.get("/api/streams", response_model=List[StreamConfigModel])
async def get_streams():
    """API endpoint to get the list of configured streams."""
    return config_manager.get_streams()

@app.get("/api/status")
async def get_status():
    """API endpoint to get current statuses of running streams."""
    return stream_statuses

@app.post("/api/streams", status_code=201)
async def add_stream(stream: StreamAddModel):
    """API endpoint to add a new stream."""
    new_stream_dict = {
        "name": stream.name.strip(),
        "url": stream.url.strip(),
        "format": stream.format,
        "enabled": True
    }
    if not new_stream_dict['name'] or not new_stream_dict['url']:
        raise HTTPException(status_code=400, detail="Stream name and URL cannot be empty.")
    
    await config_manager.add_stream(new_stream_dict)
    return {"message": "Stream added successfully. The service will pick it up shortly."}

@app.delete("/api/streams/{stream_name}", status_code=200)
async def remove_stream(stream_name: str):
    """API endpoint to remove a stream."""
    await config_manager.remove_stream(stream_name)
    # Also remove from statuses if it exists
    if stream_name in stream_statuses:
        del stream_statuses[stream_name]
    return {"message": f"Stream '{stream_name}' removed. The service will stop monitoring it shortly."}


# --- HTML Frontend ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})

# You need a 'templates' directory with 'index.html'
# Create templates/index.html with the following content:
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stream Monitor Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .status-badge { font-size: 0.9em; }
        .status-running { background-color: #198754 !important; }
        .status-stopped { background-color: #6c757d !important; }
        .status-error, .status-reconnecting { background-color: #dc3545 !important; }
        .status-connecting { background-color: #ffc107 !important; color: #000 !important; }
        .log-box {
            font-family: 'Courier New', Courier, monospace;
            background-color: #212529;
            color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 100px;
            overflow-y: auto;
        }
        .card { transition: box-shadow .3s; }
        .card:hover { box-shadow: 0 0 15px rgba(0,0,0,0.15); }
    </style>
</head>
<body>
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Audio Stream Monitor</h1>
            <span id="loading-indicator" class="spinner-border text-primary" role="status" style="display: none;"></span>
        </div>

        <!-- Add Stream Form -->
        <div class="card mb-4">
            <div class="card-header">
                Add New Stream
            </div>
            <div class="card-body">
                <form id="add-stream-form">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <input type="text" class="form-control" id="stream-name" placeholder="Stream Name (e.g., LBC-News)" required>
                        </div>
                        <div class="col-md-6">
                            <input type="url" class="form-control" id="stream-url" placeholder="Stream URL (http://...)" required>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">Add Stream</button>
                        </div>
                    </div>
                </form>
                 <div id="form-message" class="mt-2"></div>
            </div>
        </div>
        
        <!-- Streams List -->
        <div id="streams-list" class="row g-4">
            <!-- Stream cards will be injected here -->
        </div>
    </div>

    <script>
        const streamsList = document.getElementById('streams-list');
        const addStreamForm = document.getElementById('add-stream-form');
        const formMessage = document.getElementById('form-message');
        const loadingIndicator = document.getElementById('loading-indicator');

        // --- Main Function to Render Streams ---
        async function renderStreams() {
            try {
                const [streamsResponse, statusResponse] = await Promise.all([
                    fetch('/api/streams'),
                    fetch('/api/status')
                ]);
                const configuredStreams = await streamsResponse.json();
                const activeStatuses = await statusResponse.json();

                streamsList.innerHTML = ''; // Clear current list

                if (configuredStreams.length === 0) {
                    streamsList.innerHTML = '<p class="text-muted">No streams configured. Add one using the form above.</p>';
                    return;
                }

                configuredStreams.forEach(stream => {
                    const statusData = activeStatuses[stream.name] || { status: 'Stopped', last_message: 'Not currently monitored by the service.' };
                    const statusClass = `status-${statusData.status.toLowerCase().replace(/\\s/g, '')}`;
                    
                    const card = document.createElement('div');
                    card.className = 'col-12';
                    card.innerHTML = `
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <h5 class="card-title">${stream.name}</h5>
                                        <h6 class="card-subtitle mb-2 text-muted">${stream.url}</h6>
                                        <span class="badge status-badge ${statusClass}">${statusData.status}</span>
                                    </div>
                                    <button class="btn btn-sm btn-outline-danger remove-btn" data-name="${stream.name}">Remove</button>
                                </div>
                                <hr>
                                <p class="mb-1"><strong>Last Message:</strong></p>
                                <div class="log-box">${statusData.last_message || 'N/A'}</div>
                            </div>
                        </div>
                    `;
                    streamsList.appendChild(card);
                });

            } catch (error) {
                console.error('Failed to fetch data:', error);
                streamsList.innerHTML = '<div class="alert alert-danger">Failed to load stream data. Is the server running?</div>';
            }
        }

        // --- Event Handlers ---
        addStreamForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            loadingIndicator.style.display = 'block';
            formMessage.textContent = '';

            const name = document.getElementById('stream-name').value;
            const url = document.getElementById('stream-url').value;

            try {
                const response = await fetch('/api/streams', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, url, format: 'mp3' })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    formMessage.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
                    addStreamForm.reset();
                    await renderStreams(); // Refresh list immediately
                } else {
                    formMessage.innerHTML = `<div class="alert alert-danger">${result.detail || 'An error occurred.'}</div>`;
                }
            } catch (error) {
                formMessage.innerHTML = `<div class="alert alert-danger">Request failed: ${error}</div>`;
            } finally {
                loadingIndicator.style.display = 'none';
            }
        });

        streamsList.addEventListener('click', async (e) => {
            if (e.target.classList.contains('remove-btn')) {
                const streamName = e.target.getAttribute('data-name');
                if (confirm(`Are you sure you want to remove the stream "${streamName}"?`)) {
                    loadingIndicator.style.display = 'block';
                    try {
                        const response = await fetch(`/api/streams/${streamName}`, { method: 'DELETE' });
                        if (response.ok) {
                            await renderStreams(); // Refresh list
                        } else {
                            alert('Failed to remove stream.');
                        }
                    } catch (error) {
                        alert(`Error: ${error}`);
                    } finally {
                        loadingIndicator.style.display = 'none';
                    }
                }
            }
        });

        // --- Initial Load and Periodic Refresh ---
        window.onload = renderStreams;
        setInterval(renderStreams, 5000); // Refresh every 5 seconds
    </script>
</body>
</html>
"""

import os
if not os.path.exists("templates"):
    os.makedirs("templates")
with open("templates/index.html", "w") as f:
    f.write(html_content)