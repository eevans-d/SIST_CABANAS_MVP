import { useState } from 'react';
import type { WebSocketNotification } from '../hooks/useWebSocket';

interface NotificationCenterProps {
  notifications: WebSocketNotification[];
  isConnected: boolean;
  onClear: () => void;
}

const NotificationCenter = ({ notifications, isConnected, onClear }: NotificationCenterProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const unreadCount = notifications.length;

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'nueva_reserva':
        return '🎉';
      case 'pago_confirmado':
        return '💰';
      case 'checkin_hoy':
        return '🏠';
      case 'reservation_expired':
        return '⏰';
      default:
        return '🔔';
    }
  };

  const getNotificationTitle = (type: string) => {
    switch (type) {
      case 'nueva_reserva':
        return 'Nueva Reserva';
      case 'pago_confirmado':
        return 'Pago Confirmado';
      case 'checkin_hoy':
        return 'Check-in Hoy';
      case 'reservation_expired':
        return 'Reserva Expirada';
      default:
        return 'Notificación';
    }
  };

  return (
    <div className="relative">
      {/* Bell Icon con Badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors"
        aria-label="Notificaciones"
      >
        <span className="text-xl">🔔</span>

        {/* Connection Status Indicator */}
        <span
          className={`absolute top-1 right-1 w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-gray-300'
          }`}
          title={isConnected ? 'Conectado' : 'Desconectado'}
        />

        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900">
                Notificaciones
                {unreadCount > 0 && (
                  <span className="ml-2 text-gray-500">({unreadCount})</span>
                )}
              </h3>
              {unreadCount > 0 && (
                <button
                  onClick={onClear}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Limpiar
                </button>
              )}
            </div>

            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-gray-500">
                  <p className="text-sm">No hay notificaciones</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {notifications.map((notification, index) => (
                    <div
                      key={`${notification.timestamp}-${index}`}
                      className="px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl flex-shrink-0">
                          {getNotificationIcon(notification.type)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900">
                            {getNotificationTitle(notification.type)}
                          </p>
                          <p className="text-sm text-gray-600 mt-1">
                            {notification.data.guest_name && (
                              <span>{notification.data.guest_name}</span>
                            )}
                            {notification.data.accommodation_name && (
                              <span> - {notification.data.accommodation_name}</span>
                            )}
                          </p>
                          {notification.data.reservation_code && (
                            <p className="text-xs text-gray-500 mt-1">
                              Código: {notification.data.reservation_code}
                            </p>
                          )}
                          {notification.data.total_amount && (
                            <p className="text-xs text-green-600 mt-1 font-medium">
                              ${notification.data.total_amount.toLocaleString()}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(notification.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>
                  Estado: {isConnected ? (
                    <span className="text-green-600 font-medium">● Conectado</span>
                  ) : (
                    <span className="text-gray-400">○ Desconectado</span>
                  )}
                </span>
                <span>Alertas en tiempo real</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationCenter;
