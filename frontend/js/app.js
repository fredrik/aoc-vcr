import { Player } from './player.js';
import { GridRenderer } from './renderers/grid.js';
import { PointsRenderer } from './renderers/points.js';

const API_BASE = 'http://localhost:8000';

class App {
    constructor() {
        this.player = null;
        this.currentRun = null;
        this.eventSource = null;

        this.canvas = document.getElementById('vcr-canvas');
        this.gridRenderer = new GridRenderer(this.canvas);
        this.pointsRenderer = new PointsRenderer(this.canvas);

        this.initElements();
        this.initEventListeners();
        this.loadRuns();
    }

    initElements() {
        this.runList = document.getElementById('run-list');
        this.runInfo = document.getElementById('run-info');
        this.seekBar = document.getElementById('seek-bar');
        this.frameCounter = document.getElementById('frame-counter');
        this.speedSelect = document.getElementById('speed-select');
        this.stateData = document.getElementById('state-data');

        this.btnFirst = document.getElementById('btn-first');
        this.btnPrev = document.getElementById('btn-prev');
        this.btnPlay = document.getElementById('btn-play');
        this.btnNext = document.getElementById('btn-next');
        this.btnLast = document.getElementById('btn-last');
    }

    initEventListeners() {
        this.btnFirst.addEventListener('click', () => this.player?.first());
        this.btnPrev.addEventListener('click', () => this.player?.prev());
        this.btnPlay.addEventListener('click', () => this.togglePlay());
        this.btnNext.addEventListener('click', () => this.player?.next());
        this.btnLast.addEventListener('click', () => this.player?.last());

        this.seekBar.addEventListener('input', (e) => {
            this.player?.seek(parseInt(e.target.value));
        });

        this.speedSelect.addEventListener('change', (e) => {
            if (this.player) {
                this.player.setSpeed(parseFloat(e.target.value));
            }
        });

        document.addEventListener('keydown', (e) => {
            if (!this.player) return;
            switch (e.key) {
                case ' ':
                    e.preventDefault();
                    this.togglePlay();
                    break;
                case 'ArrowLeft':
                    this.player.prev();
                    break;
                case 'ArrowRight':
                    this.player.next();
                    break;
                case 'Home':
                    this.player.first();
                    break;
                case 'End':
                    this.player.last();
                    break;
            }
        });
    }

    togglePlay() {
        if (!this.player) return;
        if (this.player.isPlaying()) {
            this.player.pause();
            this.btnPlay.textContent = '▶';
        } else {
            this.player.play();
            this.btnPlay.textContent = '❚❚';
        }
    }

    async loadRuns() {
        try {
            const response = await fetch(`${API_BASE}/runs`);
            const runs = await response.json();
            this.renderRunList(runs);
        } catch (err) {
            console.error('Failed to load runs:', err);
            this.runList.innerHTML = '<li>Failed to load runs</li>';
        }
    }

    renderRunList(runs) {
        this.runList.innerHTML = '';

        if (runs.length === 0) {
            this.runList.innerHTML = '<li>No runs available</li>';
            return;
        }

        runs.forEach(run => {
            const li = document.createElement('li');
            li.dataset.runId = run.run_id;

            const title = document.createElement('div');
            title.className = 'run-title';
            title.textContent = `Day ${run.day} Part ${run.part}`;

            const meta = document.createElement('div');
            meta.className = 'run-meta';
            const date = new Date(run.timestamp);
            meta.textContent = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
            if (run.total_iterations) {
                meta.textContent += ` • ${run.total_iterations} frames`;
            }

            li.appendChild(title);
            li.appendChild(meta);
            li.addEventListener('click', () => this.selectRun(run.run_id));

            this.runList.appendChild(li);
        });
    }

    async selectRun(runId) {
        // Update active state in list
        this.runList.querySelectorAll('li').forEach(li => {
            li.classList.toggle('active', li.dataset.runId === runId);
        });

        // Close any existing SSE connection
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        try {
            const response = await fetch(`${API_BASE}/runs/${runId}`);
            const run = await response.json();
            this.loadRun(run);
        } catch (err) {
            console.error('Failed to load run:', err);
        }
    }

    loadRun(run) {
        this.currentRun = run;

        // Update header info
        const meta = run.metadata;
        this.runInfo.textContent = `Day ${meta.day} Part ${meta.part} • ${run.events.length} frames`;

        // Create player
        this.player = new Player(run.events, {
            onFrame: (frame, index) => this.renderFrame(frame, index),
            onStateChange: (state) => this.updatePlayButton(state),
            fps: 10,
            speed: parseFloat(this.speedSelect.value)
        });

        // Update seek bar
        this.seekBar.max = run.events.length - 1;
        this.seekBar.value = 0;

        // Render first frame
        if (run.events.length > 0) {
            this.renderFrame(run.events[0], 0);
        }
    }

    renderFrame(frame, index) {
        const data = frame.data;

        // Update seek bar and counter
        this.seekBar.value = index;
        this.frameCounter.textContent = `Frame: ${index + 1}/${this.currentRun.events.length}`;

        // Render visualization based on data type
        let rendered = false;

        for (const [key, value] of Object.entries(data)) {
            if (value && typeof value === 'object') {
                if (value.type === 'grid') {
                    this.gridRenderer.render(value);
                    rendered = true;
                    break;
                } else if (value.type === 'points') {
                    this.pointsRenderer.render(value);
                    rendered = true;
                    break;
                }
            }
        }

        // Show state data (excluding rendered visualization data)
        const stateForDisplay = {};
        for (const [key, value] of Object.entries(data)) {
            if (!value || typeof value !== 'object' || !value.type) {
                stateForDisplay[key] = value;
            }
        }
        this.stateData.textContent = JSON.stringify(stateForDisplay, null, 2);
    }

    updatePlayButton(state) {
        this.btnPlay.textContent = state === 'playing' ? '❚❚' : '▶';
    }

    connectStream(runId) {
        this.eventSource = new EventSource(`${API_BASE}/runs/${runId}/stream`);

        this.eventSource.addEventListener('metadata', (e) => {
            const meta = JSON.parse(e.data);
            this.runInfo.textContent = `Day ${meta.day} Part ${meta.part} • Live`;
        });

        this.eventSource.addEventListener('state', (e) => {
            const state = JSON.parse(e.data);
            if (this.currentRun) {
                this.currentRun.events.push(state);
                this.seekBar.max = this.currentRun.events.length - 1;

                // If playing or at end, show new frame
                if (this.player?.isPlaying() || this.seekBar.value == this.seekBar.max - 1) {
                    this.player?.last();
                }
            }
        });

        this.eventSource.addEventListener('finish', (e) => {
            const data = JSON.parse(e.data);
            this.runInfo.textContent = this.runInfo.textContent.replace('Live', `${data.total_iterations} frames`);
        });

        this.eventSource.onerror = () => {
            console.error('SSE connection error');
            this.eventSource.close();
        };
    }
}

// Initialize app
new App();
