import requests
from bs4 import BeautifulSoup
from time import strftime
def get_news_source(source, url, element, class_, amount):
    news = []

    # Fetch headlines from the source
    news_response = requests.get(url)
    news_soup = BeautifulSoup(news_response.text, 'html.parser')
    news_headlines = news_soup.find_all(element, class_=class_)
    for headline in news_headlines[:amount]:
        news.append(f"{source}: {headline.get_text()}")

    return news

def format_news(news_list):
    # Get the current date and weekday
    current_date = strftime("%A, %B %d, %Y")
    
    # Start the formatted news with the date and weekday
    formatted_news = f"Daily Tech News Digest\n\n{current_date}\n\n"

    prev_news = news_list[0].split(':')[0]
    news_num = []
    count = 0
    
    for idx, news_item in enumerate(news_list, 1):
        current_news = news_item.split(':')[0]

        if current_news != prev_news or idx == len(news_list):
            formatted_news += f'\n\n{prev_news} Top {count}\n\n'

            for news in news_num:
                formatted_news += news

            count = 1
            news_num = []
            prev_news = current_news
        else:
            count += 1

        news_num += [f"{count}. {news_item.replace(current_news+': ', '')}\n"]

    return formatted_news

if __name__ == "__main__":
    fetch = [
        # ['Hacker News', 'https://news.ycombinator.com/', 'span', 'titleline', 10],
        ['TechCrunch', 'https://techcrunch.com/', 'h2', 'wp-block-post-title', 5],
        ['The Verge', 'https://www.theverge.com/', 'h2', 'leading-100', 5],
        ['Ars Technica', 'https://arstechnica.com/', 'h2', '', 5],
        ['Wired', 'https://www.wired.com/category/security/', 'h3', 'summary-item__hed', 15]
    ]

    news = []

    for source in fetch:
        news.extend(get_news_source(*source))

    formatted_news = format_news(news)
    print(formatted_news)