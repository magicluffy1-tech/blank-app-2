# streamlit_app.py

import streamlit as st
import pandas as pd
import random
import numpy as np

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Gems의 스마트 시간표 생성기",
    page_icon="🛡️",
    layout="wide"
)

# --- 기본 데이터 설정 ---
SUBJECT_LISTS = {
    1: ["국어", "영어", "수학", "사회", "과학", "음악", "미술", "체육", "보건", "기술가정", "정보", "도덕"],
    2: ["국어", "영어", "수학", "역사", "과학", "음악", "미술", "체육", "진로", "보건", "기술가정", "도덕"],
    3: ["국어", "영어", "수학", "사회", "역사", "과학", "음악", "미술", "체육", "진로", "기술가정", "도덕"]
}

# --- 상태 관리 (State Management) ---
# 'target_hours'를 추가하여 학년별 목표 총 시간을 저장합니다.
if 'subject_hours' not in st.session_state:
    st.session_state.subject_hours = {1: {}, 2: {}, 3: {}}
if 'target_hours' not in st.session_state:
    st.session_state.target_hours = {1: 4, 2: 4, 3: 4} # 기본 목표 시간을 4시간으로 설정

# --- 함수 정의 (내부 로직은 변경 없음) ---
def initialize_timetable(num_periods):
    if num_periods == 0: num_periods = 1
    periods = [f"{i}교시" for i in range(1, num_periods + 1)]
    grades = ["1학년", "2학년", "3학년"]
    return pd.DataFrame("", index=periods, columns=grades)

def generate_auto_timetable_compact(subject_hours, num_periods):
    timetable = initialize_timetable(num_periods)
    conflict_groups = [{'사회', '역사'}]
    lessons_to_schedule = {grade: [] for grade in range(1, 4)}
    for grade, subjects in subject_hours.items():
        for subject, hours in subjects.items():
            lessons_to_schedule[grade].extend([subject] * int(hours))
    for grade in range(1, 4):
        random.shuffle(lessons_to_schedule[grade])

    for period in range(1, num_periods + 1):
        subjects_in_period = set(timetable.loc[f"{period}교시"].values)
        for grade in range(1, 4):
            if lessons_to_schedule[grade] and timetable.loc[f"{period}교시", f"{grade}학년"] == "":
                for subject_to_try in lessons_to_schedule[grade]:
                    if subject_to_try in subjects_in_period: continue
                    is_conflict_clash = False
                    for group in conflict_groups:
                        if subject_to_try in group and not subjects_in_period.isdisjoint(group):
                            is_conflict_clash = True
                            break
                    if is_conflict_clash: continue
                    timetable.loc[f"{period}교시", f"{grade}학년"] = subject_to_try
                    subjects_in_period.add(subject_to_try)
                    lessons_to_schedule[grade].remove(subject_to_try)
                    break
    
    unscheduled_lessons = [ (g, l) for g, lessons in lessons_to_schedule.items() for l in lessons ]
    return timetable, unscheduled_lessons

# --- 사이드바 (사용자 입력) ---
with st.sidebar:
    st.header("📚 과목별 수업 시수 입력")
    st.write("학년별 **목표 총 시간**을 설정하고, 과목별 시간을 배분하세요.")
    
    # [신규] 모든 학년의 입력값이 유효한지 추적하는 플래그
    is_all_input_valid = True

    for grade in range(1, 4):
        with st.expander(f"**{grade}학년 수업 시수 설정**", expanded=(grade==1)):
            
            # --- 1. 목표 총 시간 입력 ---
            st.markdown("##### 🎯 목표 총 시간")
            target_hours = st.number_input(
                "이 학년에 배정할 총 수업 시간",
                min_value=0, max_value=40, step=1,
                value=st.session_state.target_hours.get(grade, 0),
                key=f"target_hours_{grade}",
                label_visibility="collapsed"
            )
            st.session_state.target_hours[grade] = target_hours

            st.markdown("---")
            st.markdown("##### 📖 과목별 시간 배분")
            
            # --- 2. 과목별 시간 입력 및 합계 계산 ---
            current_sum = 0
            for subject in SUBJECT_LISTS[grade]:
                hours = st.number_input(
                    f"**{subject}**",
                    min_value=0, max_value=40, step=1,
                    value=st.session_state.subject_hours.setdefault(grade, {}).get(subject, 0),
                    key=f"hours_{grade}_{subject}"
                )
                st.session_state.subject_hours[grade][subject] = hours
                current_sum += hours
            
            # --- 3. 실시간 검증 및 피드백 ---
            st.markdown("---")
            if current_sum == target_hours:
                st.success(f"✔️ 합계: {current_sum} / {target_hours} 시간 (일치)")
            else:
                # 목표와 합계가 다르면, 전체 유효성 플래그를 False로 변경
                is_all_input_valid = False
                if current_sum > target_hours:
                    st.error(f"🚨 합계: {current_sum} / {target_hours} 시간 (초과)")
                else: # current_sum < target_hours
                    st.warning(f"⚠️ 합계: {current_sum} / {target_hours} 시간 (부족)")

# --- 메인 화면 ---
st.title("🛡️ Gems의 스마트 시간표 생성기")
st.markdown("학년별 **목표 총 시간**과 과목별 시간의 합계가 일치해야 시간표 생성이 가능합니다.")

# [업데이트] 버튼을 누르기 전, 사이드바의 유효성 검사 결과를 다시 확인
if not is_all_input_valid:
    st.error("❗ 사이드바의 입력값을 확인해주세요. 목표 총 시간과 과목별 시간의 합계가 일치하지 않는 학년이 있습니다.")

# [업데이트] disabled 속성을 사용하여 조건이 안 맞으면 버튼을 비활성화
if st.button("시간표 자동 생성 🚀", use_container_width=True, type="primary", disabled=not is_all_input_valid):
    # 이 부분은 is_all_input_valid가 True일 때만 실행됩니다.
    
    hours_per_grade = [st.session_state.target_hours.get(g, 0) for g in range(1, 4)]
    max_periods = int(max(hours_per_grade)) if hours_per_grade else 0
    
    if max_periods == 0:
        st.warning("⚠️ 목표 수업 시수를 1시간 이상 입력해주세요.")
        st.dataframe(initialize_timetable(1), use_container_width=True)
    else:
        with st.spinner(f"최대 {max_periods}교시를 기준으로 시간표를 생성합니다..."):
            final_timetable, unscheduled = generate_auto_timetable_compact(st.session_state.subject_hours, max_periods)

            st.subheader("📆 자동 생성 결과")
            st.dataframe(final_timetable, use_container_width=True)
            
            # 후처리 결과 표시 로직 (기존과 동일)
            if unscheduled:
                st.error("❗ 다음 과목들은 배정하지 못했습니다. 제약 조건이 너무 많거나 시간이 부족할 수 있습니다.")
                failed_summary = { f"{g}학년 {s}":0 for g,s in unscheduled }
                for g, s in unscheduled: failed_summary[f"{g}학년 {s}"] += 1
                for key, count in failed_summary.items(): st.write(f"- {key}: {count} 시간")
            else:
                st.success("🎉 모든 과목이 성공적으로 시간표에 배정되었습니다!")
else:
    # 페이지 초기 로딩 시 보여주는 화면
    if is_all_input_valid:
        max_p = int(max(st.session_state.target_hours.values())) if st.session_state.target_hours else 1
        st.info(f"현재 설정된 최대 교시는 **{max_p}교시**입니다. 사이드바에서 정보를 입력하고 생성 버튼을 눌러주세요.")
        st.dataframe(initialize_timetable(max_p), use_container_width=True)