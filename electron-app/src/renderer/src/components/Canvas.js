import { AnimatePresence, motion } from 'framer-motion';
import {
    Bookmark,
    Clock,
    Copy,
    FileText,
    Move,
    Plus,
    RotateCcw,
    Trash2,
    X,
    ZoomIn,
    ZoomOut
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

const Canvas = ({ 
  items = [], 
  onAddItem, 
  onRemoveItem, 
  onUpdateItem,
  onClearCanvas,
  onSearch,
  onDragStart,
  onCopy,
  className = ""
}) => {
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [draggedItem, setDraggedItem] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [relatedSuggestions, setRelatedSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeItem, setActiveItem] = useState(null);
  
  const canvasRef = useRef(null);
  const isDragging = useRef(false);
  const lastPanPoint = useRef({ x: 0, y: 0 });

  // Handle canvas panning
  const handleCanvasMouseDown = (e) => {
    if (e.target === canvasRef.current) {
      isDragging.current = true;
      lastPanPoint.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleCanvasMouseMove = (e) => {
    if (isDragging.current) {
      const deltaX = e.clientX - lastPanPoint.current.x;
      const deltaY = e.clientY - lastPanPoint.current.y;
      
      setPan(prev => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY
      }));
      
      lastPanPoint.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleCanvasMouseUp = () => {
    isDragging.current = false;
  };

  // Handle item dragging
  const handleItemMouseDown = (item, e) => {
    e.stopPropagation();
    setDraggedItem(item);
    
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  const handleItemMouseMove = (e) => {
    if (draggedItem) {
      const canvasRect = canvasRef.current.getBoundingClientRect();
      const newPosition = {
        x: (e.clientX - canvasRect.left - dragOffset.x - pan.x) / zoom,
        y: (e.clientY - canvasRect.top - dragOffset.y - pan.y) / zoom
      };
      
      onUpdateItem(draggedItem.id, { position: newPosition });
    }
  };

  const handleItemMouseUp = () => {
    setDraggedItem(null);
  };

  // Handle item selection and related suggestions
  const handleItemClick = async (item) => {
    setActiveItem(item);
    setSelectedItems(new Set([item.id]));
    
    // Get related suggestions for this item
    if (onSearch) {
      try {
        const suggestions = await onSearch(item.content.substring(0, 100));
        setRelatedSuggestions(suggestions.filter(s => s.id !== item.id));
        setShowSuggestions(true);
      } catch (error) {
        console.error('Error getting related suggestions:', error);
      }
    }
  };

  // Canvas controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev * 1.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.3));
  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Delete' && selectedItems.size > 0) {
        selectedItems.forEach(id => onRemoveItem(id));
        setSelectedItems(new Set());
      }
      if (e.key === 'Escape') {
        setSelectedItems(new Set());
        setShowSuggestions(false);
        setActiveItem(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedItems, onRemoveItem]);

  // Mouse event handlers
  useEffect(() => {
    const handleMouseMove = (e) => {
      handleCanvasMouseMove(e);
      handleItemMouseMove(e);
    };

    const handleMouseUp = () => {
      handleCanvasMouseUp();
      handleItemMouseUp();
    };

    if (isDragging.current || draggedItem) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [draggedItem]);

  return (
    <div className={`relative w-full h-full bg-gray-50 overflow-hidden ${className}`}>
      {/* Canvas Controls */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        <div className="bg-white rounded-lg shadow-lg p-2 flex flex-col gap-1">
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 rounded"
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 rounded"
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={handleResetView}
            className="p-2 hover:bg-gray-100 rounded"
            title="Reset View"
          >
            <RotateCcw size={16} />
          </button>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-2">
          <div className="text-xs text-gray-600 mb-1">Zoom: {Math.round(zoom * 100)}%</div>
          <div className="text-xs text-gray-600">Items: {items.length}</div>
        </div>
      </div>

      {/* Canvas Actions */}
      <div className="absolute top-4 right-4 z-10">
        <div className="bg-white rounded-lg shadow-lg p-2 flex gap-1">
          <button
            onClick={onClearCanvas}
            className="p-2 hover:bg-red-100 text-red-600 rounded"
            title="Clear Canvas"
            disabled={items.length === 0}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Main Canvas */}
      <div
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleCanvasMouseDown}
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0'
        }}
      >
        {/* Canvas Items */}
        <AnimatePresence>
          {items.map((item) => (
            <CanvasItem
              key={item.id}
              item={item}
              isSelected={selectedItems.has(item.id)}
              isActive={activeItem?.id === item.id}
              onMouseDown={(e) => handleItemMouseDown(item, e)}
              onClick={() => handleItemClick(item)}
              onCopy={() => onCopy(item.content)}
              onDragStart={(e) => onDragStart(item, e)}
              onRemove={() => onRemoveItem(item.id)}
            />
          ))}
        </AnimatePresence>

        {/* Connection Lines (future feature) */}
        {/* Could add lines connecting related items */}
      </div>

      {/* Related Suggestions Panel */}
      <AnimatePresence>
        {showSuggestions && relatedSuggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className="absolute top-0 right-0 w-80 h-full bg-white shadow-2xl border-l border-gray-200 z-20"
          >
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-sm">Related Content</h3>
                <button
                  onClick={() => setShowSuggestions(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X size={16} />
                </button>
              </div>
              {activeItem && (
                <p className="text-xs text-gray-600 mt-1">
                  Related to: {activeItem.content.substring(0, 50)}...
                </p>
              )}
            </div>
            
            <div className="p-4 overflow-y-auto h-full">
              {relatedSuggestions.map((suggestion, index) => (
                <SuggestionItem
                  key={index}
                  suggestion={suggestion}
                  onAddToCanvas={() => {
                    onAddItem({
                      ...suggestion,
                      position: {
                        x: Math.random() * 400,
                        y: Math.random() * 300
                      }
                    });
                  }}
                  onCopy={() => onCopy(suggestion.content)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State */}
      {items.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <Bookmark className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">Canvas is Empty</h3>
            <p className="text-sm">
              Add items from search results or context suggestions to start building your canvas
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// Canvas Item Component
const CanvasItem = ({
  item,
  isSelected,
  isActive,
  onMouseDown,
  onClick,
  onCopy,
  onDragStart,
  onRemove
}) => {
  const getSourceIcon = (source) => {
    if (source.includes('.pdf')) return FileText;
    if (source.includes('readwise')) return Bookmark;
    return FileText;
  };

  const SourceIcon = getSourceIcon(item.source);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className={`absolute cursor-move select-none ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      } ${isActive ? 'ring-2 ring-green-500' : ''}`}
      style={{
        left: item.position?.x || 0,
        top: item.position?.y || 0,
        width: '280px'
      }}
      onMouseDown={onMouseDown}
      onClick={onClick}
      draggable
      onDragStart={(e) => onDragStart(e)}
    >
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-3 hover:shadow-xl transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <SourceIcon className="w-4 h-4 text-gray-500 flex-shrink-0" />
            <div className="text-sm font-medium text-gray-900 truncate">
              {item.title || item.source.split('/').pop()}
            </div>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onCopy();
              }}
              className="p-1 hover:bg-gray-100 rounded"
              title="Copy"
            >
              <Copy size={12} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="p-1 hover:bg-red-100 text-red-600 rounded"
              title="Remove"
            >
              <X size={12} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="text-xs text-gray-600 mb-3 line-clamp-4">
          {item.content.substring(0, 200)}...
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-2xs text-gray-500">
          <div className="flex items-center gap-2">
            <Clock size={10} />
            <span>Score: {((item.score || item.similarity || 0) * 100).toFixed(0)}%</span>
          </div>
          <div className="flex items-center gap-1">
            {item.is_readwise && (
              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                Readwise
              </span>
            )}
            {item.highlight_color && (
              <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                {item.highlight_color}
              </span>
            )}
          </div>
        </div>

        {/* Drag Handle */}
        <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Move size={12} className="text-gray-400" />
        </div>
      </div>
    </motion.div>
  );
};

// Suggestion Item Component
const SuggestionItem = ({ suggestion, onAddToCanvas, onCopy }) => {
  return (
    <div className="p-3 mb-2 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors group">
      <div className="text-sm font-medium text-gray-900 mb-1 truncate">
        {suggestion.title || suggestion.source.split('/').pop()}
      </div>
      <div className="text-xs text-gray-600 mb-2 line-clamp-3">
        {suggestion.content.substring(0, 150)}...
      </div>
      <div className="flex items-center justify-between">
        <div className="text-2xs text-gray-500">
          Score: {((suggestion.score || suggestion.similarity || 0) * 100).toFixed(0)}%
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onCopy}
            className="p-1 hover:bg-gray-100 rounded"
            title="Copy"
          >
            <Copy size={12} />
          </button>
          <button
            onClick={onAddToCanvas}
            className="p-1 hover:bg-blue-100 text-blue-600 rounded"
            title="Add to Canvas"
          >
            <Plus size={12} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Canvas;
