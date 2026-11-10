import axios from 'axios'
import { installInterceptors } from '../utils/request'

export const http = axios.create({ baseURL: '/api', timeout: 60000 })
installInterceptors(http)

export function fileUrl(kind: 'artifacts' | 'previews', relPath: string | null | undefined): string {
  if (!relPath) return ''
  return `/api/files/${kind}/${relPath}`
}

export default http
