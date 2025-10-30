/**
 * Custom hook for Server-Sent Events (SSE) connection with POST support.
 *
 * Uses fetch with ReadableStream instead of EventSource to support POST requests.
 * Manages SSE connection lifecycle, progress updates, and error handling.
 */

import { useEffect, useState, useRef } from 'react';

export interface ProgressUpdate {
  type: 'progress' | 'complete' | 'error';
  step?: string;
  message: string;
  progress: number;
  result?: any;
}

interface UseSSEOptions {
  enabled: boolean;
  body?: string; // JSON body for POST request
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

export function useSSE(url: string, options: UseSSEOptions) {
  const { enabled, body, onComplete, onError } = options;

  const [data, setData] = useState<ProgressUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!enabled || !url) {
      return;
    }

    // Reset state
    setData(null);
    setIsComplete(false);
    setError(null);
    setIsConnected(false);

    // Create abort controller for cleanup
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Start SSE connection
    const connectSSE = async () => {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          },
          body: body,
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        setIsConnected(true);

        // Read the stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No response body');
        }

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // Decode chunk
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonData = line.slice(6); // Remove "data: " prefix

              try {
                const update: ProgressUpdate = JSON.parse(jsonData);
                setData(update);

                if (update.type === 'complete') {
                  setIsComplete(true);
                  reader.cancel();

                  if (onComplete && update.result) {
                    onComplete(update.result);
                  }

                  break;
                } else if (update.type === 'error') {
                  const errorMsg = update.message || 'Analysis failed';
                  setError(errorMsg);
                  reader.cancel();

                  if (onError) {
                    onError(errorMsg);
                  }

                  break;
                }
              } catch (err) {
                console.error('Failed to parse SSE message:', err);
                setError('Failed to parse progress update');
                reader.cancel();
                break;
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          // Expected when component unmounts
          return;
        }

        console.error('SSE connection error:', err);
        setError(err.message || 'Connection failed');
        setIsConnected(false);

        if (onError && !isComplete) {
          onError(err.message || 'Connection failed');
        }
      }
    };

    connectSSE();

    // Cleanup on unmount
    return () => {
      abortController.abort();
      setIsConnected(false);
    };
  }, [url, body, enabled]); // Removed onComplete, onError, isComplete from dependencies to prevent reconnections

  return {
    data,
    isConnected,
    isComplete,
    error,
    /**
     * Manually close the SSE connection.
     */
    close: () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        setIsConnected(false);
      }
    }
  };
}
