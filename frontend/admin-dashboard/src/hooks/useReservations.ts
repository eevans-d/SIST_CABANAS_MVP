import { useQuery } from '@tanstack/react-query';
import { reservationsService, type ReservationFilters } from '../services/reservationsService';
import type { Reservation } from '../types';

/**
 * Hook personalizado para obtener reservas con filtros
 *
 * Utiliza React Query para cache y refetch automático
 *
 * @param filters - Filtros opcionales (status, accommodation_id, dates, search)
 * @param enabled - Si el query debe ejecutarse (default: true)
 * @returns Query result con reservations, loading y error
 */
export const useReservations = (filters: ReservationFilters = {}, enabled = true) => {
  return useQuery<Reservation[], Error>({
    queryKey: ['reservations', filters],
    queryFn: () => reservationsService.getReservations(filters),
    enabled,
    staleTime: 10000, // Considerar datos frescos por 10 segundos
    retry: 2,
  });
};
