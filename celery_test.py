from celery import Celery
import time

app = Celery(
    "celery_test",
    broker="redis://localhost:6379/0"
)


@app.task
def slow_task(number):
    print(f"Starting task {number}")

    time.sleep(5)

    print(f"Finished task {number}")

    return number