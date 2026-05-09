import asyncio

from news_common.repositories import PostsRepository, SentimentsRepository

from api_gateway.schemas.responses import StatsResponse


class StatsService:
    def __init__(self, posts: PostsRepository, sentiments: SentimentsRepository) -> None:
        self._posts = posts
        self._sentiments = sentiments

    async def collect(self) -> StatsResponse:
        posts_res, sent_res = await asyncio.gather(
            self._posts.stats(),
            self._sentiments.by_label_aggregation(),
        )
        return StatsResponse(
            posts_total=posts_res["hits"]["total"]["value"],
            by_source=posts_res["aggregations"]["by_source"]["buckets"],
            by_day=posts_res["aggregations"]["by_day"]["buckets"],
            by_sentiment=sent_res["aggregations"]["by_label"]["buckets"],
        )
