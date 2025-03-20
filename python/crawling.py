from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd

# 왼쪽 프레임으로 전환
def switch_left() :
    driver.switch_to.parent_frame()
    # implicitly_wait로 못잡길래 아래처럼 변경
    iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="searchIframe"]')))
    driver.switch_to.frame(iframe)

# 오른쪽 프레임으로 전환
def switch_right() :
    driver.switch_to.parent_frame()
    try:
        # implicitly_wait로 못잡길래 아래처럼 변경
        iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]')))
        driver.switch_to.frame(iframe)

        # 다시 한번더 확인
    except Exception as e:
        iframe = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]')))
        driver.switch_to.frame(iframe)

# 영업시간 추출
def find_business_hours() :
    # 영업시간 더보기 버튼 찾기
    WebDriverWait(driver, 2).until(
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
URL = 'https://map.naver.com/search/00동 맛집'
driver.get(URL)
# 10초 안에 웹 페이지를 로드하면 바로 넘어가거나, 10초를 기다림
driver.implicitly_wait(10)

# 가게 정보 리스트 초기화
stores = []
# 첫 번째 저장 여부를 추적하는 변수
is_first_save = True

div = '//*[@id="app-root"]/div/div[3]/div[2]/'


while(loop):
    # searchIframe 으로 프레임 변경
    switch_left()

    try:
        # 다음 페이지 true, false 여부 확인
        # 다음 페이지가 disabled 속성인지 [true / false]
        # 페이지 넘길때마다 계속 확인해줘야 함(페이지 새로 로드 시, 버튼 상태 값이 바뀜)
        # [@id="app-root"]/div/div[3] 인지 [@id="app-root"]/div/div[2]인지 계속 확인해야될 필요가 있음
        next_page = driver.find_element(By.XPATH, div + 'a[7]').get_attribute(
            'aria-disabled')
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
            driver.find_element(By.XPATH, div+'a[4]').click()
            print("3 페이지를 진행합니다.")
            page_no = driver.find_element(By.XPATH, '//a[contains(@class, "mBN2s qxokY")]').text

        # 맨 밑까지 스크롤
        scrollable_element = driver.find_element(By.XPATH,
                                                 '// *[ @ id = "_pcmap_list_scroll_container"]')  # 스크롤 컨테이너 찾기
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

        # 현재 페이지에 등록된 모든 가게 조회
        # 광고 걸린 업체들은 또 출력되기 때문에 거릅니다.
        restaurant_elements = driver.find_elements(By.XPATH,
                                                   '//*[@id="_pcmap_list_scroll_container"]//li[@data-laim-exp-id="undefinedundefined"]')

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

            switch_left()  # 다시 왼쪽 프레임으로 돌아와야 함
            e.find_element(By.XPATH, './div[@class="CHC5F"]').find_element(By.XPATH, ".//a/div/div/span").click()
            driver.implicitly_wait(3)
            switch_right()
            driver.implicitly_wait(3)

            # 여기부터 크롤링 시작
            # 제목 표시되는 부분
            try:
                title = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="zD5Nm undefined"]'))
                )
            except Exception as e:
                print("타이틀 추출 실패")
                time.sleep(1)
                driver.refresh()  # 사이트를 불러오지 못 하는 경우가 있어서 새로고침 코드 추가
                switch_right()
                title = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="zD5Nm undefined"]'))
                )

            # 가게이름 / 카테고리 / 미쉐린,착한가격업소,식약처인증우수음식점 여부
            try:
                store_name = title.find_element(By.XPATH, './/div[1]/div[1]/span[1]').text  # 가게 이름
                category = title.find_element(By.XPATH, './/div[1]/div[1]/span[2]').text  # 카테고리
                option = title.find_element(By.CSS_SELECTOR, 'div.XtBbS').text  # 미쉐린 또는 착한 가격 또는 식약처 인증 우수 음식점
            except Exception as e:
                store_name = title.find_element(By.XPATH, './/div[1]/div[1]/span[1]').text  # 가게 이름
                category = title.find_element(By.XPATH, './/div[1]/div[1]/span[2]').text  # 카테고리

            # 주소
            try:
                address = driver.find_element(By.CLASS_NAME, 'LDgIH').text
            except Exception as e:
                print(store_name + " : 주소 추출 오류")
                address = driver.find_element(By.CLASS_NAME, 'LDgIH').text

            # 전화번호
            try:
                tel = driver.find_element(By.CLASS_NAME, 'xlx7Q').text
            except Exception as e:
                # 휴대폰 번호를 연결해놓은 가게
                try:
                    print(store_name + " : 전화번호가 없나?")
                    tel_box = driver.find_element(By.XPATH,
                                                  '//div[contains(@class, "O8qbU nbXkr")]//div[@class="mqM2N"]')
                    if tel_box:
                        print(store_name + " : tel_box를 찾음")
                        tel_box_a = tel_box.find_element(By.XPATH, './/a')
                        tel_box_a.click()
                        print("tel_box_a는 눌렀음")
                        tel = tel_box.find_element(By.XPATH,
                                                   './/div[contains(@class, "_YI7T kH0zp")]/div[@class="J7eF_"]/em').text
                # 전화번호 진짜 없음
                except Exception as e:
                    print(store_name + " : 전화번호 없음")

            # 영업시간
            try:
                find_business_hours()

                # business_hours가 비어있거나 값이 없는 경우 스크롤 내리기
                if not any(business_hours):
                    driver.execute_script("window.scrollBy(0, 600);")  # 화면에 보이지 않는 경우를 고려하여 600px 아래로 스크롤
                    time.sleep(1)  # 잠시 대기
                    find_business_hours()

            except Exception as e:
                print(store_name + " : 영업시간 진짜 없음")

            # 편의
            try:
                # 일단 대기
                driver.implicitly_wait(3)
                container = driver.find_element(By.XPATH,
                                                '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]/div')
                amenity = container.text
            except Exception as e:
                try:
                    # print("편의시설 추출 오류")
                    driver.execute_script("window.scrollBy(0, 600);")  # 화면에 보이지 않는 경우를 고려하여 600px 아래로 스크롤
                    time.sleep(1)  # 잠시 대기

                    container = driver.find_element(By.XPATH,
                                                    '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]')
                    amenity = container.text
                except Exception as e:
                    print(store_name + " : 편의시설 진짜 없음")

            # 방송 출연
            try:
                try:  # 우선 방송출연 블럭 찾기
                    tv_box = driver.find_element(By.XPATH, 'div.O8qbU.TMK4W')

                except Exception as e:
                    # 방송 출연 블럭이 안 찾아진다면 스크롤 내리기
                    driver.execute_script("window.scrollBy(0, 600);")  # 화면에 보이지 않는 경우를 고려하여 600px 아래로 스크롤
                    time.sleep(1)  # 잠시 대기

                    tv_box = driver.find_element(By.CSS_SELECTOR, 'div.O8qbU.TMK4W')  # 다시 방송출연 블럭 찾기

                exclude_indices = list(range(len(business_hours)))
                if tv_box:
                    tv_box.click()
                    tv_text = tv_box.find_elements(By.XPATH,
                                                   '//div[@class="vV_z_"]//div[@class="w9QyJ"]/div[@class="y6tNq"]/*[@class="A_cdD"]')

                    for index, span in enumerate(tv_text):
                        if index in exclude_indices:  # 첫 번째 요소를 제외
                            continue
                        broad_text = span.text
                        broadcast.append(broad_text)

            except Exception as e:
                print(store_name + " : 방송출연 한적 없습니다.")
                
            # 가게 고유 아이디
            try:
                store_id = \
                driver.find_element(By.XPATH, '//div[@class="flicking-camera"]/a').get_attribute('href').split('/')[4]
            except Exception as e:
                switch_right()  # 프레임 벗어난 경우를 고려
                store_id = \
                driver.find_element(By.XPATH, '//div[@class="flicking-camera"]/a').get_attribute('href').split('/')[4]

            # 메뉴
            try:
                # 메뉴 탭 찾기
                is_menu = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@class="flicking-camera"]/a/span[text()="메뉴"]'))
                )
                if is_menu:
                    is_menu.click()

                    # 1. 네이버 지도 내 메뉴
                    try:
                        # body = driver.find_element((By.XPATH,
                        #                                    '//div[contains(@class, "place_section") and contains(@class, "no_margin")]/div[@class="place_section_content"]'))
                        body = WebDriverWait(driver, 2).until(  # 스크롤 컨테이너 찾기
                            EC.presence_of_element_located((By.XPATH,
                                                            '//div[contains(@class, "place_section") and contains(@class, "no_margin")]/div[@class="place_section_content"]'))
                        )
                        # 초기 스크롤 높이 설정
                        previous_scroll_height = 0

                        while True:
                            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", body)
                            time.sleep(1)  # 스크롤 후 로딩 시간 대기

                            try:
                                WebDriverWait(driver, 2).until(
                                    EC.element_to_be_clickable((By.XPATH, '//div[@class="lfH3O"]'))
                                ).click()  # 더보기 버튼 찾기

                            except Exception as e:
                                # 더보기 버튼이 없으면 스크롤 내리지 않습니다.
                                break

                            # 현재 스크롤 높이 가져오기
                            new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", body)

                            # 이전 스크롤 높이와 비교
                            if new_scroll_height == previous_scroll_height:  # 이전 스크롤 높이와 같다면 더 이상 스크롤할 내용이 없다
                                break

                            # 현재 스크롤 높이를 이전 스크롤 높이로 업데이트
                            previous_scroll_height = new_scroll_height

                        ul_element = body.find_element(By.XPATH, './/ul')  # body 안에 ul 요소 찾기
                        driver.implicitly_wait(10)
                        li_elements = ul_element.find_elements(By.XPATH, './li[@class="E2jtL"]/a')  # ul 안에 li 요소 찾기

                        if li_elements:
                            # 각 li 안의 div[@class="MXkFw"] 요소의 텍스트 출력 span 요소들의 텍스트 출력
                            for li in li_elements:
                                menu_elements = li.find_elements(By.XPATH, './div[@class="MXkFw"]')

                                for single_menu in menu_elements:
                                    text = single_menu.text
                                    if text:  # 비어있지 않은 경우
                                        menu.append(text)

                    # 2. 네이버 주문(포장 + 배달)
                    except Exception as e:
                        try:
                            # print("배달 가능 메뉴입니다.")
                            # body = driver.find_element((By.XPATH, '//div[@class="order_list"]'))
                            body = WebDriverWait(driver, 2).until(
                                EC.presence_of_element_located((By.XPATH, '//div[@class="order_list"]'))
                            )
                            menu_container = body.find_elements(By.XPATH,
                                                                '//div[@class="order_list_inner"]/ul[@class="order_list_area"]/li[@class="order_list_item"]//div[@class="info_detail"]')
                            for menus in menu_container:
                                text = menus.text
                                menu.append(text)

                        # 3. 배달 주문
                        # 감탄계 숯불치킨 강남역점....
                        except Exception as e:
                            body = driver.find_element(By.XPATH, '//div[@data-nclicks-area-code="bmv"]')

                            # 초기 높이 설정
                            previous_scroll_height = 0
                            while True:
                                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", body)
                                time.sleep(1)  # 스크롤 후 로딩 시간 대기

                                try:
                                    button = driver.find_elements(By.XPATH,
                                                                  '//div[@class="NSTUp"]/div[@class="lfH3O"]/a[@class="fvwqf"]').click()  # 더보기 버튼 찾기
                                except Exception as e:
                                    # 더보기 버튼이 없으면 스크롤 내리지 않습니다.
                                    break

                                # 현재 스크롤 높이 가져오기
                                new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", body)

                                # 이전 스크롤 높이와 비교
                                if new_scroll_height == previous_scroll_height:  # 이전 스크롤 높이와 같다면 더 이상 스크롤할 내용이 없다
                                    break

                                # 현재 스크롤 높이를 이전 스크롤 높이로 업데이트
                                previous_scroll_height = new_scroll_height

                            menu_container = body.find_elements(By.XPATH,
                                                                '//div[contains(@class, "place_section") and contains(@class, "gkWf3")]/div[@class="place_section_content"]')

                            # 각 메뉴 컨테이너에서 ul 요소를 찾기
                            for container in menu_container:
                                ul_element = container.find_elements(By.XPATH, './/ul')

                                for ul in ul_element:
                                    driver.implicitly_wait(10)
                                    li_elements = ul.find_elements(By.XPATH, './li/a')  # ul 안에 li 요소 찾기

                                    if li_elements:
                                        for li in li_elements:
                                            menu_elements = li.find_elements(By.XPATH, './div[@class="MXkFw"]')

                                            for single_menu in menu_elements:
                                                text = single_menu.text
                                                if text:  # 비어있지 않다면
                                                    menu.append(text)


            except Exception as e:
                print(store_name + " : 메뉴 진짜 없음")

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

        if stores:
            df = pd.DataFrame(stores)
            df.to_csv('00동 맛집.csv', mode='a', encoding='utf-8-sig', index=False, header=is_first_save)

            # 첫 번째 저장 이후에는 is_first_save를 false로 변경
            is_first_save = False

            print("파일 저장 완료")
            del stores
            stores = []

            # mode='a' 파일을 열어서 기존 데이터 뒤에 새로운 데이터를 추가한다
            # 파일이 없으면 새로 생성한다
            # 기존의 내용을 지우지 않고, 새로운 내용을 추가하는 데 사용된다.

            # mode='w' 파일을 열어서 기존 내용을 모두 지우고 새로운 내용을 작성한다.
            # 파일이 없으면 새로 생성한다.
            # 기존의 데이터는 삭제되므로 주의

        switch_left()

        # 페이지 다음 버튼이 활성화 상태일 경우 계속 진행
        if (next_page == 'false'):
            driver.find_element(By.XPATH, div+'a[7]').click()
            print("다음 페이지를 진행합니다.")
        # 아닐 경우 루프 정지
        else:
            loop = False

    except Exception as e:
        div = '//*[@id="app-root"]/div/div[2]/div[2]/'

        # 다음 페이지 true, false 여부 확인
        # 다음 페이지가 disabled 속성인지 [true / false]
        # 페이지 넘길때마다 계속 확인해줘야 함(페이지 새로 로드 시, 버튼 상태 값이 바뀜)
        # [@id="app-root"]/div/div[3] 인지 [@id="app-root"]/div/div[2]인지 계속 확인해야될 필요가 있음
        next_page = driver.find_element(By.XPATH, div + 'a[7]').get_attribute(
            'aria-disabled')
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
            driver.find_element(By.XPATH, div+'a[4]').click()
            print("3 페이지를 진행합니다.")
            page_no = driver.find_element(By.XPATH, '//a[contains(@class, "mBN2s qxokY")]').text

        # 맨 밑까지 스크롤

        scrollable_element = driver.find_element(By.XPATH,
                                                 '// *[ @ id = "_pcmap_list_scroll_container"]')  # 스크롤 컨테이너 찾기
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
                # print("현재 높이와 새 높이가 " + str(last_height) + "로 같습니다.")
                break

            last_height = new_height

        # 현재 페이지에 등록된 모든 가게 조회
        # 광고 걸린 업체들은 또 출력되기 때문에 거릅니다.
        restaurant_elements = driver.find_elements(By.XPATH,
                                                   '//*[@id="_pcmap_list_scroll_container"]//li[@data-laim-exp-id="undefinedundefined"]')

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

            switch_left()  # 다시 왼쪽 프레임으로 돌아와야 함
            e.find_element(By.XPATH, './div[@class="CHC5F"]').find_element(By.XPATH, ".//a/div/div/span").click()
            driver.implicitly_wait(3)
            switch_right()
            driver.implicitly_wait(3)

            # 여기부터 크롤링 시작
            # 제목 표시되는 부분
            try:
                title = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="zD5Nm undefined"]'))
                )
            except Exception as e:
                print("타이틀 추출 실패")
                time.sleep(1)
                driver.refresh()  # 사이트를 불러오지 못 하는 경우가 있어서 새로고침 코드 추가
                switch_right()
                title = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="zD5Nm undefined"]'))
                )

            # 가게이름 / 카테고리 / 미쉐린,착한가격업소,식약처인증우수음식점 여부
            try:
                store_name = title.find_element(By.XPATH, './/div[1]/div[1]/span[1]').text  # 가게 이름
                category = title.find_element(By.XPATH, './/div[1]/div[1]/span[2]').text  # 카테고리
                option = title.find_element(By.CSS_SELECTOR, 'div.XtBbS').text  # 미쉐린 또는 착한 가격 또는 식약처 인증 우수 음식점
            except Exception as e:
                store_name = title.find_element(By.XPATH, './/div[1]/div[1]/span[1]').text  # 가게 이름
                category = title.find_element(By.XPATH, './/div[1]/div[1]/span[2]').text  # 카테고리

            # 주소
            try:
                address = driver.find_element(By.CLASS_NAME, 'LDgIH').text
            except Exception as e:
                print(store_name + " : 주소 추출 오류")
                address = driver.find_element(By.CLASS_NAME, 'LDgIH').text

            # 전화번호
            try:
                tel = driver.find_element(By.CLASS_NAME, 'xlx7Q').text
            except Exception as e:
                # 휴대폰 번호를 연결해놓은 가게
                try:
                    print(store_name + " : 전화번호가 없나?")
                    tel_box = driver.find_element(By.XPATH,
                                                  '//div[contains(@class, "O8qbU nbXkr")]//div[@class="mqM2N"]')
                    if tel_box:
                        print(store_name + " : tel_box를 찾음")
                        tel_box_a = tel_box.find_element(By.XPATH, './/a')
                        tel_box_a.click()
                        print("tel_box_a는 눌렀음")
                        tel = tel_box.find_element(By.XPATH,
                                                   './/div[contains(@class, "_YI7T kH0zp")]/div[@class="J7eF_"]/em').text
                # 전화번호 진짜 없음
                except Exception as e:
                    print(store_name + " : 전화번호 없음")

            # 영업시간
            try:
                find_business_hours()

                # business_hours가 비어있거나 값이 없는 경우 스크롤 내리기
                if not any(business_hours):
                    driver.execute_script("window.scrollBy(0, 600);")  # 화면에 보이지 않는 경우를 고려하여 600px 아래로 스크롤
                    time.sleep(1)  # 잠시 대기
                    find_business_hours()

            except Exception as e:
                print(store_name + " : 영업시간 진짜 없음")

            # 편의
            try:
                # 일단 대기
                driver.implicitly_wait(3)
                container = driver.find_element(By.XPATH,
                                                '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]/div')
                amenity = container.text
            except Exception as e:
                try:
                    # print("편의시설 추출 오류")
                    driver.execute_script("window.scrollBy(0, 600);")  # 화면에 보이지 않는 경우를 고려하여 600px 아래로 스크롤
                    time.sleep(1)  # 잠시 대기

                    container = driver.find_element(By.XPATH,
                                                    '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]')
                    amenity = container.text
                except Exception as e:
                    print(store_name + " : 편의시설 진짜 없음")

            # 방송 출연
            try:
                try:  # 우선 방송출연 블럭 찾기
                    tv_box = driver.find_element(By.XPATH, 'div.O8qbU.TMK4W')

                except Exception as e:
                    # 방송 출연 블럭이 안 찾아진다면 스크롤 내리기
                    driver.execute_script("window.scrollBy(0, 600);")  # 화면에 보이지 않는 경우를 고려하여 600px 아래로 스크롤
                    time.sleep(1)  # 잠시 대기

                    tv_box = driver.find_element(By.CSS_SELECTOR, 'div.O8qbU.TMK4W')  # 다시 방송출연 블럭 찾기

                exclude_indices = list(range(len(business_hours)))
                if tv_box:
                    tv_box.click()
                    tv_text = tv_box.find_elements(By.XPATH,
                                                   '//div[@class="vV_z_"]//div[@class="w9QyJ"]/div[@class="y6tNq"]/*[@class="A_cdD"]')

                    for index, span in enumerate(tv_text):
                        if index in exclude_indices:  # 첫 번째 요소를 제외
                            continue
                        broad_text = span.text
                        broadcast.append(broad_text)

            except Exception as e:
                print(store_name + " : 방송출연 한적 없습니다.")

            # 가게 고유 아이디
            try:
                store_id = \
                    driver.find_element(By.XPATH, '//div[@class="flicking-camera"]/a').get_attribute('href').split('/')[
                        4]
            except Exception as e:
                switch_right()  # 프레임 벗어난 경우를 고려
                store_id = \
                    driver.find_element(By.XPATH, '//div[@class="flicking-camera"]/a').get_attribute('href').split('/')[
                        4]

            # 메뉴
            try:
                # 메뉴 탭 찾기
                is_menu = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@class="flicking-camera"]/a/span[text()="메뉴"]'))
                )
                if is_menu:
                    is_menu.click()

                    # 1. 네이버 지도 내 메뉴
                    try:
                        # body = driver.find_element((By.XPATH,
                        #                                    '//div[contains(@class, "place_section") and contains(@class, "no_margin")]/div[@class="place_section_content"]'))
                        body = WebDriverWait(driver, 2).until(  # 스크롤 컨테이너 찾기
                            EC.presence_of_element_located((By.XPATH,
                                                            '//div[contains(@class, "place_section") and contains(@class, "no_margin")]/div[@class="place_section_content"]'))
                        )
                        # 초기 스크롤 높이 설정
                        previous_scroll_height = 0

                        while True:
                            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", body)
                            time.sleep(1)  # 스크롤 후 로딩 시간 대기

                            try:
                                WebDriverWait(driver, 2).until(
                                    EC.element_to_be_clickable((By.XPATH, '//div[@class="lfH3O"]'))
                                ).click()  # 더보기 버튼 찾기

                            except Exception as e:
                                # 더보기 버튼이 없으면 스크롤 내리지 않습니다.
                                break

                            # 현재 스크롤 높이 가져오기
                            new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", body)

                            # 이전 스크롤 높이와 비교
                            if new_scroll_height == previous_scroll_height:  # 이전 스크롤 높이와 같다면 더 이상 스크롤할 내용이 없다
                                break

                            # 현재 스크롤 높이를 이전 스크롤 높이로 업데이트
                            previous_scroll_height = new_scroll_height

                        ul_element = body.find_element(By.XPATH, './/ul')  # body 안에 ul 요소 찾기
                        driver.implicitly_wait(10)
                        li_elements = ul_element.find_elements(By.XPATH, './li[@class="E2jtL"]/a')  # ul 안에 li 요소 찾기

                        if li_elements:
                            # 각 li 안의 div[@class="MXkFw"] 요소의 텍스트 출력 span 요소들의 텍스트 출력
                            for li in li_elements:
                                menu_elements = li.find_elements(By.XPATH, './div[@class="MXkFw"]')

                                for single_menu in menu_elements:
                                    text = single_menu.text
                                    if text:  # 비어있지 않은 경우
                                        menu.append(text)

                    except Exception as e:
                        try:
                            body = driver.find_element(By.XPATH, '//div[@data-nclicks-area-code="bmv"]')

                            # 초기 높이 설정
                            previous_scroll_height = 0
                            while True:
                                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", body)
                                time.sleep(1)  # 스크롤 후 로딩 시간 대기

                                try:
                                    button = driver.find_elements(By.XPATH,
                                                                  '//div[@class="NSTUp"]/div[@class="lfH3O"]/a[@class="fvwqf"]').click()  # 더보기 버튼 찾기
                                except Exception as e:
                                    # 더보기 버튼이 없으면 스크롤 내리지 않습니다.
                                    break

                                # 현재 스크롤 높이 가져오기
                                new_scroll_height = driver.execute_script("return arguments[0].scrollHeight", body)

                                # 이전 스크롤 높이와 비교
                                if new_scroll_height == previous_scroll_height:  # 이전 스크롤 높이와 같다면 더 이상 스크롤할 내용이 없다
                                    break

                                # 현재 스크롤 높이를 이전 스크롤 높이로 업데이트
                                previous_scroll_height = new_scroll_height

                            menu_container = body.find_elements(By.XPATH,
                                                                '//div[contains(@class, "place_section") and contains(@class, "gkWf3")]/div[@class="place_section_content"]')

                            # 각 메뉴 컨테이너에서 ul 요소를 찾기
                            for container in menu_container:
                                ul_element = container.find_elements(By.XPATH, './/ul')

                                for ul in ul_element:
                                    driver.implicitly_wait(10)
                                    li_elements = ul.find_elements(By.XPATH, './li/a')  # ul 안에 li 요소 찾기

                                    if li_elements:
                                        for li in li_elements:
                                            menu_elements = li.find_elements(By.XPATH, './div[@class="MXkFw"]')

                                            for single_menu in menu_elements:
                                                text = single_menu.text
                                                if text:  # 비어있지 않다면
                                                    menu.append(text)


                        # 3. 네이버 주문(포장 + 배달)
                        except Exception as e:
                            # print("배달 가능 메뉴입니다.")
                            # body = driver.find_element((By.XPATH, '//div[@class="order_list"]'))
                            body = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, '//div[@class="order_list"]'))
                            )
                            menu_container = body.find_elements(By.XPATH,
                                                                '//div[@class="order_list_inner"]/ul[@class="order_list_area"]/li[@class="order_list_item"]//div[@class="info_detail"]')
                            for menus in menu_container:
                                text = menus.text
                                menu.append(text)



            except Exception as e:
                print(store_name + " : 메뉴 진짜 없음")

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

        if stores:
            df = pd.DataFrame(stores)
            df.to_csv('00동 맛집.csv', mode='a', encoding='utf-8-sig', index=False, header=is_first_save)

            # 첫 번째 저장 이후에는 is_first_save를 false로 변경
            is_first_save = False

            print("파일 저장 완료")
            del stores
            stores = []

            # mode='a' 파일을 열어서 기존 데이터 뒤에 새로운 데이터를 추가한다
            # 파일이 없으면 새로 생성한다
            # 기존의 내용을 지우지 않고, 새로운 내용을 추가하는 데 사용된다.

            # mode='w' 파일을 열어서 기존 내용을 모두 지우고 새로운 내용을 작성한다.
            # 파일이 없으면 새로 생성한다.
            # 기존의 데이터는 삭제되므로 주의

        switch_left()

        # 페이지 다음 버튼이 활성화 상태일 경우 계속 진행
        if (next_page == 'false'):
            driver.find_element(By.XPATH, div+'a[7]').click()
            print("다음 페이지를 진행합니다.")
        # 아닐 경우 루프 정지
        else:
            loop = False

driver.close()

#######################여기 까지 ############################
