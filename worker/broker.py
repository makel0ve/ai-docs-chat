import taskiq_fastapi
from taskiq_dashboard import DashboardMiddleware
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from app.config import get_settings

settings = get_settings()

result_backend = RedisAsyncResultBackend(redis_url=settings.redis_url)

broker = (
    ListQueueBroker(url=settings.redis_url)
    .with_result_backend(result_backend)
    .with_middlewares(
        DashboardMiddleware(
            url="http://dashboard:8000",
            api_token="supersecret",
            broker_name="aidocs_worker",
        )
    )
)

taskiq_fastapi.init(broker, "app.main:app")
