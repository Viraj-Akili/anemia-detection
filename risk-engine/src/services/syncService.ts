import { OfflineSyncItem } from '../types';

const SYNC_QUEUE_KEY = 'prahari_offline_sync_queue';
const OFFLINE_MODE_KEY = 'prahari_simulated_offline_mode';

export class SyncService {
  private static instance: SyncService;
  private listeners: Array<() => void> = [];

  private constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.notify());
      window.addEventListener('offline', () => this.notify());
    }
  }

  public static getInstance(): SyncService {
    if (!SyncService.instance) {
      SyncService.instance = new SyncService();
    }
    return SyncService.instance;
  }

  public subscribe(listener: () => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach((l) => l());
  }

  public getIsSimulatedOffline(): boolean {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(OFFLINE_MODE_KEY) === 'true';
  }

  public setSimulatedOffline(offline: boolean) {
    if (typeof window === 'undefined') return;
    localStorage.setItem(OFFLINE_MODE_KEY, offline ? 'true' : 'false');
    this.notify();
  }

  public getIsOnline(): boolean {
    if (typeof window === 'undefined') return true;
    if (this.getIsSimulatedOffline()) return false;
    return navigator.onLine;
  }

  public getSyncQueue(): OfflineSyncItem[] {
    if (typeof window === 'undefined') return [];
    try {
      const data = localStorage.getItem(SYNC_QUEUE_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  public addToQueue(item: Omit<OfflineSyncItem, 'id' | 'timestamp' | 'status' | 'attempts'>): OfflineSyncItem {
    const queue = this.getSyncQueue();
    const newItem: OfflineSyncItem = {
      ...item,
      id: `SYNC-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      timestamp: new Date().toISOString(),
      status: 'PENDING',
      attempts: 0,
    };
    queue.push(newItem);
    localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
    this.notify();

    // If online, auto trigger sync
    if (this.getIsOnline()) {
      this.triggerSync();
    }

    return newItem;
  }

  public async triggerSync(): Promise<{ syncedCount: number; failedCount: number }> {
    if (!this.getIsOnline()) {
      return { syncedCount: 0, failedCount: 0 };
    }

    const queue = this.getSyncQueue();
    if (queue.length === 0) return { syncedCount: 0, failedCount: 0 };

    let syncedCount = 0;
    let failedCount = 0;

    const updatedQueue: OfflineSyncItem[] = [];

    for (const item of queue) {
      item.status = 'SYNCING';
      this.notify();

      // Simulate backend server payload transmission delay
      await new Promise((res) => setTimeout(res, 600));

      // 95% success simulation
      if (Math.random() < 0.95) {
        item.status = 'SUCCESS';
        syncedCount++;
      } else {
        item.attempts += 1;
        item.status = 'FAILED';
        item.error = 'Network timeout on remote gateway';
        failedCount++;
        updatedQueue.push(item);
      }
    }

    localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(updatedQueue));
    this.notify();

    return { syncedCount, failedCount };
  }

  public clearQueue() {
    localStorage.removeItem(SYNC_QUEUE_KEY);
    this.notify();
  }
}

export const syncService = SyncService.getInstance();
