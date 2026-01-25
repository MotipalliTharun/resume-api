from jobs.celery_app import celery_app

@celery_app.task(name="jobs.tasks.tailor_async")
def tailor_async(payload: dict) -> dict:
    # You can move /tailor logic here for async processing
    # For MVP, keep it simple.
    return {"status": "todo", "payload_keys": list(payload.keys())}
