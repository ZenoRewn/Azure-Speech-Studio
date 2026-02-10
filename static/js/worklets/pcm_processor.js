/**
 * AudioWorklet processor for PCM16 capture.
 * Collects Float32 samples, converts to Int16, and posts buffers.
 */
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buffer = [];
    // Send every ~100ms of audio at 16kHz = 1600 samples
    this._targetSamples = 1600;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const channelData = input[0]; // mono channel
    for (let i = 0; i < channelData.length; i++) {
      this._buffer.push(channelData[i]);
    }

    while (this._buffer.length >= this._targetSamples) {
      const chunk = this._buffer.splice(0, this._targetSamples);
      const int16 = new Int16Array(chunk.length);
      for (let i = 0; i < chunk.length; i++) {
        const s = Math.max(-1, Math.min(1, chunk[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      this.port.postMessage(int16.buffer, [int16.buffer]);
    }

    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
