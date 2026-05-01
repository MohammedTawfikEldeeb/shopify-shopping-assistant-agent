class ShortTermMemory:
    def __init__(self):
        self.last_product_ids: list[str] = []
        self.last_products: list[dict] = []

    def set_products(self, products: list[dict]):
        self.last_products = products
        self.last_product_ids = [p["id"] for p in products]

    def clear(self):
        self.last_products = []
        self.last_product_ids = []
