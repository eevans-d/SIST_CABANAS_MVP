import api from './api';

export interface CalendarAvailability {
  date: string;
  accommodation_id: number;
  accommodation_name: string;
  status: 'available' | 'pre_reserved' | 'confirmed' | 'blocked';
  reservation_code?: string;
  guest_name?: string;
  check_in?: string;
  check_out?: string;
}

export interface CalendarResponse {
  month: string;
  year: number;
  accommodations: Array<{
    id: number;
    name: string;
    availability: CalendarAvailability[];
  }>;
}

/**
 * Obtener disponibilidad de calendario para un mes específico
 */
export const getCalendarAvailability = async (
  month: number,
  year: number,
  accommodationId?: number
): Promise<CalendarResponse> => {
  const params = new URLSearchParams({
    month: month.toString(),
    year: year.toString(),
  });

  if (accommodationId) {
    params.append('accommodation_id', accommodationId.toString());
  }

  const response = await api.get(`/admin/calendar/availability?${params.toString()}`);
  return response.data;
};

const calendarService = {
  getCalendarAvailability,
};

export default calendarService;
