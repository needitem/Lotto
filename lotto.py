import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


def get_lotto_numbers(n):
    # 1. URL 및 헤더 설정 (변경 없음)
    url = "https://www.dhlottery.co.kr/gameResult.do?method=statByNumber"
    headers = {"User-Agent": "Mozilla/5.0"}

    # 2. HTML 요청 및 파싱 (변경 없음)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    # 3. 테이블 찾기 (변경 없음)
    table = soup.find("table", {"class": "tbl_data tbl_data_col"})

    # 4. 테이블 데이터 추출 (당첨 비율 컬럼 형변환)
    data = []
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]
        data.append(cols)

    # 5. 데이터프레임 생성 및 전처리 (빈 문자열 처리 추가)
    headers = ["숫자", "당첨 횟수", "당첨 비율"]
    df = pd.DataFrame(data, columns=headers)

    # 당첨 비율 컬럼에서 빈 문자열('')을 0으로 대체
    df["당첨 비율"] = df["당첨 비율"].astype(str).str.replace("", "0", regex=False)

    # 숫자와 '.' 이외의 문자 제거 후 float으로 변환
    df["당첨 비율"] = (
        df["당첨 비율"].astype(str).str.replace(r"[^\d.]", "", regex=True).astype(float)
    )

    # 6. 가중치 리스트 생성 (당첨 비율 기반)
    weights = df["당첨 비율"].tolist()

    # 7. 로또 번호 추첨 (n번, 중복 최소화)
    lotto_numbers = []
    while len(lotto_numbers) < n:
        numbers = np.random.choice(
            df["숫자"], size=6, replace=False, p=weights / np.sum(weights)
        )
        lotto_set = set(numbers.tolist())  # 중복 제거를 위한 set 변환
        if (
            lotto_set not in lotto_numbers
        ):  # 기존에 뽑힌 번호 조합과 중복되지 않을 때만 추가
            lotto_numbers.append(lotto_set)

    return lotto_numbers


def generate_lotto():
    try:
        n = int(num_combinations_entry.get())
        if n <= 0:
            raise ValueError("양수를 입력해야 합니다.")
        lotto_combinations = get_lotto_numbers(n)

        result_text.config(state=tk.NORMAL)  # 결과 출력 창 활성화
        result_text.delete(1.0, tk.END)  # 기존 내용 삭제
        for i, numbers in enumerate(lotto_combinations):
            result_text.insert(tk.END, f"{i+1}번째 조합: {sorted(numbers)}\n")
        result_text.config(state=tk.DISABLED)  # 결과 출력 창 비활성화
    except ValueError as e:
        messagebox.showerror("오류", str(e))


# UI 생성
window = tk.Tk()
window.title("로또 번호 추첨기")

# 조합 개수 입력
ttk.Label(window, text="조합 개수:").grid(row=0, column=0, padx=5, pady=5)
num_combinations_entry = ttk.Entry(window)
num_combinations_entry.grid(row=0, column=1, padx=5, pady=5)

# 버튼
generate_button = ttk.Button(window, text="번호 생성", command=generate_lotto)
generate_button.grid(row=1, column=0, columnspan=2, pady=10)

# 결과 출력 창
result_text = tk.Text(window, wrap=tk.WORD, state=tk.DISABLED)  # 초기 상태: 비활성화
result_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

window.mainloop()
