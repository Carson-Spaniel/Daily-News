import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import strftime
from secret import API_KEY, TOKEN, QUOTE_API, GMAIL_USER, GMAIL_KEY, RECIPIENTS
from bs4 import BeautifulSoup
import requests

def get_news_source(source, url, element, class_, amount, excludes=[]):
    news = []

    # Fetch headlines from the source
    news_response = requests.get(url)
    news_soup = BeautifulSoup(news_response.text, 'html.parser')
    news_headlines = news_soup.find_all(element, class_=class_)

    for headline in news_headlines:
        if len(excludes):
            for ex_element, ex_class in excludes:
                exclusion = headline.find(ex_element, class_=ex_class)
                if exclusion:
                    exclusion.decompose()
        link = headline.find('a')['href'] if headline.find('a') else url
        if link.startswith('/'):
            link = url + link
        if (source, headline.get_text(), link) not in news:
            news.append((source, headline.get_text(), link))
        if len(news) == amount:
            break

    return news

def get_public_ip():
    # Fetch public IP using ipinfo.io
    response = requests.get('https://ipinfo.io')
    data = response.json()
    return data.get('ip')

def get_weather(api_key):
    ip_address = get_public_ip()
    url = f'https://ipinfo.io/{ip_address}?token={TOKEN}'
    response = requests.get(url)
    data = response.json()

    if 'city' in data:
        city = data['city']
        region = data['region']
        lat, lon = data['loc'].split(',')
        weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        weather_response = requests.get(weather_url)

        weather_data = weather_response.json()

        if weather_data['cod'] == 200:
            weather_description = weather_data['weather'][0]['description'].title()
            temp_celsius = weather_data['main']['temp']
            temp_fahrenheit = round(temp_celsius * 9/5 + 32, 1)
            temp_feels_like_celsius = weather_data['main']['feels_like']
            temp_feels_like_fahrenheit = round(temp_feels_like_celsius * 9/5 + 32, 1)
            wind_speed_mps = weather_data['wind']['speed']
            wind_speed_mph = round(wind_speed_mps * 2.237, 1)  # Convert m/s to mph
            return f"{city}, {region}: {weather_description}, {temp_feels_like_fahrenheit}°F, {wind_speed_mph} mph\n"
        else:
            return "Failed to fetch weather information"
    else:
        return "Failed to determine location"

def get_daily_quote(api_key):
    url = f'http://quotes.rest/qod.json?api_key={api_key}'
    response = requests.get(url)
    data = response.json()

    if 'contents' in data and 'quotes' in data['contents']:
        quote = data['contents']['quotes'][0]['quote']
        author = data['contents']['quotes'][0]['author']
        return f'"{quote}" - {author}'
    else:
        print(data)
        return "Good morning. Let's have a great day."

def format_news(news_list):
    # Get the current date and weekday
    current_date = strftime(" %I:%M %p %A, %B %d, %Y")
    weather_info = get_weather(API_KEY)  # Fetch detailed weather information
    daily_quote = get_daily_quote(QUOTE_API)
    
    # Start the formatted news with the date and weekday
    formatted_news = f"""
    <html>
        <head>
            <style>
                body, div.main {{
                    font-family: 'Courier New', Monospace;
                    line-height: 1.6;
                    background-color: #f0f2f5; /* Lighter background */
                    margin: 0;
                    padding: 20px;
                    color: #1f2937; /* Darker text color */
                    max-width: 800px;
                    margin: 0 auto;
                }}
                h1 {{
                    color: #1f2937; /* Darker heading color */
                    text-align: center;
                    margin-bottom: 20px;
                    font-size: 2.5em;
                    text-transform: uppercase;
                }}
                p {{
                    color: #1f2937; /* Darker paragraph text color */
                    text-align: center;
                    margin-bottom: 10px;
                }}
                .quote {{
                    font-style: italic;
                    text-align: center;
                    margin-bottom: 30px;
                    color: #4a5568; /* Slightly darker quote text */
                }}
                .weather {{
                    font-weight: bold;
                    color: #007bff; /* Accent color */
                    text-align: center;
                    white-space: pre-line; /* Maintain line breaks in <p> */
                }}
                ul {{
                    list-style-type: none;
                    padding-left: 0;
                    margin-top: 10px;
                }}
                li {{
                    margin-bottom: 10px;
                    padding: 10px;
                    background-color: #e2e8f0; /* Lighter background for list items */
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                a {{
                    color: #007bff; /* Accent color for links */
                    text-decoration: none;
                    font-weight: bold;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="main">
                <h1>Daily_Newsletter</h1>
                <h2 class="weather">{current_date}</h2>
                <p class="weather">{weather_info}</p>
                <p class="quote">{daily_quote}</p>
                <ul>
    """

    prev_news = news_list[0][0]
    news_num = []
    count = 0
    
    for idx, news_item in enumerate(news_list, 1):
        current_news = news_item[0]

        if current_news != prev_news or idx == len(news_list):
            formatted_news += f'<h2>Latest from {prev_news}</h2><ul>'

            for news in news_num:
                formatted_news += news

            formatted_news += '</ul>'

            count = 1
            news_num = []
            prev_news = current_news
        else:
            count += 1

        news_num += [f"<a href='{news_item[2]}' target='_blank'><li>{count-1}. {news_item[1]}</li></a>"]

    formatted_news += "</ul></div></body></html>"

    return formatted_news

def send_email(html_content):
    # Email information
    sender_email = GMAIL_USER
    sender_password = GMAIL_KEY
    receiver_email = RECIPIENTS
    subject = "Daily_Newsletter"

    # Setup the MIME
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Attach HTML content to the email
    message.attach(MIMEText(html_content, "html"))

    # Connect to SMTP server and send email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")

if __name__ == "__main__":
    amount = 10

    fetch = [
        ['Engadget', 'https://www.engadget.com', 'h2', 'My(0)', amount],
        ['TechCrunch', 'https://techcrunch.com/', 'h2', 'wp-block-post-title', amount],
        ['Gizmodo', 'https://gizmodo.com/latest', 'div', 'flex-1 self-center w-full', amount, [['div', 'hidden sm:block'],['p','mt-2 line-clamp-3 sm:line-clamp-2 font-serif xs:text-lg text-ellipsis break-words'],['div','mt-3 text-sm sm:text-base']]],
        ['Ars Technica', 'https://arstechnica.com/', 'h2', '', amount],
        ['Mashable', 'https://mashable.com', 'div', 'flex flex-col flex-wrap mr-4 w-3/4 text-left md:mt-0 xl:relative items-around', amount, [['div', 'hidden text-base md:block md:mt-1 md:leading-tight text-primary-400 font-regular'],['div', 'flex flex-row mt-3 font-serif italic md:justify-start']]],
    ]

    news = []

    for i, source in enumerate(fetch):
        if i == len(fetch)-1:
            source[4] += 1
        try:
            news.extend(get_news_source(*source))
        except:
            pass

    formatted_news = format_news(news)

    with open('newsletter.html', 'w') as news:
        news.write(formatted_news)
    
    send_email(formatted_news)
