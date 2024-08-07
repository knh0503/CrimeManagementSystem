import random
import psycopg2
import datetime
import string

def connectDB(USER,pwd):
# connect to database
    global conn
    global cur
    conn = psycopg2.connect(
        dbname="crimemanagementsystem",
        user=USER, 
        password=pwd, 
        host="localhost", 
        port="5432")

    # make cursor
    cur = conn.cursor()

############ 경찰_관리자

def police_deployment():
    while (True):      
            # 지역을 입력하고, 해당 지역의 경찰 목록 출력
            while (True):
                print("어떤 지역의 인원 배치를 변경하시겠습니까?(0~77)--------예시: 1")
                region = int(input())
                print(f"----------해당 지역의 경찰 목록을 출력합니다.-----------")
                cur.execute(f"""select *
                            from police 
                            where police_station_id in 
                                (select id 
                                from police_station 
                                where region_id = {region})""")
                police = cur.fetchall()
                if police:
                    break
                else:
                    print("지역을 다시 입력해주세요.")
            for i in police:
                print(f"id : {i[0]}, name : {i[1]}, phone_number : {i[2]}")
            # 이동을 원하는 경찰의 id를 선택한 후, 어디로 이동시킬 건지 입력
            print()
            while (True):
                print("배치 이동을 원하는 경찰의 id를 입력해주세요-----------예시: 1132437577")
                select_police = input()
                police_list = [sub[0] for sub in police]
                if select_police not in police_list:
                    print("경찰 id 조회 실패. 다시 입력해 주세요.")
                else: break
            while (True):
                print("배치 이동을 원하는 지역을 선택해 주세요-----------예시: 2")
                select_region = int(input())
                if (select_region>=0 and select_region<=77):
                    break
                else:
                    print("지역을 다시 선택해 주세요.")
            # 선택한 경찰을 해당 직역으로 이동 후, 경찰서의 인원을 조정 -> transaction
            cur.execute(f"""UPDATE police 
                            SET police_station_id = 
                                (SELECT id 
                                FROM police_station 
                                WHERE region_id = {select_region}) 
                            WHERE id = '{select_police}'""")
            conn.commit()
            cur.execute(f"""begin;
                        update police_station
                        set num_of_police = num_of_police-1
                        where region_id = {region};
                        update police_station
                        set num_of_police = num_of_police+1
                        where region_id = {select_region};
                        commit;""")
            cur.execute(f"select region_id, num_of_police from police_station where region_id in ({region}, {select_region})")
            new_police_station = cur.fetchall()
            print()
            print("완료되었습니다. 새로운 경찰 인원은 다음과 같습니다.")
            print("---------------------------------------------------")
            for i in new_police_station:
                print(f"region_id = {i[0]} : num_of_police = {i[1]}")
            print("---------------------------------------------------\n")
            return

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
    while (True):
        try:
            # 위험도 변경 시 경찰 인원 변경 요청창
            print(f"{region}번 지역의 위험도 상승으로 인하여 지역의 배치 인원을 조정합니다.")
            # 해당 지역의 경찰서의 id, 경찰수, 경찰 id 리스트(중복 확인용)를 요청
            cur.execute(f"select id, num_of_police from police_station where region_id = {region}")
            station_inf = cur.fetchone()
            police_station_id = station_inf[0]
            num_of_police = station_inf[1]
            cur.execute("select id from police")
            police_list = cur.fetchall()
            # 해당 지역의 경찰 수/10 만큼 새로운 경찰을 투입
            # 투입된 경찰의 정보를 출력
            new_num = num_of_police//10
            for i in range(new_num):
                id = generate_police_id(police_list)
                phone_number = generate_police_phone_number()
                print(f"id: '{id}', police_station_id : '{police_station_id}', phone_number: '{phone_number}'")
                cur.execute(f"""insert into police
                                values('{id}', '{police_station_id}', '{phone_number}')""")
                conn.commit()
            cur.execute(f"update police_station set num_of_police = num_of_police+{new_num}  where region_id = {region}")
            conn.commit()
            # 기존 인원과 현재 인원을 출력
            print(f"{region}번 지역의 경찰 수가 기존 인원 {num_of_police}명에서 {new_num}만큼 증가하여 현재 {num_of_police+new_num}명이 되었습니다.")
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

