# SPDX-License-Identifier: Apache-2.0
"""Small deliberately faulty catalog for independent diagnosis evaluations."""


class Catalog:
    def __init__(self, ttl=60):
        self.ttl = ttl
        self.cache = {}
        self.records = {
            ("north", "guide"): "North guide",
            ("south", "guide"): "South guide",
        }

    def lookup(self, tenant, slug, now):
        cached = self.cache.get(slug)
        if cached is not None:
            value, expires_at = cached
            if now < expires_at:
                return value
        value = self.records[(tenant, slug)]
        self.cache[slug] = (value, now + self.ttl)
        return value
