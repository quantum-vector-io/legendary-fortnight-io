/**
 * Azure Speech Services Integration for AI Avatar
 *
 * Includes:
 * - Speech-to-Text (real-time recognition)
 * - Text-to-Speech with neural voices
 * - Viseme events for lip-sync
 * - Custom voice styling with SSML
 */

import * as sdk from 'microsoft-cognitiveservices-speech-sdk';

export interface SpeechConfig {
  subscriptionKey: string;
  region: string;
  language?: string;
  voiceName?: string;
}

export interface VisemeEvent {
  audioOffset: number;
  visemeId: number;
  timestamp: number;
}

export interface SpeechResult {
  text: string;
  duration: number;
  confidence: number;
}

/**
 * Speech-to-Text: Convert user's voice to text
 */
export class SpeechRecognizer {
  private recognizer: sdk.SpeechRecognizer;
  private audioConfig: sdk.AudioConfig;

  constructor(config: SpeechConfig) {
    const speechConfig = sdk.SpeechConfig.fromSubscription(
      config.subscriptionKey,
      config.region
    );

    speechConfig.speechRecognitionLanguage = config.language || 'en-US';

    // Use microphone as audio source
    this.audioConfig = sdk.AudioConfig.fromDefaultMicrophoneInput();

    this.recognizer = new sdk.SpeechRecognizer(speechConfig, this.audioConfig);
  }

  /**
   * Start continuous recognition
   * Useful for ongoing conversations
   */
  async startContinuousRecognition(
    onRecognized: (text: string) => void,
    onRecognizing?: (text: string) => void
  ): Promise<void> {
    // Event for intermediate results (while user is speaking)
    this.recognizer.recognizing = (s, e) => {
      if (e.result.reason === sdk.ResultReason.RecognizingSpeech) {
        console.log(`🎤 Recognizing: ${e.result.text}`);
        onRecognizing?.(e.result.text);
      }
    };

    // Event for final recognized text
    this.recognizer.recognized = (s, e) => {
      if (e.result.reason === sdk.ResultReason.RecognizedSpeech) {
        console.log(`✅ Recognized: ${e.result.text}`);
        onRecognized(e.result.text);
      } else if (e.result.reason === sdk.ResultReason.NoMatch) {
        console.log('❌ No speech recognized');
      }
    };

    // Error handling
    this.recognizer.canceled = (s, e) => {
      console.error(`❌ Recognition canceled: ${e.reason}`);
      if (e.reason === sdk.CancellationReason.Error) {
        console.error(`Error details: ${e.errorDetails}`);
      }
    };

    // Start recognition
    await this.recognizer.startContinuousRecognitionAsync();
    console.log('🎙️ Continuous recognition started');
  }

  /**
   * Stop continuous recognition
   */
  async stopContinuousRecognition(): Promise<void> {
    await this.recognizer.stopContinuousRecognitionAsync();
    console.log('🛑 Recognition stopped');
  }

  /**
   * Recognize from audio file
   */
  static async recognizeFromFile(
    config: SpeechConfig,
    audioFilePath: string
  ): Promise<SpeechResult> {
    const speechConfig = sdk.SpeechConfig.fromSubscription(
      config.subscriptionKey,
      config.region
    );

    const audioConfig = sdk.AudioConfig.fromWavFileInput(
      require('fs').readFileSync(audioFilePath)
    );

    const recognizer = new sdk.SpeechRecognizer(speechConfig, audioConfig);

    return new Promise((resolve, reject) => {
      recognizer.recognizeOnceAsync(
        (result) => {
          if (result.reason === sdk.ResultReason.RecognizedSpeech) {
            resolve({
              text: result.text,
              duration: result.duration,
              confidence: result.properties.getProperty(
                sdk.PropertyId.SpeechServiceResponse_JsonResult
              )
            });
          } else {
            reject(new Error('Recognition failed'));
          }
          recognizer.close();
        },
        (error) => {
          recognizer.close();
          reject(error);
        }
      );
    });
  }

  close(): void {
    this.recognizer.close();
    this.audioConfig.close();
  }
}

/**
 * Text-to-Speech: Convert avatar's text to natural speech with lip-sync
 */
export class SpeechSynthesizer {
  private synthesizer: sdk.SpeechSynthesizer;
  private visemeEvents: VisemeEvent[] = [];

