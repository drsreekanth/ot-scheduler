import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time

st.title("Smart OT Scheduler")

# Load or create schedule
try:
    df = pd.read_csv("schedule.csv")
except:
    df = pd.DataFrame(columns=["Date", "Start", "End", "OT", "Surgeon", "Patient", "Procedure", "Duration"])

# --- BASIC DURATION MAP (you can expand this) ---
DURATION_MAP = {
    "mastectomy": 120,
    "lap chole": 60,
    "hernia": 90,
    "thyroidectomy": 150
}

def get_duration(procedure):
    for key in DURATION_MAP:
        if key in procedure.lower():
            return DURATION_MAP[key]
    return 90  # default

# --- FIND NEXT AVAILABLE SLOT ---
def find_slot(df, duration):
    ots = ["OT1", "OT2", "OT3"]
    start_day = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    end_day = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)

    for ot in ots:
        current_time = start_day

        ot_cases = df[(df["OT"] == ot) & (df["Date"] == str(start_day.date()))]
        ot_cases = ot_cases.sort_values(by="Start")

        for _, case in ot_cases.iterrows():
            case_start = datetime.strptime(case["Start"], "%H:%M")
            case_end = datetime.strptime(case["End"], "%H:%M")

            if current_time + timedelta(minutes=duration) <= case_start:
                return ot, current_time

            current_time = max(current_time, case_end)

        if current_time + timedelta(minutes=duration) <= end_day:
            return ot, current_time

    return None, None

# --- INPUT ---
st.subheader("Add Case (Auto Scheduling)")

patient = st.text_input("Patient Name")
procedure = st.text_input("Procedure")
surgeon = st.text_input("Surgeon")

if st.button("Find Slot & Schedule"):
    if patient and procedure and surgeon:
        duration = get_duration(procedure)
        ot, start_time = find_slot(df, duration)

        if ot:
            end_time = start_time + timedelta(minutes=duration)

            new_entry = {
                "Date": str(start_time.date()),
                "Start": start_time.strftime("%H:%M"),
                "End": end_time.strftime("%H:%M"),
                "OT": ot,
                "Surgeon": surgeon,
                "Patient": patient,
                "Procedure": procedure,
                "Duration": duration
            }

            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            df.to_csv("schedule.csv", index=False)

            st.success(f"Scheduled in {ot} from {new_entry['Start']} to {new_entry['End']}")
        else:
            st.error("No available slot today")
    else:
        st.warning("Fill all fields")

# --- DISPLAY ---
st.subheader("Today's Schedule")
today = str(datetime.now().date())
today_df = df[df["Date"] == today]

st.dataframe(today_df.sort_values(by=["OT", "Start"]))