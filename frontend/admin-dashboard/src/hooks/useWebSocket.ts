import { useEffect, useRef, useState, useCallback } from 'react';
import toast from 'react-hot-toast';

export interface WebSocketNotification {
  type: 'nueva_reserva' | 'pago_confirmado' | 'checkin_hoy' | 'reservation_expired';
  data: {
    reservation_code?: string;
    guest_name?: string;
    accommodation_name?: string;
    total_amount?: number;
    check_in?: string;
    check_out?: string;
    message?: string;
  };
  timestamp: string;
}

interface UseWebSocketOptions {
  onMessage?: (notification: WebSocketNotification) => void;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    onMessage,
    reconnectDelay = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<WebSocketNotification[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);

  // Get token from authService directly
  const token = localStorage.getItem('auth_token');

  const connect = useCallback(() => {
    if (!token) {
      console.log('No token available, skipping WebSocket connection');
      return;
    }

    // Determinar URL del WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = import.meta.env.VITE_API_PORT || '8000';
    const wsUrl = `${protocol}//${host}:${port}/api/v1/admin/ws?token=${token}`;

    console.log('Connecting to WebSocket:', wsUrl);

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;

        // Mostrar toast de conexión
        toast.success('Conectado al sistema de alertas', {
          duration: 2000,
          icon: '🔔',
        });
      };

      ws.onmessage = (event) => {
        try {
          const notification: WebSocketNotification = JSON.parse(event.data);
          console.log('WebSocket notification received:', notification);

          // Agregar a la lista de notificaciones
          setNotifications(prev => [notification, ...prev].slice(0, 50)); // Mantener últimas 50

          // Llamar callback personalizado
          if (onMessage) {
            onMessage(notification);
          }

          // Mostrar toast según el tipo
          showNotificationToast(notification);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Intentar reconectar
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        } else {
          toast.error('No se pudo conectar al sistema de alertas', {
            duration: 5000,
          });
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setIsConnected(false);
    }
  }, [token, reconnectDelay, maxReconnectAttempts, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    notifications,
    clearNotifications,
    reconnect: connect,
  };
};

// Función helper para mostrar toasts según el tipo de notificación
function showNotificationToast(notification: WebSocketNotification) {
  const { type, data } = notification;

  switch (type) {
    case 'nueva_reserva':
      toast.success(
        `Nueva Reserva: ${data.guest_name} - ${data.accommodation_name} (${data.reservation_code})`,
        {
          duration: 5000,
          icon: '🎉',
        }
      );
      break;

    case 'pago_confirmado':
      toast.success(
        `Pago Confirmado: ${data.guest_name} - $${data.total_amount?.toLocaleString()} (${data.reservation_code})`,
        {
          duration: 5000,
          icon: '💰',
        }
      );
      break;

    case 'checkin_hoy':
      toast(
        `Check-in Hoy: ${data.guest_name} - ${data.accommodation_name}`,
        {
          duration: 4000,
          icon: '🏠',
        }
      );
      break;

    case 'reservation_expired':
      toast.error(
        `Reserva Expirada: ${data.guest_name} - ${data.reservation_code}`,
        {
          duration: 4000,
          icon: '⏰',
        }
      );
      break;

    default:
      console.log('Unknown notification type:', type);
  }
}
