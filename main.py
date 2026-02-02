"""Main entry point for the Merge & Diff Tool."""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('merge_tool.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("MergeDiffTool")

def main():
    """Application entry point."""
    logger.info("Starting Merge & Diff Tool...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    
    try:
        from PySide6.QtWidgets import QApplication
        logger.info("Successfully imported PySide6.QtWidgets")
    except ImportError as e:
        logger.error(f"Failed to import PySide6: {e}")
        sys.exit(1)
    
    logger.info("Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Merge & Diff Tool")
    app.setApplicationVersion("0.1.0")
    logger.info("QApplication created successfully")
    
    try:
        from src.gui.main_window import MainWindow
        logger.info("Successfully imported MainWindow")
    except ImportError as e:
        logger.error(f"Failed to import MainWindow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    logger.info("Creating MainWindow...")
    window = MainWindow()
    logger.info("MainWindow created successfully")
    
    logger.info("Showing window...")
    window.show()
    logger.info("Window show() called")
    
    # Process events to ensure window is shown
    app.processEvents()
    logger.info("Events processed")
    
    logger.info("Entering main event loop...")
    sys.exit(app.exec())
