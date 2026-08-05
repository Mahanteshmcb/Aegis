import { useEffect, useRef } from 'react';

// Lightweight Socket.IO client hook using dynamic import to avoid SSR issues
export default function useRealtime({ url = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'), token, onConnect, onDisconnect, onMessage } = {}) {
  const socketRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    async function init() {
      try {
        const io = (await import('socket.io-client')).default;
        const opts = { path: '/socket.io', transports: ['websocket'] };
        if (token) opts.auth = { token };
        const socket = io(url, opts);
        socketRef.current = socket;
        socket.on('connect', () => { onConnect && onConnect(socket.id); });
        socket.on('disconnect', (reason) => { onDisconnect && onDisconnect(reason); });
        socket.on('message', (msg) => { onMessage && onMessage(msg); });
      } catch (e) {
        console.warn('Realtime init error (socket.io-client may be missing):', e);
      }
    }
    init();
    return () => {
      mounted = false;
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [url, token]);

  return {
    socket: socketRef,
    send: (event, payload) => socketRef.current && socketRef.current.emit(event, payload),
  };
}
