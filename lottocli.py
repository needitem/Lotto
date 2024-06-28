import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

def get_lotto_numbers(n, allow_duplicates=False):
    url = "https://www.dhlottery.co.kr/gameResult.do?method=statByNumber"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", {"class": "tbl_data tbl_data_col"})

    data = []
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]
        if len(cols) == 3 and cols[0]:  # 빈 문자열 제외
            data.append(cols)

    headers = ["숫자", "당첨 횟수", "당첨 비율"]
    df = pd.DataFrame(data, columns=headers)

    df["당첨 비율"] = (
        df["당첨 비율"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("", "0")  # 빈 문자열을 0으로 대체
    )

    # 숫자 이외의 문자 제거 후 float 형변환
    df["당첨 비율"] = (
        df["당첨 비율"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)
    )

    # 당첨 비율이 0보다 크고 빈 문자열이 아닌 숫자만 필터링
    valid_numbers = df[(df["당첨 비율"] > 0) & (df["숫자"] != "")]["숫자"].tolist()
    weights = df[(df["당첨 비율"] > 0) & (df["숫자"] != "")]["당첨 비율"].tolist()

    lotto_numbers = []
    available_numbers = valid_numbers.copy()
    while len(lotto_numbers) < n:
        # 중복 허용 여부에 따라 로또 번호 추출
        if allow_duplicates:
            numbers = np.random.choice(
                valid_numbers, size=6, replace=True, p=weights / np.sum(weights)
            ).tolist()
        else:
            if len(available_numbers) < 6:
                available_numbers = valid_numbers.copy()  # 사용 가능한 번호 초기화
            numbers = np.random.choice(available_numbers, size=6, replace=False).tolist()
            for num in numbers:
                available_numbers.remove(num)

        lotto_numbers.append(numbers)  # 정렬하지 않고추가

    return lotto_numbers

if __name__ == "__main__":
    while True:
        try:
            combinations = int(input("생성할 조합 개수를 입력하세요 (0 입력 시 종료): "))
            if combinations == 0:
                break
            if combinations < 0:
                raise ValueError("양수를 입력해야 합니다.")

            duplicate_input = input("중복을 허용하시겠습니까? (y/n): ")
            allow_duplicates = duplicate_input.lower() == "y"

            lotto_combinations = get_lotto_numbers(combinations, allow_duplicates)

            for i, numbers in enumerate(lotto_combinations):
                print(f"{i+1}번째 조합: {sorted(numbers)}")  # 오름차순 정렬하여 출력

        except ValueError as e:
            print(f"오류: {e}")
