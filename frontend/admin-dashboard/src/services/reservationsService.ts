import api from './api';
import type { Reservation } from '../types';

/**
 * Reservations API service
 *
 * Maneja todas las llamadas relacionadas con reservas del admin
 */

export interface ReservationFilters {
  status?: string;
  statuses?: string[];
  accommodation_id?: number;
  from_date?: string;
  to_date?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export const reservationsService = {
  /**
   * Obtiene lista de reservas con filtros y paginación
   *
   * @param filters - Filtros opcionales (status, accommodation_id, dates, search)
   * @returns Promise con lista de reservas
   */
  async getReservations(
    filters: ReservationFilters = {}
  ): Promise<Reservation[]> {
    const params = new URLSearchParams();

    // Agregar filtros
    if (filters.status) params.append('status', filters.status);
    if (filters.statuses && filters.statuses.length > 0) {
      filters.statuses.forEach(status => params.append('status', status));
    }
    if (filters.accommodation_id) params.append('accommodation_id', filters.accommodation_id.toString());
    if (filters.from_date) params.append('from_date', filters.from_date);
    if (filters.to_date) params.append('to_date', filters.to_date);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);

    // TODO: Agregar búsqueda cuando backend lo soporte
    // if (filters.search) params.append('search', filters.search);

    const response = await api.get<Reservation[]>(
      `/admin/reservations?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Exporta reservas a CSV
   *
   * @returns Promise con blob del CSV
   */
  async exportToCsv(): Promise<Blob> {
    const response = await api.get('/admin/reservations/export.csv', {
      responseType: 'blob',
    });
    return response.data;
  },
};
