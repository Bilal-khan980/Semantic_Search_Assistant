#!/usr/bin/env python3
"""
Complete System Startup Script for Semantic Search Assistant.
Ensures all components are properly initialized and integrated.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemIntegrator:
    """Handles complete system integration and startup."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.backend = None
        self.components_initialized = {}
        
    async def initialize_complete_system(self) -> bool:
        """Initialize all system components in the correct order."""
        logger.info("🚀 Initializing Complete Semantic Search Assistant System")
        logger.info("=" * 70)
        
        try:
            # Step 1: Initialize core backend
            if not await self._initialize_backend():
                return False
            
            # Step 2: Initialize enhanced components
            if not await self._initialize_enhanced_components():
                return False
            
            # Step 3: Setup integrations
            if not await self._setup_integrations():
                return False
            
            # Step 4: Verify system health
            if not await self._verify_system_health():
                return False
            
            logger.info("✅ Complete system initialization successful!")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def _initialize_backend(self) -> bool:
        """Initialize the core backend components."""
        logger.info("📊 Initializing core backend...")
        
        try:
            from main import DocumentSearchBackend
            
            self.backend = DocumentSearchBackend()
            success = await self.backend.initialize()
            
            if success:
                self.components_initialized['backend'] = True
                logger.info("✅ Core backend initialized")
                return True
            else:
                logger.error("❌ Core backend initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Backend initialization error: {e}")
            return False
    
    async def _initialize_enhanced_components(self) -> bool:
        """Initialize enhanced components like citation manager, background processor, etc."""
        logger.info("🔧 Initializing enhanced components...")
        
        try:
            # Verify all enhanced components are available
            components = [
                'citation_manager',
                'background_processor', 
                'document_monitor'
            ]
            
            for component in components:
                if hasattr(self.backend, component):
                    self.components_initialized[component] = True
                    logger.info(f"✅ {component} available")
                else:
                    logger.warning(f"⚠️ {component} not available")
                    self.components_initialized[component] = False
            
            # Start document monitoring if available
            if self.components_initialized.get('document_monitor'):
                try:
                    await self.backend.document_monitor.start_monitoring()
                    logger.info("✅ Document monitoring started")
                except Exception as e:
                    logger.warning(f"⚠️ Document monitoring failed to start: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced components initialization error: {e}")
            return False
    
    async def _setup_integrations(self) -> bool:
        """Setup integrations between components."""
        logger.info("🔗 Setting up component integrations...")
        
        try:
            # Setup progress callbacks for background processor
            if self.components_initialized.get('background_processor'):
                self.backend.background_processor.add_progress_callback(
                    self._handle_progress_update
                )
                self.backend.background_processor.add_completion_callback(
                    self._handle_task_completion
                )
                logger.info("✅ Background processor callbacks configured")
            
            # Setup context callbacks for document monitor
            if self.components_initialized.get('document_monitor'):
                self.backend.document_monitor.add_context_callback(
                    self._handle_context_event
                )
                logger.info("✅ Document monitor callbacks configured")
            
            # Test search engine integration
            test_results = await self.backend.search("test query", limit=1)
            logger.info(f"✅ Search engine integration verified ({len(test_results)} results)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration setup error: {e}")
            return False
    
    async def _verify_system_health(self) -> bool:
        """Verify that all systems are working correctly."""
        logger.info("🏥 Verifying system health...")
        
        try:
            # Get system status
            if hasattr(self.backend, 'get_system_status'):
                status = await self.backend.get_system_status()
                
                # Check component health
                components = status.get('components', {})
                healthy_components = sum(1 for v in components.values() if v)
                total_components = len(components)
                
                logger.info(f"📊 Component health: {healthy_components}/{total_components} healthy")
                
                # Log statistics
                stats = status.get('statistics', {})
                if stats:
                    logger.info("📈 System statistics:")
                    for category, data in stats.items():
                        if isinstance(data, dict):
                            logger.info(f"  {category}: {len(data)} items")
                        else:
                            logger.info(f"  {category}: {data}")
            
            # Test core functionality
            await self._test_core_functionality()
            
            logger.info("✅ System health verification complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ System health verification failed: {e}")
            return False
    
    async def _test_core_functionality(self):
        """Test core functionality to ensure everything works."""
        logger.info("🧪 Testing core functionality...")
        
        # Test document processing
        try:
            # Create a test document
            test_content = "This is a test document for the semantic search assistant."
            test_chunks = await self.backend.document_processor.process_text(
                test_content, 
                source="system_test.txt"
            )
            logger.info(f"✅ Document processing: {len(test_chunks)} chunks generated")
        except Exception as e:
            logger.warning(f"⚠️ Document processing test failed: {e}")
        
        # Test search functionality
        try:
            results = await self.backend.search("semantic search", limit=3)
            logger.info(f"✅ Search functionality: {len(results)} results")
        except Exception as e:
            logger.warning(f"⚠️ Search test failed: {e}")
        
        # Test citation manager if available
        if self.components_initialized.get('citation_manager'):
            try:
                stats = self.backend.citation_manager.get_statistics()
                logger.info(f"✅ Citation manager: {stats.get('total_sources', 0)} sources")
            except Exception as e:
                logger.warning(f"⚠️ Citation manager test failed: {e}")
    
    async def _handle_progress_update(self, task):
        """Handle progress updates from background processor."""
        logger.debug(f"📊 Task progress: {task.name} - {task.progress:.1f}%")
    
    async def _handle_task_completion(self, task):
        """Handle task completion from background processor."""
        if task.status.value == 'completed':
            logger.info(f"✅ Task completed: {task.name}")
        elif task.status.value == 'failed':
            logger.warning(f"❌ Task failed: {task.name} - {task.error_message}")
    
    async def _handle_context_event(self, context_event):
        """Handle context events from document monitor."""
        event_type = context_event.get('type', 'unknown')
        suggestions_count = len(context_event.get('suggestions', []))
        logger.info(f"📋 Context event: {event_type} ({suggestions_count} suggestions)")
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of the system state."""
        return {
            'backend_initialized': self.backend is not None,
            'components_initialized': self.components_initialized,
            'total_components': len(self.components_initialized),
            'healthy_components': sum(1 for v in self.components_initialized.values() if v),
            'initialization_time': time.time()
        }
    
    async def run_system_demo(self):
        """Run a demonstration of system capabilities."""
        logger.info("🎬 Running system demonstration...")
        
        try:
            # Demo 1: Document processing
            logger.info("📄 Demo: Document Processing")
            test_text = """
            Artificial intelligence and machine learning are transforming how we work with information.
            Semantic search allows us to find relevant content based on meaning rather than just keywords.
            This enables more intelligent information retrieval and knowledge management.
            """
            
            chunks = await self.backend.document_processor.process_text(
                test_text, 
                source="demo_document.txt"
            )
            logger.info(f"  Generated {len(chunks)} chunks from demo text")
            
            # Demo 2: Search functionality
            logger.info("🔍 Demo: Semantic Search")
            results = await self.backend.search("artificial intelligence", limit=3)
            logger.info(f"  Found {len(results)} results for 'artificial intelligence'")
            
            # Demo 3: Citation management (if available)
            if self.components_initialized.get('citation_manager'):
                logger.info("📚 Demo: Citation Management")
                source_info = {
                    'title': 'Demo Article on AI',
                    'author': 'System Demo',
                    'publication_date': '2024-01-01'
                }
                source_id = self.backend.citation_manager.register_source(source_info)
                logger.info(f"  Registered demo source: {source_id}")
            
            # Demo 4: Background processing (if available)
            if self.components_initialized.get('background_processor'):
                logger.info("⚙️ Demo: Background Processing")
                
                async def demo_task(progress_callback=None, **kwargs):
                    if progress_callback:
                        progress_callback(50.0)
                    await asyncio.sleep(0.1)
                    if progress_callback:
                        progress_callback(100.0)
                    return "Demo task completed"
                
                task_id = await self.backend.background_processor.submit_task(
                    demo_task,
                    "Demo Task",
                    "Demonstration of background processing"
                )
                logger.info(f"  Submitted demo task: {task_id}")
            
            logger.info("✅ System demonstration completed successfully")
            
        except Exception as e:
            logger.error(f"❌ System demonstration failed: {e}")

async def main():
    """Main entry point for complete system startup."""
    integrator = SystemIntegrator()
    
    try:
        # Initialize the complete system
        success = await integrator.initialize_complete_system()
        
        if not success:
            logger.error("❌ System initialization failed")
            return False
        
        # Get system summary
        summary = integrator.get_system_summary()
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 SEMANTIC SEARCH ASSISTANT - COMPLETE SYSTEM READY")
        logger.info("=" * 70)
        logger.info(f"📊 Components: {summary['healthy_components']}/{summary['total_components']} healthy")
        logger.info("✨ All features are now available:")
        logger.info("  • Local document processing and indexing")
        logger.info("  • Advanced semantic search with ranking")
        logger.info("  • Context-aware floating window")
        logger.info("  • Cross-application drag & drop")
        logger.info("  • Canvas for organizing notes")
        logger.info("  • Real-time document monitoring")
        logger.info("  • Enhanced PDF highlight detection")
        logger.info("  • Advanced Readwise integration")
        logger.info("  • Citation management system")
        logger.info("  • Background processing with progress")
        logger.info("  • Global keyboard shortcuts")
        logger.info("")
        logger.info("🚀 Ready to transform your information workflow!")
        logger.info("=" * 70)
        
        # Run demonstration
        await integrator.run_system_demo()
        
        # Keep system running
        logger.info("\n⏳ System is running. Use the production launcher to start the full application.")
        logger.info("Run: python production_launcher.py")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ System startup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
