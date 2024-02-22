from scraper_jd import JDScraper
from scraper_taobao import TaobaoScraper


test_data = [
    {"product1": "西班牙风味香肠500g", "product2": "丹麦皇冠西班牙风味香肠500g", "is_same": True},
    {"product1": "西班牙风味香肠500g", "product2": "香肠500g", "is_same": False},
    {"product1": "西班牙风味香肠500g", "product2": "幕尼黑风味白肠500g", "is_same": False},
    {"product1": "丹麦皇冠西班牙风味香肠500g", "product2": "丹麦皇冠幕尼黑风味白肠500g", "is_same": False},
    {"product1": "丹麦皇冠西班牙风味香肠500g", "product2": "丹麦皇冠西班牙风味香肠350g", "is_same": False},
    {"product1": "丹麦皇冠西班牙风味香肠500g", "product2": "西班牙风味香肠", "is_same": False},
    {"product1": "丹麦皇冠西班牙风味香肠500g", "product2": "丹麦皇冠西班牙风味香肠", "is_same": False},
    {"product1": "丹麦皇冠西班牙风味香肠500g", "product2": "西班牙香肠500g", "is_same": True},
    {"product1": "丹麦皇冠西班牙风味香肠500g", "product2": "丹麦皇冠西班牙香肠500g", "is_same": True},
    {"product1": "西班牙风味香肠500g", "product2": "西班牙风味白肠500g", "is_same": False}
]


if __name__ == "__main__":
    scraper = TaobaoScraper(products_limit=10, sleep_time=1)
    correct = 0
    for data in test_data:
        score = scraper.check_name_matching_gpt(data["product1"], data["product2"])
        if score == data['is_same']:
            correct += 1
        print(f'{data["product1"]} - {data["product2"]} | gpt: {score} | real: {data["is_same"]}')
    print(f'Correct {correct}/{len(test_data)}')
