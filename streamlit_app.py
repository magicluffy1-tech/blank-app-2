# streamlit_app.py

import streamlit as st
import pandas as pd
import random

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Gems의 AI 시간표 생성기",
    page_icon="🧑‍🏫",
    layout="wide"
)

# --- 기본 데이터 설정 ---
# 학년별 과목 목록을 딕셔너리로 관리하여 확장성을 높입니다.
SUBJECT_LISTS = {
    1: ["국어", "영어", "수학", "사회", "과학", "음악", "미술", "체육", "보건", "기술가정", "정보", "도덕"],
    2: ["국어", "영어", "수학", "역사", "과학", "음악", "미술", "체육", "진로", "보건", "기술가정", "도덕"],
    3: ["국어", "영어", "수학", "사회", "역사", "과학", "음악", "미술", "체육", "진로", "기술가정", "도덕"]
}

# --- 상태 관리 (State Management) ---
# st.session_state를 사용하여 사용자의 수업 시수 입력을 보존합니다.
if 'subject_hours' not in st.session_state:
    st.session_state.subject_hours = {1: {}, 2: {}, 3: {}}

# --- 함수 정의 ---
def initialize_timetable():
    """빈 시간표 데이터프레임을 생성하는 함수"""
    periods = [f"{i}교시" for i in range(1, 8)]
    grades = ["1학년", "2학년", "3학년"]
    return pd.DataFrame("", index=periods, columns=grades)

def generate_auto_timetable(subject_hours):
    """
    입력된 수업 시수와 제약 조건에 따라 시간표를 자동으로 생성하는 함수.
    [업데이트] '사회'와 '역사'는 동일 교시에 중복 배정 불가 규칙 추가.
    """
    # 1. 초기화
    timetable = initialize_timetable()
    
    # 2. 배정해야 할 전체 수업 목록 생성
    lessons_to_schedule = []
    for grade, subjects in subject_hours.items():
        for subject, hours in subjects.items():
            lessons_to_schedule.extend([(grade, subject)] * int(hours)) # 시간은 정수여야 함
    
    random.shuffle(lessons_to_schedule)
    
    # 3. 시간표 배정 알고리즘
    
    # [신규] 리소스 공유(교사 1명)로 인해 동시 배정 불가한 과목 그룹 정의
    conflict_groups = [{'사회', '역사'}]
    
    unscheduled_lessons = []

    for lesson in lessons_to_schedule:
        grade, subject = lesson
        is_scheduled = False
        
        # 해당 수업을 배정할 수 있는 최적의 슬롯 탐색 (교시를 무작위로 탐색하여 편중 방지)
        available_periods = list(range(1, 8))
        random.shuffle(available_periods)

        for period in available_periods:
            # --- 제약 조건 검사 ---
            
            # 조건 1: 해당 학년, 해당 교시가 비어있는가?
            if timetable.loc[f"{period}교시", f"{grade}학년"] != "":
                continue # 이미 수업이 있으면 다음 교시 탐색
            
            # 조건 2: 동일 교시에 다른 학년에 동일 과목이 있는가?
            subjects_in_period = set(timetable.loc[f"{period}교시"].values)
            if subject in subjects_in_period:
                continue # 동일 과목이 있으면 다음 교시 탐색
            
            # [업데이트] 조건 3: 동일 교시에 '사회'-'역사' 충돌이 발생하는가?
            is_conflict_group_clash = False
            for group in conflict_groups:
                # 현재 배정하려는 과목이 충돌 그룹에 속하는 경우
                if subject in group:
                    # 해당 교시에 이미 다른 충돌 그룹 과목이 있는지 확인
                    if not subjects_in_period.isdisjoint(group):
                        is_conflict_group_clash = True
                        break # 충돌 발생, 루프 탈출
            if is_conflict_group_clash:
                continue # 충돌이 있으면 다음 교시 탐색

            # --- 모든 조건 통과 시 시간표에 배정 ---
            timetable.loc[f"{period}교시", f"{grade}학년"] = subject
            is_scheduled = True
            break
        
        if not is_scheduled:
            unscheduled_lessons.append(lesson)
            
    return timetable, unscheduled_lessons

# --- 사이드바 (사용자 입력) ---
with st.sidebar:
    st.header("📚 과목별 수업 시수 입력")
    st.write("각 학년별로 주당 몇 시간의 수업을 배정할지 입력하세요.")

    for grade in range(1, 4):
        if grade not in st.session_state.subject_hours:
            st.session_state.subject_hours[grade] = {}

        with st.expander(f"**{grade}학년 수업 시수 설정**", expanded=True):
            # 해당 학년의 과목 목록을 가져와 UI를 생성
            for subject in SUBJECT_LISTS[grade]:
                hours = st.number_input(
                    f"**{subject}**",
                    min_value=0, max_value=7, step=1,
                    value=st.session_state.subject_hours[grade].get(subject, 0),
                    key=f"hours_{grade}_{subject}"
                )
                st.session_state.subject_hours[grade][subject] = hours

# --- 메인 화면 (시간표 출력) ---
st.title("🧑‍🏫 Gems의 AI 시간표 생성기")
st.markdown("사이드바에서 학년별 과목의 **수업 시수**를 설정하세요.  \n**사회**와 **역사** 과목은 한 선생님이 담당하시므로 같은 교시에 배정되지 않습니다.")

if st.button("시간표 자동 생성 🚀", use_container_width=True, type="primary"):
    total_hours = sum(h for g in st.session_state.subject_hours.values() for h in g.values())

    if total_hours == 0:
        st.warning("⚠️ 수업 시수를 1시간 이상 입력해주세요.")
    else:
        with st.spinner("최적의 시간표를 생성하는 중입니다... 이 작업은 몇 초 정도 걸릴 수 있습니다."):
            final_timetable, unscheduled = generate_auto_timetable(st.session_state.subject_hours)

            st.subheader("📆 자동 생성 결과")
            st.dataframe(final_timetable, use_container_width=True)

            if unscheduled:
                st.error("❗ 다음 과목들은 시간표에 배정하지 못했습니다. 수업 시수를 조정하거나, 다시 생성해보세요.")
                failed_summary = {}
                for grade, subject in unscheduled:
                    key = f"{grade}학년 {subject}"
                    failed_summary[key] = failed_summary.get(key, 0) + 1
                for key, count in failed_summary.items():
                    st.write(f"- {key}: {count} 시간")
            else:
                st.success("🎉 모든 과목이 성공적으로 시간표에 배정되었습니다!")
else:
    st.info("좌측 사이드바에서 정보를 입력하고 '시간표 자동 생성' 버튼을 눌러주세요.")
    st.dataframe(initialize_timetable(), use_container_width=True)