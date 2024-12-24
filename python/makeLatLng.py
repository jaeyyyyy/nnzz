from dotenv import load_dotenv
import os
import pandas as pd
import requests
import json

# 네이버 검색 api 사용해서 위도 경도 가져오기
load_dotenv()

CLIENT_ID = os.getenv('client_id')
CLIENT_SECRET = os.getenv('client_secret')

# 역 별로 크롤링한 데이터를 합친 csv파일에 위/경도를 추가
df = pd.read_csv('식당 데이터.csv')

mapx_list = []
mapy_list = []

for name in df['name']:
  url =  f"https://openapi.naver.com/v1/search/local.json?query={name}&display=5&start=1&sort=random"
  headers = {
    'X-Naver-Client-Id': CLIENT_ID,
    'X-Naver-Client-Secret': CLIENT_SECRET
  }

  response = requests.get(url, headers=headers)

  if response.status_code == 200:
    result = response.json()
    print(result)  # API 응답을 출력하여 확인

    # items의 개수가 하나 이상 있다면
    if len(result['items']) > 1:
      found = False
      for item in result['items']:
        if 'roadAddress' in item:
          road_address_parts = item['roadAddress'].split()
          filtered_road_address = ' '.join(road_address_parts[1:]) # 00특별시 제외

          # address가 filtered_road_address를 포함하는지 확인
          if filtered_road_address in df.loc[df['name'] == name, 'address'].values[0]:
            mapx = int(item['mapx']) / 10000000
            mapy = int(item['mapy']) / 10000000
            mapx_list.append(mapx)
            mapy_list.append(mapy)
            found = True
            break

      # 5개 중에 해당하는 결과가 없다면, 이름과 카테고리를 함께 검색
      if not found:
        gu_ro_parts = df.loc[df['name'] == name, 'address'].values[0].split()
        gu_ro = ' '.join(gu_ro_parts[1:3])  # '00구 00로'을 만들기 위해 1번과 2번 인덱스를 사용
        combined_query = f"{name} {gu_ro}"
        url = f"https://openapi.naver.com/v1/search/local.json?query={combined_query}&display=5&start=1&sort=random"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
          result = response.json()
          print(result)  # API 응답을 출력하여 확인

          if len(result['items']) > 0:
            found = False
            for item in result['items']:
              if 'roadAddress' in item:
                road_address_parts = item['roadAddress'].split()
                filtered_road_address = ' '.join(road_address_parts[1:])  # 00특별시 제외

                # address가 filtered_road_address를 포함하는지 확인
                if filtered_road_address in df.loc[df['name'] == name, 'address'].values[0]:
                  mapx = int(item['mapx']) / 10000000
                  mapy = int(item['mapy']) / 10000000
                  mapx_list.append(mapx)
                  mapy_list.append(mapy)
                  found = True
                  break

          if not found:
            mapx_list.append(None)
            mapy_list.append(None)
        else:
          mapx_list.append(None)
          mapy_list.append(None)

    else:
      mapx_list.append(None)
      mapy_list.append(None)
  else:
    mapx_list.append(None)
    mapy_list.append(None)

df['mapx'] = mapx_list
df['mapy'] = mapy_list

df.to_csv('식당 데이터(위경도o).csv', index=False, encoding='utf-8-sig')

