import os
from dotenv import load_dotenv
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import xml.etree.ElementTree as ET
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException


def scroll_page(driver, scroll_speed=50, scroll_pause_time=0.3):

    # Отримуємо висоту екрану
    driver.execute_script("return window.innerHeight;")
    current_scroll_position = 0

    while True:

        # Прокручуємо на один крок
        driver.execute_script(f"window.scrollTo(0, {current_scroll_position + scroll_speed});")
        current_scroll_position += scroll_speed

        # Чекаємо, доки контент завантажиться
        time.sleep(scroll_pause_time)

        # Якщо досягли кінця сторінки, виходимо із циклу
        if current_scroll_position >= driver.execute_script("return document.body.scrollHeight;"):
            break


def parse_page(driver, base_url):

    # Отримуємо HTML-код сторінки після повного завантаження контенту
    
    with open("project_all.html", "a+", encoding="utf-8") as file:
        file.write(driver.page_source)

    # Зчитуємо данні
    with open("project_all.html", encoding="utf-8") as f:
        html_code = f.read()

    # Створюємо об'єкт BeautifulSoup
    soup = BeautifulSoup(html_code, "html.parser")

    # Знаходимо всі елементи <li> з даними
    product_cards = soup.find_all("li", {"data-testid": "productCard"})

    # Список для зберігання даних про товари
    products_data = []

    # Парсим дані про кожен товар
    for product_card in product_cards[:120]:  # Обмеження до 120 товарів

        id = product_card.find("div")["itemid"].split("-")[-1].split(".")[0]
        title = product_card.find("img")["alt"]
        brand = product_card.find("p", {"data-component": "ProductCardBrandName"})
        description = product_card.find("p", {"data-component": "ProductCardDescription"})
        link = product_card.find("a")["href"]
        image_link = product_card.find("img")["src"]
        additional_image_link = product_card.find("img")["src"]
        size = product_card.find("p", {"data-component": "ProductCardSizesAvailable"})
        gender = "female"
        price = product_card.find("div", class_="ltr-l3ndox").text.strip()[1:].split("-")[0]
        available = product_card.find("p", class_="ltr-2pfgen-Body-BodyBold")
        if available.text.strip() == "Available in":
            available.string.replace_with("in_stock")

        products_data.append({
            "title": title,
            "brand": brand.text.strip(),
            "description": description.text.strip(),
            "link": urljoin(base_url, link),
            "image_link": image_link,
            "item_group_id": id,
            "size": size.text.strip().split(",")[0],
            "gender": gender,
            "price": f"{price} USD",
            "id": id,
            "available": available.text.strip(),
            "product_type": urljoin(base_url, link),
            "mpn": id,
            "google_product_category": "2271",
            "color": "None",
            "additional_image_link": additional_image_link,
            "age_group": "None",
            "condition": "None"
        })
    
    return products_data


def save_to_xml(products_data):

    # Створюємо кореневий елемент
    channel = ET.Element("channel")
    description = ET.SubElement(channel, "description")
    description.text = "Farfetch Women's Dresses"

    # Додаємо дані про кожен товар у XML
    for product_data in products_data:
        item = ET.SubElement(channel, "item")

        # Додаємо дані про товар у вигляді дочірніх елементів
        for key, value in product_data.items():
            element = ET.SubElement(item, key)
            element.text = value

    # Створюємо об'єкт ElementTree та записуємо дані у XML файл
    tree = ET.ElementTree(channel)
    with open("Farfetch_Womens_Dresses.xml", "wb") as xml_file:
        tree.write(xml_file, encoding="utf-8", xml_declaration=True)


def main():
    try:
        load_dotenv()
        # Створюємо екземпляр веб-драйвера
        service = Service(os.getenv("SERVICE"))  # path до chromedriver
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(service=service, options=options)
        
        base_url = os.getenv("BASE_URL")


        # Завантажуємо сторінки
        for page_number in range(1, 3):  # Перебір сторінок 1 та 2
            URL = os.getenv("URL")
            url = f"{URL}?page={page_number}&view=96&sort=3"
            driver.get(url)

            # Чекаємо, доки з'явиться хоча б один елемент
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-testid="productCard"]')))

            # Прокручуємо сторінку до кінця, щоб завантажити всі товари
            scroll_page(driver)

            # Парсим дані про товари
            products_data = parse_page(driver, base_url)

            # Зберігаємо дані в XML
            save_to_xml(products_data)

    except WebDriverException as e:
        print("Помилка WebDriver:", e)
    except Exception as e:
        print("Виникла помилка:", e)
    finally:
        # Завжди закриваємо браузер після використання
        driver.quit()


if __name__ == "__main__":
    main()

