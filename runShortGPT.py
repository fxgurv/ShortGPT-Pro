import uvicorn

if __name__ == "__main__":
    # Start Uvicorn with reload enabled, to detect code changes
    uvicorn.run("app.main:app", host="0.0.0.0", port=31415, reload=True)