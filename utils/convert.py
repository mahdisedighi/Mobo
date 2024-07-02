import hashlib
import json
import math


def mobo_to_biid(mobo_product ,main_category=435):
    discount = 10
    mobo_price = int(mobo_product['price'])
    biid_price = mobo_price + 140_000

    biid_product_info = {
        "name": mobo_product["title"],
        "main_category": main_category,
        "price": biid_price,
        "compare_at_price": biid_price,
        "product_identifier": mobo_product["product_id"],
        "stock": int(mobo_product["stock"]),
        "stock_type": "unlimited" if int(mobo_product["stock"]) else "out_of_stock",
        "barcode": mobo_product['product_id']
    }
    colors = []

    if '' not in mobo_product["color"]:
        for color in mobo_product["color"]:
            colors.append(color)
    elif '' not in mobo_product["design"]:
        for design in mobo_product["design"]:
            colors.append(design)

    return biid_product_info ,colors


def hash_product(dictionary):
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()
