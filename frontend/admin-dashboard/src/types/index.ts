// API Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Reservation Types
export interface Reservation {
  id: number;
  code: string;
  accommodation_id: number;
  accommodation_name?: string;
  guest_name: string;
  guest_phone: string;
  guest_email: string | null;
  check_in: string;
  check_out: string;
  guests_count: number;
  total_price: string;
  deposit_percentage: string;
  deposit_amount: string;
  payment_status: PaymentStatus;
  reservation_status: ReservationStatus;
  channel_source: string;
  expires_at: string | null;
  confirmation_code: string | null;
  notes: string | null;
  created_at: string;
  confirmed_at: string | null;
}

export type PaymentStatus = 'pending' | 'partial' | 'completed' | 'refunded' | 'cancelled';
export type ReservationStatus = 'pending' | 'pre_reserved' | 'confirmed' | 'checked_in' | 'checked_out' | 'cancelled' | 'expired';

// Accommodation Types
export interface Accommodation {
  id: number;
  name: string;
  type: string;
  capacity: number;
  base_price: string;
  description: string | null;
  amenities: Record<string, any> | null;
  photos: string[] | null;
  location: Record<string, any> | null;
  policies: Record<string, any> | null;
  ical_export_token: string | null;
  active: boolean;
  created_at: string;
}

// Dashboard Stats
export interface DashboardStats {
  total_reservations: number;
  total_guests: number;
  monthly_revenue: number;
  pending_confirmations: number;
  avg_occupancy_rate: number;
  last_updated: string;
}

// User/Auth Types
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'staff';
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Filter Types
export interface ReservationFilters {
  status?: ReservationStatus;
  payment_status?: PaymentStatus;
  check_in_from?: string;
  check_in_to?: string;
  accommodation_id?: number;
  search?: string;
}
