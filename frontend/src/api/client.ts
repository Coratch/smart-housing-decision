import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface WeightsConfig {
  price: number;
  school: number;
  facilities: number;
  property_mgmt: number;
  developer: number;
}

export interface SearchRequest {
  city: string;
  district?: string;
  price_min: number;
  price_max: number;
  weights?: WeightsConfig;
}

export interface SubScores {
  price: number;
  school: number;
  facilities: number;
  property_mgmt: number;
  developer: number;
}

export interface CommunityBrief {
  id: number;
  name: string;
  city: string;
  district: string | null;
  avg_price: number | null;
  score: number;
  sub_scores: SubScores;
  pros: string[];
  cons: string[];
  tags: string[];
}

export interface SearchResponse {
  total: number;
  communities: CommunityBrief[];
}

export interface POIResponse {
  category: string;
  name: string;
  distance: number | null;
  walk_time: number | null;
}

export interface SchoolDistrictResponse {
  primary_school: string | null;
  middle_school: string | null;
  school_rank: string | null;
  year: number | null;
}

export interface CommunityDetail {
  id: number;
  name: string;
  city: string;
  district: string | null;
  address: string | null;
  avg_price: number | null;
  build_year: number | null;
  total_units: number | null;
  green_ratio: number | null;
  volume_ratio: number | null;
  property_company: string | null;
  property_fee: number | null;
  developer: string | null;
  parking_ratio: string | null;
  score: number;
  sub_scores: SubScores;
  pros: string[];
  cons: string[];
  school_districts: SchoolDistrictResponse[];
  nearby_pois: POIResponse[];
}

export const searchCommunities = (params: SearchRequest) =>
  apiClient.post<SearchResponse>("/search", params);

export const getCommunityDetail = (id: number) =>
  apiClient.get<CommunityDetail>(`/community/${id}`);

export const getDefaultWeights = () =>
  apiClient.get<WeightsConfig>("/config/weights");
