__all__ = ["mercadopago"]

from .mercadopago import router as mercadopago_router


def setup_routes(app):
    app.include_router(mercadopago_router, prefix="/mercadopago", tags=["mercadopago"])
