from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time
from update_db_task import update_db

scheduler = BackgroundScheduler()
scheduler.start()

# Schedule the Celery task to run every day at 4:00 AM
scheduler.add_job(
    update_db.apply_async,
    'interval',
    days=1,
    start_date=datetime.combine(datetime.today(), time(18, 28, 0))
)

# Keep the script running
try:
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()