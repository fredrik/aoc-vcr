export class PointsRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        this.pointColor = '#e74c3c';
        this.pointRadius = 4;
        this.backgroundColor = '#1a1a2e';
    }

    setPointColor(color) {
        this.pointColor = color;
    }

    setPointRadius(radius) {
        this.pointRadius = radius;
    }

    render(pointsData, options = {}) {
        const { data } = pointsData;

        if (!data || data.length === 0) {
            this.clear();
            return;
        }

        // Calculate bounds
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;

        for (const point of data) {
            const [x, y] = point;
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x);
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
        }

        const width = maxX - minX + 1;
        const height = maxY - minY + 1;

        // Calculate scale to fit canvas
        const container = this.canvas.parentElement;
        const maxWidth = container.clientWidth - 20;
        const maxHeight = container.clientHeight - 20;

        const padding = this.pointRadius * 4;
        const scaleX = (maxWidth - padding * 2) / width;
        const scaleY = (maxHeight - padding * 2) / height;
        const scale = Math.min(scaleX, scaleY, 20);

        // Set canvas size
        this.canvas.width = width * scale + padding * 2;
        this.canvas.height = height * scale + padding * 2;

        // Clear canvas
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw points
        this.ctx.fillStyle = this.pointColor;
        for (const point of data) {
            const [x, y] = point;
            const canvasX = (x - minX) * scale + padding;
            const canvasY = (y - minY) * scale + padding;

            this.ctx.beginPath();
            this.ctx.arc(canvasX, canvasY, this.pointRadius, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    clear() {
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
}