def sort_by_second_value(data):
    return sorted(data, key=lambda x: x[1])

def change_risk_level(region):
    while (True):
        try:
            # 범죄 유형, 범죄 빈도, 수배중인 범죄자의 여부에 따라 위험도 변경
            print("------------------------------------------------")
            print(f"{region}번 지역의 위험도를 변경합니다.")
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
            # 위험도 갱신
            for i in sorted_region_risk:
                cur.execute(f"update region set degree_of_danger = {sorted_region_risk.index(i)+1} where id = {i[0]}")
            conn.commit()
            # 갱신된 위험도 안내
            new_risk_level = next((i for i, x in enumerate(sorted_region_risk) if x[0] == region), None)
            print(f"{region}번 지역의 현재 위험도는 {new_risk_level+1}등급 입니다.")
            # 위험도 상승 시, emergency_deployment 실행하여 해당 지역의 배치 인원을 증가
            if new_risk_level > risk_level:
                print(f"{region}번 지역의 위험도가 상승하였습니다. 긴급 경찰 인력 배치를 실행합니다.")
                emergency_deployment(region)
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

def enter_crime_info():
    while (True):
        try:            
            # 범죄 신고 조회 후, 범죄를 입력
            print(f"신고 접수 목록을 출력합니다.")
            print(f"-------------------------------------------")
            cur.execute(f"select * from notify_crime")
            notify = cur.fetchall()
            for i in notify:
                print(f"id : {i[0]}, date = {i[1]}, crime_type = {i[2]}, witness : {i[3]}")
            print("---------------------------------------------")
            print(f"사건의 세부 내용을 입력해 주세요.\n")
            print(f"offender id : ......ex) 5489557")
            offender_id = int(input())
            print(f"id : ...............ex) HX305513")
            id = input()
            print(f"date :  ............ex) 2023-12-11")
            date_str = input()
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            print(f"block : ............ex) 013XX W 112TH ST")
            block = input()
            print(f"iucr : .............ex) homicice = 0110")
            iucr = input()
            print(f"location description : ex ) STREET")
            location_desciption = input()
            print(f"arrest : ...........ex) True / False")
            arrest = input()
            if arrest == "True":
                arrest = True
            else:
                arrest = False
            print(f"region_id : ........ex) 0~77")
            region_id = int(input())

            # arrest의 경우, offender, offender_location에 insert
            if arrest == True:
                print("-------------------------------------------------")
                print(f"범인의 신상정보를 입력해 주세요.")
                name = input("name : ")
                gender = input("gender(M/F) : ")
                age = int(input("age: "))
                cur.execute(f"""insert into offender
                            values ({offender_id}, '{name}', '{gender}', {age}, 'n')""")
                cur.execute(f"""insert into offender_location
                            values ({offender_id}, {region_id}, '{date_str}')""")
                cur.execute(f"insert into crime values ({offender_id}, '{id}', '{date_str}', '{block}', '{iucr}', '{location_desciption}',{arrest}, {region_id})")
                conn.commit()
            else: 
                cur.execute(f"insert into crime values (null, '{id}', '{date_str}', '{block}', '{iucr}', '{location_desciption}',{arrest}, {region_id})")
                conn.commit()
            print("-----------------------------------------------")
            print(f"사건 접수가 완료되었습니다.")
            print(f"offender id : {offender_id}, crime_id : {id}, date : {date_str}, block : {block}, location : {location_desciption}, arrest : {arrest}")
            print("----------------------------------------------------------")

            ## region 테이블의 num_of_crime를 update
            cur.execute(f"update region set num_of_crime = num_of_crime+1 where id={region_id}")
            conn.commit()
            # change_risk_level 함수 실행
            change_risk_level(region_id)
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

def update_wanted_offender():

    region = int(input(f"조회하고자 하는 지역을 입력해주세요.(0~77)-----: "))

    while (True):
        try:                
            # 지역을 선택하여 해당 지역의 위치 정보가 끊긴 범죄자 출력
            cur.execute(f"""SELECT *
                        FROM offender_location ol
                        WHERE ol.region_id = {region} and ol.send_date < CURRENT_DATE - INTERVAL '1 MONTH'""")
            wanted_offender = cur.fetchall()
            print(f"최근 위치 정보 갱신으로부터 한달이 지난 범죄자들의 목록을 출력합니다.")
            print("--------------------------------------------------------------")
            for i in wanted_offender:
                print(f"offender id : {i[0]}, last_date : {i[2]}")
                # 해당 범죄자를 wanted 처리
                cur.execute(f"update offender set wanted = 'y' where id = {i[0]}")
                conn.commit()
            # change_risk_level 함수 실행
            print("--------------------------------------------------------------")
            change_risk_level(region)
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

