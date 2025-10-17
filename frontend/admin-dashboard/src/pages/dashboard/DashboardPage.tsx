import React, { useState } from 'react';
import { StatsCard } from '../../components/dashboard/StatsCard';
import { ReservationsTable } from '../../components/dashboard/ReservationsTable';
import { FilterBar, type FilterState } from '../../components/dashboard/FilterBar';
import { useDashboardStats } from '../../hooks/useDashboardStats';
import type { ReservationFilters } from '../../services/reservationsService';

const DashboardPage: React.FC = () => {
  const { data: stats, isLoading } = useDashboardStats();

  // Estado para los filtros de reservas
  const [filters, setFilters] = useState<FilterState>({
    statuses: [],
    startDate: undefined,
    endDate: undefined,
    search: undefined,
  });

  // Convertir filtros del estado a formato del servicio
  const reservationFilters: ReservationFilters = {
    statuses: filters.statuses.length > 0 ? filters.statuses : undefined,
    start_date: filters.startDate,
    end_date: filters.endDate,
    search: filters.search,
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Vista general de reservas y estadísticas
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <StatsCard
          title="Total Reservas"
          value={isLoading ? 0 : (stats?.total_reservations ?? 0)}
          icon="calendar"
          subtitle="Todas las reservas"
          loading={isLoading}
        />
        <StatsCard
          title="Huéspedes"
          value={isLoading ? 0 : (stats?.total_guests ?? 0)}
          icon="users"
          subtitle="Personas alojadas"
          loading={isLoading}
        />
        <StatsCard
          title="Ingresos del Mes"
          value={isLoading ? 0 : (stats?.monthly_revenue ?? 0)}
          icon="dollar"
          subtitle="Facturación mensual"
          trend={{ value: 12, isPositive: true }}
          loading={isLoading}
        />
        <StatsCard
          title="Pendientes"
          value={isLoading ? 0 : (stats?.pending_confirmations ?? 0)}
          icon="clock"
          subtitle="Por confirmar"
          loading={isLoading}
        />
        <StatsCard
          title="Ocupación"
          value={isLoading ? 0 : (stats?.avg_occupancy_rate ?? 0)}
          icon="home"
          subtitle="Promedio mensual"
          trend={{ value: 8, isPositive: true }}
          loading={isLoading}
        />
      </div>

      {/* Filtros */}
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
      />

      {/* Reservations Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Reservas</h2>
        </div>
        <div className="px-6 pb-6">
          <ReservationsTable filters={reservationFilters} />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
