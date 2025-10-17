import React from 'react';
import { useReservations } from '../../hooks/useReservations';
import type { ReservationFilters } from '../../services/reservationsService';
import type { Reservation } from '../../types';

interface ReservationsTableProps {
  filters?: ReservationFilters;
}

// Mapeo de estados a badges con colores
const STATUS_BADGE_MAP: Record<string, { label: string; className: string }> = {
  pending: { label: 'Pendiente', className: 'bg-gray-100 text-gray-800' },
  pre_reserved: { label: 'Pre-Reserva', className: 'bg-yellow-100 text-yellow-800' },
  confirmed: { label: 'Confirmada', className: 'bg-green-100 text-green-800' },
  checked_in: { label: 'Check-in', className: 'bg-blue-100 text-blue-800' },
  checked_out: { label: 'Check-out', className: 'bg-purple-100 text-purple-800' },
  cancelled: { label: 'Cancelada', className: 'bg-red-100 text-red-800' },
  expired: { label: 'Expirada', className: 'bg-gray-100 text-gray-500' },
};

// Skeleton de carga para filas
const TableRowSkeleton: React.FC = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-32"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
  </tr>
);

export const ReservationsTable: React.FC<ReservationsTableProps> = ({ filters = {} }) => {
  const { data: reservations, isLoading, isError, error } = useReservations(filters);

  // Formatear fecha a formato legible
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  // Formatear precio
  const formatCurrency = (amount: string) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
    }).format(parseFloat(amount));
  };

  // Calcular tiempo relativo desde creación
  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Ahora mismo';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours}h`;
    if (diffDays < 7) return `Hace ${diffDays}d`;
    return formatDate(dateString);
  };

  if (isError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 font-medium">Error al cargar reservas</p>
        <p className="text-red-600 text-sm mt-1">{error?.message || 'Error desconocido'}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Código
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Huésped
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Check-in
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Check-out
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Huéspedes
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Estado
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Total
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Creada
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              // Loading skeletons
              <>
                {[...Array(5)].map((_, i) => (
                  <TableRowSkeleton key={i} />
                ))}
              </>
            ) : reservations && reservations.length > 0 ? (
              // Datos reales
              reservations.map((reservation: Reservation) => {
                const statusBadge = STATUS_BADGE_MAP[reservation.reservation_status] || STATUS_BADGE_MAP.pending;

                return (
                  <tr key={reservation.code} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">{reservation.code}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{reservation.guest_name}</div>
                      <div className="text-sm text-gray-500">{reservation.guest_phone}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatDate(reservation.check_in)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatDate(reservation.check_out)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{reservation.guests_count}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusBadge.className}`}
                      >
                        {statusBadge.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {formatCurrency(reservation.total_price)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getRelativeTime(reservation.created_at)}
                    </td>
                  </tr>
                );
              })
            ) : (
              // Empty state
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center">
                  <div className="text-gray-500">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <p className="mt-2 text-sm">No hay reservas para mostrar</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {Object.keys(filters).length > 0
                        ? 'Intenta ajustar los filtros'
                        : 'Las reservas aparecerán aquí'}
                    </p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer con contador */}
      {reservations && reservations.length > 0 && (
        <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
          <p className="text-sm text-gray-700">
            Mostrando <span className="font-medium">{reservations.length}</span> reserva(s)
          </p>
        </div>
      )}
    </div>
  );
};
