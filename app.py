import os
import random
import pandas as pd
import streamlit as st

st.title("🌱 Rozpoznaj Beskidzkie Rośliny")


def get_image_path(pid: str) -> str | None:
  """Returns the exact path for {pid}.jpg or {pid}.jpeg if it exists."""
  for ext in (".jpg", ".jpeg", ".JPG", ".JPEG"):
    path = os.path.join("images", f"{pid}{ext}")
    if os.path.isfile(path):
      return path
  return None


# 1. Load data (cached for performance)
@st.cache_data
def load_data():
  df = pd.read_csv("plants.csv")
  df = df.dropna(subset=["id"])
  df["id"] = df["id"].astype(str).str.removesuffix(".0")

  valid_rows = [
      row for _, row in df.iterrows() if get_image_path(row["id"]) is not None
  ]
  return pd.DataFrame(valid_rows)


df = load_data()
total_plants = len(df)

st.sidebar.write(f"Liczba roślin w bazie: **{total_plants}**")

# 2. Initialize session state variables
if "seen_plants" not in st.session_state:
  st.session_state.seen_plants = []
  st.session_state.score = 0
  st.session_state.current_plant = None
  st.session_state.options = None
  st.session_state.answered = False
  st.session_state.user_choice = None


# Helper function to load a new unshown question
def get_next_question():
  unseen_df = df[~df.index.isin(st.session_state.seen_plants)]

  if len(unseen_df) == 0:
    st.session_state.current_plant = None
    return

  plant_row = unseen_df.sample(1).iloc[0]
  st.session_state.seen_plants.append(plant_row.name)
  st.session_state.current_plant = plant_row

  correct_name = plant_row["name"]
  plant_category = plant_row["category"]

  same_category_df = df[
      (df["category"] == plant_category) & (df["name"] != correct_name)
  ]

  if len(same_category_df) < 3:
    wrong_options = df[df["name"] != correct_name].sample(
        min(3, len(df) - 1)
    )
  else:
    wrong_options = same_category_df.sample(3)

  options = list(wrong_options["name"]) + [correct_name]
  random.shuffle(options)
  st.session_state.options = options
  st.session_state.answered = False
  st.session_state.user_choice = None


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
  st.success("🎉 Przeszedłeś przez wszystkie rośliny w bazie!")
  st.metric(
      label="Wynik końcowy",
      value=f"{st.session_state.score} / {total_plants}",
  )

  if st.button("🔄 Zacznij od nowa"):
    st.session_state.seen_plants = []
    st.session_state.score = 0
    st.session_state.current_plant = None
    st.session_state.user_choice = None
    st.rerun()

elif st.session_state.current_plant is not None:
  plant = st.session_state.current_plant
  pid = str(plant["id"])
  img_path = get_image_path(pid)

  # Progress bar / counter in sidebar
  current_progress = len(st.session_state.seen_plants)
  st.sidebar.progress(
      current_progress / total_plants,
      text=(
          f"Postęp: {current_progress}/{total_plants} (Wynik:"
          f" {st.session_state.score})"
      ),
  )

  try:
    if img_path:
      st.image(img_path, width=400)
    else:
      raise FileNotFoundError
  except Exception:
    st.warning(
        f"Nie można załadować zdjęcia dla ID: {pid}. Sprawdź folder 'images'."
    )

  # Quiz Form / Options
  with st.form("quiz_form"):
    choice = st.radio(
        "Wybierz odpowiedź:",
        st.session_state.options,
        index=None,
        disabled=st.session_state.answered,
    )
    submitted = st.form_submit_button(
        "Sprawdź",
        disabled=st.session_state.answered,
    )

  if submitted and not st.session_state.answered:
    if choice is None:
      st.warning("Najpierw wybierz jedną z odpowiedzi.")
    else:
      st.session_state.answered = True
      st.session_state.user_choice = choice
      if choice == plant["name"]:
        st.session_state.score += 1
      st.rerun()

  # Render feedback and Next Question button persistently once answered
  if st.session_state.answered:
    plant_info = plant.get("info")
    info_text = (
        f"\n\n**Info:** {plant_info}"
        if pd.notna(plant_info) and str(plant_info).strip()
        else ""
    )

    if st.session_state.user_choice == plant["name"]:
      st.success(f"Poprawnie! 🎉 **{plant['name']}** (ID: `{pid}`){info_text}")
    else:
      st.error(f"Błąd! To jest **{plant['name']}** (ID: `{pid}`){info_text}")

    if st.button("Następna Roślina ➡️"):
      get_next_question()
      st.rerun()
