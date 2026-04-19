import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.title("Smart OT Scheduler")

# Load or create schedule
try:
    df = pd.read_csv("schedule.csv")
except:
    df = pd.DataFrame(columns=["Date", "Start", "End", "OT", "Surgeon", "Patient", "Procedure", "Duration"])

# --- DURATION MAP ---
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
    return 90

# --- CONVERT ROW TO DATETIME ---
def get_datetime(date_str, time_str):
    return datetime.strptime(date_str + " " + time_str, "%Y-%m-%d %H:%M")

# --- CHECK OVERLAP ---
def overlaps(start1, end1, start2, end2):
    return start1 < end2 and end1 > start2

# --- FIND SLOT ---
def find_slot(df, duration, surgeon):
    ots = ["OT1", "OT2", "OT3"]

    start_day = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
last_start_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
end_day = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)

for ot in ots:
        current_time = start_day

        ot_cases = df[(df["OT"] == ot) & (df["Date"] == str(start_day.date()))]
        ot_cases = ot_cases.sort_values(by="Start")

for _, case in ot_cases.iterrows():
            case_start = get_datetime(case["Date"], case["Start"])
            case_end = get_datetime(case["Date"], case["End"])

            proposed_end = current_time + timedelta(minutes=duration)
if current_time > last_start_time:
    break
            # Check OT gap
           if proposed_end <= case_start and current_time <= last_start_time:
                # Check surgeon conflict
                surgeon_conflict = False

                for _, s_case in df[df["Date"] == str(start_day.date())].iterrows():
                    s_start = get_datetime(s_case["Date"], s_case["Start"])
                    s_end = get_datetime(s_case["Date"], s_case["End"])

                    if s_case["Surgeon"].lower() == surgeon.lower():
                        if overlaps(current_time, proposed_end, s_start, s_end):
                            surgeon_conflict = True
                            break

                if not surgeon_conflict:
                    return ot, current_time

            current_time = max(current_time, case_end)

        # Check end of day slot
        proposed_end = current_time + timedelta(minutes=duration)
        if proposed_end <= end_day and current_time <= last_start_time:
            surgeon_conflict = False

            for _, s_case in df[df["Date"] == str(start_day.date())].iterrows():
                s_start = get_datetime(s_case["Date"], s_case["Start"])
                s_end = get_datetime(s_case["Date"], s_case["End"])

                if s_case["Surgeon"].lower() == surgeon.lower():
                    if overlaps(current_time, proposed_end, s_start, s_end):
                        surgeon_conflict = True
                        break

            if not surgeon_conflict:
                return ot, current_time

    return None, None

# --- INPUT ---
st.subheader("Auto Schedule Case")

patient = st.text_input("Patient Name")
procedure = st.text_input("Procedure")
surgeon = st.text_input("Surgeon")

if st.button("Find Slot & Schedule"):
    if patient and procedure and surgeon:
        duration = get_duration(procedure)
        ot, start_time = find_slot(df, duration, surgeon)

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
st.subheader("Delete Surgery")

today = str(datetime.now().date())
today_df = df[df["Date"] == today].reset_index()

if not today_df.empty:
    # Create a readable label for each case
    today_df["Label"] = today_df.apply(
        lambda row: f"{row['Start']} | {row['OT']} | {row['Patient']} | {row['Procedure']}",
        axis=1
    )

    selected = st.selectbox("Select case to delete", today_df["Label"])

    if st.button("Delete Selected Case"):
        index_to_delete = today_df[today_df["Label"] == selected]["index"].values[0]

        df = df.drop(index_to_delete)
        df.to_csv("schedule.csv", index=False)

        st.success("Case deleted successfully")
        st.rerun()
else:
    st.info("No cases scheduled today")
