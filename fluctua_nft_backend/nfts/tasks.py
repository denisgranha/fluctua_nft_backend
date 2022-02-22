from config import celery_app


@celery_app.task()
def get_one():
    """A pointless Celery task to demonstrate usage."""
    return 1
