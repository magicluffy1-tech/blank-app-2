# streamlit_app.py

import streamlit as st
import pandas as pd
import random
import numpy as np

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Gems의 최종 시간표 생성기",
    page_icon="🎓",
    layout="wide"
)

# --- 기본 데이터 설정 ---
SUBJECT_LISTS = {
    1: ["국어", "영어", "수학", "사회", "과학", "음악", "미술", "체육", "보건", "기술가정", "정보", "도덕"],
    2: ["국어", "영어", "수학", "역사", "과학", "음악", "미술", "체육", "진로", "보건", "기술가정", "도덕"],
    3: ["국어", "영어", "수학", "사회", "역사", "과학", "음악", "미술", "체육", "진로", "기술가정", "도덕"]
}

# --- 상태 관리 (State Management) ---
if 'subject_hours' not in st.session_state:
    st.session_state.subject_hours = {1: {}, 2: {}, 3: {}}

# --- 함수 정의 ---
def initialize_timetable(num_periods):
    """지정된 교시 수만큼 빈 시간표 데이터프레임을 생성하는 함수"""
    if num_periods == 0: num_periods = 1
    periods = [f"{i}교시" for i in range(1, num_periods + 1)]
    grades = ["1학년", "2학년", "3학년"]
    return pd.DataFrame("", index=periods, columns=grades)

def generate_auto_timetable_compact(subject_hours, num_periods):
    """
    [업데이트] 각 학년의 수업을 1교시부터 빈틈없이 채워넣는 '압축' 로직 적용.
    """
    # 1. 초기화
    timetable = initialize_timetable(num_periods)
    conflict_groups = [{'사회', '역사'}]
    
    # 2. 학년별로 배정해야 할 수업 목록을 별도로 관리
    lessons_to_schedule = {grade: [] for grade in range(1, 4)}
    for grade, subjects in subject_hours.items():
        for subject, hours in subjects.items():
            lessons_to_schedule[grade].extend([subject] * int(hours))
    
    # 각 학년별 수업 목록을 섞어 매번 다른 결과 유도
    for grade in range(1, 4):
        random.shuffle(lessons_to_schedule[grade])

    # 3. 시간표 배정 알고리즘 (Period-First)
    # 교시 순서대로(1교시 -> 2교시 ...) 순회하며 빈자리를 채움
    for period in range(1, num_periods + 1):
        # 현재 교시에 배정된 과목들을 확인 (선생님 중복 체크용)
        subjects_in_period = set(timetable.loc[f"{period}교시"].values)
        
        # 학년 순서대로(1학년 -> 2학년 ...) 순회
        for grade in range(1, 4):
            # 해당 학년에 배정할 수업이 남아있고, 현재 교시가 비어있다면 배정 시도
            if lessons_to_schedule[grade] and timetable.loc[f"{period}교시", f"{grade}학년"] == "":
                
                # 배정 가능한 과목 탐색
                for subject_to_try in lessons_to_schedule[grade]:
                    # --- 제약 조건 검사 ---
                    # 조건 1: 다른 학년에 동일 과목이 이미 있는가?
                    if subject_to_try in subjects_in_period:
                        continue # 있으면 다른 과목으로 재시도
                    
                    # 조건 2: '사회'-'역사' 충돌이 발생하는가?
                    is_conflict_clash = False
                    for group in conflict_groups:
                        if subject_to_try in group and not subjects_in_period.isdisjoint(group):
                            is_conflict_clash = True
                            break
                    if is_conflict_clash:
                        continue # 충돌 시 다른 과목으로 재시도

                    # --- 모든 조건 통과 시 배정 ---
                    timetable.loc[f"{period}교시", f"{grade}학년"] = subject_to_try
                    subjects_in_period.add(subject_to_try) # 현재 교시에 배정된 과목으로 추가
                    lessons_to_schedule[grade].remove(subject_to_try) # 배정 완료 목록에서 제거
                    break # 과목 배정 완료, 다음 학년으로 이동

    # 4. 최종적으로 배정되지 못한 수업들을 모아서 반환
    unscheduled_lessons = []
    for grade, lessons in lessons_to_schedule.items():
        for lesson in lessons:
            unscheduled_lessons.append((grade, lesson))
            
    return timetable, unscheduled_lessons


# --- 사이드바 (사용자 입력) ---
with st.sidebar:
    st.header("📚 과목별 수업 시수 입력")
    st.write("각 학년별 주당 수업 시간을 입력하면, 시간표의 교시가 자동으로 조절됩니다.")

    for grade in range(1, 4):
        with st.expander(f"**{grade}학년 수업 시수 설정**", expanded=(grade==1)):
            for subject in SUBJECT_LISTS[grade]:
                hours = st.number_input(
                    f"**{subject}**",
                    min_value=0, max_value=40, step=1,
                    value=st.session_state.subject_hours.setdefault(grade, {}).get(subject, 0),
                    key=f"hours_{grade}_{subject}"
                )
                st.session_state.subject_hours[grade][subject] = hours

# --- 메인 화면 ---
st.title("🎓 Gems의 최종 시간표 생성기")
st.markdown("학년별 수업을 **1교시부터 빈틈없이 배정**합니다.  \n'사회'와 '역사' 과목은 선생님이 같아 같은 교시에 배정되지 않습니다.")

# 동적 교시 계산 로직
try:
    hours_per_grade = [sum(st.session_state.subject_hours.get(g, {}).values()) for g in range(1, 4)]
    max_periods = int(max(hours_per_grade)) if hours_per_grade else 1
except Exception:
    max_periods = 1

# 메인 로직 (버튼 클릭)
if st.button("시간표 자동 생성 🚀", use_container_width=True, type="primary"):
    if max_periods == 0:
        st.warning("⚠️ 수업 시수를 1시간 이상 입력해주세요.")
        st.dataframe(initialize_timetable(1), use_container_width=True)
    else:
        with st.spinner(f"최대 {max_periods}교시를 기준으로 수업을 빈틈없이 채워넣습니다..."):
            final_timetable, unscheduled = generate_auto_timetable_compact(st.session_state.subject_hours, max_periods)

            st.subheader("📆 자동 생성 결과")
            st.dataframe(final_timetable, use_container_width=True)

            if unscheduled:
                st.error("❗ 다음 과목들은 시간표에 배정하지 못했습니다. 제약 조건이 너무 많거나 시간이 부족할 수 있습니다.")
                failed_summary = {}
                for grade, subject in unscheduled:
                    key = f"{grade}학년 {subject}"
                    failed_summary[key] = failed_summary.get(key, 0) + 1
                for key, count in failed_summary.items():
                    st.write(f"- {key}: {count} 시간")
            else:
                st.success("🎉 모든 과목이 성공적으로 시간표에 배정되었습니다!")
else:
    st.info(f"현재 설정된 최대 교시는 **{max_periods}교시**입니다. 사이드바에서 정보를 입력하고 생성 버튼을 눌러주세요.")
    st.dataframe(initialize_timetable(max_periods), use_container_width=True)