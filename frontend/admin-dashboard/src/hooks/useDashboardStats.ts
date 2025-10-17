import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboardService';
import type { DashboardStats } from '../types';

/**
 * Hook personalizado para obtener estadísticas del dashboard
 *
 * Utiliza React Query para cache y refetch automático
 *
 * @param refetchInterval - Intervalo de refetch en ms (default: 30000 = 30s)
 * @returns Query result con stats, loading y error
 */
export const useDashboardStats = (refetchInterval = 30000) => {
  return useQuery<DashboardStats, Error>({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardService.getStats,
    refetchInterval, // Auto-refetch cada 30 segundos
    staleTime: 20000, // Considerar datos frescos por 20 segundos
    retry: 2,
  });
};
