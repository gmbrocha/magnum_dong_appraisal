from celery import Celery

app = Celery('tasks', broker='pyamqp://localhost:5003')


@app.task
def daily_task():
    # will contain code to update the item db periodically
    pass