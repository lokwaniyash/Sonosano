import Fuse from 'fuse.js'
import { SoulseekFile } from '../types'

// Calculate quality score for each file (0-100)
const getQualityScore = (file: SoulseekFile): number => {
  let score = 0

  // Bitrate contribution (up to 50 points)
  if (file.bitrate) {
    // FLAC/lossless typically shows as very high bitrate or specific quality string
    if (file.quality?.toLowerCase().includes('lossless')) {
      score += 50
    } else if (file.bitrate >= 320) {
      score += 45
    } else if (file.bitrate >= 256) {
      score += 35
    } else if (file.bitrate >= 192) {
      score += 25
    } else if (file.bitrate >= 128) {
      score += 15
    } else {
      score += 5
    }
  }

  // File extension contribution (up to 30 points)
  const ext = file.extension?.toLowerCase() || file.path.split('.').pop()?.toLowerCase()
  if (ext === 'flac' || ext === 'wav') {
    score += 30
  } else if (ext === 'mp3' && file.bitrate && file.bitrate >= 320) {
    score += 25
  } else if (ext === 'mp3' && file.bitrate && file.bitrate >= 256) {
    score += 20
  } else if (ext === 'mp3') {
    score += 15
  } else if (ext === 'm4a' || ext === 'aac') {
    score += 20
  } else if (ext === 'ogg' || ext === 'opus') {
    score += 18
  }

  // File size contribution (up to 20 points) - larger usually means better quality
  if (file.size > 50000000) {
    // > 50MB
    score += 20
  } else if (file.size > 20000000) {
    // > 20MB
    score += 15
  } else if (file.size > 10000000) {
    // > 10MB
    score += 10
  } else if (file.size > 5000000) {
    // > 5MB
    score += 5
  }

  return score
}

export const sortSoulseekFiles = (soulseekFiles: SoulseekFile[], searchQuery: string): SoulseekFile[] => {
  if (!soulseekFiles || soulseekFiles.length === 0 || !searchQuery) {
    return soulseekFiles
  }

  // Don't re-sort - backend already sorted by priority (FLAC first, highest bitrate, lowest queue)
  // Only apply Fuse search if user types additional filters, otherwise trust backend ordering
  return soulseekFiles
}
