import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

allow_duplicates = False

def get_lotto_numbers(n):
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
        data.append(cols)

    headers = ["숫자", "당첨 횟수", "당첨 비율"]
    df = pd.DataFrame(data, columns=headers)

    df["당첨 비율"] = df["당첨 비율"].astype(str).str.replace("", "0", regex=False)
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

def generate_lotto():
    try:
        n = int(num_combinations_entry.get())
        if n <= 0:
            raise ValueError("양수를 입력해야 합니다.")
        lotto_combinations = get_lotto_numbers(n)

        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        for i, numbers in enumerate(lotto_combinations):
            result_text.insert(tk.END, f"{i+1}번째 조합: {sorted(numbers)}\n")
        result_text.config(state=tk.DISABLED)
    except ValueError as e:
        messagebox.showerror("오류", str(e))

def toggle_duplicates():
    global allow_duplicates
    allow_duplicates = not allow_duplicates
    duplicate_status_label.config(text=f"중복 {'허용' if allow_duplicates else '불가'}")

window = tk.Tk()
window.title("로또 번호 추첨기")

ttk.Label(window, text="조합 개수:").grid(row=0, column=0, padx=5, pady=5)
num_combinations_entry = ttk.Entry(window)
num_combinations_entry.grid(row=0, column=1, padx=5, pady=5)

generate_button = ttk.Button(window, text="번호 생성", command=generate_lotto)
generate_button.grid(row=1, column=0, columnspan=2, pady=10)

toggle_button = ttk.Button(window, text="중복 토글", command=toggle_duplicates)
toggle_button.grid(row=1, column=2, padx=5, pady=10)

duplicate_status_label = ttk.Label(window, text="중복 불가")
duplicate_status_label.grid(row=0, column=2, padx=5, pady=5)

result_text = tk.Text(window, wrap=tk.WORD, state=tk.DISABLED)
result_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

window.mainloop()
