import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import VallenewsItem
from itemloaders.processors import TakeFirst
import requests
import json
from scrapy import Selector

pattern = r'(\xa0)?'

url = "https://vallbanc.ad/en/views/ajax?_wrapper_format=drupal_ajax"

payload="view_name=news&view_display_id=page_news&view_args=&view_path=%2Fnews&view_base_path=news&view_dom_id=4733a1e7529760920c7af9b81e9e89f5f070c6d97858f32a2d9d236016a539dd&pager_element=0&page={}&_drupal_ajax=1&ajax_page_state%5Btheme%5D=vallbanc&ajax_page_state%5Btheme_token%5D=&ajax_page_state%5Blibraries%5D=core%2Fhtml5shiv%2Ceu_cookie_compliance%2Feu_cookie_compliance_default%2Clang_dropdown%2Flang-dropdown-form%2Csystem%2Fbase%2Cvallbanc%2Fglobal-scripts%2Cvallbanc%2Fglobal-styling%2Cvallbanc%2Fhead-scripts%2Cvallbanc%2Fview-scripts%2Cviews%2Fviews.ajax%2Cviews%2Fviews.module%2Cviews_infinite_scroll%2Fviews-infinite-scroll"
headers = {
  'Connection': 'keep-alive',
  'Pragma': 'no-cache',
  'Cache-Control': 'no-cache',
  'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
  'Accept': 'application/json, text/javascript, */*; q=0.01',
  'X-Requested-With': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': 'https://vallbanc.ad',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Dest': 'empty',
  'Referer': 'https://vallbanc.ad/en/news',
  'Accept-Language': 'en-US,en;q=0.9',
  'Cookie': 'cookie-agreed-version=1.0.0; cookie-agreed=2; _ga=GA1.2.742929110.1612168163; languagevb=1; _gid=GA1.2.1345886951.1615803864; TS010ff5de=0114ef075f90e04f1e532b765cdf3e23277c774a6ca2badf746f1f6e1f071bfd47bfa348ca9d2542fbfb12ebc960c86b1f3340e66d; _gat_UA-72467931-1=1; TS010ff5de=0114ef075f90e04f1e532b765cdf3e23277c774a6ca2badf746f1f6e1f071bfd47bfa348ca9d2542fbfb12ebc960c86b1f3340e66d'
}

class VallenewsSpider(scrapy.Spider):
	name = 'vallenews'
	start_urls = ['https://vallbanc.ad/en/news']
	page = 0
	def parse(self, response):
		data = requests.request("POST", url, headers=headers, data=payload.format(self.page), verify = False)
		data = json.loads(data.text)
		try:
			container = data[2]['data']
		except IndexError:
			container = data[1]['data']
		articles = Selector(text= container).xpath('//div[@class="article-teaser__content"]')

		for article in articles:
			date = article.xpath('.//div[@class="article-teaser__date"]/text()').get().strip()
			link = article.xpath('.//div[@class="article-teaser__cta"]/a/@href').get()
			yield response.follow(link, self.parse_post, cb_kwargs=dict(date=date))

		if not any('September 2016' in text for text in Selector(text=container).xpath('//div[@class="article-teaser__date"]/text()').getall()):
			self.page += 1
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response, date):
		title = response.xpath('(//span[@property="schema:name"])[1]/text()').get()
		content = response.xpath('//div[@class="node-article__body"]//text()').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=VallenewsItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
