/**
 * Frontend HTTP API Client for PRAHARI Backend.
 *
 * Connects the React/TypeScript frontend to the FastAPI orchestration endpoint:
 * POST /api/screenings/evaluate-multimodal
 */

import { BackendMultimodalResponse } from '../types';

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') ||
  'http://localhost:8000';

export class ApiError extends Error {
  public status: number;
  public detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export class ApiClient {
  private static instance: ApiClient;

  private constructor() {}

  public static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  /**
   * Health check to verify if the PRAHARI backend is reachable.
   */
  public async checkHealth(): Promise<{ isHealthy: boolean; status?: string; service?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });
      if (!response.ok) {
        return { isHealthy: false };
      }
      const data = await response.json();
      return { isHealthy: true, status: data.status, service: data.service };
    } catch {
      return { isHealthy: false };
    }
  }

  /**
   * Submit multimodal point-of-care screening payload to PRAHARI Backend.
   *
   * Form data fields:
   * - age_years: float (required)
   * - gender: str ('MALE' | 'FEMALE', required)
   * - patient_name: str (optional)
   * - beneficiary_id: int (optional)
   * - is_pregnant: bool (optional)
   * - trimester: int (1 | 2 | 3, optional)
   * - weight_kg: float (optional)
   * - height_cm: float (optional)
   * - muac_cm: float (optional)
   * - diet_iron_rich: bool (optional)
   * - diet_frequency: str ('never' | 'rare' | 'sometimes' | 'often')
   * - diet_diversity: int (0-9)
   * - ifa_adherence: str ('good' | 'poor' | 'unknown')
   * - symptom_severe_pallor: bool (optional)
   * - symptom_breathlessness: bool (optional)
   * - symptom_bilateral_oedema: bool (optional)
   * - symptom_fatigue: bool (optional)
   * - device_id: str (optional)
   * - image: UploadFile (optional conjunctival image file)
   * - ppg_csv: UploadFile (optional 250-sample 25Hz MAX30102 CSV)
   */
  public async evaluateMultimodalScreening(formData: FormData): Promise<BackendMultimodalResponse> {
    const url = `${API_BASE_URL}/api/screenings/evaluate-multimodal`;

    let response: Response;
    try {
      // NOTE: Do NOT set Content-Type header manually; fetch automatically adds
      // multipart/form-data with the correct boundary string.
      response = await fetch(url, {
        method: 'POST',
        body: formData,
      });
    } catch (networkErr: any) {
      throw new ApiError(
        `Unable to reach backend server at ${API_BASE_URL}. Ensure PRAHARI backend is running.`,
        0,
        networkErr?.message || 'Network request failed'
      );
    }

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || JSON.stringify(errorJson);
      } catch {
        // use response statusText
      }

      throw new ApiError(
        `Screening evaluation failed (${response.status}): ${errorDetail}`,
        response.status,
        errorDetail
      );
    }

    const result: BackendMultimodalResponse = await response.json();
    return result;
  }
}

export const apiClient = ApiClient.getInstance();
