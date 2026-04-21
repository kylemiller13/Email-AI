from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import emails, feedback, admin, oauth
from db.database import init_db

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Email Risk AI API",
    description="Phishing detection REST API",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(emails.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(oauth.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Email Risk AI API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "emails": "/emails",
            "feedback": "/feedback",
            "admin": "/admin",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
