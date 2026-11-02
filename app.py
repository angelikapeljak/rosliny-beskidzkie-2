import random
import pandas as pd
import streamlit as st

st.title("🌱 Rozpoznaj Beskidzkie Rośliny")


# 1. Load data (cached for performance)
@st.cache_data
def load_data():
    df = pd.read_csv("plants.csv")
    # Filter out rows that don't have an image assigned
    df = df.dropna(subset=["image_file"])
    return df

df = load_data()
total_plants = len(df)

# Display total number of plants in the database
st.sidebar.write(f"Liczba roślin w bazie: **{total_plants}**")

# 2. Initialize session state variables
if "seen_plants" not in st.session_state:
  st.session_state.seen_plants = []
  st.session_state.score = 0
  st.session_state.current_plant = None
  st.session_state.options = None
  st.session_state.answered = False


# Helper function to load a new unshown question
def get_next_question():
  # Find plants that haven't been seen yet
  unseen_df = df[~df.index.isin(st.session_state.seen_plants)]

  if len(unseen_df) == 0:
    # All plants have been shown!
    st.session_state.current_plant = None
    return

  # Pick a random unseen plant
  plant_row = unseen_df.sample(1).iloc[0]
  st.session_state.seen_plants.append(plant_row.name)
  st.session_state.current_plant = plant_row

  correct_name = plant_row["name"]

  # Pick 3 wrong options from the rest of the dataset
  wrong_options = df[df["name"] != correct_name].sample(
      min(3, len(df) - 1)
  )

  # Combine and shuffle options
  options = list(wrong_options["name"]) + [correct_name]
  random.shuffle(options)
  st.session_state.options = options
  st.session_state.answered = False


# Trigger first question if none is active and we haven't finished
if st.session_state.current_plant is None and len(
    st.session_state.seen_plants
) < len(df):
  get_next_question()

# 3. Check if quiz is finished
if len(st.session_state.seen_plants) >= total_plants and (
    st.session_state.current_plant is None
):
  st.balloons()
  st.success("🎉 You've gone through all the plants in the database!")
  st.metric(
      label="Final Score",
      value=f"{st.session_state.score} / {total_plants}",
  )

  if st.button("🔄 Restart Quiz"):
    st.session_state.seen_plants = []
    st.session_state.score = 0
    st.session_state.current_plant = None
    st.rerun()

elif st.session_state.current_plant is not None:
  plant = st.session_state.current_plant
  img_path = f"images/{plant['image_file']}"

  # Progress bar / counter in sidebar
  current_progress = len(st.session_state.seen_plants)
  st.sidebar.progress(
      current_progress / total_plants,
      text=(
          f"Progress: {current_progress}/{total_plants} (Score:"
          f" {st.session_state.score})"
      ),
  )

  # Display the image
  try:
    st.image(img_path, width=400)
  except Exception:
    st.warning(
        f"Nie można załadować zdjęcia. Sprawdź ścieżkę w pliku plants.csv."
    )

  # Quiz Form / Options
  with st.form("quiz_form"):
    choice = st.radio("Wybierz odpowiedź:", st.session_state.options, index=None)
    submitted = st.form_submit_button("Sprawdź")

  if submitted:
    st.session_state.answered = True
    if choice == plant["name"]:
      st.session_state.score += 1
      st.success("Poprawnie! 🎉")
    else:
      st.error(f"Błąd! To jest **{plant['name']}**.")

  # Next Question Button
  if st.session_state.answered:
    if st.button("Następna Roślina ➡️"):
      get_next_question()
      st.rerun()