def generate_investigation_id():
    # investigation_id에 대한 리스트
    cur.execute(f"select id from investigation")
    list = cur.fetchall()
    inv_list = [sublist[0] for sublist in list]
    while True:
        investigation_id = "".join(str(random.randint(0, 9)) for _ in range(8))
        if investigation_id not in inv_list:
            return investigation_id

def investigation():
    while (True):
        try:
            # 아직 investigation이 이루어지지 않은 사건을 조회
            cur.execute(f"""select c.id
                        from crime c
                        where c.investigation_id is null;""")
            non_investigation_crime = cur.fetchall()
            print("----------------------------------------------------------------------------------")
            print(f"아직 조사가 이루어지지 않은 crime이 {len(non_investigation_crime)}회 확인되었습니다.\n")

            for i in non_investigation_crime:
                # 새로운 investigation 생성
                # id는 랜덤으로 생성, 날짜는 현재 날짜에서 시작하여 열흘 뒤 종료, 담당 조사관은 랜덤으로 선택
                investigation_id = generate_investigation_id()
                cur.execute(f"""insert into investigation
                            select '{investigation_id}', CURRENT_DATE, CURRENT_DATE + INTERVAL '10 days', id
                            from police
                            order by random()
                            limit 1""" )
                # 해당 crime에 investigation_id 추가
                cur.execute(f"update crime set investigation_id = '{investigation_id}' where id = '{i[0]}'")
                conn.commit()
                print(f"crime_id가 {i[0]}인 사건에 대해 investigation_id가 {investigation_id}인 조사를 시작하였습니다.")
                print()
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")