  constructor(config: SpeechConfig) {
    const speechConfig = sdk.SpeechConfig.fromSubscription(
      config.subscriptionKey,
      config.region
    );

    // Set neural voice
    speechConfig.speechSynthesisVoiceName =
      config.voiceName || 'en-US-JennyNeural';

    // Use speaker output
    const audioConfig = sdk.AudioConfig.fromDefaultSpeakerOutput();

    this.synthesizer = new sdk.SpeechSynthesizer(speechConfig, audioConfig);

    // Subscribe to viseme events for lip-sync
    this.synthesizer.visemeReceived = (s, e) => {
      this.visemeEvents.push({
        audioOffset: e.audioOffset / 10000, // Convert to milliseconds
        visemeId: e.visemeId,
        timestamp: Date.now()
      });
    };
  }

  /**
   * Synthesize speech from plain text
   */
  async speak(text: string): Promise<VisemeEvent[]> {
    this.visemeEvents = [];

    return new Promise((resolve, reject) => {
      this.synthesizer.speakTextAsync(
        text,
        (result) => {
          if (result.reason === sdk.ResultReason.SynthesizingAudioCompleted) {
            console.log(`🔊 Speech synthesized: "${text}"`);
            console.log(`📊 Viseme events: ${this.visemeEvents.length}`);
            resolve(this.visemeEvents);
          } else {
            reject(new Error(`Synthesis failed: ${result.reason}`));
          }
        },
        (error) => reject(error)
      );
    });
  }

  /**
   * Synthesize speech with SSML for advanced control
   *
   * SSML allows control over:
   * - Speaking style (cheerful, empathetic, etc.)
   * - Speed and pitch
   * - Pauses and emphasis
   * - Pronunciation
   */
  async speakSSML(ssml: string): Promise<VisemeEvent[]> {
    this.visemeEvents = [];

    return new Promise((resolve, reject) => {
      this.synthesizer.speakSsmlAsync(
        ssml,
        (result) => {
          if (result.reason === sdk.ResultReason.SynthesizingAudioCompleted) {
            console.log('🔊 SSML speech synthesized');
            resolve(this.visemeEvents);
          } else {
            reject(new Error(`Synthesis failed: ${result.reason}`));
          }
        },
        (error) => reject(error)
      );
    });
  }

  /**
   * Generate SSML with custom styling
   */
  static generateSSML(
    text: string,
    voiceName: string = 'en-US-JennyNeural',
    style?: 'cheerful' | 'empathetic' | 'customerservice' | 'chat',
    speakingRate?: number,
    pitch?: string
  ): string {
    let ssml = `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
                 xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
      <voice name="${voiceName}">`;

    if (style) {
      ssml += `<mstts:express-as style="${style}">`;
    }

    if (speakingRate || pitch) {
      ssml += `<prosody`;
      if (speakingRate) ssml += ` rate="${speakingRate}"`;
      if (pitch) ssml += ` pitch="${pitch}"`;
      ssml += `>`;
    }

    ssml += text;

    if (speakingRate || pitch) {
      ssml += `</prosody>`;
    }

    if (style) {
      ssml += `</mstts:express-as>`;
    }

    ssml += `</voice></speak>`;

    return ssml;
  }

  /**
   * Stream audio to file instead of speaker
   */
  async synthesizeToFile(
    text: string,
    outputPath: string
  ): Promise<void> {
    const speechConfig = sdk.SpeechConfig.fromSubscription(
      process.env.AZURE_SPEECH_KEY!,
      process.env.AZURE_SPEECH_REGION!
    );

    const audioConfig = sdk.AudioConfig.fromAudioFileOutput(outputPath);
    const synthesizer = new sdk.SpeechSynthesizer(speechConfig, audioConfig);

    return new Promise((resolve, reject) => {
      synthesizer.speakTextAsync(
        text,
        (result) => {
          synthesizer.close();
          if (result.reason === sdk.ResultReason.SynthesizingAudioCompleted) {
            console.log(`💾 Audio saved to: ${outputPath}`);
            resolve();
          } else {
            reject(new Error('Synthesis failed'));
          }
        },
        (error) => {
          synthesizer.close();
          reject(error);
        }
      );
    });
  }

  close(): void {
    this.synthesizer.close();
  }
}

/**
 * Viseme ID to Avatar Blend Shape Mapping
 * Based on Speech SDK viseme IDs
 */
