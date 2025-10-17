import { useQuery } from '@tanstack/react-query';
import calendarService from '../services/calendarService';
import type { CalendarResponse } from '../services/calendarService';

export const useCalendarAvailability = (
  month: number,
  year: number,
  accommodationId?: number
) => {
  return useQuery<CalendarResponse>({
    queryKey: ['calendar', 'availability', month, year, accommodationId],
    queryFn: () => calendarService.getCalendarAvailability(month, year, accommodationId),
    staleTime: 1000 * 60 * 5, // 5 minutos
    refetchInterval: 1000 * 60 * 2, // Auto-refetch cada 2 minutos
  });
};
