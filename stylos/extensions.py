# stylos/extensions.py
import sentry_sdk
from scrapy import signals

class SentryLoggingExtension:
    """
    Inicializa Sentry al abrir un spider y establece el contexto global.
    """
    def __init__(self, dsn, environment, release):
        self.dsn = dsn
        self.environment = environment
        self.release = release

    @classmethod
    def from_crawler(cls, crawler):
        # Lee la configuración desde settings.py
        dsn = crawler.settings.get('SENTRY_DSN')
        environment = crawler.settings.get('SENTRY_ENVIRONMENT')
        release = crawler.settings.get('SENTRY_RELEASE')
        
        ext = cls(dsn, environment, release)

        # Conecta los métodos de la extensión a las señales de Scrapy
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        
        return ext

    def spider_opened(self, spider):
        # El mejor lugar para inicializar Sentry. Se ejecuta una vez por spider.
        if self.dsn:
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                release=self.release,
                traces_sample_rate=1.0 # Opcional: para performance monitoring
            )
            # Configura el scope global para esta ejecución con tags útiles
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("spider_name", spider.name)

    def spider_closed(self, spider, reason):
        # Asegura que todos los eventos pendientes se envíen antes de que el spider se cierre
        sentry_sdk.flush()