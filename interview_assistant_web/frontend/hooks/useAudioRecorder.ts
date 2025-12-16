'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { audioAPI } from '@/lib/api';

export type AudioInputMode = 'internal' | 'external';

export interface AudioDevice {
  deviceId: string;
  label: string;
  isBlackHole: boolean;
}

interface UseAudioRecorderReturn {
  isRecording: boolean;
  audioLevel: number;
  liveText: string;
  inputMode: AudioInputMode;
  currentDevice: AudioDevice | null;
  availableDevices: AudioDevice[];
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string>;
  cancelRecording: () => void;
  toggleRecording: () => Promise<string | void>;
  toggleInputMode: () => void;
  setInputMode: (mode: AudioInputMode) => void;
  selectDevice: (deviceId: string) => void;
  refreshDevices: () => Promise<void>;
  startRecordingWithMode: (mode: AudioInputMode) => Promise<void>;
  isStreamReady: boolean;
  warmUpStream: () => Promise<void>;
}

const BLACKHOLE_KEYWORDS = ['blackhole', 'black hole', 'soundflower', 'virtual', 'loopback'];

export function useAudioRecorder(): UseAudioRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [liveText, setLiveText] = useState('');
  const [inputMode, setInputMode] = useState<AudioInputMode>('internal');
  const [currentDevice, setCurrentDevice] = useState<AudioDevice | null>(null);
  const [availableDevices, setAvailableDevices] = useState<AudioDevice[]>([]);
  const [isStreamReady, setIsStreamReady] = useState(false);
  
  // Active recording refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const animationFrameRef = useRef<number | null>(null);
  const liveTranscriptionRef = useRef<NodeJS.Timeout | null>(null);
  const transcriptionCountRef = useRef<number>(0);
  
  // PRE-WARMED stream - always ready for instant recording
  const warmStreamRef = useRef<MediaStream | null>(null);
  const warmAudioContextRef = useRef<AudioContext | null>(null);
  const warmAnalyserRef = useRef<AnalyserNode | null>(null);
  const warmSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const selectedDeviceIdRef = useRef<string | null>(null);
  
  // Check if a device name indicates BlackHole/internal audio
  const isBlackHoleDevice = useCallback((label: string): boolean => {
    const lowerLabel = label.toLowerCase();
    return BLACKHOLE_KEYWORDS.some(keyword => lowerLabel.includes(keyword));
  }, []);

  // Warm up the audio stream (call this early to have instant recording)
  const warmUpStream = useCallback(async () => {
    try {
      // Clean up existing warm stream if any
      if (warmStreamRef.current) {
        warmStreamRef.current.getTracks().forEach(track => track.stop());
      }
      if (warmAudioContextRef.current) {
        try { warmAudioContextRef.current.close(); } catch (e) {}
      }
      
      const audioConstraints: MediaTrackConstraints = {
        channelCount: 1,
        sampleRate: { ideal: 16000 },
      };
      
      if (selectedDeviceIdRef.current) {
        audioConstraints.deviceId = { exact: selectedDeviceIdRef.current };
      }
      
      // For BlackHole, disable processing
      if (inputMode === 'internal') {
        audioConstraints.echoCancellation = false;
        audioConstraints.noiseSuppression = false;
        audioConstraints.autoGainControl = false;
      } else {
        audioConstraints.echoCancellation = true;
        audioConstraints.noiseSuppression = true;
      }
      
      console.log('🔥 Warming up audio stream...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
      warmStreamRef.current = stream;
      
      // Pre-create AudioContext and analyser
      warmAudioContextRef.current = new AudioContext();
      warmSourceRef.current = warmAudioContextRef.current.createMediaStreamSource(stream);
      warmAnalyserRef.current = warmAudioContextRef.current.createAnalyser();
      warmAnalyserRef.current.fftSize = 256;
      warmSourceRef.current.connect(warmAnalyserRef.current);
      
      setIsStreamReady(true);
      console.log('✅ Audio stream ready - recording will be INSTANT');
      
    } catch (error) {
      console.error('Failed to warm up stream:', error);
      setIsStreamReady(false);
    }
  }, [inputMode]);

  // Enumerate available audio devices
  const refreshDevices = useCallback(async () => {
    try {
      // Request permission first
      await navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => stream.getTracks().forEach(track => track.stop()));
      
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices
        .filter(device => device.kind === 'audioinput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || `Microphone ${device.deviceId.slice(0, 8)}`,
          isBlackHole: isBlackHoleDevice(device.label),
        }));
      
      setAvailableDevices(audioInputs);
      
      // Auto-select BlackHole if available, otherwise first device
      const blackHoleDevice = audioInputs.find(d => d.isBlackHole);
      const targetDevice = blackHoleDevice || audioInputs[0];
      
      if (targetDevice) {
        setCurrentDevice(targetDevice);
        selectedDeviceIdRef.current = targetDevice.deviceId;
        setInputMode(targetDevice.isBlackHole ? 'internal' : 'external');
      }
      
      console.log('🎧 Audio devices:', audioInputs.map(d => 
        `${d.label}${d.isBlackHole ? ' ⭐' : ''}`
      ));
      
      // Warm up stream after device selection
      setTimeout(() => warmUpStream(), 100);
      
    } catch (error) {
      console.error('Failed to enumerate audio devices:', error);
    }
  }, [isBlackHoleDevice, warmUpStream]);

  // Toggle between internal (BlackHole) and external (Mic) modes
  const toggleInputMode = useCallback(() => {
    const newMode = inputMode === 'internal' ? 'external' : 'internal';
    setInputMode(newMode);
    
    const targetDevice = availableDevices.find(d => 
      newMode === 'internal' ? d.isBlackHole : !d.isBlackHole
    );
    
    if (targetDevice) {
      setCurrentDevice(targetDevice);
      selectedDeviceIdRef.current = targetDevice.deviceId;
      console.log(`🎧 Switched to ${newMode === 'internal' ? 'BlackHole' : 'Microphone'}: ${targetDevice.label}`);
      // Re-warm stream with new device
      warmUpStream();
    }
  }, [inputMode, availableDevices, warmUpStream]);

  // Select a specific device
  const selectDevice = useCallback((deviceId: string) => {
    const device = availableDevices.find(d => d.deviceId === deviceId);
    if (device) {
      setCurrentDevice(device);
      selectedDeviceIdRef.current = deviceId;
      setInputMode(device.isBlackHole ? 'internal' : 'external');
      console.log(`🎧 Selected: ${device.label}`);
      warmUpStream();
    }
  }, [availableDevices, warmUpStream]);

  // Set input mode directly
  const setInputModeDirectly = useCallback((mode: AudioInputMode) => {
    setInputMode(mode);
    
    const targetDevice = availableDevices.find(d => 
      mode === 'internal' ? d.isBlackHole : !d.isBlackHole
    );
    
    if (targetDevice) {
      setCurrentDevice(targetDevice);
      selectedDeviceIdRef.current = targetDevice.deviceId;
      warmUpStream();
    }
  }, [availableDevices, warmUpStream]);

  // Audio level meter
  const updateAudioLevel = useCallback(() => {
    const analyser = warmAnalyserRef.current;
    if (!analyser) {
      setAudioLevel(0);
      return;
    }

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
    
    const sum = dataArray.reduce((acc, val) => acc + val, 0);
    const avg = sum / dataArray.length;
    const level = Math.min(100, Math.round((avg / 255) * 100));
    
    setAudioLevel(level);
    
    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, [isRecording]);

  // Live transcription - updates every second with accumulated audio
  const transcribeLive = useCallback(async () => {
    if (!isRecording || audioChunksRef.current.length === 0) {
      return;
    }
    
    try {
      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      
      // Need at least 500 bytes of audio
      if (blob.size < 500) {
        return;
      }
      
      transcriptionCountRef.current += 1;
      const id = transcriptionCountRef.current;
      
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64 = (reader.result as string).split(',')[1];
        
        try {
          console.log(`📝 [#${id}] Live transcribe ${(blob.size / 1024).toFixed(1)}KB`);
          const result = await audioAPI.transcribe(base64, 'webm');
          
          if (result.success && result.text?.trim()) {
            const newText = result.text.trim();
            // Only update if we got actual text (not silence)
            if (newText.length > 0) {
              setLiveText(newText);
              console.log(`✅ [#${id}] "${newText.slice(0, 80)}${newText.length > 80 ? '...' : ''}"`);
            }
          }
        } catch (error) {
          console.error(`❌ [#${id}] Error:`, error);
        }
      };
      reader.readAsDataURL(blob);
    } catch (error) {
      console.error('Transcription error:', error);
    }
  }, [isRecording]);

  // === INSTANT START RECORDING ===
  const startRecording = useCallback(async () => {
    console.log('⚡ START RECORDING - INSTANT');
    
    // Clear any existing recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) {}
    }
    audioChunksRef.current = [];
    
    // Use warm stream if available, otherwise get new one
    let stream = warmStreamRef.current;
    
    if (!stream || stream.getTracks().every(t => t.readyState === 'ended')) {
      console.log('⚠️ No warm stream, getting new one...');
      try {
        const audioConstraints: MediaTrackConstraints = {
          channelCount: 1,
          sampleRate: { ideal: 16000 },
        };
        
        if (selectedDeviceIdRef.current) {
          audioConstraints.deviceId = { exact: selectedDeviceIdRef.current };
        }
        
        if (inputMode === 'internal') {
          audioConstraints.echoCancellation = false;
          audioConstraints.noiseSuppression = false;
          audioConstraints.autoGainControl = false;
        }
        
        stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
        warmStreamRef.current = stream;
        
        // Also create audio context for the stream
        if (!warmAudioContextRef.current || warmAudioContextRef.current.state === 'closed') {
          warmAudioContextRef.current = new AudioContext();
          warmSourceRef.current = warmAudioContextRef.current.createMediaStreamSource(stream);
          warmAnalyserRef.current = warmAudioContextRef.current.createAnalyser();
          warmAnalyserRef.current.fftSize = 256;
          warmSourceRef.current.connect(warmAnalyserRef.current);
        }
      } catch (error) {
        console.error('Failed to get audio stream:', error);
        throw error;
      }
    }
    
    // Create MediaRecorder IMMEDIATELY
    try {
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current = mediaRecorder;
      
      // START IMMEDIATELY - no delay!
      mediaRecorder.start(250); // Collect every 250ms for faster feedback
      
      setIsRecording(true);
      setLiveText(''); // Start empty, will show text as it comes
      transcriptionCountRef.current = 0;
      
      // Start audio level animation
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
      
      // Start live transcription after 800ms (need some audio first)
      setTimeout(() => {
        if (mediaRecorderRef.current?.state === 'recording') {
          transcribeLive();
          liveTranscriptionRef.current = setInterval(() => {
            if (mediaRecorderRef.current?.state === 'recording') {
              transcribeLive();
            }
          }, 1000); // Transcribe every 1 second for faster updates
        }
      }, 800);
      
      console.log('✅ Recording STARTED - capturing from moment 0');
      
    } catch (error) {
      console.error('Failed to create MediaRecorder:', error);
      throw error;
    }
  }, [inputMode, updateAudioLevel, transcribeLive]);

  // Cancel recording without transcription
  const cancelRecording = useCallback(() => {
    console.log('⚡ Cancel recording');
    
    setIsRecording(false);
    setAudioLevel(0);
    setLiveText('');
    
    if (liveTranscriptionRef.current) {
      clearInterval(liveTranscriptionRef.current);
      liveTranscriptionRef.current = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.onstop = null;
      try { mediaRecorderRef.current.stop(); } catch (e) {}
    }
    
    audioChunksRef.current = [];
    mediaRecorderRef.current = null;
    
    // DON'T stop the warm stream - keep it ready for next recording
  }, []);

  // Stop recording and get transcription
  const stopRecording = useCallback(async (): Promise<string> => {
    setIsRecording(false);
    setAudioLevel(0);
    setLiveText('⚡ Processing...');
    
    if (liveTranscriptionRef.current) {
      clearInterval(liveTranscriptionRef.current);
      liveTranscriptionRef.current = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    return new Promise((resolve, reject) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        setLiveText('');
        reject(new Error('No recording in progress'));
        return;
      }
      
      const chunksToProcess = [...audioChunksRef.current];
      
      mediaRecorderRef.current.onstop = async () => {
        try {
          const blob = new Blob(chunksToProcess, { type: 'audio/webm' });
          
          if (blob.size === 0) {
            setLiveText('');
            reject(new Error('No audio recorded'));
            return;
          }
          
          console.log(`📦 Audio: ${(blob.size / 1024).toFixed(1)}KB`);
          
          const reader = new FileReader();
          reader.onloadend = async () => {
            const base64 = (reader.result as string).split(',')[1];
            
            try {
              const result = await audioAPI.transcribe(base64, 'webm');
              if (result.success && result.text) {
                const finalText = result.text.trim();
                console.log(`✅ Final: "${finalText.slice(0, 60)}..."`);
                setLiveText('');
                resolve(finalText);
              } else {
                setLiveText('');
                reject(new Error(result.error || 'Transcription failed'));
              }
            } catch (error) {
              setLiveText('');
              reject(error);
            }
          };
          reader.readAsDataURL(blob);
        } catch (error) {
          setLiveText('');
          reject(error);
        }
      };
      
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        setLiveText('');
        reject(e);
      }
      
      audioChunksRef.current = [];
      mediaRecorderRef.current = null;
    });
  }, []);

  const toggleRecording = useCallback(async (): Promise<string | void> => {
    if (isRecording) {
      return await stopRecording();
    } else {
      await startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const startRecordingWithMode = useCallback(async (mode: AudioInputMode): Promise<void> => {
    if (isRecording) {
      await stopRecording();
      return;
    }
    
    setInputModeDirectly(mode);
    await new Promise(resolve => setTimeout(resolve, 50));
    await startRecording();
  }, [isRecording, stopRecording, setInputModeDirectly, startRecording]);

  // Initialize on mount
  useEffect(() => {
    refreshDevices();
    
    const handleDeviceChange = () => {
      console.log('🔌 Devices changed');
      refreshDevices();
    };
    
    navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange);
    return () => {
      navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange);
    };
  }, [refreshDevices]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (liveTranscriptionRef.current) {
        clearInterval(liveTranscriptionRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (warmStreamRef.current) {
        warmStreamRef.current.getTracks().forEach(track => track.stop());
      }
      if (warmAudioContextRef.current) {
        try { warmAudioContextRef.current.close(); } catch (e) {}
      }
    };
  }, []);

  return {
    isRecording,
    audioLevel,
    liveText,
    inputMode,
    currentDevice,
    availableDevices,
    startRecording,
    stopRecording,
    cancelRecording,
    toggleRecording,
    toggleInputMode,
    setInputMode: setInputModeDirectly,
    selectDevice,
    refreshDevices,
    startRecordingWithMode,
    isStreamReady,
    warmUpStream,
  };
}
