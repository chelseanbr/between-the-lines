import requests             
from bs4 import BeautifulSoup 
import csv                  
import webbrowser
import io

def display(content, filename='output.html'):
    with open(filename, 'wb') as f:
        f.write(content)
        webbrowser.open(filename)

def get_soup(session, url, show=False):
    r = session.get(url)
    if show:
        display(r.content, 'temp.html')

    if r.status_code != 200: # not OK
        print('[get_soup] status code:', r.status_code)
    else:
        return BeautifulSoup(r.text, 'html.parser')
    
def post_soup(session, url, params, show=False):
    '''Read HTML from server and convert to Soup'''

    r = session.post(url, data=params)
    
    if show:
        display(r.content, 'temp.html')

    if r.status_code != 200: # not OK
        print('[post_soup] status code:', r.status_code)
    else:
        return BeautifulSoup(r.text, 'html.parser')
    
def scrape(url, lang='ALL'):

    # create session to keep all cookies (etc.) between requests
    session = requests.Session()

    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
    })


    items = parse(session, url + '?filterLang=' + lang)

    return items

def parse(session, url):
    '''Get number of reviews and start getting subpages with reviews'''

    print('[parse] url:', url)

    soup = get_soup(session, url)

    if not soup:
        print('[parse] no soup:', url)
        return

    # num_reviews = soup.find('span', class_='reviews_header_count').text # get text
    num_reviews = soup.find('span', class_='hotels-hotel-review-about-with-photos-Reviews__seeAllReviews--3PpLR').text # get text
    # num_reviews = num_reviews[1:-1] 
    num_reviews = num_reviews.replace(',', '')
    num_reviews = num_reviews.replace('reviews', '')
    num_reviews = int(num_reviews) # convert text into integer
    print('[parse] num_reviews ALL:', num_reviews)

    url_template = url.replace('.html', '-or{}.html')
    # print('[parse] url_template:', url_template)

    items = []

    offset = 0

    while(True):
        subpage_url = url_template.format(offset)

        subpage_items = parse_reviews(session, subpage_url)
        if not subpage_items:
            break

        items += subpage_items

        if len(subpage_items) < 5:
            break

        offset += 5

    return items

def get_reviews_ids(soup):

    items = soup.find_all('div', attrs={'data-reviewid': True})

    if items:
        reviews_ids = [x.attrs['data-reviewid'] for x in items][::2] # mini test
        # reviews_ids = [x.attrs['data-reviewid'] for x in items][0:10000:1] # get 10,000 reviews
        # reviews_ids = [x.attrs['data-reviewid'] for x in items][::1] # get all reviews
        print('[get_reviews_ids] data-reviewid:', reviews_ids)
        return reviews_ids
    
def get_more(session, reviews_ids):

    url = 'https://www.tripadvisor.com/OverlayWidgetAjax?Mode=EXPANDED_HOTEL_REVIEWS_RESP&metaReferer=Hotel_Review'

    payload = {
        'reviews': ','.join(reviews_ids), # ie. "577882734,577547902,577300887",
        #'contextChoice': 'DETAIL_HR', # ???
        'widgetChoice': 'EXPANDED_HOTEL_REVIEW_HSX', # ???
        'haveJses': 'earlyRequireDefine,amdearly,global_error,long_lived_global,apg-Hotel_Review,apg-Hotel_Review-in,bootstrap,desktop-rooms-guests-dust-en_US,responsive-calendar-templates-dust-en_US,taevents',
        'haveCsses': 'apg-Hotel_Review-in',
        'Action': 'install',
    }

    soup = post_soup(session, url, payload)

    return soup

def parse_reviews(session, url):
    '''Get all reviews from one page'''

    print('[parse_reviews] url:', url)

    soup =  get_soup(session, url)

    if not soup:
        print('[parse_reviews] no soup:', url)
        return

    hotel_name = soup.find('h1', id='HEADING').text

    reviews_ids = get_reviews_ids(soup)
    if not reviews_ids:
        return

    soup = get_more(session, reviews_ids)

    if not soup:
        print('[parse_reviews] no soup:', url)
        return

    items = []

    for idx, review in enumerate(soup.find_all('div', class_='reviewSelector')):
        try:
            badgets = review.find_all('span', class_='badgetext')
            # print(badgets)
            if len(badgets) > 0:
                contributions = badgets[0].text
            else:
                contributions = '0'

            if len(badgets) > 1:
                helpful_vote = badgets[1].text
            else:
                helpful_vote = '0'
            user_loc = review.select_one('div.userLoc strong')
            if user_loc:
                user_loc = user_loc.text
            else:
                user_loc = ''
                
            bubble_rating = review.select_one('span.ui_bubble_rating')['class']
            bubble_rating = int(bubble_rating[1].split('_')[-1])/10
            # print(bubble_rating)

            review_id = reviews_ids[idx]

            item = {
                'hotel_name': hotel_name,
                'review_body': review.find('p', class_='partial_entry').text,
                'review_date': review.find('span', class_='ratingDate')['title'], # 'ratingDate' instead of 'relativeDate'
                'rating': bubble_rating,
                # 'contributions': contributions,
                'helpful_vote': helpful_vote,
                'user_location': user_loc,
                'review_id': review_id,
                'url': url
            }

            items.append(item)
            # print('\n--- review ---\n')
            # for key,val in item.items():
            #     print(' ', key, ':', val)

        except:
            print("Something went wrong with review #" + review_id)
            continue

    print()

    return items

