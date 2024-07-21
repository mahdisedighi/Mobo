import datetime

from django.core.management import BaseCommand
from django.db.models import Q
from tqdm import tqdm
from utils.api_and_crawl import Mobo ,Biid
from db.models import Product
from utils.convert import mobo_to_biid, hash_product


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--product_ids", nargs="+", type=int, required=False)
        parser.add_argument("--update_all", action='store_true')

    def handle(self, *args, **options):
        b = Biid()
        mo = Mobo()
        now = datetime.datetime.now()
        period = datetime.timedelta(hours=0)
        checkpoint = now - period

        queryset = Product.objects.filter(
            Q(synced_at__lt=checkpoint) | Q(synced_at__isnull=True),
              from_mobo=True,
              deleted=False)

        if options["product_ids"]:
            queryset = queryset.filter(pk__in=options["product_ids"])

        for product_object in tqdm(list(queryset) , desc="updating"):
            main_category = b.get_product(product_object.id)['main_category']
            mobo_id = product_object.identifier.split("---")[0]
            identifier = product_object.identifier
            mobo_product = mo.get_info(mobo_id)
            for item in mobo_product:
                if item != "category" and item != "product_id":
                    if f"{mobo_id}---{item}" == identifier: # در موبو موجود است
                        biid_product, colors = mobo_to_biid(mobo_product[item],main_category)
                        product_hash = hash_product(biid_product)
                        # if (product_object.product_hash == product_hash) and not options['product_ids']:
                        #     continue

                        product_object.commit = False
                        product_object.save()

                        update_keys = ['stock', 'stock_type', 'product_identifier', 'price', 'compare_at_price']

                        biid_updates = {key: biid_product[key] for key in update_keys}

                        try:
                            b.get_product(product_object.id)
                        except HTTPError as e:
                            if '404 Client Error' in str(e):
                                print(f"product id={product_object.id} deleted")
                                product_object.delete()
                                continue


                        if len(colors) == 0:
                            biid_updates["has_variants"] = False


                        b.remove_colors_from_product(product_object.id)

                        variants = b.get_product_variants(product_object.id)

                        for variant in variants:
                            b.remove_product_variant(product_object.id, variant['id'])



                        b.update_product(product_object.id, biid_updates)

                        if colors:
                            b.add_colors_to_product(product_object.id, colors)


                        if len(colors) != 0:
                            variants = b.get_product_variants(product_object.id)
                            for variant in variants:
                                b.update_product_variant(product_object.id, variant['id'],
                                                         {'product_identifier': biid_product['barcode'],
                                                          "price": biid_product['price'],
                                                          'compare_at_price': biid_product['compare_at_price']})



                        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        product_object.synced_at = time
                        product_object.updated_at = time
                        product_object.product_hash = product_hash
                        product_object.commit = True
                        product_object.save()
                        print(f"update succesfuly {product_object.id}")


