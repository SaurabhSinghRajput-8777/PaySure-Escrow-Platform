import { useState, useEffect, useRef } from 'react';
import Pusher from 'pusher-js';

const PUSHER_KEY = import.meta.env.VITE_PUSHER_KEY;
const PUSHER_CLUSTER = import.meta.env.VITE_PUSHER_CLUSTER || 'ap2';
const API_BASE = import.meta.env.VITE_API_URL;

// Singleton Pusher instance to avoid multiple connections
let pusherInstance = null;

function getPusher(getToken) {
  if (!pusherInstance) {
    if (!PUSHER_KEY) {
      console.warn('VITE_PUSHER_KEY is missing. Chat will not be real-time.');
      return null;
    }

    pusherInstance = new Pusher(PUSHER_KEY, {
      cluster: PUSHER_CLUSTER,
      forceTLS: true,
      authEndpoint: `${API_BASE}/api/v1/pusher/auth`,
      auth: {
        async transport(params, callback) {
          try {
            const token = await getToken();
            const response = await fetch(`${API_BASE}/api/v1/pusher/auth`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Bearer ${token}`
              },
              body: new URLSearchParams(params.data).toString()
            });

            if (!response.ok) {
              throw new Error(`Pusher auth failed: ${response.status}`);
            }

            const data = await response.json();
            callback(false, data);
          } catch (error) {
            console.error('Pusher auth error:', error);
            callback(true, error);
          }
        }
      }
    });
  }
  return pusherInstance;
}

/**
 * usePusherChat — real-time chat hook for invoice rooms using Pusher Channels.
 * 
 * Architecture:
 * 1. Subscribes to a private channel: `private-chat-<invoiceId>`
 * 2. Authenticates via the backend using the current Clerk JWT.
 * 3. Listens for the `new-message` event.
 */
export function usePusherChat(invoiceId, { enabled, getToken, onMessage }) {
  const [connected, setConnected] = useState(false);
  const channelRef = useRef(null);

  useEffect(() => {
    if (!enabled || !invoiceId || !getToken) return;

    const pusher = getPusher(getToken);
    if (!pusher) return;

    const channelName = `private-chat-${invoiceId}`;
    
    // Subscribe to the private channel
    const channel = pusher.subscribe(channelName);
    channelRef.current = channel;

    channel.bind('pusher:subscription_succeeded', () => {
      setConnected(true);
    });

    channel.bind('pusher:subscription_error', (status) => {
      console.error('Pusher subscription error:', status);
      setConnected(false);
    });

    // Listen for new messages
    channel.bind('new-message', (data) => {
      onMessage?.(data);
    });

    return () => {
      if (channelRef.current) {
        channelRef.current.unbind_all();
        pusher.unsubscribe(channelName);
        channelRef.current = null;
      }
      setConnected(false);
    };
  }, [enabled, invoiceId, getToken, onMessage]);

  return { connected };
}