def write_in_csv(items, filename='results.csv',
                  headers=['review id', 'hotel name', 'review title', 'review body',
                           'review date', 'contributions', 'helpful vote',
                           'user name' , 'user location', 'rating', 'url'],
                  mode='w'):

    print('--- CSV ---')

    with io.open(filename, mode, encoding="utf-8") as csvfile:
        csv_file = csv.DictWriter(csvfile, headers)

        if mode == 'w':
            csv_file.writeheader()

        csv_file.writerows(items)

def main(start_urls, pg):
    DB_COLUMN0  = 'review_id'
    DB_COLUMN1  = 'url'
    DB_COLUMN2 = 'hotel_name'
    DB_COLUMN3 = 'review_date'
    DB_COLUMN4 = 'review_body'
    DB_COLUMN5 = 'user_location'
    # DB_COLUMN6 = 'contributions'
    DB_COLUMN7 = 'helpful_vote'
    DB_COLUMN8 = 'rating'

    start_urls = start_urls

    lang = 'en'

    headers = [ 
        DB_COLUMN0,
        DB_COLUMN1, 
        DB_COLUMN2, 
        DB_COLUMN3,
        DB_COLUMN4,
        DB_COLUMN5,
        # DB_COLUMN6,
        DB_COLUMN7,
        DB_COLUMN8
    ]

    for url in start_urls:
        try:
            # get all reviews for 'url' and 'lang'
            items = scrape(url, lang)

            if not items:
                print('No reviews')
            else:
                # write in CSV
                filename = url.split('Reviews-')[1][:-5] + '__' + lang
                print('filename:', filename)

                # file_dir = '../data/web_scraped/'
                # file_dir = 'data/web_scraped/aws/' + pg + '/'
                file_dir = 'data/web_scraped/aws_test/' + pg +'/'

                write_in_csv(items, file_dir + filename + '.csv', headers, mode='w')
        except:
            print("Something went wrong with " + url)
            continue


