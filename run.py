import psycopg2, random, sys, traceback
from flask import Flask, redirect, request, render_template, url_for, jsonify, session, g
from itertools import islice
from functools import wraps
import string
import joblib
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import folium

global alert_msg

app = Flask(__name__)
app.secret_key = '1234'

# crime_predictor_model 로드
with open("crime_predictor_model.pkl","rb") as f:
    crime_model = joblib.load(f)

# offender_location_predict 로드
with open("offender_location_predict.pkl","rb") as f:
    location_model = joblib.load(f)

def connectDB(USER,pwd):
    global conn,cur
# connect to database
    try:
        conn = psycopg2.connect(
            dbname="crimemanagementsystem",
            user=USER, 
            password=pwd, 
            host="localhost",  # 로컬에서 작업할 때는 localhost, AWS 작업할 때는 0.0.0.0 설정 -> 티스토리 참고
            port="5432")
        # make cursor
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None, None
    
def get_db():
    if 'db' not in g:
        g.db, g.cur = connectDB(session.get('user'), session.get('password'))
    return g.db, g.cur

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def with_transaction(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conn, cur = get_db()
        if not conn or not cur:
            return "데이터베이스 연결 오류", 500
        try:
            conn.autocommit = False
            result = f(cur, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            print("오류 발생:")
            print(traceback.format_exc())
            return str(e), 500
        finally:
            conn.autocommit = True
    return decorated_function

# main page
@app.route("/")
def main():
    return render_template('main.html',title='main_page')

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    pwd  = request.form.get('pwd')

    # connect to database
    conn, cur = connectDB(user, pwd)

    if conn and cur:
        session['user'] = user
        session['password'] = pwd
        
        if user == 'police_manager':
            return redirect(url_for('police_manager'))
        elif user == 'police_detective':
            return redirect(url_for('police_detective'))
        elif user == 'citizen':
            return redirect(url_for('citizen'))
        elif user == 'offender':
            return redirect(url_for('offender'))
    else:
        return render_template("main.html", flag="데이터 베이스 연결에 실패했습니다. 다시 시도해주세요.")

#animal page
@app.route("/animal")
def animal():
    return render_template('animal.html')

#dog page
@app.route("/dog")
def dog():
    return render_template('dog.html')

#police_manager page
@app.route("/police_manager")
def police_manager():
    return render_template('police_manager.html')


#police_detetive page
@app.route("/police_detective")
def police_detective():
    return render_template('police_detective.html')

#citizen page
@app.route("/citizen")
def citizen():
    return render_template('citizen.html')


#offender page
@app.route("/offender")
def offender():
    return render_template('offender.html')

###############################
# police_manager
#get_police
@app.route("/get_police")
@with_transaction
def get_police(cur):
    region = request.args.get("region")
    cur.execute(f"""select *
                    from police 
                    where police_station_id in 
                        (select id 
                        from police_station 
                        where region_id = {region})""")
    polices = cur.fetchall()
    police_list_html = ""
    for police in polices:
        police_list_html += """<tr><td class='tg-c3ow' id='police_id'>{}</td><td class='tg-c3ow' id='name'>{}</td><td class='tg-c3ow' id='number'>{}</td><td class='tg-c3ow'><select id='new_region'>""".format(police[0], police[1], police[2])
        for i in range(78):
            police_list_html += """<option value="{}">{}</option>""".format(i, i)
        police_list_html += """</select><button onclick="select_new_region(this)">선택</button></td></tr>"""
    return police_list_html

#select_police
@app.route("/select_police")
@with_transaction
def select_police(cur):
    id = request.args.get("id")
    new_region = request.args.get("new_region")
    region = request.args.get("region")
    cur.execute(f"""UPDATE police 
                    SET police_station_id = 
                        (SELECT id
                        FROM police_station
                        WHERE region_id = {new_region}) 
                    WHERE id = '{id}';
                    commit;""")
    cur.execute(f"""with tb as (select region_id, count(*) as ct
			                from police, police_station ps
			                where police.police_station_id = ps.id
			                group by region_id
			                order by region_id)
                update police_station 
                set num_of_police = tb.ct
                from tb
                where police_station.region_id = tb.region_id;
                """)
    cur.execute(f"select region_id, num_of_police from police_station where region_id in ({region}, {new_region})")
    new_police_station = cur.fetchall()
    msg = ""
    for i in new_police_station:
        msg += f"{i[0]}번 구역의 경찰 인원이 {i[1]}명으로 조정 되었습니다.\n"
    return msg

#get report list from db
@app.route("/get_report_list", methods=['POST'])
@with_transaction
def get_report_list(cur):
    cur.execute(f"select * from notify_crime")
    reports = cur.fetchall()
    report_msg = ""
    for report in reports:
        report_msg += """<tr><td class='tg-c3ow' id='report_id'>{}</td><td class='tg-c3ow' id='date'>{}</td><td class='tg-c3ow' id='crime_type'>{}</td><td class='tg-c3ow' id='witness'>{}</td></tr>""".format(report[0], report[1], report[2], report[3])
    return report_msg

@app.route('/enroll_crime', methods=['POST'])
@with_transaction
def enroll_crime(cur):
    offender_id = request.form['offender_id']
    id = request.form['id']
    date= request.form['date']
    block = request.form['block']
    iucr = request.form['iucr']
    location_desciption = request.form['location_description']
    region = request.form['region']
    arrest = request.form.get('arrest', 'false') == 'true'
    alert_msg = ""

    if arrest:
        name = request.form['name']
        gender = request.form['gender']
        age = request.form['age']
        ########################## 용의자 id가 이미 테이블에 존재하면, 용의자 위치 정보만 갱신  ##########################
        cur.execute(f"""insert into offender
                    values ({offender_id}, '{name}', '{gender}', {age}, 'n')""")
        cur.execute(f"""insert into offender_location
                    values ({offender_id}, {region}, '{date}')""")
        cur.execute(f"insert into crime values ({offender_id}, '{id}', '{date}', '{block}', '{iucr}', '{location_desciption}',True, {region})")
        
        # SweetAlert2 메세지용
        alert_msg += f"""------------------------------------------------------------<br>
        용의자 정보<br>
        -----------------------------------------------------------<br>
        id : {offender_id}<br>
        name : {name}<br>
        gender : {gender}<br>
        age : {age}<br>
        wanted : n<br>
        -----------------------------------------------------------<br>
        용의자 위치 정보<br>
        -----------------------------------------------------------<br>
        offender_id : {offender_id}<br>
        region : {region}<br>
        date : {date}<br>
        -----------------------------------------------------------<br>
        사건<br>
        -----------------------------------------------------------<br>
        id : {id}<br>
        date : {date}<br>
        block : {block}<br>
        iucr : {iucr}<br>
        location_description : {location_desciption}<br>
        arrest : {arrest}<br>
        region : {region}<br>
        """

    else:
        cur.execute(f"insert into crime values (null, '{id}', '{date}', '{block}', '{iucr}', '{location_desciption}',False, {region})")
        alert_msg += f""" 사건 정보<br>
        -----------------------------------------------------------<br>
        id : {id}<br>
        date : {date}<br>
        block : {block}<br>
        iucr : {iucr}<br>
        location_description : {location_desciption}<br>
        arrest : {arrest}<br>
        region : {region}<br>
        """
    ## region 테이블의 num_of_crime를 update
    cur.execute(f"update region set num_of_crime = num_of_crime+1 where id={region}")
    # change_risk_level 함수 실행
    alert_msg += change_risk_level(region)[0]

    return alert_msg

def sort_by_second_value(data):
    return sorted(data, key=lambda x: x[1], reverse=True)

def change_risk_level(region):
    # 범죄 유형, 범죄 빈도, 수배중인 범죄자의 여부에 따라 위험도 변경
    cur.execute(f"select degree_of_danger from region where id = {region}")
    inf = cur.fetchone()
    risk_level = inf[0]
    # 살인, 강간, 인신매매 -> 5
    # 강도, 마약 -> 4
    # 폭행 -> 3
    # 절도 -> 2
    # 나머지 -> 1 의 가중치 부여
    # region_id, 유형별 범죄빈도*가중치의 합, 수배중인 범죄자 수
    cur.execute(f"""with tb2 as
                    (select ol.region_id , count(*) as cnt2
                    from offender o, offender_location ol 
                    where o.id = ol.offender_id and o.wanted ='y'
                    group by ol.region_id),
                tb as(
                    select c.region_id , ct.weight , count(*) as cnt
                    from crime c , crime_type ct 
                    where c.iucr = ct.iucr 
                    group by c.region_id , ct.weight)
                select tb.region_id, sum(weight*cnt), tb2.cnt2
                from tb left join tb2 on tb.region_id = tb2.region_id
                where tb.region_id is not null 
                group by tb.region_id, tb2.cnt2;""")
    region_risk = cur.fetchall()
    new_region_risk = []
    # 각 지역의 위험도는 (유형별 범죄 빈도*weight)의 합에 수배자의 수만큼 가중치(0.5)를 준 값이다.
    for i in region_risk:
        region_id = i[0]
        sum_crime = int(i[1])
        num_wanted = i[2]
        if num_wanted is None:
            new_risk_level = sum_crime
        else:
            new_risk_level = sum_crime*(1+num_wanted*0.5)
        new_region_risk.append((region_id, new_risk_level))
    # 위험도를 기준으로 정렬
    sorted_region_risk = sort_by_second_value(new_region_risk)
    # 위험도 순위 갱신
    for i in sorted_region_risk:
        cur.execute(f"update region set degree_of_danger = {sorted_region_risk.index(i)+1} where id = {i[0]}")
    # 갱신된 위험도 순위 안내
    # next(이터레이터, 디폴트) : 이터레이터에서 순회하면서 첫번째 값을 반환함
    # iterator - iter([1,2,3]) 혹은 제너레이터 표현식으로 표현 가능
    # 제너레이터 표현식 - (expression for item in iterable if condition)
    # ex - (i for i,x in enumerate(sorte_list) if x[0]==region)
    # list를 순회하면서 index(i), 값(x)을 찾고, 조건에 맞는 경우에만 i를 반화하는 제너레이터를 생성, 이는 이터레이터가 된다.
    # enumerate 함수 - for i,x in enumerate() : i는 인덱스, x는 값 (0, (1, 200))
    new_risk_level = next((i for i, x in enumerate(sorted_region_risk) if x[0] == int(region)), 99)
    new_risk_level = int(new_risk_level)+1
    msg = f"----------------------------------------------------------<br>"
    msg += f" {region}번 지역의 기존 위험도는 {risk_level}등급 입니다.<br>"
    msg += f" {region}번 지역의 현재 위험도는 {new_risk_level}등급 입니다<br>"
    msg += f"------------------------------------------------------------<br>"
    html_msg = ""
    # 위험도 상승 시, emergency_deployment 실행하여 해당 지역의 배치 인원을 증가
    if new_risk_level > risk_level:
        msg += f" {region}번 지역의 위험도가 상승하였습니다. 긴급 경찰 인력 배치를 실행합니다.<br>"
        (new_msg, html_msg) = emergency_deployment(region)
        msg += new_msg
               
    return (msg, html_msg)

def generate_police_id(police_list):
    while True:
        police_id = "".join(str(random.randint(0, 9)) for _ in range(10))
        if police_id not in police_list:
            return police_id

def generate_police_phone_number():
    area_code = random.randint(0, 9999)
    last_four_digits = random.randint(0, 9999)
    return f"010-{area_code:03d}-{last_four_digits:04d}"

def emergency_deployment(region):
    # 위험도 변경 시 경찰 인원 변경 요청창
    # 해당 지역의 경찰서의 id, 경찰수, 경찰 id 리스트(중복 확인용)를 요청
    cur.execute(f"select id, num_of_police from police_station where region_id = {region}")
    station_inf = cur.fetchone()
    police_station_id = station_inf[0]
    num_of_police = station_inf[1]
    cur.execute("select id from police")
    police_list = cur.fetchall()
    # 해당 지역의 경찰 수/10 만큼 새로운 경찰을 투입
    # 투입된 경찰의 정보를 출력
    html_msg = ""
    new_num = num_of_police//10
    for i in range(new_num):
        id = generate_police_id(police_list)
        phone_number = generate_police_phone_number()
        html_msg += f"<tr><td class='tg-c3ow' id='police_id'>{id}</td><td class='tg-c3ow' id='police_station_id'>{police_station_id}</td><td class='tg-c3ow' id='phone_number'>{phone_number}</td></tr>"
        cur.execute(f"""insert into police
                        values('{id}', '{police_station_id}', '{phone_number}')""")
    cur.execute(f"update police_station set num_of_police = num_of_police+{new_num}  where region_id = {region}")
    # 기존 인원과 현재 인원을 출력
    msg = f"{region}번 지역의 경찰 수가 기존 인원 {num_of_police}명에서 {new_num}만큼 증가하여 현재 {num_of_police+new_num}명이 되었습니다."

    return (msg, html_msg)

@app.route('/view_region_offender', methods=['POST'])
@with_transaction
def view_region_offender(cur):
    region = request.form.get('region_offender')
    offender_html = ""               
    # 지역을 선택하여 해당 지역의 위치 정보가 끊긴 범죄자 출력
    cur.execute(f"""SELECT *
                FROM offender_location ol
                WHERE ol.region_id = {region} and ol.send_date < CURRENT_DATE - INTERVAL '3 MONTH'""")
    wanted_offender = cur.fetchall()
    for i in wanted_offender:
        offender_html += f"<tr><td class='tg-c3ow' id='offender_id'>{i[0]}</td><td class='tg-c3ow' id='last_date'>{i[2]}</td></tr>"
        # 해당 범죄자를 wanted 처리
        cur.execute(f"update offender set wanted = 'y' where id = {i[0]}")
    # change_risk_level 함수 실행
    (message, police_html) = change_risk_level(region)
    formatted_message = message.replace('\n','<br>')
    return jsonify({'message': formatted_message,
                    'police_html': police_html,
                    'offender_html': offender_html
                    })

def generate_investigation_id():
    # investigation_id에 대한 리스트
    cur.execute(f"select id from investigation")
    list = cur.fetchall()
    inv_list = [sublist[0] for sublist in list]
    while True:
        investigation_id = "".join(str(random.randint(0, 9)) for _ in range(8))
        if investigation_id not in inv_list:
            return investigation_id

@app.route('/investigation', methods=['POST'])
@with_transaction
def investigation(cur):
    # 아직 investigation이 이루어지지 않은 사건을 조회
    cur.execute(f"""select *
                from crime c
                where c.investigation_id is null;""")
    non_investigation_crime = cur.fetchall()
    investigation_html = ""
    for i in islice(non_investigation_crime,10):
        # 새로운 investigation 생성
        # id는 랜덤으로 생성, 날짜는 현재 날짜에서 시작하여 열흘 뒤 종료, 담당 조사관은 랜덤으로 선택
        investigation_id = generate_investigation_id()
        cur.execute(f"""insert into investigation
                        SELECT 
                            '{investigation_id}', CURRENT_DATE, CURRENT_DATE + INTERVAL '10 days', p.id
                        FROM 
                            police p
                        JOIN 
                            police_station ps ON p.police_station_id = ps.id
                        WHERE 
                            ps.region_id = 1
                        ORDER BY 
                            RANDOM()
                        LIMIT 1
                        RETURNING *;""" )
        #investigation_table에 삽입할 행 추가
        inserted_row = cur.fetchone()
        investigation_html += f"<tr><td class='tg-c3ow' id='investigation_id'>{inserted_row[0]}</td><td class='tg-c3ow' id='crime_id'>{i[1]}</td><td class='tg-c3ow' id='start_date'>{inserted_row[1]}</td><td class='tg-c3ow' id='last_date'>{inserted_row[2]}</td><td class='tg-c3ow' id='police_id'>{inserted_row[3]}</td></tr>"
        # 해당 crime에 investigation_id 추가
        cur.execute(f"update crime set investigation_id = '{investigation_id}' where id = '{i[1]}'")

    return investigation_html
    
@app.route('/get_non_investigation_list', methods=['POST'])
@with_transaction
def get_non_investigation_list(cur):
    html_msg = ""
    cur.execute(f"""select *
                    from crime c
                    where c.investigation_id is null;""")
    non_investigation_crime = cur.fetchall()
    for crime in non_investigation_crime:
        html_msg += f"<tr><td class='tg-c3ow' id='id'>{crime[1]}</td><td class='tg-c3ow' id='date'>{crime[2]}</td><td class='tg-c3ow' id='iucr'>{crime[4]}</td><td class='tg-c3ow' id='arrest'>{crime[6]}</td><td class='tg-c3ow' id='region_id'>{crime[7]}</td></tr>"
    return html_msg

def get_week_of_month(date_obj):
    # 해당 월의 첫 날
    first_day_of_month = date_obj.replace(day=1)
    
    # 첫 번째 주의 시작 날짜 (월요일 기준으로 계산)
    start_of_week = first_day_of_month - timedelta(days=first_day_of_month.weekday())
    
    # 주 번호 계산
    delta_days = (date_obj - start_of_week).days
    week_number = (delta_days // 7) + 1
    return week_number

@app.route("/crime_risk_prediction", methods=['POST'])
@with_transaction
def crime_risk_prediction(cur):
    region = request.form['region']
    date_str = request.form['date']
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')

    # 월, 주, 요일 추출
    month = date_obj.month
    week_number = get_week_of_month(date_obj)  # 해당 월의 주 번호
    weekday = date_obj.strftime('%A')  # 요일 이름 (예: Sunday)
    
    # 요일을 원하는 순서로 인코딩 (일월화수목금토 = 0123456)
    day_mapping = {
        'Sunday' : 0,
        'Monday' : 1,
        'Tuesday' : 2,
        'Wednesday' : 3,
        'Thursday' : 4,
        'Friday' : 5,
        'Saturday' : 6
    }

    # 요일을 인코딩된 숫자로 변환
    day_encoded = day_mapping[weekday]

    # 학습 시 사용한 특성 이름
    feature_names = ['region', 'month', 'week', 'day_of_week_encoded']

    # 예측 데이터를 DataFrame으로 변환
    input_data = pd.DataFrame([[region, month, week_number, day_encoded]], columns=feature_names)

    # 예측 수행
    prediction = crime_model.predict(input_data)[0]
    result = round(prediction, 2)
    
    # 범죄 횟수 통계 : 25% : 15회, 50%: 30회, 75%:65회
    if (result<=15):
        result_html = f"""  <img src="/static/safe.png" height="100px">
                            <p>{region}번 지역에서 {date_str}에 예측된 범죄 횟수는 {result}번입니다.</p>
                            <button onclick="re_enter()">다시 입력</button>
                        """
    elif (result<=65):
        result_html = f"""  <img src="/static/caution.png" height="100px">
                            <p>{region}번 지역에서 {date_str}에 예측된 범죄 횟수는 {result}번입니다.</p>
                            <button onclick="re_enter()">다시 입력</button>
                        """
    else:
        result_html = f"""  <img src="/static/danger.png" height="100px">
                            <p>{region}번 지역에서 {date_str}에 예측된 범죄 횟수는 {result}번입니다.</p>
                            <button onclick="re_enter()">다시 입력</button>
                        """

    # 결과를 HTML에 전달
    return result_html

#######################
#  Police_Detective
@app.route('/get_investigation_list', methods=['POST'])
@with_transaction
def get_investigation_list(cur):
        police_id = request.form['police_id']
        # 최근 시작한 10개의 investigation을 출력합니다.
        cur.execute(f"""select *
                        from investigation i
                        where i.police_in_charge = '{police_id}'
                        order by i.start_date desc ;""")
        inv_list = cur.fetchall()
        investigation_html = ""
        for i in inv_list:
            investigation_html += f"<tr><td class='tg-c3ow' id='investigation_id'>{i[0]}</td><td class='tg-c3ow' id='start_date'>{i[1]}</td><td class='tg-c3ow' id='end_date'>{i[2]}</td><td class='tg-c3ow' id='select_button'><button onclick='select_investigation(this)'>보기</button></td></tr>"
        return investigation_html

@app.route('/view_investigation_info')
@with_transaction
def view_investigation_info(cur):
    investigation_id = request.args.get('id')

    # 해당 조사의 crime 정보
    cur.execute(f"""select *
                    from crime c 
                    where c.investigation_id = '{investigation_id}';""")
    crime_info = cur.fetchone()
    crime_info_html = f"<tr><td class='tg-c3ow' id='offender_id'>{crime_info[0]}</td><td class='tg-c3ow' id='crime_id'>{crime_info[1]}</td><td class='tg-c3ow' id='date'>{crime_info[2]}</td><td class='tg-c3ow' id='block'>{crime_info[3]}</td><td class='tg-c3ow' id='iucr'>{crime_info[4]}</td><td class='tg-c3ow' id='location_description'>{crime_info[5]}</td><td class='tg-c3ow' id='arrest'>{crime_info[6]}</td><td class='tg-c3ow' id='region'>{crime_info[7]}</td></tr>"
    
    #해당 조사의 증거물 정보
    cur.execute(f"""select *
                    from evidence e 
                    where e.investigation_id = '{investigation_id}';
                    """)
    evidence_infos = cur.fetchall()
    evidence_info_html = ""
    for evidence_info in evidence_infos:
        evidence_info_html += f"<tr><td class='tg-c3ow' id='id'>{evidence_info[0]}</td><td class='tg-c3ow' id='evidence_type'>{evidence_info[2]}</td><td class='tg-c3ow' id='evidence_collected_date'>{evidence_info[3]}</td></tr>"
    
    #해당 조사의 증인 정보
    cur.execute(f"""select *
                    from witness w 
                    where w.crime_id = (
                    select id
                    from crime c
                    where c.investigation_id = '{investigation_id}');
                    """)
    witness_infos = cur.fetchall()
    witness_info_html = ""
    for witness_info in witness_infos:
        witness_info_html += f"<tr><td class='tg-c3ow' id='id'>{witness_info[0]}</td><td class='tg-c3ow' id='name'>{witness_info[1]}</td><td class='tg-c3ow' id='gender'>{witness_info[2]}</td><td class='tg-c3ow' id='age'>{witness_info[3]}</td></tr>"

    #해당 사건의 피해자 정보
    cur.execute(f"""select *
                    from victim v 
                    where v.crime_id = (
                    select id
                    from crime c
                    where c.investigation_id = '{investigation_id}');
                    """)
    victim_infos = cur.fetchall()
    victim_info_html = ""
    for victim_info in victim_infos:
        victim_info_html += f"<tr><td class='tg-c3ow' id='id'>{victim_info[0]}</td><td class='tg-c3ow' id='name'>{victim_info[1]}</td><td class='tg-c3ow' id='gender'>{victim_info[2]}</td><td class='tg-c3ow' id='age'>{victim_info[3]}</td></tr>"

    return render_template('/investigation_info.html', 
                        crime_info_html=crime_info_html ,
                        evidence_info_html=evidence_info_html,
                        witness_info_html=witness_info_html,
                        victim_info_html=victim_info_html)

def generate_evidence_id():
    # evidence_id : 랜덤 문자4+숫자4 으로 이루어진 문자열 ->  중복체크
    cur.execute(f"select id from evidence")
    list = cur.fetchall()
    evd_list = [sublist[0] for sublist in list]
    while True:
        random_chars = ''.join(random.choices(string.ascii_letters, k=5))
        random_numbers = ''.join(random.choices(string.digits, k=5))
        evidence_id = random_chars + random_numbers
        if evidence_id not in evd_list:
            return evidence_id

@app.route('/enroll_evidence', methods=['POST'])
@with_transaction
def enroll_evidence(cur):
    evidence_id = generate_evidence_id()
    investigation_id = request.form['investigation_id']
    evidence_type = request.form['evidence_type']
    date = request.form['date']

    cur.execute(f"insert into evidence values ('{evidence_id}', '{investigation_id}','{evidence_type}','{date}')")

    msg = f"""증거 등록 정보<br>
    --------------------------------<br>
    id : {evidence_id}<br>
    조사 id : {investigation_id}<br>
    증거물 종류 : {evidence_type}<br>
    날짜 : {date}<br>
    ---------------------------------"""

    return msg

def generate_id(table):
   while True:
        id = ''.join(random.choices(string.ascii_letters, k=7))
        cur.execute(f"SELECT id FROM {table} WHERE id = %s", (id,))
        if cur.fetchone() is None:
            return id

@app.route('/enroll_witness', methods=['POST'])
@with_transaction
def enroll_witness(cur):
    witness_id = generate_id('witness')
    name = request.form['name']
    gender = request.form['gender']
    age = int(request.form['age'])
    investigation_id = request.form['investigation_id']

    cur.execute(f"select id from crime c where c.investigation_id = '{investigation_id}'")
    crime_id = cur.fetchone()[0]

    cur.execute(f"insert into witness values ('{witness_id}', '{name}','{gender}',{age}, '{crime_id}')")

    msg = f"""증인 등록 정보<br>
    --------------------------------<br>
    id : {witness_id}<br>
    이름 : {name}<br>
    성별 : {gender}<br>
    나이 : {age}<br>
    사건 id : {crime_id}<br>
    ---------------------------------"""

    return msg

@app.route('/enroll_victim', methods=['POST'])
@with_transaction
def enroll_victim(cur):
    victim_id = generate_id('victim')
    name = request.form['name']
    gender = request.form['gender']
    age = int(request.form['age'])
    investigation_id = request.form['investigation_id']

    cur.execute(f"select id from crime c where c.investigation_id = '{investigation_id}'")
    crime_id = cur.fetchone()[0]

    cur.execute(f"insert into victim values ('{victim_id}', '{name}','{gender}',{age}, '{crime_id}')")

    msg = f"""피해자 등록 정보<br>
    --------------------------------<br>
    id : {victim_id}<br>
    이름 : {name}<br>
    성별 : {gender}<br>
    나이 : {age}<br>
    사건 id : {crime_id}<br>
    ---------------------------------"""

    return msg

@app.route('/change')
@with_transaction
def change(cur):
    # police 테이블에서 모든 id 가져오기
    cur.execute("SELECT id FROM police")
    police_ids = [row[0] for row in cur.fetchall()]

    # investigation 테이블에서 무작위로 행 선택
    cur.execute("SELECT id FROM investigation where police_in_charge = '2870890098' ORDER BY RANDOM() limit 50000")
    investigation_ids = [row[0] for row in cur.fetchall()]

    # 각 선택된 investigation 행에 대해 무작위 police id 할당
    for inv_id in investigation_ids:
        random_police_id = random.choice(police_ids)
        cur.execute("UPDATE investigation SET police_in_charge = %s WHERE id = %s", (random_police_id, inv_id))
        print(inv_id, random_police_id)

    return "success"

def predict_location_model(age, gender, height, weight, prev_lat, prev_long):

    gender_mapping = {"M":0, "F":1}
    gender_encoded = gender_mapping[gender]

# 특성 이름을 명시적으로 지정
    X_pred = pd.DataFrame([
        [int(age), gender_encoded, float(height), float(weight), float(prev_lat), float(prev_long)],
    ], columns=['age', 'gender_encoded', 'height', 'weight', 'prev_lat', 'prev_long'])

    # 예측 수행
    prediction = location_model.predict(X_pred)[0]
    return np.round(prediction, 2)

@app.route("/predict_offender_location", methods=['POST'])
@with_transaction
def predict_offender_location(cur):
    age = request.form['age']
    gender = request.form['gender']
    height = request.form['height']
    weight = request.form['weight']
    prev_lat = request.form['prev_lat']
    prev_long = request.form['prev_long']

    result = predict_location_model(age, gender, height, weight, prev_lat, prev_long)
    latitude, longitude = result[0], result[1]

    # region_data.csv 파일 읽기
    region_data = pd.read_csv('region_data.csv')
    
    # 서울 중심 좌표
    seoul_center = [37.5665, 126.9780]

    # 지도 생성 및 마커 추가
    m = folium.Map(location=seoul_center, zoom_start=1)
    for index, row in region_data.iterrows():
        if (-90 <= row['latitude'] <= 90) and (-180 <= row['longitude'] <= 180):
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"Region {row['id']}",
                tooltip=f"Region {row['id']}"
            ).add_to(m)
    
    folium.Marker(
        location=[latitude, longitude],
        popup=f"용의자 추정 위치",
        tooltip=f"용의자 추정 위치"
        ).add_to(m)

    # 지도 HTML 파일로 저장하고 내용을 읽기
    m.save('templates/predict_offender_location_map.html')
    with open('templates/predict_offender_location_map.html', 'r', encoding='utf-8') as f:
        map_html = f.read()

    # 지도와 예측된 위치를 JSON으로 반환
    return jsonify({'latitude': latitude,
                    'longitude': longitude,
                    'map_html': map_html})

############################3
# Citizen
@app.route('/check_id', methods=['POST'])
@with_transaction
def check_id(cur):
    citizen_id = request.form['citizen_id']

    # 시민 ID로 거주지를 확인
    cur.execute(f"select region from citizen where id='{citizen_id}'")
    list = cur.fetchone()

    # 조회 결과가 없으면, 범죄자인지 확인하거나 잘못된 id 입력을 확인
    if list is None:
        flag = "fail"
        msg = "id 조회 실패 - 해당하는 시민 id가 없습니다."

        # 만약 입력한 id가 offender_id와 일치하면 경고창
        if citizen_id.isdigit():
            cur.execute(f"select * from offender where id={citizen_id}")
            is_offender = cur.fetchone()
            if is_offender:
                msg = "범죄자는 범죄 정보를 조회할 수 없습니다."
    
    else:
        region = list[0]
        flag = "success"
        msg = f"현재 거주 중인 지역은 {region}번 구역으로 해당 구역의 범죄 정보를 열람하실 수 있습니다."

    result = {
        'flag'  :   flag,
        'msg'   :   msg,
        'region':   region
    }

    return jsonify(result)

def format_tuple_for_sql(t):
    return ', '.join(f"'{item}'" for item in t if item)

@app.route('/inquiry_crime', methods=['POST'])
@with_transaction
def inquiry_crime(cur):
    region = request.form['region']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    # 사용자 입력에 따른 범죄 타입을 IUCR 테이블에서 가져옴
    crime_type = request.form['crime_type']
    crime_dictionary = {
        '1' : '',
        '2' : ('HOMICIDE',),
        '3' : ('CRIM SEXUAL ASSAULT', 'SEX OFFENSE', 'OBSCENITY'),
        '4' : ('HUMAN TRAFFICKING','KIDNAPPING'),
        '5' : ('ROBBERY', 'BURGLARY','WEAPONS VIOLATION'),
        '6' : ('THEFT','MOTOR VEHICLE THEFT'),
        '7' : ('ASSAULT',),
        '8' : ('NARCOTICS','OTHER NARCOTIC VIOLATION'),
        '9' : ('DECEPTIVE PRACTICE',),
        '10' : ('ARSON',),
        '11': ''
    }
    primary_type = crime_dictionary[crime_type]
    # '모두'를 선택 시 IUCR을 전부 선택
    if crime_type == '1':
        cur.execute(f"select iucr from crime_type")
    # '기타'를 선택 시 목록을 제외한 IUCR을 선택
    elif crime_type == '11':
        cur.execute(f"select iucr from crime_type where weight = 1 ")
    # 나머지 선택 시 해당하는 IUCR을 선택
    else:
        cur.execute(f"select iucr from crime_type where primary_type in ({format_tuple_for_sql(primary_type)})")

    list = cur.fetchall()
    iucr = tuple([substr[0] for substr in list])

    # 조건에 따라 범죄 분류 및 조회
    cur.execute(f"""select id, date, block, location_description, arrest
                from crime 
                where region_id = {region}
                and iucr in {iucr}
                and date between '{start_date}' and '{end_date}'
                order by date""")
    list = cur.fetchall()

    msg = ""
    crime_html = ""
    if len(list) == 0:
        msg += f"해당 기간에 {region}번 지역에서 발생한 범죄가 없습니다."
    else:
        for i in list:
            crime_html += f"<tr><td class='tg-c3ow' id='crime_id'>{i[0]}</td><td class='tg-c3ow' id='date'>{i[1]}</td><td class='tg-c3ow' id='block'>{i[2]}</td><td class='tg-c3ow' id='location'>{i[3]}</td><td class='tg-c3ow' id='arrest'>{i[4]}</td></tr>"

    result = {
        'msg'           :   msg,
        'crime_html'    :   crime_html
    }

    return jsonify(result)

def generate_notify_id(table):
    while True:
        # 영문 2자리 생성
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        
        # 숫자 4자리 생성
        numbers = ''.join(random.choices(string.digits, k=4))
        
        # ID 조합
        id = letters + numbers
        
        # 데이터베이스에서 기존 ID 확인
        cur.execute(f"SELECT id FROM {table} WHERE id = %s", (id,))
        if cur.fetchone() is None:
            return id

@app.route('/notify_crime', methods=['POST'])
@with_transaction
def notify_crime(cur):
    id = generate_notify_id('notify_crime')
    date = request.form['date']
    details = request.form['details']
    caller_id = request.form['caller_id']

    cur.execute(f"insert into notify_crime values ('{id}','{date}','{details}','{caller_id}')")

    msg = f"""신고 내용<br>
    -------------------------------------------<br>
    접수 ID : {id}<br>
    날짜 : {date}<br>
    내용 : {details}<br>
    신고자 ID : {caller_id}<br>
    -------------------------------------------
    """

    return msg

@app.route('/inquiry_offender_location', methods=['POST'])
@with_transaction
def inquiry_offender_location(cur):
    citizen_id = request.form['citizen_id']
    cur.execute(f"select region from citizen where id = '{citizen_id}'")
    region = cur.fetchone()[0]

    # 해당 지역에서 마지막으로 목격된 수배범 목록 출력
    # 수배범 이름, 성별, 나이, 범행, 마지막 날짜 -> offender_location, offender, crime, crime_type
    cur.execute(f"""SELECT o."name" , o.gender , o.age , ol.send_date , ct.primary_type
                    FROM crime c
                    JOIN offender o ON c.offender_id = o.id
                    JOIN offender_location ol ON o.id = ol.offender_id
                    join crime_type ct ON ct.iucr = c.iucr 
                    WHERE ol.region_id  = {region} and o.wanted = 'y';""")
    wanted_offender = cur.fetchall()

    wanted_offender_html = ""
    msg = ""
    
    if len(wanted_offender)==0:
        msg += f"{region}지역에 해당하는 수배범이 없습니다."
    else:
        for i in wanted_offender:
            wanted_offender_html += f"<tr><td class='tg-c3ow' id='name'>{i[0]}</td><td class='tg-c3ow' id='gender'>{i[1]}</td><td class='tg-c3ow' id='age'>{i[2]}</td><td class='tg-c3ow' id='send_date'>{i[3]}</td><td class='tg-c3ow' id='primary_type'>{i[4]}</td></tr>"

    result = {
        'msg'                   :   msg,
        'wanted_offender_html'  :   wanted_offender_html
    }

    return jsonify(result)

@app.route('/witness_victim_inquiry', methods=['POST'])
@with_transaction
def witness_victim_inquiry(cur):
    type = request.form['type']
    id = request.form['id']
    
    cur.execute(f"""select c.id , c.date , c.region_id, c.block , c.location_description , ct.primary_type , o.name , o.gender , o.age , o.wanted , ol.region_id , ol.send_date 
                from crime c 
                join {type} on c.id = {type}.crime_id 
                join crime_type ct on c.iucr =ct.iucr 
                LEFT JOIN offender o ON o.id = c.offender_id 
                LEFT JOIN offender_location ol ON ol.offender_id = o.id
                where {type}.id = '{id}';""")
    
    inquiry_info = cur.fetchone()

    result = {
        'msg'           :   None,
        'crime_html'    :   None,
        'offender_html' :   None
    }

    if inquiry_info:
        result['crime_html'] = f"<tr><td class='tg-c3ow' id='id'>{inquiry_info[0]}</td><td class='tg-c3ow' id='date'>{inquiry_info[1]}</td><td class='tg-c3ow' id='region'>{inquiry_info[2]}</td><td class='tg-c3ow' id='block'>{inquiry_info[3]}</td><td class='tg-c3ow' id='location_description'>{inquiry_info[4]}</td><td class='tg-c3ow' id='primary_type'>{inquiry_info[5]}</td></tr>"
        if inquiry_info[6] != None:
            result['offender_html'] = f"<tr><td class='tg-c3ow' id='name'>{inquiry_info[6]}</td><td class='tg-c3ow' id='gender'>{inquiry_info[7]}</td><td class='tg-c3ow' id='age'>{inquiry_info[8]}</td><td class='tg-c3ow' id='wanted'>{inquiry_info[9]}</td><td class='tg-c3ow' id='region_id'>{inquiry_info[10]}</td><td class='tg-c3ow' id='send_date'>{inquiry_info[11]}</td></tr>"
    else:
        result['msg'] = "해당하는 ID가 존재하지 않습니다. 다시 입력해주세요."

    return jsonify(result)

####################################
## Offender

@app.route('/transfer_location', methods=['POST'])
@with_transaction
def transfer_location(cur):
    offender_id = request.form['offender_id']
    current_region = request.form['current_region']
    
    cur.execute(f"update offender_location set region_id = {current_region}, send_date=CURRENT_DATE where offender_id = '{offender_id}'")
    
    if cur.rowcount > 0:
        return "위치 갱신이 완료되었습니다."
    else:
        return "위치 갱신에 실패하였습니다. ID 및 지역 입력을 확인해주세요."


if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
