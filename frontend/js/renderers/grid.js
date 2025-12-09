export class GridRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        this.colorMap = {
            '#': '#333333',
            '.': '#eeeeee',
            '@': '#e74c3c',
            'O': '#3498db',
            'X': '#e74c3c',
            '*': '#f1c40f',
            '+': '#2ecc71',
            '-': '#95a5a6',
            '|': '#95a5a6',
            ' ': '#1a1a2e',
        };

        this.defaultColor = '#9b59b6';
        this.highlightedCells = new Set();
    }

    setColorMap(map) {
        this.colorMap = { ...this.colorMap, ...map };
    }

    render(gridData, options = {}) {
        const { data, bounds } = gridData;

        if (!bounds) return;

        const minRow = bounds.min_row;
        const maxRow = bounds.max_row;
        const minCol = bounds.min_col;
        const maxCol = bounds.max_col;

        const rows = maxRow - minRow + 1;
        const cols = maxCol - minCol + 1;

        // Calculate cell size to fit canvas
        const container = this.canvas.parentElement;
        const maxWidth = container.clientWidth - 20;
        const maxHeight = container.clientHeight - 20;

        const cellWidth = Math.floor(maxWidth / cols);
        const cellHeight = Math.floor(maxHeight / rows);
        const cellSize = Math.max(1, Math.min(cellWidth, cellHeight, 20));

        // Set canvas size
        this.canvas.width = cols * cellSize;
        this.canvas.height = rows * cellSize;

        // Clear canvas
        this.ctx.fillStyle = '#1a1a2e';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Render cells
        for (const [key, value] of Object.entries(data)) {
            const [row, col] = key.split(',').map(Number);
            const x = (col - minCol) * cellSize;
            const y = (row - minRow) * cellSize;

            this.ctx.fillStyle = this.getColor(value);
            this.ctx.fillRect(x, y, cellSize, cellSize);

            // Draw grid lines for larger cells
            if (cellSize > 4) {
                this.ctx.strokeStyle = 'rgba(0,0,0,0.2)';
                this.ctx.strokeRect(x, y, cellSize, cellSize);
            }

            // Draw character for larger cells
            if (cellSize >= 12 && value.length === 1) {
                this.ctx.fillStyle = this.getContrastColor(this.getColor(value));
                this.ctx.font = `${Math.floor(cellSize * 0.7)}px monospace`;
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(value, x + cellSize / 2, y + cellSize / 2);
            }
        }

        // Render highlighted cells
        if (this.highlightedCells.size > 0) {
            this.ctx.strokeStyle = '#e74c3c';
            this.ctx.lineWidth = 2;
            for (const key of this.highlightedCells) {
                const [row, col] = key.split(',').map(Number);
                const x = (col - minCol) * cellSize;
                const y = (row - minRow) * cellSize;
                this.ctx.strokeRect(x + 1, y + 1, cellSize - 2, cellSize - 2);
            }
        }
    }

    getColor(value) {
        return this.colorMap[value] || this.defaultColor;
    }

    getContrastColor(hexColor) {
        const r = parseInt(hexColor.slice(1, 3), 16);
        const g = parseInt(hexColor.slice(3, 5), 16);
        const b = parseInt(hexColor.slice(5, 7), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance > 0.5 ? '#000000' : '#ffffff';
    }

    highlightCells(cells) {
        this.highlightedCells = new Set(cells.map(([r, c]) => `${r},${c}`));
    }

    clearHighlights() {
        this.highlightedCells.clear();
    }
}
