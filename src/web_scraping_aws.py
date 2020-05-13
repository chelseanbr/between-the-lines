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
        # reviews_ids = [x.attrs['data-reviewid'] for x in items][::2] # mini test
        # reviews_ids = [x.attrs['data-reviewid'] for x in items][0:10000:1] # get 10,000 reviews
        reviews_ids = [x.attrs['data-reviewid'] for x in items][::1] # get all reviews
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
                file_dir = 'data/web_scraped/aws/' + pg + '/'
                # file_dir = 'data/web_scraped/aws_test/' + pg +'/'

                write_in_csv(items, file_dir + filename + '.csv', headers, mode='w')
        except:
            print("Something went wrong with " + url)
            continue


if __name__ == "__main__":
    # start_urls = ['https://www.tripadvisor.ca/Hotel_Review-g60982-d87016-Reviews-Hilton_Hawaiian_Village_Waikiki_Beach_Resort-Honolulu_Oahu_Hawaii.html',\
    #     'https://www.tripadvisor.com/Hotel_Review-g60982-d224616-Reviews-Hilton_Grand_Vacations_at_Hilton_Hawaiian_Village-Honolulu_Oahu_Hawaii.html']    
    # main(start_urls)

    start_urls_pg1 = ['https://www.tripadvisor.ca/Hotel_Review-g60982-d87016-Reviews-Hilton_Hawaiian_Village_Waikiki_Beach_Resort-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d209422-Reviews-Hilton_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d114024-Reviews-The_Royal_Hawaiian_a_Luxury_Collection_Resort_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d224616-Reviews-Hilton_Grand_Vacations_at_Hilton_Hawaiian_Village-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d114026-Reviews-Halepuna_Waikiki_by_Halekulani-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86957-Reviews-Ala_Moana_Honolulu_by_Mantra-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d114031-Reviews-Waikiki_Beachcomber_by_Outrigger-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d4020497-Reviews-Vive_Hotel_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d2555768-Reviews-Shoreline_Hotel_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86969-Reviews-The_Laylow_Autograph_Collection-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86954-Reviews-The_Polynesian_Residences_Hotel_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d219292-Reviews-Courtyard_by_Marriott_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86951-Reviews-The_New_Otani_Kaimana_Beach_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d12077161-Reviews-Holiday_Inn_Express_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87149-Reviews-Waikiki_Sand_Villa_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87035-Reviews-Manoa_Valley_Inn-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87008-Reviews-The_Equus-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86984-Reviews-Aston_Waikiki_Circle_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d90017-Reviews-DoubleTree_by_Hilton_Alana_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87018-Reviews-Ramada_Plaza_by_Wyndham_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86978-Reviews-Aston_Waikiki_Beach_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d114027-Reviews-Ambassador_Hotel_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87104-Reviews-Sheraton_Princess_Kaiulani-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d214685-Reviews-OHANA_Waikiki_Malia_by_Outrigger-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d114010-Reviews-Aston_at_the_Executive_Centre_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d559726-Reviews-Aqua_Palms_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87025-Reviews-The_Imperial_Hawaii_Resort-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86961-Reviews-Aston_at_the_Waikiki_Banyan-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87015-Reviews-Waikiki_Monarch_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86983-Reviews-Espacio_The_Jewel_of_Waikiki-Honolulu_Oahu_Hawaii.html'\
        ]

    start_urls_pg2 = ['https://www.tripadvisor.com/Hotel_Review-g60982-d10229548-Reviews-The_Ritz_Carlton_Residences-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d1818106-Reviews-The_Modern_Honolulu-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87040-Reviews-Hyatt_Place_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87095-Reviews-Queen_Kapiolani_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87052-Reviews-Outrigger_Reef_Waikiki_Beach_Resort-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87108-Reviews-Sheraton_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d214683-Reviews-Waikiki_Beach_Marriott_Resort_Spa-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d1484551-Reviews-Trump_International_Hotel_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d90108-Reviews-Lotus_Honolulu_at_Diamond_Head-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d209424-Reviews-Ilikai_Hotel_Luxury_Suites-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d10728599-Reviews-Hyatt_Centric_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d227765-Reviews-The_Surfjack_Hotel_Swim_Club-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d214680-Reviews-Park_Shore_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87111-Reviews-Alohilani_Resort_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87017-Reviews-Airport_Honolulu_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87024-Reviews-Ilima_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86966-Reviews-Coconut_Waikiki_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d2385826-Reviews-Stay_Hotel_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86973-Reviews-Pacific_Monarch_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d534764-Reviews-Waikiki_Resort_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86970-Reviews-Pearl_Hotel_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87031-Reviews-Aqua_Bamboo_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87091-Reviews-Pacific_Marina_Inn-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86959-Reviews-Aqua_Aloha_Surf_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d2202220-Reviews-White_Sands_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87039-Reviews-Marine_Surf_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86952-Reviews-Waikiki_Beachside_Hostel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d3686316-Reviews-The_Beach_Waikiki_Boutique_Hostel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87097-Reviews-Royal_Grove_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86988-Reviews-Aqua_Oasis-Honolulu_Oahu_Hawaii.html'\
        ]

    start_urls_pg3 = ['https://www.tripadvisor.com/Hotel_Review-g60982-d120684-Reviews-Outrigger_Waikiki_Beach_Resort-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87011-Reviews-Prince_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d90015-Reviews-Halekulani_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87119-Reviews-Hotel_LaCroix-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d15610197-Reviews-Real_Select_Vacations_at_The_Ritz_Carlton_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d225459-Reviews-Aston_Waikiki_Beach_Tower-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d17724495-Reviews-Pagoda_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d242435-Reviews-Hyatt_Regency_Waikiki_Beach_Resort_Spa-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d114008-Reviews-The_Kahala_Hotel_Resort-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d615153-Reviews-Embassy_Suites_By_Hilton_Waikiki_Beach_Walk-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87102-Reviews-Moana_Surfrider_A_Westin_Resort_Spa_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d4604031-Reviews-Hokulani_Waikiki_by_Hilton_Grand_Vacations-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d14124537-Reviews-Ilikai_Lite-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d13912965-Reviews-Paniolo_at_the_Equus-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87090-Reviews-Hilton_Garden_Inn_Waikiki_Beach-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d79500-Reviews-Best_Western_The_Plaza_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d596760-Reviews-Hotel_Renew-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87147-Reviews-Waikiki_Central_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d87092-Reviews-Pagoda_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d14100457-Reviews-OHANA_Waikiki_East_by_Outrigger-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d120687-Reviews-Ewa_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d214688-Reviews-Luana_Waikiki_Hotel_Suites-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d86953-Reviews-Holiday_Surf_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d8423429-Reviews-Stay_Condominiums_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d3635742-Reviews-Marina_Tower_Waikiki-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d208960-Reviews-Castle_Waikiki_Grand_Hotel-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d90159-Reviews-Aqua_Skyline_at_Island_Colony-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d15689141-Reviews-Waikiki_Studio-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d8429471-Reviews-Aqua_Ohia_Waikiki_Studio_Suites-Honolulu_Oahu_Hawaii.html',\
        'https://www.tripadvisor.com/Hotel_Review-g60982-d1567958-Reviews-Kuhio_Banyan_Club-Honolulu_Oahu_Hawaii.html'\
        ]

    start_urls_pg4 = ['https://www.tripadvisor.com/Hotel_Review-g60982-d1199673-Reviews-Grand_Waikikian_by_Hilton_Grand_Vacations-Honolulu_Oahu_Hawaii.html']
    
    url_pgs = [start_urls_pg1, start_urls_pg2, start_urls_pg3, start_urls_pg4]
    pgs = ['pg1', 'pg2', 'pg3', 'pg4']

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
    # main(start_urls_pg5, 'pg5')

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
    # main(start_urls_pg6, 'pg6')