def new_investigation():
    while (True):
        try:
            # 아직 investigation이 이루어지지 않은 사건을 조회
            cur.execute(f"""select *
                        from crime c
                        where c.investigation_id is null;""")
            non_investigation_crime = cur.fetchall()
            print("----------------------------------------------------------------------------------")
            print(f"아직 조사가 이루어지지 않은 crime이 {len(non_investigation_crime)}회 확인되었습니다.\n")

            for i in non_investigation_crime:
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
                                LIMIT 1;""" )
                # 해당 crime에 investigation_id 추가
                cur.execute(f"update crime set investigation_id = '{investigation_id}' where id = '{i[1]}'")
                conn.commit()
                print(f"crime_id가 {i[0]}인 사건에 대해 investigation_id가 {investigation_id}인 조사를 시작하였습니다.")
                print()
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(e)

######## 경찰_수사관

def generate_evidence_id(list):
    # evidence_id : 랜덤 문자4+숫자4 으로 이루어진 문자열 ->  중복체크
    while True:
        random_chars = ''.join(random.choices(string.ascii_letters, k=5))
        random_numbers = ''.join(random.choices(string.digits, k=5))
        evidence_id = random_chars + random_numbers
        if evidence_id not in list:
            return evidence_id

def enroll_evidence():
    while (True):
        try:
            # 담당 사건의 증거물에 대한 정보를 등록
            cur.execute(f"select id from evidence")
            list = cur.fetchall()
            evd_list = [sublist[0] for sublist in list]
            id = generate_evidence_id(evd_list)
            cur.execute(f"select * from investigation order by start_date limit 10")
            inv_list = cur.fetchall()
            print("\n최근 시작한 10개의 investigation을 출력합니다.\n")
            print("------------------------------------------------------------")
            for i in inv_list:
                print(f"investigation_id : '{i[0]}', start_date : {i[1]}, end_date = {i[2]}")
            print("------------------------------------------------------------\n")
            investigation_id = input(f"investigation_id를 선택해 주세요.---------ex)3e962163 : ")
            cur.execute(f"select * from evidence_type")
            type_list = cur.fetchall()
            print(f"evidence_type을 출력합니다.")
            print("--------------------------------------------------------------")
            for i in type_list:
                print(f"evidence_type : '{i[0]}', description : '{i[2]}'")
            print("---------------------------------------------------------------")
            evidence_type = input(f"\nevidence_type을 입력해 주세요.-------ex)evd007 : ")
            evidence_collected_date = input(f"\nevidence_collected_date를 입력해 주세요-------ex)2023-12-11 : ")
            cur.execute(f"insert into evidence values ('{id}', '{investigation_id}','{evidence_type}','{evidence_collected_date}')")
            conn.commit()
            print(f"\n새로운 증거물이 성공적으로 입력되었습니다.\n")
            print(f"id = '{id}', investigation_id = '{investigation_id}', evidence_type = '{evidence_type}', evidence_collected_date = {evidence_collected_date}\n")
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"\n다시 시도해주세요.")

def generate_id(list):
   while True:
        id = ''.join(random.choices(string.ascii_letters, k=7))
        if id not in list:
            return id
        
def enroll_witness():
    while (True):
        try:
            # 담당 사건의 증인에 대한 정보를 등록
            cur.execute(f"select id from witness")
            list = cur.fetchall()
            witness_list = [substr[0] for substr in list]
            id = generate_id(witness_list)
            name = input(f"\n이름을 입력하세요 : ")
            gender = input(f"\n성별을 입력하세요(F/M) : ")
            age = int(input(f"\n나이를 입력하세요 : "))
            cur.execute(f"select id,date from crime order by date limit 10")
            inv_list = cur.fetchall()
            print(f"\n최근 일어난 사건 목록을 출력합니다.")
            print("-------------------------------------------------------")
            for i in inv_list:
                print(f"crime_id : '{i[0]}', date : {i[1]}")
            print("-------------------------------------------------------")
            crime_id = input(f"crime_id를 선택해 주세요. : ")
            cur.execute(f"insert into witness values ('{id}', '{name}','{gender}',{age}, '{crime_id}')")
            conn.commit()
            print(f"\n새로운 증인이 성공적으로 입력되었습니다.")
            print(f"\nid = '{id}', name = '{name}', gender = '{gender}', age = {age}, crime_id = '{crime_id}'\n")
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

def enroll_victim():
    while (True):
        try:
            # 담당 사건의 희생자에 대한 정보를 등록
            cur.execute(f"select id from victim")
            list = cur.fetchall()
            victim_list = [substr[0] for substr in list]
            id = generate_id(victim_list)
            name = input(f"\n이름을 입력하세요 : ")
            gender = input(f"\n성별을 입력하세요(F/M) : ")
            age = int(input(f"\n나이를 입력하세요 : "))
            cur.execute(f"select id,date from crime order by date limit 10")
            inv_list = cur.fetchall()
            print("최근 일어난 사건 목록을 출력합니다.")
            print("-------------------------------------------------------")
            for i in inv_list:
                print(f"crime_id : '{i[0]}', date : {i[1]}")
            print("--------------------------------------------------------")
            crime_id = input(f"crime_id를 선택해 주세요. : ")
            cur.execute(f"\ninsert into victim values ('{id}', '{name}','{gender}',{age}, '{crime_id}')")
            conn.commit()
            print(f"\n해당 사건의 피해자가 성공적으로 입력되었습니다.")
            print(f"\nid = '{id}', name = '{name}', gender = '{gender}', age = {age}, crime_id = '{crime_id}'\n")
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

######### 시민

def inquiry_crime():
    # 현재 거주하고 있는 지역의 범죄 정보 조회
    while (True):
        try:
            id=input(f"\nid를 입력해 주세요.(예시: ddff637(o)----8811029(x:offender_id))")
            # citizen 테이블에서 id와 일치하는 지역 조회
            cur.execute(f"select region from citizen where id='{id}'")
            list = cur.fetchone()
            # 조회 결과가 없으면, 범죄자인지 확인하거나 잘못된 id 입력을 확인
            if list is None:
                # 만약 입력한 id가 offender_id와 일치하면 경고창
                if id.isdigit():
                    cur.execute(f"select * from offender where id={id}")
                    is_offender = cur.fetchone()
                    if is_offender:
                        warning()
                        return
                print(f"\nid 조회 실패 - 해당하는 시민 id가 없습니다.")
                continue
            region = list[0]
            if region:
                # 범죄 유형 조회
                while (True):
                    print(f"\n조회할 범죄 유형을 선택하세요.")
                    print(f"\n1. 모두, 2. 살인, 3. 성범죄, 4.인신매매, 5.강도, 6.절도, 7.폭행, 8. 기타")
                    crime_type = input(f"\n범죄 유형 : ")
                    crime_dictionary = {
                        '1' : '',
                        '2' : ('HOMICIDE'),
                        '3' : ('CRIM SEXUAL ASSAULT', 'SEX OFFENSE'),
                        '4' : ('HUMAN TRAFFICKING'),
                        '5' : ('ROBBERY', 'BURGLARY'),
                        '6' : ('THEFT'),
                        '7' : ('ASSAULT'),
                        '8' : ''
                    }
                    if crime_type == '1':
                        primary_type = crime_dictionary[crime_type]
                        cur.execute(f"select iucr from crime_type")
                        break
                    elif crime_type == '8':
                        primary_type = crime_dictionary[crime_type]
                        cur.execute(f"select iucr from crime_type where weight = 1 ")
                        break
                    elif crime_type == '3' or crime_type=='5':
                        primary_type = crime_dictionary[crime_type]
                        cur.execute(f"select iucr from crime_type where primary_type in {primary_type}")
                        break
                    elif crime_type=='2' or crime_type=='4' or crime_type=='6' or crime_type=='7':
                        primary_type = crime_dictionary[crime_type]
                        cur.execute(f"select iucr from crime_type where primary_type = '{primary_type}'")
                        break
                    else : 
                        print(f"\n범죄 유형 조회 실패")
                list = cur.fetchall()
                iucr = tuple([substr[0] for substr in list])
                # 조회 기간 선택
                while (True):
                    try:
                        print(f"\n조회할 기간을 선택하세요.-----------예시: 2012-01-01")
                        start_date = input(f"\n시작 날짜 : ")
                        end_date = input(f"\n종료 날짜 : ")
                        # 조건에 따라 범죄 분류 및 조회
                        cur.execute(f"""select id, date, block, location_description, arrest
                                    from crime 
                                    where region_id = {region}
                                    and iucr in {iucr}
                                    and date between '{start_date}' and '{end_date}'
                                    order by date""")
                        list = cur.fetchall()
                        if len(list) == 0:
                            print(f"\n해당 기간에 {region}번 지역에서 발생한 범죄가 없습니다. 다시 선택해주세요.")
                            continue
                        print(f"\n{start_date}부터 {end_date}까지 {region}번 지역에서 발생한 범죄 목록을 출력합니다.")
                        print("------------------------------------------------------------------------------------------")
                        for i in list:
                            print(f"crime_id : {i[0]}, date = {i[1]}, block : {i[2]}, location : {i[3]}, arrest : {i[4]}")
                        print(f"--------------------------------------------------------------------------------------------\n")
                        return
                    
                    except Exception as e:
                        cur.execute(f"rollback;")
                        print(f"\n기간 조회 오류")
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"조회 오류")

def notify_crime():
    # 목격한 범죄를 신고 가능 -> 해당 정보는 데이터 베이스에 기록됨
    while (True):
        try:
            print(f"신고 내용을 적어주세요.\n")
            cur.execute(f"select id from notify_crime")
            list = cur.fetchall()
            notify_list = [substr[0] for substr in list]
            id = generate_id(notify_list)
            date = input(f"목격 날짜------ex)2023-12-11 : ")
            crime_type = input(f"\n범죄 유형(내용) : ")
            witness = input(f"\n신고자 id------------ex)ddff637 : ")
            cur.execute(f"insert into notify_crime values ('{id}','{date}','{crime_type}','{witness}')")
            conn.commit()
            print(f"\n신고가 접수되었습니다.")
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(e)
            print(f"다시 시도해주세요")


def inquiry_offender_location():
    # 수배자의 마지막 목격 위치에 거주하고 있는 시민들은 해당 범죄자의 신상 정보 열람
    # id를 입력받아 해당 시민의 거주 지역을 확인
    while (True):
        try:
            print(f"수배자의 신상은 마지막 목격 지역에 거주하고 있는 시민들에 한해 공개됩니다.\n")
            citizen_id = input(f"id를 입력해 주세요.-------ex)cab4172 : ")
            cur.execute(f"select region from citizen where id = '{citizen_id}'")
            list = cur.fetchone()
            citizen_region = list[0]
            # 해당 지역에서 마지막으로 목격된 수배범 목록 출력
            cur.execute(f"""select o.id, o.name, o.gender , o.age
                        from offender o join offender_location ol on o.id = ol.offender_id 
                        where ol.region_id = {citizen_region} and o.wanted = 'y';""")
            list = cur.fetchall()
            print(f"{citizen_region}번 지역에서 수배 중인 수배자의 신상 정보입니다.")
            print(f"------------------------------------------------------------")
            for i in list:
                print(f"이름 : {i[1]}, 성별 : {i[2]}, 나이 : {i[3]}")
            print(f"------------------------------------------------------------\n")
            return
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

def witness_victim_inquiry():
    while (True):
        print(f"목격자와 피해자에 해당하는 사건의 가해자의 신상 정보를 확인할 수 있습니다.")
        print(f"해당 기능을 종료하려면 e를 입력하세요\n")
        try:
            flag = input(f"목격자 / 피해자 : ")
            if flag=='e' : return
            elif flag == '목격자' :
                while (True):
                    id = input(f"목격자 id---------ex)ZOTcnQL : ")
                    if (id=='e'): return
                    cur.execute(f"select * from witness where id = '{id}'")
                    witness = cur.fetchone()
                    if witness:
                        print(f"목격자 id가 확인되었습니다. 해당 사건의 피의자 신원 정보가 출력됩니다.")
                        print(f"---------------------------------------------------------------")
                        witness_crime_id = witness[4]
                        cur.execute(f"select * from crime where id = '{witness_crime_id}'")
                        crime_list = cur.fetchall()
                        for crime_info in crime_list:
                            print(f"사건 정보 - crime id: {crime_info[1]}, 날짜: {crime_info[2]}, 장소(block): {crime_info[3]}, iucr: {crime_info[4]}, 장소(location): {crime_info[5]}")
                            cur.execute(f"""select * from offender o 
                                        where o.id = (
                                        select c.offender_id 
                                        from crime c
                                        where c.id = '{witness_crime_id}');""")
                            offender = cur.fetchone()
                            print(f"범죄자 정보 - 이름: {offender[1]}, 성별: {offender[2]}, 나이: {offender[3]}세")
                        print(f"--------------------------------------------------------------------")
                        return
                    else: print(f"해당하는 목격자 id가 없습니다. 다시 입력해주세요.")
            elif flag == '피해자' :
                while (True):
                    id = input(f"피해자 id------ex)082dcb0 : ")
                    if (id=='e'): return
                    cur.execute(f"select * from victim where id = '{id}'")
                    victim = cur.fetchone()
                    if victim:
                        print(f"피해자 id가 확인되었습니다. 해당 사건의 피의자 신원 정보가 출력됩니다.")
                        print(f"--------------------------------------------------------------------")
                        victim_crime_id = victim[4]
                        cur.execute(f"select * from crime where id = '{victim_crime_id}'")
                        crime_list = cur.fetchall()
                        for crime_info in crime_list:
                            print(f"사건 정보 - crime id: {crime_info[1]}, 날짜: {crime_info[2]}, 장소(block): {crime_info[3]}, iucr: {crime_info[4]}, 장소(location): {crime_info[5]}")
                            cur.execute(f"""select * from offender o 
                                        where o.id = (
                                        select c.offender_id 
                                        from crime c
                                        where c.id = '{victim_crime_id}');""")
                            offender = cur.fetchone()
                            print(f"범죄자 정보 - 이름: {offender[1]}, 성별: {offender[2]}, 나이: {offender[3]}세\n")
                            return
                    else: print(f"해당하는 피해자 id가 없습니다. 다시 입력해주세요.")
            else : print(f"다시 입력해 주세요.")
        except Exception as e:
            cur.execute(f"rollback;")
            print(e)
            print(f"다시 시도해주세요.")



#########범죄자#######################

def transfer_location():
    while (True):
        try:
            # 일정 시간 마다 위치 정보를 입력 -> update offender_location
            print(f"위치 정보를 갱신합니다. 해당 기능을 종료하려면 e를 입력하세요.\n")
            while (True):
                id = input(f"피의자 id를 입력해주세요.-------ex)8811029 : ")
                if (id=='e'): return
                cur.execute(f"select * from offender where id = '{id}'")
                list = cur.fetchone()
                if list:
                    print(f"피의자 id를 확인했습니다. 현재 위치를 입력해주세요.")
                    while(True):
                        region = int(input(f"현재 위치:------ex)45 : "))
                        if (0<=region<=77):
                            cur.execute(f"update offender_location set region_id = {region}, send_date=CURRENT_DATE where offender_id = '{id}'")
                            print(f"\n위치 갱신이 완료되었습니다.")
                            return
                        else: print(f"위치를 다시 입력해주세요. (region: 0~77)")

                else: print(f"피의자 id가 확인되지 않습니다. 다시 입력해주세요.")
        except Exception as e:
            cur.execute(f"rollback;")
            print(f"다시 시도해주세요.")

def warning():
    print(f"범죄자는 범죄 기록을 열람할 수 없습니다.")
    return



##########main
while (True) :
    try:
        print(f"""----------------USER를 선택해주세요---------------\n1)경찰-관리자 : police_manager\n2)경찰-수사관 : police_detective\n3)시민       : citizen\n4)범죄자      : offender""")
        print(f"-------------------------------------------")
        user = input(f"USER 선택 : ")
        pwd = input(f"비밀번호를 입력해주세요: ")
        print(f"\n'{user}'유형으로 시스템에 접속합니다.\n")
        connectDB(user,pwd)
        break
    except Exception as e:
        print(f"\n시스템 접속 실패. 다시 시도해주세요.")

if (user=='police_manager'):
    while (True): 
            print(f"-------------------기능을 선택해주세요.----------------------")
            print(f"""1. 경찰 근무지 변경
    2. 범죄 등록
    3. 수배자 목록 조회 및 변경
    4. investigation 등록
    5. exit""")
            func = input("기능 선택 : ")
            print("-------------------------------------------------------------")
            if (func=='1'):
                police_deployment()
            elif (func=='2'):
                enter_crime_info()
            elif (func=='3'):
                update_wanted_offender()
            elif (func=='4'):
                new_investigation()
            elif (func=='5'):
                break
            else:
                print(f"다시 선택해주세요.")
            print("시스템을 종료합니다.")

if (user=='police_detective'):
    while (True): 
        print(f"--------------------기능을 선택해주세요.---------------------")
        print(f"""1. 증거물 등록\n2. 증인(목격자) 등록\n3. 피해자 등록\n4. exit""")
        func = input("기능 선택 : ")
        print("------------------------------------------------------------")
        if (func=='1'):
            enroll_evidence()
        elif (func=='2'):
            enroll_witness()
        elif (func=='3'):
            enroll_victim()
        elif (func=='4'):
            break
        else:
            print(f"다시 선택해주세요.")
    print("시스템을 종료합니다.")

if (user=='citizen'):
    while (True): 
        print(f"------------기능을 선택해주세요.---------------------")
        print(f"""1. 지역 범죄 조회\n2. 신고\n3. 범죄자 신상 정보 조회\n4. 범죄자 신상 정보 조회(목격자, 피해자)\n5. exit""")
        func = input("기능 선택 : ")
        print("-------------------------------------------------------")
        if (func=='1'):
            inquiry_crime()
        elif (func=='2'):
            notify_crime()
        elif (func=='3'):
            inquiry_offender_location()
        elif (func=='4'):
            witness_victim_inquiry()
        elif (func=='5'):
            break
        else:
            print(f"다시 선택해주세요.")
    print("시스템을 종료합니다.")

if (user=='offender'):
    while (True): 
        print(f"------------기능을 선택해주세요.-------------")
        print(f"""1. 위지 정보 생신\n2. exit""")
        func = input("기능 선택 : ")
        print(f"----------------------------------------------")
        if (func=='1'):
            transfer_location()
        elif (func=='2'):
            break
        else:
            print(f"다시 선택해주세요.")
    print("시스템을 종료합니다.")


# 변경사항 커밋
conn.commit()
# 연결 종료
cur.close()
conn.close()