import axios from "axios"

const API_BASE_URL = "http://127.0.0.1:8000"

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
    })
  }

  async checkHealth() {
    const response = await this.client.get("/health")
    return response.data
  }

  async search(query, options = {}) {
    const response = await this.client.post("/search", {
      query,
      limit: options.limit || 20,
      similarity_threshold: options.similarity_threshold || 0.3,
    })
    return response.data
  }

  async uploadDocuments(files) {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append("files", file)
    })

    const response = await this.client.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    })
    return response.data
  }

  async importReadwise(markdownContent) {
    const response = await this.client.post("/readwise/import", {
      markdown_content: markdownContent,
    })
    return response.data
  }

  async getProcessingStatus(taskId) {
    const response = await this.client.get(`/documents/processing/${taskId}`)
    return response.data
  }

  async getStats() {
    const response = await this.client.get("/stats")
    return response.data
  }

  async getSuggestions(query) {
    const response = await this.client.get("/suggestions", {
      params: { q: query },
    })
    return response.data
  }
}

export default new ApiService()
export { ApiService }
