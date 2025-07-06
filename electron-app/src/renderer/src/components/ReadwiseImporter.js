import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bookmark, 
  FolderOpen, 
  Upload, 
  CheckCircle, 
  AlertCircle,
  Loader,
  FileText,
  Star
} from 'lucide-react';
import { cn } from '../utils/cn';
import ApiService from '../services/ApiService';

function ReadwiseImporter({ isBackendReady, stats, onStatsUpdate }) {
  const [selectedFolder, setSelectedFolder] = useState('');
  const [importing, setImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(null);
  const [recentImports, setRecentImports] = useState([]);
  
  const apiService = new ApiService();

  const selectReadwiseFolder = async () => {
    try {
      if (window.electronAPI) {
        const folderPath = await window.electronAPI.selectFolder();
        if (folderPath) {
          setSelectedFolder(folderPath);
        }
      }
    } catch (error) {
      console.error('Failed to select folder:', error);
    }
  };

  const startImport = async () => {
    if (!selectedFolder || !isBackendReady) return;
    
    setImporting(true);
    setImportProgress({ status: 'scanning', message: 'Scanning Readwise exports...', progress: 0 });
    
    try {
      const result = await apiService.importReadwise(selectedFolder, (progress) => {
        setImportProgress(progress);
      });
      
      setRecentImports(prev => [...result.results, ...prev]);
      onStatsUpdate();
      setSelectedFolder('');
      
    } catch (error) {
      console.error('Readwise import failed:', error);
      setImportProgress({ 
        status: 'error', 
        message: error.message, 
        progress: 0 
      });
    } finally {
      setImporting(false);
      setTimeout(() => setImportProgress(null), 3000);
    }
  };

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Bookmark className="w-6 h-6 text-blue-500" />
          Readwise Integration
        </h2>
        <p className="text-muted-foreground">
          Import your Readwise highlights and annotations
        </p>
      </div>

      {/* Import Section */}
      <div className="mb-8">
        <div className="border border-border rounded-lg p-6">
          <h3 className="font-medium mb-4">Import Readwise Exports</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Readwise Export Folder
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={selectedFolder}
                  readOnly
                  placeholder="Select folder containing Readwise markdown exports"
                  className="flex-1 input"
                />
                <button
                  onClick={selectReadwiseFolder}
                  className="btn btn-secondary"
                >
                  <FolderOpen className="w-4 h-4 mr-2" />
                  Browse
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Select the folder containing your exported Readwise markdown files
              </p>
            </div>

            <button
              onClick={startImport}
              disabled={!selectedFolder || importing || !isBackendReady}
              className="btn btn-primary"
            >
              {importing ? (
                <Loader className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Upload className="w-4 h-4 mr-2" />
              )}
              Import Highlights
            </button>
          </div>
        </div>
      </div>

      {/* Import Progress */}
      <AnimatePresence>
        {importProgress && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-6 p-4 border border-border rounded-lg"
          >
            <div className="flex items-center gap-3 mb-2">
              {importProgress.status === 'error' ? (
                <AlertCircle className="w-5 h-5 text-destructive" />
              ) : importProgress.status === 'completed' ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <Loader className="w-5 h-5 animate-spin text-primary" />
              )}
              <span className="font-medium">{importProgress.message}</span>
            </div>
            {importProgress.progress > 0 && (
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${importProgress.progress}%` }}
                />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 border border-border rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Bookmark className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium">Total Highlights</span>
          </div>
          <div className="text-2xl font-bold">{stats.readwiseHighlights}</div>
        </div>
        
        <div className="p-4 border border-border rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-green-500" />
            <span className="text-sm font-medium">Books/Articles</span>
          </div>
          <div className="text-2xl font-bold">{stats.readwiseBooks || 0}</div>
        </div>
        
        <div className="p-4 border border-border rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Star className="w-4 h-4 text-yellow-500" />
            <span className="text-sm font-medium">Avg. Rating</span>
          </div>
          <div className="text-2xl font-bold">{stats.avgRating || 'N/A'}</div>
        </div>
      </div>

      {/* Recent Imports */}
      {recentImports.length > 0 && (
        <div className="flex-1">
          <h3 className="font-medium mb-4">Recently Imported</h3>
          <div className="space-y-2">
            {recentImports.slice(0, 10).map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3 p-3 border border-border rounded-lg"
              >
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div className="flex-1">
                  <div className="font-medium">{item.title || item.book_title}</div>
                  <div className="text-sm text-muted-foreground">
                    {item.highlights_count} highlights imported
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  {new Date(item.imported_at).toLocaleDateString()}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      {stats.readwiseHighlights === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <Bookmark className="w-16 h-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-medium mb-2">No Readwise Data Yet</h3>
            <p className="text-muted-foreground mb-6">
              Export your highlights from Readwise and import them here to enhance your search experience.
            </p>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>1. Go to Readwise → Export → Markdown</p>
              <p>2. Download the export file</p>
              <p>3. Extract and select the folder above</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReadwiseImporter;
