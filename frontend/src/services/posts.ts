import api from './api'
import type { ApiResponse, CommentListData, CommentPayload, Post, PostListData, PostPayload } from '@/types'

export interface PostQuery {
  page?: number
  size?: number
  keyword?: string
  category?: string
  tag?: string
  sort?: 'latest' | 'views' | 'likes'
}

export async function fetchPosts(params: PostQuery = {}): Promise<PostListData> {
  const { data } = await api.get<ApiResponse<PostListData>>('/api/posts', { params })
  return data.data
}

export async function fetchPost(postId: number): Promise<Post> {
  const { data } = await api.get<ApiResponse<Post>>(`/api/posts/${postId}`)
  return data.data
}

export async function createPost(payload: PostPayload): Promise<number> {
  const { data } = await api.post<ApiResponse<{ id: number }>>('/api/posts', payload)
  return data.data.id
}

export async function verifyPassword(postId: number, password: string): Promise<boolean> {
  const { data } = await api.post<ApiResponse<{ match: boolean }>>(`/api/posts/${postId}/verify-password`, { password })
  return data.data.match
}

export async function updatePost(postId: number, payload: PostPayload): Promise<number> {
  const { data } = await api.put<ApiResponse<{ id: number }>>(`/api/posts/${postId}`, payload)
  return data.data.id
}

export async function deletePost(postId: number, password: string): Promise<void> {
  await api.delete(`/api/posts/${postId}`, { data: { password } })
}

export async function likePost(postId: number): Promise<{ likeCount: number; liked: boolean }> {
  const { data } = await api.post<ApiResponse<{ like_count: number; liked: boolean }>>(`/api/posts/${postId}/like`)
  return { likeCount: data.data.like_count, liked: data.data.liked }
}

export async function unlikePost(postId: number): Promise<{ likeCount: number; liked: boolean }> {
  const { data } = await api.delete<ApiResponse<{ like_count: number; liked: boolean }>>(`/api/posts/${postId}/like`)
  return { likeCount: data.data.like_count, liked: data.data.liked }
}

export async function uploadPostImage(postId: number, file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<ApiResponse<{ image_url: string }>>(`/api/posts/${postId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data.data.image_url
}

export async function deletePostImage(postId: number, imageUrl: string, password: string): Promise<void> {
  await api.delete(`/api/posts/${postId}/images`, {
    data: { image_url: imageUrl, password },
  })
}

export async function fetchComments(postId: number): Promise<CommentListData> {
  const { data } = await api.get<ApiResponse<CommentListData>>(`/api/posts/${postId}/comments`)
  return data.data
}

export async function createComment(postId: number, payload: CommentPayload): Promise<number> {
  const { data } = await api.post<ApiResponse<{ id: number }>>(`/api/posts/${postId}/comments`, payload)
  return data.data.id
}

export async function updateComment(postId: number, commentId: number, payload: CommentPayload): Promise<number> {
  const { data } = await api.put<ApiResponse<{ id: number }>>(`/api/posts/${postId}/comments/${commentId}`, payload)
  return data.data.id
}

export async function deleteComment(postId: number, commentId: number, password: string): Promise<void> {
  await api.delete(`/api/posts/${postId}/comments/${commentId}`, { data: { password } })
}

export async function fetchPopularTags(): Promise<Array<{ name: string; count: number }>> {
  const { data } = await api.get<ApiResponse<{ tags: Array<{ name: string; count: number }> }>>('/api/tags', { params: { popular: true } })
  return data.data.tags
}
