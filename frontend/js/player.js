export class Player {
    constructor(frames, options = {}) {
        this.frames = frames;
        this.currentIndex = 0;
        this.state = 'paused'; // 'paused' | 'playing'
        this.intervalId = null;

        this.onFrame = options.onFrame || (() => {});
        this.onStateChange = options.onStateChange || (() => {});
        this.fps = options.fps || 10;
        this.speed = options.speed || 1;
    }

    play() {
        if (this.state === 'playing') return;
        if (this.currentIndex >= this.frames.length - 1) {
            this.currentIndex = 0;
        }

        this.state = 'playing';
        this.onStateChange(this.state);
        this.startInterval();
    }

    pause() {
        if (this.state === 'paused') return;

        this.state = 'paused';
        this.onStateChange(this.state);
        this.stopInterval();
    }

    startInterval() {
        this.stopInterval();
        const interval = 1000 / (this.fps * this.speed);
        this.intervalId = setInterval(() => this.tick(), interval);
    }

    stopInterval() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    tick() {
        if (this.currentIndex < this.frames.length - 1) {
            this.currentIndex++;
            this.emitFrame();
        } else {
            this.pause();
        }
    }

    seek(index) {
        this.currentIndex = Math.max(0, Math.min(index, this.frames.length - 1));
        this.emitFrame();
    }

    first() {
        this.seek(0);
    }

    prev() {
        this.seek(this.currentIndex - 1);
    }

    next() {
        this.seek(this.currentIndex + 1);
    }

    last() {
        this.seek(this.frames.length - 1);
    }

    setSpeed(speed) {
        this.speed = speed;
        if (this.state === 'playing') {
            this.startInterval();
        }
    }

    isPlaying() {
        return this.state === 'playing';
    }

    emitFrame() {
        if (this.frames.length > 0) {
            this.onFrame(this.frames[this.currentIndex], this.currentIndex);
        }
    }
}
