import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startupops")

# Add backend directory to Python path so `import app` resolves everywhere
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting StartupOps AI Server on 0.0.0.0:{port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