if __name__ == "__main__":
    # start_urls = ['https://www.tripadvisor.ca/Hotel_Review-g60982-d87016-Reviews-Hilton_Hawaiian_Village_Waikiki_Beach_Resort-Honolulu_Oahu_Hawaii.html',\
    #     'https://www.tripadvisor.com/Hotel_Review-g60982-d224616-Reviews-Hilton_Grand_Vacations_at_Hilton_Hawaiian_Village-Honolulu_Oahu_Hawaii.html']    
    # main(start_urls)

    # Tokyo pg1
    start_urls_pg1 = ['https://www.tripadvisor.com/Hotel_Review-g14129734-d18854227-Reviews-The_Lively_Azabujuban_Tokyo-Azabujuban_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066444-d585204-Reviews-Mandarin_Oriental_Tokyo-Chuo_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129743-d634263-Reviews-The_Ritz_Carlton_Tokyo-Akasaka_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129528-d310308-Reviews-The_Tokyo_Station_Hotel-Marunouchi_Chiyoda_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129536-d580687-Reviews-The_Peninsula_Tokyo-Yurakucho_Chiyoda_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129647-d6485175-Reviews-Andaz_Tokyo_Toranomon_Hills-Toranomon_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066461-d19392762-Reviews-Prostyle_Ryokan_Tokyo_Asakusa-Taito_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129735-d306610-Reviews-Grand_Hyatt_Tokyo-Roppongi_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066454-d2703580-Reviews-First_Cabin_Haneda_Terminal_1-Ota_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066444-d19501481-Reviews-Hotel_K5-Chuo_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129528-d301911-Reviews-Four_Seasons_Hotel_Tokyo_at_Marunouchi-Marunouchi_Chiyoda_Tokyo_Tokyo_Prefecture_Kant.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129730-d579136-Reviews-The_Prince_Park_Tower_Tokyo-Shibakoen_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129477-d12158513-Reviews-Ascott_Marunouchi_Tokyo-Otemachi_Chiyoda_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066451-d10234426-Reviews-Hotel_Allamanda_Aoyama-Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066451-d571809-Reviews-Conrad_Tokyo-Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129743-d300459-Reviews-ANA_InterContinental_Tokyo-Akasaka_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066456-d14212238-Reviews-Shibuya_Stream_Excel_Hotel_Tokyu-Shibuya_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14133667-d4994810-Reviews-Shinjuku_Granbell_Hotel-Kabukicho_Shinjuku_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129730-d301389-Reviews-Tokyo_Prince_Hotel-Shibakoen_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066443-d17667937-Reviews-Reyado_Hotel_Kudan-Chiyoda_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066458-d10082928-Reviews-BnA_HOTEL_Koenji-Suginami_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066854-d498905-Reviews-Tokyo_Marriott_Hotel-Shinagawa_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066444-d14132415-Reviews-Mitsui_Garden_Hotel_Nihonbashi_Premier-Chuo_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066443-d3676666-Reviews-Hotel_New_Otani_Garden_Tower-Chiyoda_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066451-d307378-Reviews-The_Royal_Park_Hotel_Iconic_Tokyo_Shiodome-Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14131019-d301356-Reviews-Grand_Prince_Hotel_New_Takanawa-Takanawa_Minato_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066456-d630480-Reviews-Shibuya_Granbell_hotel-Shibuya_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g1066456-d479494-Reviews-Shibuya_Tokyu_REI_Hotel-Shibuya_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14133659-d1486443-Reviews-Hotel_Keihan_Tokyo_Yotsuya-Yotsuya_Shinjuku_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14133667-d1083512-Reviews-Premier_Hotel_CABIN_Shinjuku-Kabukicho_Shinjuku_Tokyo_Tokyo_Prefecture_Kanto.html'\
        'https://www.tripadvisor.com/Hotel_Review-g1066444-d1183414-Reviews-Hotel_Villa_Fontaine_Tokyo_Hatchobori-Chuo_Tokyo_Tokyo_Prefecture_Kanto.html',\
        'https://www.tripadvisor.com/Hotel_Review-g14129477-d7371377-Reviews-Aman_Tokyo-Otemachi_Chiyoda_Tokyo_Tokyo_Prefecture_Kanto.html'\
        ]
    
    # # Tokyo pg2
    # start_urls_pg2 = ['',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     ''\
    #     ]

    # New York pg1
    start_urls_pg3 = ['https://www.tripadvisor.com/Hotel_Review-g60763-d223023-Reviews-Hudson_New_York-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d93358-Reviews-Pod_51_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d281071-Reviews-Mandarin_Oriental_New_York-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d113298-Reviews-Four_Seasons_Hotel_New_York-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d1572980-Reviews-Crosby_Street_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d224224-Reviews-The_Ritz_Carlton_New_York_Central_Park-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d3533197-Reviews-Hyatt_Union_Square_New_York-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d10846801-Reviews-The_Whitby_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d113311-Reviews-The_Peninsula_New_York-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d1462005-Reviews-W_New_York_Downtown-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d14095381-Reviews-Moxy_NYC_Downtown-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d220243-Reviews-W_New_York_Union_Square-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d93452-Reviews-LUXE_Life_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d93383-Reviews-6_Columbus_Central_Park_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d4232686-Reviews-Le_Meridien_New_York_Central_Park-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d93475-Reviews-New_York_Marriott_East_Side-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d611947-Reviews-New_York_Hilton_Midtown-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d1601249-Reviews-Hilton_New_York_Fashion_District-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d6701149-Reviews-Midtown_West_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d2151571-Reviews-Selina_Chelsea-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d1164645-Reviews-Eurostars_Wall_Street-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d93334-Reviews-Excelsior_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d93374-Reviews-Off_Soho_Suites-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d4283443-Reviews-The_High_Line_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d93401-Reviews-Heritage_Hotel_New_York_City-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d1500405-Reviews-Hampton_Inn_Manhattan_Times_Square_South-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d7595213-Reviews-Four_Points_by_Sheraton_New_York_Downtown-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d1783324-Reviews-Sheraton_Tribeca_New_York_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d596200-Reviews-Hudson_River_Hotel-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d75737-Reviews-Night_Theater_District-New_York_City_New_York.html'\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d7891458-Reviews-Arlo_SoHo-New_York_City_New_York.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60763-d249710-Reviews-Morningside_Inn-New_York_City_New_York.html'\
        ]

    # # New York pg2
    # start_urls_pg4 = ['',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     ''\
    # ]

    # url_pgs = [start_urls_pg1, start_urls_pg2, start_urls_pg3, start_urls_pg4]
    # pgs = ['pg1', 'pg2', 'pg3', 'pg4']

    url_pgs = [start_urls_pg1, start_urls_pg3]
    pgs = ['pg1', 'pg3']

    # #test
    # url_pgs = [start_urls_pg4, start_urls_pg3, start_urls_pg4]
    # pgs = ['pg4', 'pg3', 'pg4'] 
    # #test

    for url_pg, pg in zip(url_pgs, pgs):
        print(pg)
        try:
            main(url_pg, pg)
        except:
            print("Something went wrong with " + pg)
            continue

    # start_urls_pg5 = ['',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     ''\
    #     ]
    
    # start_urls_pg6 = ['',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     '',\
    #     ''\
    #     ]