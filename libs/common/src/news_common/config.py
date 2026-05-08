from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    collector_mode: str = "mock"

    vk_token: str = ""
    vk_tokens: str = ""
    vk_communities: str = "ria,tassagency"
    vk_poll_interval: int = 60
    vk_wikidata_cache_ttl: int = 86400 * 30

    tg_api_id: str = ""
    tg_api_hash: str = ""
    tg_session_name: str = "news_collector"
    tg_channels: str = "ria,tass"

    redis_url: str = "redis://localhost:6379/0"
    stream_raw_vk: str = "raw.vk"
    stream_raw_tg: str = "raw.tg"
    stream_clean: str = "clean.posts"
    stream_enriched: str = "enriched.posts"

    opensearch_url: str = "http://localhost:9200"
    opensearch_user: str = "admin"
    opensearch_pass: str = "admin"

    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_pass: str = "neopassword123"

    nlp_mode: str = "lite"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    dashboard_port: int = 8501

    log_level: str = "INFO"

    metrics_port: int = 9100

    @property
    def vk_communities_list(self) -> list[str]:
        return [c.strip() for c in self.vk_communities.split(",") if c.strip()]

    @property
    def vk_tokens_list(self) -> list[str]:
        if self.vk_tokens.strip():
            return [t.strip() for t in self.vk_tokens.split(",") if t.strip()]
        return [self.vk_token] if self.vk_token else []

    @property
    def tg_channels_list(self) -> list[str]:
        return [c.strip() for c in self.tg_channels.split(",") if c.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
