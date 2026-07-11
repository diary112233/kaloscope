import { api } from '$lib/api';
import type { MediaItem, MediaProgress, MediaProgressStatus, MediaProgressStatusResult, Resp } from '$lib/types';

export async function loadMediaProgress(ids: number[]): Promise<Map<number, MediaProgress>> {
  const uniqueIds = [...new Set(ids.filter((id) => Number.isFinite(id)))];
  if (uniqueIds.length === 0) {
    return new Map();
  }
  const result = new Map<number, MediaProgress>();
  for (let offset = 0; offset < uniqueIds.length; offset += 999) {
    const resp = await api
      .post('media/progress/list', {
        json: { ids: uniqueIds.slice(offset, offset + 999) }
      })
      .json<Resp<MediaProgress[]>>();
    for (const progress of resp.data) {
      result.set(progress.media_id, progress);
    }
  }
  return result;
}

export async function setMediaProgressStatus(
  mediaId: number,
  status: MediaProgressStatus
): Promise<MediaProgressStatusResult> {
  const resp = await api
    .post('media/progress/status', {
      json: { media_id: mediaId, status }
    })
    .json<Resp<MediaProgressStatusResult>>();
  return resp.data;
}

export function attachMediaProgress<T extends MediaItem>(items: T[], progresses: Map<number, MediaProgress>) {
  for (const item of items) {
    item.progress = progresses.get(item.id) ?? null;
  }
}

export function isWatched(progress: MediaProgress | null | undefined): boolean {
  return progress?.status === 'watched';
}

export function mediaProgressStatus(progress: MediaProgress | null | undefined): MediaProgressStatus {
  return progress?.status ?? 'unwatched';
}

export function hasProgress(progress: MediaProgress | null | undefined): boolean {
  return !!progress;
}
