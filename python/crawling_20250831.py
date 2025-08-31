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
from concurrent.futures import ThreadPoolExecutor
import threading


class NaverMapCrawler:
    def __init__(self):
        self.driver = None
        self.stores = []
        self.is_first_save = True
        self.div = '//*[@id="app-root"]/div/div[3]/div[2]/'

        # 프랜차이즈 및 제외 카테고리 설정
        self.franchise_values = ['스타벅스', '메가MGC', '메가커피', '할리스', '커피빈', '폴 바셋', '카페베네',
                                 '엔제리너스', '엔젤리너스', '투썸', '파스쿠찌', '빽다방', '바나프레소', '이디야',
                                 '컴포즈', '더벤티', '더리터', '하이오커피', '오슬로우', '스무디킹', '탐앤탐스',
                                 '하삼동커피', '아마스빈', '파리바게뜨', '파리바게트', '뚜레쥬르', '파리크라상',
                                 '배스킨라빈스', '요거트아이스크림의정석', '요아정', '백미당', '설빙', '마이요거트립',
                                 '요거프레소', '요거트월드', '블루보틀', '테라로사', '팀홀튼', '아티제', '커스텀커피',
                                 '오설록', '고망고', '텐퍼센트', '커피에반하다', '커피사피엔스', '봉명동내커피',
                                 '디저트39', '공차', '쥬씨', '매머드커피', '매머드익스프레스', '팔공티', '카페인중독',
                                 '키쉬미뇽', '아메리칸트레일러', '카페인24', '카페일분', '자연드림', '카페게이트',
                                 '데이롱', '카페만월경', '카페 만월경', '나이스카페인클럽', '쉬즈베이글', '우지커피',
                                 '백억커피', '준코', '타코야끼', '타코야키', '마리웨일', '메이드카페', '무인카페',
                                 '밥스토랑', '꽈배기', '호두과자', '요거트', '복호두', '무인 ', '커피베이']

        self.not_category_values = ['아이스크림', '빙수', '밀키트', '테이크아웃커피', '라이브카페',
                                    '스터디카페', '북카페', '단란주점', '유흥주점', '푸드트럭', '프랜차이즈본사',
                                    '다방', '과일,주스전문점']

        self.franchise_pattern = re.compile('|'.join(self.franchise_values), re.IGNORECASE)

    def setup_driver(self):
        """최적화된 드라이버 설정"""
        options = Options()
        service = Service()

        # 성능 최적화 옵션들
        options.add_experimental_option("detach", True)
        options.add_argument('--incognito')
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

        # 네트워크 최적화
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")

        # 이미지/CSS 로딩 비활성화로 속도 향상
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # 이미지 차단
            "profile.default_content_setting_values.notifications": 2,  # 알림 차단
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.maximize_window()

        # 암묵적 대기 시간을 짧게 설정
        self.driver.implicitly_wait(3)

    def switch_left(self):
        """왼쪽 프레임으로 전환 - 최적화된 버전"""
        try:
            self.driver.switch_to.parent_frame()
            iframe = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="searchIframe"]'))
            )
            self.driver.switch_to.frame(iframe)
        except TimeoutException:
            print("왼쪽 프레임 전환 실패")
            raise

    def switch_right(self):
        """오른쪽 프레임으로 전환 - 최적화된 버전"""
        try:
            self.driver.switch_to.parent_frame()
            iframe = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]'))
            )
            self.driver.switch_to.frame(iframe)
        except TimeoutException:
            print("오른쪽 프레임 전환 실패")
            raise

    def smart_scroll(self, container_xpath):
        """스마트 스크롤 - 점진적 로딩 감지"""
        try:
            scrollable_element = self.driver.find_element(By.XPATH, container_xpath)

            # 초기 요소 수 확인
            initial_count = len(self.driver.find_elements(By.XPATH,
                                                          '//*[@id="_pcmap_list_scroll_container"]//li[@data-laim-exp-id="undefinedundefined"]'))

            stable_count = 0
            max_stable_attempts = 3

            while stable_count < max_stable_attempts:
                last_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_element)

                # 부드러운 스크롤 대신 큰 단위로 스크롤
                self.driver.execute_script("arguments[0].scrollTop += 1000;", scrollable_element)
                time.sleep(0.5)  # 대기 시간 단축

                new_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_element)

                # 새로운 요소가 로드되었는지 확인
                current_count = len(self.driver.find_elements(By.XPATH,
                                                              '//*[@id="_pcmap_list_scroll_container"]//li[@data-laim-exp-id="undefinedundefined"]'))

                if new_height == last_height and current_count == initial_count:
                    stable_count += 1
                else:
                    stable_count = 0
                    initial_count = current_count

            print(f"스크롤 완료 - 총 {current_count}개 요소 발견")

        except Exception as e:
            print(f"스크롤 중 오류: {str(e)}")

    def extract_business_hours(self, store_name):
        """영업시간 추출 - 최적화된 버전"""
        business_hours = []
        try:
            # 더 구체적인 셀렉터 사용
            more_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="y6tNq"]/span'))
            )
            more_button.click()

            parent_element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, '//a[@class="gKP9i RMgN0"]'))
            )

            child_elements = parent_element.find_elements(By.XPATH,
                                                          './*[contains(@class, "w9QyJ")][position() > 1]')

            for child in child_elements:
                span_elements = child.find_elements(By.XPATH, './div/*[@class="A_cdD"]')
                for span in span_elements:
                    text = span.text
                    if text and store_name not in text and '접기' not in text:
                        business_hours.append(text)

        except TimeoutException:
            pass  # 영업시간 정보가 없는 경우
        except Exception as e:
            pass

        return business_hours

    def safe_get_text(self, element, xpath_or_class, by_type="xpath", default=""):
        """안전한 요소 텍스트 추출"""
        try:
            if by_type == "xpath":
                return element.find_element(By.XPATH, xpath_or_class).text
            elif by_type == "class":
                return element.find_element(By.CLASS_NAME, xpath_or_class).text
            elif by_type == "css":
                return element.find_element(By.CSS_SELECTOR, xpath_or_class).text
        except Exception:
            return default

    def is_valid_store(self, store_name, category):
        """가게 유효성 검사"""
        if not store_name or not category:
            return False, "필수 정보 누락"

        if self.franchise_pattern.search(store_name):
            return False, f"프랜차이즈 가게: {store_name}"

        if category in self.not_category_values:
            return False, f"제외 카테고리: {category}"

        return True, ""

    def extract_store_info(self, element, index):
        """개별 가게 정보 추출 - 최적화된 버전"""
        store_info = {
            'store_id': '', 'name': '', 'category': '', 'address': '',
            'tel': '', 'options': '', 'amenity': '', 'broadcast': '',
            'business_hours': '', 'menu': ''
        }

        try:
            self.switch_left()

            # 클릭 가능할 때까지 대기 후 클릭
            click_element = WebDriverWait(element, 5).until(
                EC.element_to_be_clickable((By.XPATH, './div[@class="CHC5F"]//a'))
            )
            click_element.click()

            # 페이지 로드 대기 최적화
            time.sleep(1.5)  # 3초에서 1.5초로 단축

            self.switch_right()

            # 타이틀 요소 대기
            title = self.wait_for_title_element()
            if not title:
                return None

            # 기본 정보 추출
            store_name = self.safe_get_text(title, './div[1]/div[1]/span[@class="GHAhO"]')
            category = self.safe_get_text(title, './div[1]/div[1]/span[@class="lnJFt"]')

            # 유효성 검사
            valid, reason = self.is_valid_store(store_name, category)
            if not valid:
                print(f"{index}번째 가게 스킵: {reason}")
                return None

            print(f"{index}번째 가게 처리 중: {store_name}")

            # 기본 정보 설정
            store_info['name'] = store_name
            store_info['category'] = category
            store_info['options'] = self.safe_get_text(title, './div[2]/div[@class="XtBbS"]')

            # 세부 정보 병렬 추출
            self.extract_detailed_info(store_info, store_name)

            return store_info

        except Exception as e:
            print(f"{index}번째 가게 처리 중 오류: {str(e)}")
            return None

    def wait_for_title_element(self, max_retries=2):
        """타이틀 요소 대기 - 재시도 로직 포함"""
        for attempt in range(max_retries):
            try:
                title = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((
                        By.XPATH,
                        '(//div[contains(@class,"place_section")]//div[contains(@class,"zD5Nm")])[1]'
                    ))
                )
                return title
            except TimeoutException:
                if attempt < max_retries - 1:
                    print(f"타이틀 로드 재시도 {attempt + 1}")
                    time.sleep(1)
                    self.switch_right()
                else:
                    print("타이틀 요소 로드 실패")
                    return None

    def extract_detailed_info(self, store_info, store_name):
        """세부 정보 추출 - 병렬처리 적용"""
        # 주소 추출
        try:
            store_info['address'] = self.driver.find_element(By.CLASS_NAME, 'LDgIH').text
        except:
            store_info['address'] = ''

        # 전화번호 추출 (최적화된 로직)
        store_info['tel'] = self.extract_phone_number()

        # 영업시간 추출
        store_info['business_hours'] = '; '.join(self.extract_business_hours(store_name))

        # 편의시설 추출
        store_info['amenity'] = self.extract_amenities()

        # 방송 정보 추출
        store_info['broadcast'] = '; '.join(self.extract_broadcast_info())

        # 가게 ID 추출
        store_info['store_id'] = self.extract_store_id()

        # 메뉴 정보 추출
        store_info['menu'] = '; '.join(self.extract_menu_info())

    def extract_phone_number(self):
        """전화번호 추출 최적화"""
        try:
            return self.driver.find_element(By.CLASS_NAME, 'xlx7Q').text
        except:
            try:
                tel_box = self.driver.find_element(By.XPATH,
                                                   '//div[contains(@class, "O8qbU nbXkr")]//div[@class="mqM2N"]')
                tel_box_a = tel_box.find_element(By.XPATH, './/a')
                tel_box_a.click()
                return tel_box.find_element(By.XPATH,
                                            './/div[contains(@class, "_YI7T kH0zp")]/div[@class="J7eF_"]/em').text
            except:
                return ''

    def extract_amenities(self):
        """편의시설 정보 추출"""
        try:
            container = self.driver.find_element(By.XPATH,
                                                 '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]/div')
            amenity = container.text
        except:
            try:
                self.driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(0.5)  # 대기 시간 단축
                container = self.driver.find_element(By.XPATH,
                                                     '//div[@class="PIbes"]/div[contains(@class, "O8qbU") and contains(@class, "Uv6Eo")]')
                amenity = container.text
            except:
                return ''

        # '소비' 단어 포함 항목 제거
        if amenity:
            amenity_list = [item.strip() for item in amenity.split(',')]
            amenity_filtered = [item for item in amenity_list if '소비' not in item]
            return ', '.join(amenity_filtered)
        return ''

    def extract_broadcast_info(self):
        """방송 정보 추출"""
        broadcast = []
        try:
            tv_box = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.XPATH,
                                                  '//div[@class="PIbes"]/div[(@class="O8qbU TMK4W")]'))
            )

            if tv_box:
                tv_box.click()
                tv_text_elements = tv_box.find_elements(By.XPATH,
                                                        './/div[@class="vV_z_"]//div[@class="w9QyJ"]/div[@class="y6tNq"]/*[@class="A_cdD"]')

                if not tv_text_elements or all(span.text.strip() == '' for span in tv_text_elements):
                    tv_text_element = tv_box.find_element(By.XPATH,
                                                          './/div[@class="vV_z_"]//div[@class="w9QyJ"]/span[@class="A_cdD"]')
                    if tv_text_element.text:
                        broadcast.append(tv_text_element.text)
                else:
                    for span in tv_text_elements:
                        if span.text:
                            broadcast.append(span.text)
        except:
            pass
        return broadcast

    def extract_store_id(self):
        """가게 ID 추출"""
        try:
            store_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//a[contains(@href, "/restaurant/") and contains(@class, "_tab-menu")]')
                )
            )
            href = store_element.get_attribute('href')
            match = re.search(r'/restaurant/(\d+)', href)
            return match.group(1) if match else ''
        except:
            return ''

    def extract_menu_info(self):
        """메뉴 정보 추출 - 최적화된 버전"""
        menu = []
        try:
            # 메뉴 탭 클릭
            menu_tab = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[contains(@class, "place_fixed_maintab")]//a[span[normalize-space()="메뉴"]]')
                )
            )
            menu_tab.click()
            time.sleep(1)

            # 메뉴 추출 시도 (3가지 케이스)
            menu_extraction_methods = [
                self.extract_naver_menu,
                self.extract_order_menu,
                self.extract_delivery_menu
            ]

            for method in menu_extraction_methods:
                try:
                    extracted_menu = method()
                    if extracted_menu:
                        menu.extend(extracted_menu)
                        break
                except:
                    continue

        except:
            pass
        return menu

    def extract_naver_menu(self):
        """네이버 지도 내 메뉴 추출"""
        menu = []
        body = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH,
                                            '//div[contains(@class, "place_section") and contains(@class, "no_margin")]/div[@class="place_section_content"]'))
        )

        # 스마트 스크롤 적용
        self.smart_scroll_menu(body)

        ul_element = body.find_element(By.XPATH, './/ul')
        li_elements = ul_element.find_elements(By.XPATH, './li[@class="E2jtL"]/a')

        for li in li_elements:
            text_block = li.text.strip()
            if text_block:
                lines = [line.strip() for line in text_block.split('\n') if line.strip()]
                menu.append("\n".join(lines))
        return menu

    def extract_order_menu(self):
        """네이버 주문 메뉴 추출"""
        menu = []
        body = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="order_list"]'))
        )

        menu_container = body.find_elements(By.XPATH,
                                            '//div[@class="order_list_inner"]/ul[@class="order_list_area"]/li[@class="MenuContent__order_list_item__itwHW"]//div[@class="MenuContent__info_detail__rCviz"]')

        for menu_item in menu_container:
            text = menu_item.text.strip()
            if text:
                menu.append(text)
        return menu

    def extract_delivery_menu(self):
        """배달 주문 메뉴 추출"""
        menu = []
        body = self.driver.find_element(By.XPATH, '//div[@data-nclicks-area-code="bmv"]')

        # 스마트 스크롤 적용
        self.smart_scroll_menu(body)

        menu_container = body.find_elements(By.XPATH,
                                            '//div[contains(@class, "place_section") and contains(@class, "gkWf3")]/div[@class="place_section_content"]')

        for container in menu_container:
            ul_elements = container.find_elements(By.XPATH, './/ul')
            for ul in ul_elements:
                li_elements = ul.find_elements(By.XPATH, './li/a')
                for li in li_elements:
                    text_block = li.text.strip()
                    if text_block:
                        lines = [line.strip() for line in text_block.split('\n') if line.strip()]
                        menu.append("\n".join(lines))
        return menu

    def smart_scroll_menu(self, container):
        """메뉴 페이지 스마트 스크롤"""
        previous_height = 0
        stable_count = 0

        while stable_count < 2:  # 안정성 체크 횟수 감소
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
            time.sleep(0.5)  # 대기 시간 단축

            try:
                # 더보기 버튼 클릭 시도
                more_button = self.driver.find_element(By.XPATH, '//div[@class="lfH3O"]')
                if more_button.is_displayed():
                    more_button.click()
                    time.sleep(0.5)
            except:
                pass

            new_height = self.driver.execute_script("return arguments[0].scrollHeight", container)
            if new_height == previous_height:
                stable_count += 1
            else:
                stable_count = 0
            previous_height = new_height

    def batch_save_data(self, batch_size=10):
        """배치 단위로 데이터 저장"""
        if len(self.stores) >= batch_size:
            df = pd.DataFrame(self.stores)
            df.to_csv('종로구/이화동 맛집.csv', mode='a', encoding='utf-8-sig',
                      index=False, header=self.is_first_save)

            print(f"배치 저장 완료 - {len(self.stores)}개 가게")
            self.stores.clear()
            self.is_first_save = False

    def handle_page_navigation(self, page_no):
        """페이지 네비게이션 처리"""
        if page_no == '3':
            print("페이지 3 - 드라이버 재시작")
            self.driver.quit()
            self.setup_driver()

            URL = 'https://map.naver.com/search/이화동 맛집'
            self.driver.get(URL)
            time.sleep(2)  # 페이지 로드 대기

            self.switch_left()
            self.driver.find_element(By.XPATH, self.div + 'a[4]').click()
            print("3 페이지 진행")

        return self.driver.find_element(By.XPATH, '//a[contains(@class, "mBN2s qxokY")]').text

    def crawl_current_page(self):
        """현재 페이지 크롤링"""
        self.switch_left()

        # 페이지 정보 확인
        try:
            next_page = self.driver.find_element(By.XPATH, self.div + 'a[7]').get_attribute('aria-disabled')
        except:
            self.div = '//*[@id="app-root"]/div/div[2]/div[2]/'
            next_page = self.driver.find_element(By.XPATH, self.div + 'a[7]').get_attribute('aria-disabled')

        page_no = self.driver.find_element(By.XPATH, '//a[contains(@class, "mBN2s qxokY")]').text

        # 페이지 3 처리
        if page_no == '3':
            page_no = self.handle_page_navigation(page_no)

        # 스마트 스크롤로 모든 요소 로드
        self.smart_scroll('//*[@id="_pcmap_list_scroll_container"]')

        # 가게 요소들 수집
        restaurant_elements = self.driver.find_elements(
            By.XPATH,
            '//*[@id="_pcmap_list_scroll_container"]//li[@data-laim-exp-id="undefinedundefined" and count(div) > 2]'
        )

        print(f'페이지 {page_no}: {len(restaurant_elements)}개 가게 발견')

        # 각 가게 정보 추출 (병렬 처리 대신 순차 처리 - 네이버 지도 특성상)
        for index, element in enumerate(restaurant_elements, start=1):
            store_info = self.extract_store_info(element, index)
            if store_info:
                self.stores.append(store_info)

            # 배치 저장
            self.batch_save_data(batch_size=5)  # 더 자주 저장

        return next_page == 'false'

    def run(self):
        """메인 크롤링 실행"""
        self.setup_driver()

        try:
            URL = 'https://map.naver.com/search/이화동 맛집'
            self.driver.get(URL)
            time.sleep(3)  # 초기 로드 대기

            while True:
                can_continue = self.crawl_current_page()

                if can_continue:
                    try:
                        self.switch_left()
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, self.div + 'a[7]'))
                        )
                        next_button.click()
                        print("다음 페이지 진행")
                        time.sleep(2)  # 페이지 로드 대기
                    except:
                        print("다음 페이지 클릭 실패, 종료")
                        break
                else:
                    print("마지막 페이지 도달, 크롤링 종료")
                    break

        except Exception as e:
            print(f"크롤링 중 오류 발생: {str(e)}")
        finally:
            # 남은 데이터 저장
            if self.stores:
                df = pd.DataFrame(self.stores)
                df.to_csv('종로구/이화동 맛집.csv', mode='a', encoding='utf-8-sig',
                          index=False, header=self.is_first_save)
                print(f"최종 저장 - {len(self.stores)}개 가게")

            self.driver.quit()
            print("크롤링 완료!")


# 크롤링 실행
if __name__ == "__main__":
    crawler = NaverMapCrawler()
    crawler.run()
