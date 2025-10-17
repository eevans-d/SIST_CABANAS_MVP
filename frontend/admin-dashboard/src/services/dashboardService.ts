import api from './api';
import type { DashboardStats } from '../types';

/**
 * Dashboard API service
 *
 * Maneja todas las llamadas relacionadas con el dashboard admin
 */

export const dashboardService = {
  /**
   * Obtiene estadísticas del dashboard
   *
   * @returns Promise con las estadísticas del dashboard
   */
  async getStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/admin/dashboard/stats');
    return response.data;
  },
};
