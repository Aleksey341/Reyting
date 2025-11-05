import axios from 'axios'

// Use VITE_API_BASE from .env or default to /api (proxied through Nginx)
const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

// Interfaces for API responses
export interface Health {
  status: string
  service: string
}

export interface RatingItem {
  mo_id: number
  mo_name: string
  score_total?: number
  zone?: string
}

export interface RatingResponse {
  data: RatingItem[]
  total?: number
  page?: number
  page_size?: number
}

export interface MapData {
  regions: unknown[]
}

// Health check
export async function getHealth(): Promise<Health> {
  const res = await client.get<Health>('/health')
  return res.data
}

// Get rating list with optional pagination
export async function getRating(
  page: number = 1,
  page_size: number = 50
): Promise<RatingResponse> {
  const res = await client.get<RatingResponse>('/rating', {
    params: { page, page_size },
  })
  return res.data
}

// Get map data
export async function getMap(): Promise<MapData> {
  const res = await client.get<MapData>('/map')
  return res.data
}

export default client
