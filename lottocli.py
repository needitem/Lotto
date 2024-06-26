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
        # 데이터가 3개 미만인 경우(잘못된 데이터) 제외
        if len(cols) == 3:
            data.append(cols)

    headers = ["숫자", "당첨 횟수", "당첨 비율"]
    df = pd.DataFrame(data, columns=headers)

    # 빈 문자열을 0으로 대체
    df["당첨 비율"] = (
        df["당첨 비율"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("", "0")
    )

    # 숫자 이외의 문자 제거 후 float 형변환
    df["당첨 비율"] = (
        df["당첨 비율"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)
    )

    weights = df["당첨 비율"].tolist()

    lotto_numbers = []
    available_numbers = list(df["숫자"])
    while len(lotto_numbers) < n:
        if allow_duplicates or len(available_numbers) < 6:
            numbers = np.random.choice(
                df["숫자"], size=6, replace=True, p=weights / np.sum(weights)
            )
        else:
            numbers = np.random.choice(available_numbers, size=6, replace=False)
            for num in numbers:
                available_numbers.remove(num)
        lotto_numbers.append(set(numbers.tolist()))

    return lotto_numbers


if __name__ == "__main__":
    while True:
        try:
            combinations = int(
                input("생성할 조합 개수를 입력하세요 (0 입력 시 종료): ")
            )
            if combinations == 0:
                break
            if combinations < 0:
                raise ValueError("양수를 입력해야 합니다.")

            duplicate_input = input("중복을 허용하시겠습니까? (y/n): ")
            allow_duplicates = duplicate_input.lower() == "y"

            lotto_combinations = get_lotto_numbers(combinations, allow_duplicates)

            for i, numbers in enumerate(lotto_combinations):
                print(f"{i+1}번째 조합: {sorted(numbers)}")

        except ValueError as e:
            print(f"오류: {e}")
