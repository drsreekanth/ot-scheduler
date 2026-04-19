import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.title("OT Scheduling App (Smart Version)")

# Load or create schedule
try:
    df = pd.read_csv("schedule.csv")
except:
    df = pd.DataFrame(columns=["Date", "Start", "End", "OT", "Surgeon", "Procedure", "Duration"])

st.subheader("Add Surgery")

date = st.date_input("Date")
start_time = st.time_input("Start Time")
duration = st.number_input("Duration (minutes)", min_value=15, max_value=600, step=15)

ot = st.selectbox("Operation Theatre", ["OT1", "OT2", "OT3"])
surgeon = st.text_input("Surgeon Name")
procedure = st.text_input("Procedure")

# Calculate end time
start_dt = datetime.combine(date, start_time)
end_dt = start_dt + timedelta(minutes=duration)

if st.button("Add to Schedule"):
    new_entry = {
        "Date": str(date),
        "Start": start_dt.strftime("%H:%M"),
        "End": end_dt.strftime("%H:%M"),
        "OT": ot,
        "Surgeon": surgeon,
        "Procedure": procedure,
        "Duration": duration
    }

    conflicts = []

    for _, row in df.iterrows():
        if row["Date"] != str(date):
            continue

        existing_start = datetime.strptime(row["Start"], "%H:%M")
        existing_end = datetime.strptime(row["End"], "%H:%M")

        new_start = datetime.strptime(new_entry["Start"], "%H:%M")
        new_end = datetime.strptime(new_entry["End"], "%H:%M")

        overlap = (new_start < existing_end) and (new_end > existing_start)

        same_ot = row["OT"] == ot
        same_surgeon = row["Surgeon"].lower() == surgeon.lower()

        if overlap and (same_ot or same_surgeon):
            conflicts.append(row)

    if conflicts:
        st.error("⚠️ Conflict detected with existing schedule!")
        st.dataframe(pd.DataFrame(conflicts))
    else:
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv("schedule.csv", index=False)
        st.success("Surgery added successfully")

st.subheader("Today's Schedule")

today = str(datetime.today().date())
today_df = df[df["Date"] == today]

st.dataframe(today_df.sort_values(by="Start"))

st.subheader("Full Schedule")
st.dataframe(df.sort_values(by=["Date", "Start"]))