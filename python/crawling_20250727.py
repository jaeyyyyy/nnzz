from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import time
import pandas as pd


# 왼쪽 프레임으로 전환
def switch_left():
    driver.switch_to.parent_frame()
    # implicitly_wait로 못잡길래 아래처럼 변경
    iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="searchIframe"]')))
    driver.switch_to.frame(iframe)


# 오른쪽 프레임으로 전환
def switch_right():
    driver.switch_to.parent_frame()
    try:
        # implicitly_wait로 못잡길래 아래처럼 변경
        iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]')))
        driver.switch_to.frame(iframe)
    except Exception as e:
        iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]')))
        driver.switch_to.frame(iframe)


# 영업시간 추출
def find_business_hours():
    try:
        # 영업시간 더보기 버튼 찾기
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="y6tNq"]/span'))
        ).click()

        # 영업 시간 더보기 버튼을 누르고 부모요소 발견될때까지 기다림
        parent_element = WebDriverWait(driver, 1).until(
            EC.visibility_of_element_located((By.XPATH, '//a[@class="gKP9i RMgN0"]'))
        )

        # 부모요소 발견되면 자식요소 찾기(영업종료 / 영업 중 - 운영시간 00 에 영업 시작은 제외)
        child_elements = parent_element.find_elements(By.XPATH,
                                                      './*[contains(@class, "w9QyJ")][position() > 1]')

        for child in child_elements:
            # 각 자식 요소 내에서 div 안에 있으며, 클래스가 'A_cdD'인 요소 찾기
            span_elements = child.find_elements(By.XPATH, './div/*[@class="A_cdD"]')

            # 찾은 span 요소들의 텍스트 출력
            for span in span_elements:
                text = span.text
                if text and (store_name not in text) and ('접기' not in text):  # 비어있지 않고 store_name이나 '접기'를 포함하지 않는 경우
                    business_hours.append(text)
    except Exception as e:
        pass  # 영업시간 정보가 없는 경우


# 안전한 요소 텍스트 추출
def safe_get_text(element, xpath_or_class, by_type="xpath", default=""):
    try:
        if by_type == "xpath":
            return element.find_element(By.XPATH, xpath_or_class).text
        elif by_type == "class":
            return element.find_element(By.CLASS_NAME, xpath_or_class).text
        elif by_type == "css":
            return element.find_element(By.CSS_SELECTOR, xpath_or_class).text
    except Exception:
        return default


# 브라우저 옵션
options = Options()
service = Service()
options.add_experimental_option("detach", True)  # 꺼짐 방지 옵션
options.add_argument("disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--user-data-dir:C:/Work/cache")
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")
options.add_argument('--incognito')

# 크롬 드라이버 실행
driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()
# 반복 종료 조건
loop = True

# 네이버 지도 로드
URL = 'https://map.naver.com/search/광장동 맛집'
driver.get(URL)
# 10초 안에 웹 페이지를 로드하면 바로 넘어가거나, 10초를 기다림
driver.implicitly_wait(10)

# 가게 정보 리스트 초기화
stores = []
# 첫 번째 저장 여부를 추적하는 변수
is_first_save = True

div = '//*[@id="app-root"]/div/div[3]/div[2]/'

franchise_values = ['스타벅스', '메가MGC', '메가커피', '할리스', '커피빈', '폴 바셋', '카페베네', '엔제리너스', '엔젤리너스', '투썸', '파스쿠찌', '빽다방',
                    '바나프레소', '이디야', '컴포즈', '더벤티', '더리터', '하이오커피', '오슬로우', '스무디킹', '탐앤탐스', '하삼동커피', '아마스빈',
                    '파리바게뜨', '파리바게트', '뚜레쥬르', '파리크라상',
                    '배스킨라빈스', '요거트아이스크림의정석', '요아정', '백미당', '설빙', '마이요거트립', '요거프레소', '요거트월드',
                    '블루보틀', '테라로사', '팀홀튼', '아티제', '커스텀커피', '오설록', '고망고',
                    '텐퍼센트', '커피에반하다', '커피사피엔스', '봉명동내커피',
                    '디저트39', '공차', '쥬씨', '매머드커피', '매머드익스프레스', '팔공티', '카페인중독', '키쉬미뇽', '아메리칸트레일러', '카페인24', '카페일분',
                    '자연드림', '카페게이트', '데이롱',
                    '카페만월경', '카페 만월경', '나이스카페인클럽', '쉬즈베이글', '우지커피', '백억커피',
                    '준코', '타코야끼', '타코야키', '마리웨일', '메이드카페', '무인카페', '밥스토랑',
                    '꽈배기', '호두과자', '요거트', '복호두', '무인 ', '커피베이']

