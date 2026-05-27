"""SOE Investment Compliance - App Factory"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def create_app():
    app = FastAPI(
        title="国企投资合规审查系统",
        description="三重一大决策校验 + 三单匹配 + 责任链追溯",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017, log_level="info")