import pandas as pd
from sqlalchemy import create_engine

# PostgreSQL 연결 설정
username = 'dbproject'  # PostgreSQL 사용자 이름
password = '1234'  # PostgreSQL 비밀번호
database_name = 'crimemanagementsystem'  # 데이터베이스 이름
host = 'localhost'  # 데이터베이스 호스트
port = '5432'  # PostgreSQL 기본 포트

# PostgreSQL 연결 URI 생성
engine = create_engine(f'postgresql://{username}:{password}@{host}:{port}/{database_name}')

# SQL 쿼리 실행하여 데이터 가져오기
query = "SELECT * FROM offender_description"  # 원하는 쿼리 작성
df = pd.read_sql(query, engine)  # 쿼리 결과를 pandas DataFrame으로 읽어오기

# DataFrame을 CSV 파일로 저장
df.to_csv('offender_desciption_data.csv', index=False)  # index=False는 행 인덱스를 CSV에 포함하지 않도록 설정
