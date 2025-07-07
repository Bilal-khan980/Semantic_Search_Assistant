import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
    });
  }

  async checkHealth() {
    try {
      const response = await this.client.get("/health");
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  async search(query, options = {}) {
    try {
      const response = await this.client.post("/search", {
        query,
        limit: options.limit || 50,
        similarity_threshold: options.similarity_threshold || 0.3,
      });
      return response.data;
    } catch (error) {
      throw new Error(`Search failed: ${error.message}`);
    }
  }

  async processDocuments(filePaths, onProgress = null) {
    try {
      const response = await this.client.post("/process", {
        file_paths: filePaths,
      });

      const taskId = response.data.task_id;

      // Poll for progress if callback provided
      if (onProgress) {
        return this.pollProcessingStatus(taskId, onProgress);
      }

      return response.data;
    } catch (error) {
      throw new Error(`Document processing failed: ${error.message}`);
    }
  }

  async pollProcessingStatus(taskId, onProgress) {
    return new Promise((resolve, reject) => {
      const pollInterval = setInterval(async () => {
        try {
          const response = await this.client.get(`/process/status/${taskId}`);
          const status = response.data;

          if (onProgress) {
            onProgress(status);
          }

          if (status.status === "completed") {
            clearInterval(pollInterval);
            resolve(status);
          } else if (status.status === "error") {
            clearInterval(pollInterval);
            reject(new Error(status.message || "Processing failed"));
          }
        } catch (error) {
          clearInterval(pollInterval);
          reject(error);
        }
      }, 1000);
    });
  }

  async importReadwise(folderPath, onProgress = null) {
    try {
      const response = await this.client.post("/readwise/import", {
        folder_path: folderPath,
      });

      const taskId = response.data.task_id;

      // Poll for progress if callback provided
      if (onProgress) {
        return this.pollProcessingStatus(taskId, onProgress);
      }

      return response.data;
    } catch (error) {
      throw new Error(`Readwise import failed: ${error.message}`);
    }
  }

  async getStats() {
    try {
      const response = await this.client.get("/stats");
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get stats: ${error.message}`);
    }
  }

  async getSuggestions(partialQuery) {
    try {
      const response = await this.client.get("/suggestions", {
        params: { q: partialQuery },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get suggestions: ${error.message}`);
    }
  }

  async deleteDocument(documentId) {
    try {
      const response = await this.client.delete(`/documents/${documentId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to delete document: ${error.message}`);
    }
  }

  async clearDatabase() {
    try {
      const response = await this.client.post("/database/clear");
      return response.data;
    } catch (error) {
      throw new Error(`Failed to clear database: ${error.message}`);
    }
  }

  async getDocuments(limit = 50, offset = 0) {
    try {
      const response = await this.client.get("/documents", {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get documents: ${error.message}`);
    }
  }

  async updateSettings(settings) {
    try {
      const response = await this.client.post("/settings", settings);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update settings: ${error.message}`);
    }
  }

  async getSettings() {
    try {
      const response = await this.client.get("/settings");
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get settings: ${error.message}`);
    }
  }
}

export default ApiService;
