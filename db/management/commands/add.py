import datetime
from time import sleep
from django.core.management.base import BaseCommand
from db.models import Product
from utils.api_and_crawl import Biid , Mobo
from utils.convert import mobo_to_biid , hash_product
import json
import pandas as pd


class Command(BaseCommand):

    @staticmethod
    def product_exists(mobo_product):
        try:
            Product.objects.get(identifier=mobo_product)
            return True
        except:
            return False

    def handle(self ,*args ,**options):
        mo =Mobo()
        b =Biid()
        print("Aef")

        for mobo_product_short in mo.get_products():

            mobo_product_info = mo.get_info(mobo_product_short)
            for item in mobo_product_info:
                if item != "category" and item != "product_id":
                    product_id = mobo_product_info["product_id"]
                    product_identifier = f"{product_id}---{item}"

                    if self.product_exists(product_identifier):
                        print(f"product id={product_id} already exists")
                        continue

                    category = mobo_product_info["category"]
                    mobo_product = mobo_product_info[item]

                    biid_product, colors = mobo_to_biid(mobo_product, category)

                    if not biid_product['stock']:
                        print(f"product id={product_id} is out of stock")
                        continue

                    images_url = mo.get_images(product_id)
                    if not images_url:
                        print(f"product id={product_id} has no image")
                        continue

                    category = mobo_product_info['category']

                    product_id = b.add_product(biid_product, category)

                    p = Product.objects.create(id=product_id,
                                               identifier=product_identifier,
                                               from_mobo=True,
                                               )

                    for image_url in images_url:
                        try:
                            b.add_image_to_product(product_id, image_url=image_url, image_alt=biid_product['name'])
                        except:
                            pass

                    b.add_colors_to_product(product_id, colors)
                    variants = b.get_product_variants(product_id)
                    for variant in variants:
                        b.update_product_variant(product_id, variant['id'],
                                                 {'product_identifier': biid_product['barcode']})

                    try:
                        if item["status_title"] == "no":
                            file_path = "productId.xlsx"
                            sheet_name = "Sheet1"
                            column_name = "A"
                            df =pd.read_excel(file_path,sheet_name=sheet_name)
                            df.loc[len(df) ,column_name] = product_id
                            df.to_excel(file_path,index=False,sheet_name=sheet_name)

                    except:
                        pass


                    value = biid_product['name']
                    pro_id = product_id
                    b.add_tag(product_id=pro_id, value=value)
                    p.commit = True
                    p.save()
                    print(
                        f"mobo product id={mobo_product_info['product_id']} successfully added to biid product id={product_id}")




















