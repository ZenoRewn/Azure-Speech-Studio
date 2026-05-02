/**
 * MicCapture: Browser microphone capture via AudioWorklet → PCM16 chunks.
 * AudioPlayback: Web Audio API playback of PCM16 audio from server.
 */

class MicCapture {
  constructor(sampleRate = 16000) {
    this.sampleRate = sampleRate;
    this.audioContext = null;
    this.workletNode = null;
    this.sourceNode = null;
    this.stream = null;
    this.onAudioData = null; // callback(ArrayBuffer)
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: this.sampleRate,
        echoCancellation: true,
        noiseSuppression: true,
      }
    });

    this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
    await this.audioContext.audioWorklet.addModule('/static/js/worklets/pcm_processor.js');

    this.sourceNode = this.audioContext.createMediaStreamSource(this.stream);
    this.workletNode = new AudioWorkletNode(this.audioContext, 'pcm-processor');

    this.workletNode.port.onmessage = (event) => {
      if (this.onAudioData) {
        this.onAudioData(event.data);
      }
    };

    this.sourceNode.connect(this.workletNode);
    this.workletNode.connect(this.audioContext.destination);
  }

  stop() {
    if (this.workletNode) {
      this.workletNode.disconnect();
      this.workletNode = null;
    }
    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}


class AudioPlayback {
  constructor(sampleRate = 24000) {
    this.sampleRate = sampleRate;
    this.audioContext = null;
    this.queue = [];
    this.playing = false;
  }

  _ensureContext() {
    if (!this.audioContext) {
      this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
    }
  }

  /**
   * Queue base64-encoded PCM16 audio for playback.
   */
  queueAudio(base64Audio) {
    this._ensureContext();
    const binary = atob(base64Audio);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    const int16 = new Int16Array(bytes.buffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / 32768;
    }

    this.queue.push(float32);
    if (!this.playing) {
      this._playNext();
    }
  }

  _playNext() {
    if (this.queue.length === 0) {
      this.playing = false;
      return;
    }

    this.playing = true;
    const samples = this.queue.shift();
    const buffer = this.audioContext.createBuffer(1, samples.length, this.sampleRate);
    buffer.getChannelData(0).set(samples);

    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(this.audioContext.destination);
    source.onended = () => this._playNext();
    source.start();
  }

  /**
   * Skip all pending audio (for interruption).
   */
  skipPending() {
    this.queue = [];
  }

  close() {
    this.queue = [];
    this.playing = false;
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}

