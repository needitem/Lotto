import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pandas as pd
import numpy as np
import openpyxl
from tensorflow.keras.utils import to_categorical
import requests
from bs4 import BeautifulSoup


# 데이터 불러오기 (xlsx 파일)
def read_data(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active
    rounds = []
    winning_numbers = []
    for row in sheet.iter_rows(values_only=True):
        rounds.append(row[1])
        winning_numbers.append(row[13:19])
    df = pd.DataFrame({"회차": rounds, "당첨번호": winning_numbers})
    df.dropna(inplace=True)
    return df


# 웹 스크래핑 (당첨 횟수 및 비율)
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
numberrate = pd.DataFrame(data, columns=headers)
numberrate.dropna(inplace=True)  # None 값 제거
numberrate["숫자"] = numberrate["숫자"].astype(int)
numberrate["당첨 횟수"] = (
    numberrate["당첨 횟수"]
    .astype(str)
    .str.replace(r"[^\d]", "", regex=True)
    .astype(int)
)
numberrate["당첨 비율"] = (
    numberrate["당첨 비율"]
    .astype(str)
    .str.replace(r"[^\d.]", "", regex=True)
    .astype(float)
    / 100
)  # 백분율을 소수로 변환

# 데이터 불러오기
df = read_data("dataset.xlsx")
df.dropna(inplace=True)

# 데이터 분할
train_size = int(0.8 * len(df))
train_data = df[:train_size]
test_data = df[train_size:]


# 특성 및 레이블 생성 (이전 당첨 번호 기반)
def create_sequences(data, seq_length):
    X = []
    y = []
    for i in range(len(data) - seq_length):
        seq = data.iloc[i : i + seq_length]["당첨번호"].explode().tolist()
        if any(x is None for x in seq):
            continue
        X.append(seq)
        y.append(list(data.iloc[i + seq_length]["당첨번호"]))
    return np.array(X), np.array(y)


seq_length = 10
X_train, y_train = create_sequences(train_data, seq_length)
X_test, y_test = create_sequences(test_data, seq_length)

print("X_train shape:", X_train.shape)
print("y_train shape:", y_train.shape)

# 모델 구축 (수정)
model = keras.Sequential(
    [
        layers.Input(shape=(seq_length * 6,)),
        layers.Embedding(input_dim=46, output_dim=8),
        layers.LSTM(64),
        layers.RepeatVector(6),  # 6개 숫자 예측으로 변경
        layers.LSTM(32, return_sequences=True),
        layers.TimeDistributed(layers.Dense(46)),
        layers.Activation("softmax"),
    ]
)


# 예측 함수 (TensorFlow)
def predict_next_round_tf(model, last_rounds, num_predictions=5):
    last_rounds = np.array(last_rounds).reshape(1, seq_length * 6)
    predictions = []
    for _ in range(num_predictions):
        logits = model.predict(last_rounds)
        probabilities = tf.nn.softmax(logits, axis=-1)
        top_indices = tf.argsort(probabilities, direction="DESCENDING")[:, :, :6]
        predictions.append([idx + 1 for idx in top_indices[0].numpy()])
    return predictions


# 예측 함수 (당첨 비율 가중치)
def predict_next_round(numberrate, num_predictions=5):
    num_balls = 6
    predictions = []
    for _ in range(num_predictions):
        probabilities = numberrate["당첨 비율"] / numberrate["당첨 비율"].sum()
        pred = np.random.choice(
            numberrate["숫자"], size=num_balls, replace=False, p=probabilities
        )
        predictions.append(sorted(pred))
    return predictions


# 모델 컴파일 및 학습
model.compile(
    loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"]
)
model.fit(
    X_train,
    y_train,
    epochs=50,
    batch_size=32,
    validation_data=(X_test, y_test),
)

# 예측 및 출력
last_rounds = df["당첨번호"].tail(seq_length).explode().tolist()
next_round_predictions_tf = predict_next_round_tf(model, last_rounds)
print("다음 회차 예상 번호 (TensorFlow):")
for prediction in next_round_predictions_tf:
    print(prediction)

next_round_predictions_rate = predict_next_round(numberrate)
print("\n다음 회차 예상 번호 (당첨 비율 가중치):")
for prediction in next_round_predictions_rate:
    print(prediction)
