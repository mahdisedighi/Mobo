import json
import logging
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from requests import HTTPError

import requests
from bs4 import BeautifulSoup
from time import sleep

from utils.config import configs
from utils.request import BaseRequests
from db.models import Product_model , Product_model

class Biid(BaseRequests):
    TOKEN = configs.get('biid_token')
    BASE_URL = 'https://biid.shop/api/management/v1'

    def __init__(self):
        super(Biid, self).__init__()
        self.session = requests.Session()
        self._login()

    def _login(self):
        driver = webdriver.Firefox()
        driver.get("https://biid.shop/admin/login/")
        driver.implicitly_wait(100)

        username = driver.find_element(By.XPATH, "/html/body/div[1]/div/form/div[1]/input")
        username.clear()
        username.send_keys(configs.get('biid_username'))

        password = driver.find_element(By.XPATH, "/html/body/div[1]/div/form/div[2]/input")
        password.clear()
        password.send_keys(configs.get('biid_password'))

        login_btn = driver.find_element(By.XPATH, "/html/body/div[1]/div/form/button")
        login_btn.click()
        cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        self.cookies = cookies_dict
        driver.close()

    @property
    def _headers(self):
        headers = {
            'authority': 'biid.shop',
            'accept': 'application/json',
            'accept-language': 'en,fa;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': configs.get('biid_cookie'),
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'service-worker-navigation-preload': 'true',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        return headers

    @property
    def headers(self):
        headers = {
            "Authorization": f"Api-Key {self.TOKEN}",
            "content_type": "application/json",
        }
        return headers

    #   not finish
    def get_products(self, page=1):

        next_url = f"{self.BASE_URL}/products/?page={page}"
        while next_url:
            logging.warning(next_url)
            next_url = next_url.replace('http://', 'https://')
            response = requests.get(next_url, headers=self._headers, cookies=self.cookies)
            data = response.json()
            next_url = data.get('next')
            for product in data['result']:
                yield product

    def get_product(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/"
        response = requests.get(url, headers=self._headers, cookies=self.cookies)

        product = response.json()
        return product

    def get_product_variants(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/variants/"
        response = requests.get(url, headers=self._headers, cookies=self.cookies)
        try:
            data = response.json()
            return data['result']
        except:
            pass

    def remove_product_variant(self, product_id, variant_id):
        url = f"{self.BASE_URL}/products/{product_id}/variants/{variant_id}/"
        response = requests.delete(url, headers=self.headers, cookies=self.cookies)
        return response

    def remove_product(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/"
        response = self.delete(url, headers=self.headers, cookies=self.cookies)
        return response

    def update_product_variant(self, product_id, variant_id, updates):
        url = f"{self.BASE_URL}/products/{product_id}/variants/{variant_id}/"
        response = requests.put(
            url,
            headers=self.headers,
            json=updates,
            cookies=self.session.cookies
        )
        return response

    def add_product_attribute(self, product_id, attribute, value):
        url = f"{self.BASE_URL}/products/{product_id}/attributes/secondary/"
        payload = {"attribute": attribute, "value": value}
        response = requests.post(
            url,
            headers=self.headers,
            data=payload,
            cookies=self.session.cookies
        )
        return response

    def get_images(self, product_id):
        url = f"{self.BASE_URL}/products/{product_id}/images/"
        response = requests.get(url, headers=self._headers, cookies=self.cookies)
        data = response.json()
        images = data['result']
        return images

    def update_image(self, product_id, image_id, updates):
        url = f"{self.BASE_URL}/products/{product_id}/images/{image_id}/"
        response = requests.put(url, headers=self.headers, json=updates, cookies=self.session.cookies)
        return response.json()

    def remove_image(self, product_id, image_id):
        url = f"{self.BASE_URL}/products/{product_id}/images/{image_id}/"
        response = requests.delete(url, headers=self.headers, cookies=self.session.cookies)
        return response

    def get_categories(self):
        url = f"{self.BASE_URL}/categories/"
        response = requests.get(url, headers=self._headers, cookies=self.cookies)
        return response.json()

    def add_category(self, category):
        url = f"{self.BASE_URL}/categories/"
        response = requests.post(url, headers=self.headers, json=category, cookies=self.session.cookies)
        return response

    def add_tag(self, product_id, value):
        url = f'{self.BASE_URL}/products/{product_id}/tags/'
        tag = {
            'pk': product_id,
            'value': value[0:64]
        }
        response = requests.post(url, headers=self.headers, json=tag, cookies=self.session.cookies)
        return response

    def add_product(self, product, category):
        url = f"{self.BASE_URL}/products/"
        cat_id = 0
        res = False
        parent = 435
        for cat in self.get_categories()['result']:
            if cat['name'] == category and cat["parent"] ==parent:
                parent = int(cat['id'])
                res = True
        if res == False:
            cat_j = {
                "name": f"{category}",
                'parent': parent,
            }
            x = self.add_category(cat_j)
            parent = int(x.json()['id'])

        product['main_category'] = parent



        response = requests.post(
            url,
            headers=self.headers,
            json=product,
            cookies=self.session.cookies
        )
        data = response.json()
        product_id = data['id']
        return product_id

    def update_product(self, product_id, updates):
        url = f"{self.BASE_URL}/products/{product_id}/"

        response = requests.put(
            url,
            headers=self.headers,
            json=updates,
            cookies=self.session.cookies
        )

        return response

    def update_price(self, product_id, price):
        updates = {"price": int(price), "compare_at_price": int(price * 1.18)}
        return self.update_product(product_id, updates)

    def set_product_out_of_stock(self, product_id):
        updates = {"stock_type": "out_of_stock", "stock": 0}
        return self.update_product(product_id, updates)

    def set_product_stock(self, product_id, stock):
        updates = {"stock_type": "limited", "stock": stock}
        return self.update_product(product_id, updates)

    def add_image_to_product(self, product_id, image_url, image_alt):
        url = f"{self.BASE_URL}/products/{product_id}/images/"
        response = requests.post(
            url,
            headers=self.headers,
            data={"image_url": image_url, "image_alt": image_alt},
            cookies=self.session.cookies
        )
        return response

    def add_colors_to_product(self, product_id, colors):
        url = f"{self.BASE_URL}/products/{product_id}/attributes/main/"

        try:
            response = requests.post(
                url,
                headers=self.headers,
                data={"attribute": "رنگ", "value": colors},
                cookies=self.session.cookies
            )
            return response
        except:
            return False

    def remove_colors_from_product(self, product_id):
        attribute = 'رنگ'
        url = f"{self.BASE_URL}/products/{product_id}/attributes/main/{attribute}/"

        try:
            response = requests.delete(
                url,
                headers=self.headers,
                cookies=self.session.cookies
            )
            return True
        except HTTPError:
            return False

    def get_brands(self):
        url = f"{self.BASE_URL}/brands/"
        response = requests.get(
            url,
            headers=self.headers,
            cookies=self.session.cookies
        )
        return response.json()

    def add_brand(self, name):
        url = f"{self.BASE_URL}/brands/"

        response = requests.post(
            url,
            json=name,
            headers=self.headers,
            cookies=self.session.cookies
        )

        return response


class Mobo():

    BASE_URL = 'https://mobomobo.ir/'
    def get_response(self, url):
        response = requests.get(url)
        return response

    def get_soup(self , response):
        soup = BeautifulSoup(response.text ,"html.parser")
        return soup

    def get_products(self , page=1):
        categories = [
            "case",
            "airpods",
            "applewatch",
            "accessories-2",
            "accessories",
        ]
        counter = 0
        for category in categories:
            temp = True
            url = f"{self.BASE_URL}products/{category}?page={page}"
            response = self.get_response(url)
            soup1 = self.get_soup(response)
            while temp:
                url = f"{self.BASE_URL}products/{category}?page={page}"
                response = self.get_response(url)
                soup = self.get_soup(response)
                if soup1==soup and page!=1:
                    temp = False
                    page = 1
                else:
                    elements = soup.find_all(attrs={'class': "store-product"})
                    for element in elements:
                        attrs_element = element.attrs["class"]
                        link = element.find("a").get("href").replace("/", "")
                        if 'store-full-product-outofstock' in attrs_element:
                            continue
                        else:
                            counter +=1
                            sleep(5)
                            yield link
                    page += 1

    def get_title(self,product_id):
        url = f'{self.BASE_URL}{product_id}'
        response = self.get_response(url)
        soup = self.get_soup(response)
        title = soup.find(attrs={'class': "product-title"}).text.replace("\t","").replace("\n","")
        title = re.sub(r'\([^)]*\)','',title)
        if title[-1] == " ":
            title = title[:-1]
        return title

    def get_info(self,product_id):
        url = f'{self.BASE_URL}{product_id}'
        response = self.get_response(url)
        soup = self.get_soup(response)
        title = self.get_title(product_id)
        product_models = Product_model.objects.all()
        product_groups = {}
        all_products = []
        num = [f"-{i}" for i in range(0,50)]
        if "قاب" in title:
            elements = soup.find_all(attrs={'class':'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t","").replace("\n","")
                    split_text = text.split("،")
                    for item in split_text:
                        if "\u200f" in item:
                            index = split_text.index(item)
                            split_text[index] = item.replace("\u200f", "")

                    for it in split_text:
                        for n in num:
                            n = n[::-1]
                            if n in it:
                                index = split_text.index(it)
                                split_text[index] = it.replace(n,"")

                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n , "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    if "آیفون سامسونگ شیائومی" in title:
                        title =title.replace("آیفون سامسونگ شیائومی" ,"")
                    elif "آیفون / سامسونگ / شیائومی" in title:
                        title =title.replace("آیفون / سامسونگ / شیائومی" ,"")
                    elif "آیفون ، سامسونگ ، شیائومی" in title:
                        title =title.replace("آیفون ، سامسونگ ، شیائومی" ,"")
                    elif "سامسونگ و شیائومی" in title:
                        title =title.replace("سامسونگ و شیائومی" ,"")
                    elif "آیفونی" in title:
                        title =title.replace("آیفون" ,"")
                    elif "آیفون" in title:
                        title =title.replace("آیفون" ,"")




                    #[model , design , color , price]
                    new_list = ["","","" , f"{price}" , f'{data_stock}']
                    for item in split_text:
                        if "مدل:" in item:
                            new_list[0] =item.replace("مدل: ", "")
                            if new_list[0][0] == " ":
                                new_list[0] = new_list[0][1:]
                        elif "Phone Model:" in item:
                            new_list[0] =item.replace("Phone Model: ", "")
                        elif "مدل موبایل:" in item:
                            new_list[0] =item.replace("مدل موبایل: ", "")
                        elif "مدل گوشی:" in item:
                            new_list[0] =item.replace("مدل گوشی: ", "")
                        elif "Apple:" in item:
                            new_list[0] =item.replace("Apple: ")
                        elif "iPhone:" in item:
                            new_list[0] =item.replace("iPhone: ", "")

                        if "طرح:" in item:
                            new_list[1] =item.replace("طرح: ", "")
                        elif "شاسی:" in item:
                            new_list[1] =item.replace("شاسی: ", "")
                        elif "بازیکن:" in item:
                            new_list[1] =item.replace("بازیکن: " ,"")

                        if "رنگ:" in item:
                            new_list[2] =item.replace("رنگ: ","")


                    all_products.append(new_list)
            for product in all_products:

                temp = title

                for xxx in product_models:
                    name = xxx.model.lower()
                    try:
                        jj =product[0].replace(" ","")
                    except:
                        pass
                    jj = jj.lower()
                    if "iphone" in jj:
                        brand_id = 4
                        break
                    elif (jj in name) or (name in jj):
                        brand_id =xxx.id
                        brand_name = Product_model.objects.get(id=brand_id)
                        brand_id = brand_name.id
                        break

                if str(brand_id) == "1":
                    brand_name = "سامسونگ "
                    status_title = "yes"
                elif str(brand_id) == "2" or str(brand_id) == "3":
                    brand_name = "شیائومی "
                    status_title = "yes"
                elif str(brand_id) == "4":
                    brand_name = "آیفون "
                    status_title = "yes"
                else:
                    brand_name =""
                    status_title = "no"

                title = f"{title} مناسب برای {brand_name +product[0]}"
                product_name = title
                title =temp
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": f"{product_name}",
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": 1 if product[4] != "0" else 0,
                        "status_title" : status_title,

                    }
                    product_groups["category"] ="قاب"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "کاور ایرپاد" in title:
            elements = soup.find_all(attrs={'class':'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text =i.text.replace("\t","").replace("\n","")
                    split_text =text.split("،")

                    for it in split_text:
                        for n in num:
                            n = n[::-1]
                            if n in it:
                                index = split_text.index(it)
                                split_text[index] = it.replace(n,"")

                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n , "")
                        if " " in price:
                            price = price.raplace(" ", "")


                    # [model , design , color , price]
                    new_list = ["","","" , f"{price}" , f'{data_stock}']

                    for item in split_text:
                        if "مدل:" in item:
                            new_list[0] =item.replace("مدل: ","")
                            if new_list[0][0] == " ":
                                new_list[0] = new_list[0][1:]


                        if "رنگ:" in item:
                            new_list[2] =item.replace("رنگ: " ,"")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]

                        elif "طرح:" in item:
                            new_list[2] =item.replace("طرح: " ,"")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]

                        all_products.append(new_list)


            for product in all_products:
                temp =title
                title = f"{title} مناسب برای {product[0]}"
                product_name =title
                title =temp
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": f"{product_name}",
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[4] != "0" else "0",

                    }
                    product_groups["category"] = "کاور ایرپاد"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "محافظ کابل" in title:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text =i.text.replace("\t","").replace("\n","")
                    split_text =text.split("،")

                    for it in split_text:
                        for n in num:
                            n = n[::-1]
                            if n in it:
                                index = split_text.index(n)
                                split_text[index] = it.replace(n, "")

                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")


                    # [model , design , color , price]
                    new_list = ["","","" , f"{price}" , f'{data_stock}']

                    for item in split_text:

                        if "مدل:" in item:
                            new_list[0] = item.replace("مدل: " ,"")
                            if new_list[0][0] ==" ":
                                new_list[0] = new_list[0][1:]

                        if "رنگ:" in item:
                            new_list[2] =item.replace("رنگ: " ,"")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]

                        all_products.append(new_list)

            for product in all_products:
                product_name = title
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": title,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock" : "1" if product[4] != "0" else "0",
                    }
                    product_groups["category"] = "محافظ کابل"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "جاکارتی" in title:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t", "").replace("\n", "")
                    split_text = text.split("،")
                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    # [model , design , color/model , price]
                    new_list = ["","","" , f"{price}" , f'{data_stock}']

                    for item in split_text:

                        if "مدل:" in item:
                            new_list[2] = item.replace("مدل: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]

            for product in all_products:
                product_name = title
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": title,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[0] != "0" else "0",

                    }
                    product_groups["category"] = "جاکارتی"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "اپل واچ" in title:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t", "").replace("\n", "")
                    split_text = text.split("،")
                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    # [model/size , design , color , price]
                    new_list = ["","","" , f"{price}" , f'{data_stock}']

                    for item in split_text:

                        if "مدل:" in item:
                            new_list[0] =item.replace("مدل: " ,"")
                            if new_list[0][0] ==" ":
                                new_list[0] = new_list[0][1:]
                        elif "سایز:" in item:
                            new_list[0] = item.replace("سایز: ", "")
                            if new_list[0][0] == " ":
                                new_list[0] = new_list[0][1:]




                        if "طرح:" in item:
                            new_list[2] =item.replace("طرح: " ,"")
                            if new_list[2][0] ==" ":
                                new_list[2] =new_list[2][1:]
                        elif "رنگ:" in item:
                            new_list[2] = item.replace("رنگ: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]
                        elif "رنگ بر اساس گارد:" in item:
                            new_list[2] = item.replace("رنگ بر اساس گارد: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]

                        all_products.append(new_list)

            for product in all_products:
                temp =title
                title = f"{title}مناسب برای سایز{product[0]}"
                product_name =title
                title =temp
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": product_name,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[4] != "0" else "0",

                    }
                    product_groups["category"] = "اپل واچ"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "بند" in title:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t", "").replace("\n", "")
                    split_text = text.split("،")
                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    # [model/size , design , color , price]
                    new_list = ["","","" , f"{price}" , f'{data_stock}']

                    for item in split_text:
                        if "مدل: " in title:
                            new_list[2] = item.replace("مدل: " ,"")
                            if new_list[2][0] ==" ":
                                new_list[2] = new_list[2][1:]
                        elif "رنگ:" in item:
                            new_list[2] = item.replace("رنگ: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]
                        elif "طرح:" in item:
                            new_list[2] = item.replace("طرح: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]


                        all_products.append(new_list)

            for product in all_products:
                product_name = title
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": title,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[4] != "0" else "0",

                    }
                    product_groups["category"] = "بند"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "استند" in title:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t", "").replace("\n", "")
                    split_text = text.split("،")
                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    # [model/size , design , color , price]
                    new_list = ["", "", "", f"{price}" , f'{data_stock}']

                    for item in split_text:
                        if "مدل: " in title:
                            new_list[2] = item.replace("مدل: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]

                            all_products.append(new_list)

            for product in all_products:
                product_name = title
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": title,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[4] != "0" else "0",

                    }
                    product_groups["category"] = "استند"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "جاسیگاری" in title:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t", "").replace("\n", "")
                    split_text = text.split("،")
                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    # [model/size , design , color , price]
                    new_list = ["", "", "", f"{price}" , f'{data_stock}']

                    for item in split_text:
                        if "مدل: " in title:
                            new_list[0] = item.replace("مدل: ", "")
                            if new_list[0][0] == " ":
                                new_list[0] = new_list[0][1:]

                            all_products.append(new_list)

            for product in all_products:
                product_name = title
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": title,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[4] != "0" else "0",

                    }
                    product_groups["category"] = "جاسیگاری"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        elif "کیسه آب گرم" in title:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t", "").replace("\n", "")
                    split_text = text.split("،")
                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    # [model/size , design , color , price]
                    new_list = ["", "", "", f"{price}" , f'{data_stock}']

                    for item in split_text:
                        if "مدل: " in title:
                            new_list[2] = item.replace("مدل: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]
                        elif "رنگ: " in title:
                            new_list[2] =item.replace("رنگ: " ,"")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]
                        elif "طرح: " in title:
                            new_list[2] = item.replace("طرح: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]


                        all_products.append(new_list)

            for product in all_products:
                product_name = title
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": title,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[4] != "0" else "0",

                    }
                    product_groups["category"] = "کیسه آب گرم"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups

        else:
            elements = soup.find_all(attrs={'class': 'product-variant-input'})[0].find_all("option")
            for i in elements:
                data_stock = i.get("data-stock")
                if data_stock != "0":
                    text = i.text.replace("\t", "").replace("\n", "")
                    split_text = text.split("،")
                    price = i.get("data-price")
                    for n in num:
                        if n in price:
                            price = price.replace(n, "")
                        if " " in price:
                            price = price.raplace(" ", "")

                    # [model/size , design , color , price]
                    new_list = ["", "", "", f"{price}" , f'{data_stock}']

                    for item in split_text:
                        if "مدل: " in title:
                            new_list[2] = item.replace("مدل: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]
                        elif "رنگ: " in title:
                            new_list[2] = item.replace("رنگ: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]
                        elif "طرح: " in title:
                            new_list[2] = item.replace("طرح: ", "")
                            if new_list[2][0] == " ":
                                new_list[2] = new_list[2][1:]

                        all_products.append(new_list)

            for product in all_products:
                product_name = title
                if product_name in product_groups:
                    if product[1] not in product_groups[product_name]["design"]:
                        product_groups[product_name]["design"].append(product[1])
                    if product[2] not in product_groups[product_name]["color"]:
                        product_groups[product_name]["color"].append(product[2])
                else:
                    product_groups[product_name] = {
                        "product_id": f"{product_id}",
                        "title": title,
                        "design": [product[1]],  # لیست خالی برای طرح ها
                        "color": [product[2]],
                        "price": product[3],
                        "stock": "1" if product[4] != "0" else "0",

                    }
                    product_groups["category"] = "متفرقه"
                    product_groups["product_id"] =f"{product_id}"


            return product_groups


    def get_images(self ,product_id):
        url = f'{self.BASE_URL}{product_id}'
        response = self.get_response(url)
        soup = self.get_soup(response)
        images = soup.find_all(attrs={"class": "product-images-item"})
        image = soup.find_all(attrs={'class':"product-image-element"})[0].get('src')
        image = [image]
        images = [item.get('src') for item in images]
        images = images + image
        temp = []
        for item in images:
            find = item.index("?")
            item = item.replace(item[find:] ,"")
            temp.append(item)
        images =temp
        images = [f'{self.BASE_URL}{item}' for item in images]

        return images
