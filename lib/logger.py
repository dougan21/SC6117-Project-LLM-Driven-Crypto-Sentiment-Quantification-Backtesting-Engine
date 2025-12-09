# lib/logger.py
import logging
import sys

# ==========================================
# macro config
# ==========================================
# True = enable debug mode (print detailed logs)
# False = production mode (only print errors)
DEBUG_MODE = False 

# ==========================================
# Initialization Configuration (Singleton Pattern)
# ==========================================
# Ensure configuration is done only once to avoid duplicate logs
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO if DEBUG_MODE else logging.WARNING,
        # [time] [level] [module] message
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# Create a global Logger instance
logger = logging.getLogger("SC6117_System")

# ==========================================
# Macro Function Exports
# ==========================================

def LOG(msg: str):
    """
    Normal debug log
    Only output when DEBUG_MODE = True
    """
    if DEBUG_MODE:
        # stacklevel=2 allows the log to show the caller's line number instead of logger.py's line number
        logger.info(msg, stacklevel=2)

def LOG_ERR(msg: str):
    """
    Error log
    Output regardless of mode, usually highlighted in red (depending on terminal support)
    """
    logger.error(msg, stacklevel=2)