not_category_values = [
    '아이스크림', '빙수', '밀키트', '테이크아웃커피', '라이브카페', '스터디카페', '북카페',
    '단란주점', '유흥주점', '푸드트럭', '프랜차이즈본사', '다방', '과일,주스전문점'
]

# 정규 표현식 패턴 생성
franchise_pattern = re.compile('|'.join(franchise_values), re.IGNORECASE)

while (loop):
    # searchIframe 으로 프레임 변경
    switch_left()

    try:
        # 다음 페이지 true, false 여부 확인
        next_page = driver.find_element(By.XPATH, div + 'a[7]').get_attribute('aria-disabled')
        print("next_page 값 :" + str(next_page))
    except Exception as e:
        div = '//*[@id="app-root"]/div/div[2]/div[2]/'
        next_page = driver.find_element(By.XPATH, div + 'a[7]').get_attribute('aria-disabled')
        print("next_page 값 :" + str(next_page))

    # 현재 page 숫자 가져오기
    page_no = driver.find_element(By.XPATH, '//a[contains(@class, "mBN2s qxokY")]').text

    if page_no == '3':
        # 드라이버 끄고
        driver.quit()
        # 드라이버 초기화
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        # 네이버 지도 다시 로드
        driver.get(URL)
        # 10초 안에 웹 페이지를 로드하면 바로 넘어가거나, 10초를 기다림
        driver.implicitly_wait(10)
        switch_left()
        # 3 페이지를 클릭합니다.
        driver.find_element(By.XPATH, div + 'a[4]').click()
        print("3 페이지를 진행합니다.")
        page_no = driver.find_element(By.XPATH, '//a[contains(@class, "mBN2s qxokY")]').text

    # 맨 밑까지 스크롤
    scrollable_element = driver.find_element(By.XPATH, '//*[@id="_pcmap_list_scroll_container"]')  # 스크롤 컨테이너 찾기
    last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_element)
    while True:
        # 요소 내에서 아래로 650px 스크롤
        driver.execute_script("arguments[0].scrollTop += 650;", scrollable_element)
        # 페이지 로드를 기다림
        time.sleep(1)
        # 새 높이 계산
        new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_element)
        # 스크롤이 더 이상 늘어나지 않으면 루프 종료
        if new_height == last_height:
            break
        last_height = new_height

    # 현재 페이지에 등록된 모든 가게들 중에 사진이 등록된 가게들만 조회
    restaurant_elements = driver.find_elements(
        By.XPATH,
        '//*[@id="_pcmap_list_scroll_container"]//li[@data-laim-exp-id="undefinedundefined" and count(div) > 2]'
    )
    # 페이지당 70개 정도의 가게가 출력됨
    print('현재 ' + str(page_no) + ' 페이지, ' + '총 ' + str(len(restaurant_elements)) + '개의 가게를 찾았습니다.')
    switch_left()

    # 뽑아놓은 elements 들 반복해서 돌기
    for index, e in enumerate(restaurant_elements, start=1):
        store_name = ''  # 가게 이름
        category = ''  # 카테고리
        store_id = ''  # 가게 고유 번호
        address = ''  # 가게 주소
        amenity = ''  # 편의
        option = ''  # 미쉐린, 착한 가게
        business_hours = []  # 영업 시간
        broadcast = []  # 방송
        menu = []  # 메뉴
        tel = ''  # 전화번호

        try:
            switch_left()  # 다시 왼쪽 프레임으로 돌아와야 함
            e.find_element(By.XPATH, './div[@class="CHC5F"]').find_element(By.XPATH, './div[@class="bSoi3"]/a').click()
            driver.implicitly_wait(3)
            switch_right()
            driver.implicitly_wait(3)

            # 여기부터 크롤링 시작
            # 제목 표시되는 부분
            title = None
            try:
                title = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="zD5Nm undefined"]'))
                )
            except Exception as e:
                print(f"{index}번째 가게 - 타이틀 추출 실패 첫 시도: {str(e)}")
                time.sleep(2)
                try:
                    title = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@class="zD5Nm undefined"]'))
                    )
                except Exception as e:
                    print(f"{index}번째 가게 - 타이틀 추출 실패 두 번째 시도, 스킵합니다.")
                    continue

            if title is None:
                print(f"{index}번째 가게 - 가게 정보를 가져올 수 없어 스킵합니다.")
                continue

            # 가게이름 / 카테고리 추출 (더 안전한 방법)
            try:
                # 모든 span 요소를 찾아서 처리
                spans = title.find_elements(By.XPATH, './/span')
                if len(spans) >= 2:
                    store_name = spans[0].text.strip() if spans[0].text else ''
                    category = spans[1].text.strip() if spans[1].text else ''
                else:
                    # 대안적인 방법
                    store_name = safe_get_text(title, './/div[1]/div[1]/span[contains(@class, "GHAhO")]')
                    category = safe_get_text(title, './/div[1]/div[1]/span[2]')

                # 옵션 정보 (미쉐린, 착한가격 등)
                option = safe_get_text(title, 'div.XtBbS', "css")

            except Exception as e:
                print(f"{index}번째 가게 - 가게명/카테고리 추출 실패: {str(e)}")
                continue

            # 필수 정보 검증
            if not store_name:
                print(f"{index}번째 가게 - 가게명이 없어 스킵합니다.")
                continue

            if not category:
                print(f"{index}번째 가게 - 카테고리가 없어 스킵합니다.")
                continue

            # 프랜차이즈 가게는 스킵
            if franchise_pattern.search(store_name):
                print(f"프랜차이즈 가게 스킵: {store_name}")
                continue

            # 카테고리 필터링
            if category in not_category_values:
                print(f"제외 카테고리 스킵: {store_name} (카테고리: {category})")
                continue

            print(f"{index}번째 가게 처리 중: {store_name}")

            # 주소
            try:
                address = driver.find_element(By.CLASS_NAME, 'LDgIH').text
            except Exception as e:
                print(f"{store_name} : 주소 추출 오류")
                address = ''

            # 전화번호
            try:
                tel = driver.find_element(By.CLASS_NAME, 'xlx7Q').text
            except Exception as e:
                # 휴대폰 번호를 연결해놓은 가게
                try:
                    tel_box = driver.find_element(By.XPATH,
                                                  '//div[contains(@class, "O8qbU nbXkr")]//div[@class="mqM2N"]')
                    if tel_box:
                        tel_box_a = tel_box.find_element(By.XPATH, './/a')
                        tel_box_a.click()
                        tel = tel_box.find_element(By.XPATH,
                                                   './/div[contains(@class, "_YI7T kH0zp")]/div[@class="J7eF_"]/em').text
                except Exception as e:
                    tel = ''

            # 영업시간
            try:
                find_business_hours()
                # business_hours가 비어있거나 값이 없는 경우 스크롤 내리기
                if not any(business_hours):
                    driver.execute_script("window.scrollBy(0, 600);")
                    time.sleep(1)
                    find_business_hours()
            except Exception as e:
                pass

            # 편의시설
            try:
                container = driver.find_element(By.XPATH,
                                                '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]/div')
                amenity = container.text
            except Exception as e:
                try:
                    driver.execute_script("window.scrollBy(0, 600);")
                    time.sleep(1)
                    container = driver.find_element(By.XPATH,
                                                    '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]')
                    amenity = container.text
                except Exception as e:
                    amenity = ''

            # '소비'라는 단어를 포함한 항목 제거
            if amenity:
                amenity_list = [item.strip() for item in amenity.split(',')]
                amenity_filtered = [item for item in amenity_list if '소비' not in item]
                amenity = ', '.join(amenity_filtered)


            # 방송 출연
            try:
                try:
                    tv_box = driver.find_element(By.XPATH, 'div.O8qbU.TMK4W')
                except Exception as e:
                    driver.execute_script("window.scrollBy(0, 600);")
                    time.sleep(1)
                    tv_box = driver.find_element(By.CSS_SELECTOR, 'div.O8qbU.TMK4W')

                exclude_indices = list(range(len(business_hours)))
                if tv_box:
                    tv_box.click()
                    tv_text = tv_box.find_elements(By.XPATH,
                                                   '//div[@class="vV_z_"]//div[@class="w9QyJ"]/div[@class="y6tNq"]/*[@class="A_cdD"]')

                    for idx, span in enumerate(tv_text):
                        if idx in exclude_indices:
                            continue
                        broad_text = span.text
                        if broad_text:
                            broadcast.append(broad_text)
            except Exception as e:
                pass

            # 가게 고유 아이디
            try:
                wait = WebDriverWait(driver, 10)
                store_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//a[contains(@href, "/restaurant/") and contains(@class, "_tab-menu")]')
                ))
                href = store_element.get_attribute('href')
                match = re.search(r'/restaurant/(\d+)', href)
                store_id = match.group(1) if match else ''
            except Exception as e:
                try:
                    switch_right()
                    wait = WebDriverWait(driver, 5)
                    store_element = wait.until(EC.presence_of_element_located(
                        (By.XPATH, '//a[contains(@href, "/restaurant/") and contains(@class, "_tab-menu")]')
                    ))
                    href = store_element.get_attribute('href')
                    match = re.search(r'/restaurant/(\d+)', href)
                    store_id = match.group(1) if match else ''
                except Exception as e:
                    store_id = ''

            # 메뉴
            try:
                # 메뉴 탭 찾기
                is_menu = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//div[contains(@class, "place_fixed_maintab")]//a[span[normalize-space()="메뉴"]]'))
                )
                if is_menu:
                    is_menu.click()

                    # 1. 네이버 지도 내 메뉴
                    try:
                        body = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH,
                                                            '//div[contains(@class, "place_section") and contains(@class, "no_margin")]/div[@class="place_section_content"]'))
                        )

                        previous_scroll_height = 0
                        while True:
                            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", body)
                            time.sleep(1)

                            try:
                                WebDriverWait(driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, '//div[@class="lfH3O"]'))
                                ).click()
                            except Exception as e:
                                break

                            new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", body)
                            if new_scroll_height == previous_scroll_height:
                                break
                            previous_scroll_height = new_scroll_height

                        ul_element = body.find_element(By.XPATH, './/ul')
                        li_elements = ul_element.find_elements(By.XPATH, './li[@class="E2jtL"]/a')

                        if li_elements:
                            for li in li_elements:
                                menu_elements = li.find_elements(By.XPATH, './div[@class="MXkFw"]')
                                for single_menu in menu_elements:
                                    text = single_menu.text
                                    if text:
                                        menu.append(text)

                    # 2. 네이버 주문(포장 + 배달)
                    except Exception as e:
                        try:
                            body = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, '//div[@class="order_list"]'))
                            )
                            menu_container = body.find_elements(By.XPATH,
                                                                '//div[@class="order_list_inner"]/ul[@class="order_list_area"]/li[@class="order_list_item"]//div[@class="info_detail"]')
                            for menus in menu_container:
                                text = menus.text
                                if text:
                                    menu.append(text)

                        # 3. 배달 주문
                        except Exception as e:
                            try:
                                body = driver.find_element(By.XPATH, '//div[@data-nclicks-area-code="bmv"]')
                                previous_scroll_height = 0

                                while True:
                                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", body)
                                    time.sleep(1)

                                    try:
                                        driver.find_element(By.XPATH,
                                                            '//div[@class="NSTUp"]/div[@class="lfH3O"]/a[@class="fvwqf"]').click()
                                    except Exception as e:
                                        break

                                    new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", body)
                                    if new_scroll_height == previous_scroll_height:
                                        break
                                    previous_scroll_height = new_scroll_height

                                menu_container = body.find_elements(By.XPATH,
                                                                    '//div[contains(@class, "place_section") and contains(@class, "gkWf3")]/div[@class="place_section_content"]')

                                for container in menu_container:
                                    ul_element = container.find_elements(By.XPATH, './/ul')
                                    for ul in ul_element:
                                        li_elements = ul.find_elements(By.XPATH, './li/a')
                                        if li_elements:
                                            for li in li_elements:
                                                menu_elements = li.find_elements(By.XPATH, './div[@class="MXkFw"]')
                                                for single_menu in menu_elements:
                                                    text = single_menu.text
                                                    if text:
                                                        menu.append(text)
                            except Exception as e:
                                pass
            except Exception as e:
                pass

            # 저장할 정보
            stores_info = {
                'store_id': store_id,
                'name': store_name,
                'category': category,
                'address': address,
                'tel': tel,
                'options': option,
                'amenity': amenity,
                'broadcast': '; '.join(broadcast),
                'business_hours': '; '.join(business_hours),
                'menu': '; '.join(menu)
            }

            stores.append(stores_info)
            print(f"{store_name} 정보 수집 완료")

        except Exception as e:
            print(f"{index}번째 가게 처리 중 오류 발생: {str(e)}")
            continue

    # 데이터 저장
    if stores:
        df = pd.DataFrame(stores)
        # 파일명을 바꿔주세요.
        df.to_csv('광진구/광장동 맛집.csv', mode='a', encoding='utf-8-sig', index=False, header=is_first_save)

        # 첫 번째 저장 이후에는 is_first_save를 false로 변경
        is_first_save = False

        print(f"파일 저장 완료 - {len(stores)}개 가게 정보 저장")
        del stores
        stores = []

    switch_left()

    # 페이지 다음 버튼이 활성화 상태일 경우 계속 진행
    if (next_page == 'false'):
        try:
            driver.find_element(By.XPATH, div + 'a[7]').click()
            print("다음 페이지를 진행합니다.")
        except Exception as e:
            print("다음 페이지 클릭 실패, 종료합니다.")
            loop = False
    else:
        loop = False

driver.close()
print("크롤링 완료!")

#######################여기 까지 ############################