export const VISEME_TO_BLENDSHAPE: Record<number, string> = {
  0: 'sil',      // Silence
  1: 'ae',       // as in "bat"
  2: 'aa',       // as in "father"
  3: 'ao',       // as in "bought"
  4: 'ey',       // as in "bait"
  5: 'eh',       // as in "bet"
  6: 'ih',       // as in "bit"
  7: 'iy',       // as in "beat"
  8: 'uh',       // as in "book"
  9: 'uw',       // as in "boot"
  10: 'ah',      // as in "but"
  11: 'er',      // as in "bird"
  12: 'r',       // as in "red"
  13: 'l',       // as in "lid"
  14: 's',       // as in "sit"
  15: 'sh',      // as in "ship"
  16: 'z',       // as in "zoo"
  17: 'ch',      // as in "chip"
  18: 'f',       // as in "fun"
  19: 'th',      // as in "think"
  20: 'p',       // as in "pit"
  21: 'k',       // as in "kit"
};

// ============================================
// USAGE EXAMPLES
// ============================================

async function exampleSpeechToText() {
  const config: SpeechConfig = {
    subscriptionKey: process.env.AZURE_SPEECH_KEY!,
    region: process.env.AZURE_SPEECH_REGION!,
    language: 'en-US'
  };

  const recognizer = new SpeechRecognizer(config);

  console.log('🎤 Speak into your microphone...');

  await recognizer.startContinuousRecognition(
    (finalText) => {
      console.log(`✅ Final: ${finalText}`);
      // Send to Copilot Studio or Azure OpenAI
    },
    (interimText) => {
      console.log(`⏳ Interim: ${interimText}`);
      // Show in UI as user is speaking
    }
  );

  // Run for 30 seconds
  await new Promise(resolve => setTimeout(resolve, 30000));

  await recognizer.stopContinuousRecognition();
  recognizer.close();
}

async function exampleTextToSpeech() {
  const config: SpeechConfig = {
    subscriptionKey: process.env.AZURE_SPEECH_KEY!,
    region: process.env.AZURE_SPEECH_REGION!,
    voiceName: 'en-US-JennyNeural'
  };

  const synthesizer = new SpeechSynthesizer(config);

  // Example 1: Simple text
  const text = "Hello! I'm your AI avatar assistant. How can I help you today?";
  const visemes = await synthesizer.speak(text);

  console.log('\n📊 Viseme Timeline:');
  visemes.forEach((v, i) => {
    console.log(`  ${i}: ${v.audioOffset}ms - ${VISEME_TO_BLENDSHAPE[v.visemeId]}`);
  });

  // Example 2: SSML with styling
  const ssml = SpeechSynthesizer.generateSSML(
    "I'm really excited to help you with this!",
    'en-US-JennyNeural',
    'cheerful',
    1.1,  // 10% faster
    '+5%' // Slightly higher pitch
  );

  await synthesizer.speakSSML(ssml);

  synthesizer.close();
}

async function exampleConversationLoop() {
  const speechConfig: SpeechConfig = {
    subscriptionKey: process.env.AZURE_SPEECH_KEY!,
    region: process.env.AZURE_SPEECH_REGION!,
    language: 'en-US',
    voiceName: 'en-US-JennyNeural'
  };

  const recognizer = new SpeechRecognizer(speechConfig);
  const synthesizer = new SpeechSynthesizer(speechConfig);

  console.log('🤖 Avatar conversation started. Say "goodbye" to exit.\n');

  let isListening = true;

  await recognizer.startContinuousRecognition(async (userText) => {
    if (userText.toLowerCase().includes('goodbye')) {
      isListening = false;
      await synthesizer.speak("Goodbye! Have a great day!");
      return;
    }

    console.log(`👤 User said: "${userText}"`);

    // Generate response (in real app: call Azure OpenAI)
    const response = `You said: ${userText}. How else can I assist you?`;

    console.log(`🤖 Avatar responds: "${response}"`);

    // Speak with visemes for lip-sync
    const visemes = await synthesizer.speak(response);

    // In real app: send visemes to avatar renderer
    // avatarRenderer.animateMouth(visemes);
  });

  // Wait until user says goodbye
  while (isListening) {
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  await recognizer.stopContinuousRecognition();
  recognizer.close();
  synthesizer.close();
}

// Export for use in other modules
export default {
  SpeechRecognizer,
  SpeechSynthesizer,
  VISEME_TO_BLENDSHAPE
};

// Run examples
if (require.main === module) {
  console.log('🚀 Azure Speech Services Examples\n');

  // Uncomment to run:
  // exampleSpeechToText();
  // exampleTextToSpeech();
  // exampleConversationLoop();
}
